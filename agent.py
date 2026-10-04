import os
from typing import Annotated, TypedDict, Literal
from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
import psycopg
from pgvector.psycopg import register_vector
from pydantic import BaseModel

def extract_text(content: str | list | None) -> str:
    """Normalises string or list-structured model message content to plain text."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
        return "".join(parts)
    return str(content)

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

@tool
def query_service_health(service_name: str) -> str:
    """Check the current health of a backend service."""
    health_status = {
        "auth": "DEGRADED (504 Gateway Timeout)",
        "database": "HEALTHY",
        "payments": "HEALTHY"
    }
    return health_status.get(service_name.lower(), "Service not found.")

@tool
def search_remediation_runbooks(query: str) -> str:
    """Search internal runbooks for remediation steps."""
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        task_type="RETRIEVAL_QUERY",
        output_dimensionality=768,
    )
    db_url = os.environ["DATABASE_URL"]
    
    emb = embeddings.embed_query(query)
    
    with psycopg.connect(db_url) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT content FROM match_incident_docs(%s::vector, 2, '{}')
            """, (emb,))
            rows = cur.fetchall()
            if not rows:
                return "No relevant runbooks found."
            return "\n\n".join(row[0] for row in rows)

@tool
def escalate_ticket(ticket_title: str, severity: str) -> str:
    """CRITICAL: Escalate the incident by opening a ticket and paging the on-call team."""
    return f"Ticket created: {ticket_title} (Severity: {severity})"

tools = [query_service_health, search_remediation_runbooks, escalate_ticket]

def get_agent_app(checkpointer=None, custom_llm=None):
    active_llm = custom_llm if custom_llm is not None else ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite").bind_tools(tools)

    def agent_node(state: AgentState):
        prompt = (
            "You are an Autonomous Incident Triage Agent. When an engineer describes an incident, "
            "you MUST first check the health of the affected services using query_service_health. "
            "Then, search runbooks for matching remediation steps using search_remediation_runbooks. "
            "If the service is degraded or requires manual intervention/escalation, "
            "you MUST invoke the escalate_ticket tool to propose the escalation. "
            "Do not ask for approval in text instead of calling escalate_ticket; "
            "calling the escalate_ticket tool will automatically submit the escalation for human engineer approval before execution."
        )
        response = active_llm.invoke([SystemMessage(content=prompt)] + state["messages"])
        return {"messages": [response]}

    def route_tools(state: AgentState) -> Literal["safe_tools", "sensitive_tools", "__end__"]:
        last_message = state["messages"][-1]
        if not last_message.tool_calls:
            return END
        
        # Check if ANY tool call is sensitive
        is_sensitive = any(tc["name"] == "escalate_ticket" for tc in last_message.tool_calls)
        return "sensitive_tools" if is_sensitive else "safe_tools"

    def execute_safe_tools(state: AgentState):
        last_message = state["messages"][-1]
        results = []
        for tc in last_message.tool_calls:
            if tc["name"] == "query_service_health":
                res = query_service_health.invoke(tc["args"])
                results.append(ToolMessage(content=str(res), tool_call_id=tc["id"]))
            elif tc["name"] == "search_remediation_runbooks":
                res = search_remediation_runbooks.invoke(tc["args"])
                results.append(ToolMessage(content=str(res), tool_call_id=tc["id"]))
        return {"messages": results}

    def execute_sensitive_tools(state: AgentState):
        last_message = state["messages"][-1]
        results = []
        for tc in last_message.tool_calls:
            if tc["name"] == "escalate_ticket":
                res = escalate_ticket.invoke(tc["args"])
                results.append(ToolMessage(content=str(res), tool_call_id=tc["id"]))
        return {"messages": results}

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("safe_tools", execute_safe_tools)
    workflow.add_node("sensitive_tools", execute_sensitive_tools)
    
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", route_tools)
    workflow.add_edge("safe_tools", "agent")
    workflow.add_edge("sensitive_tools", "agent")
    
    if checkpointer is None:
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            pool = ConnectionPool(db_url, max_size=10, kwargs={"autocommit": True, "prepare_threshold": None})
            checkpointer = PostgresSaver(pool)
            try:
                checkpointer.setup()
            except Exception:
                pass
        else:
            from langgraph.checkpoint.memory import MemorySaver
            checkpointer = MemorySaver()

    app = workflow.compile(checkpointer=checkpointer, interrupt_before=["sensitive_tools"])
    return app

