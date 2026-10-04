import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from agent import (
    get_agent_app,
    query_service_health,
    search_remediation_runbooks,
    escalate_ticket,
    extract_text
)

def test_extract_text_normalization():
    assert extract_text("hello") == "hello"
    assert extract_text(["hello ", "world"]) == "hello world"
    assert extract_text([{"type": "text", "text": "structured content"}]) == "structured content"
    assert extract_text(None) == ""

def test_query_service_health():
    assert "DEGRADED" in query_service_health.invoke({"service_name": "auth"})
    assert "HEALTHY" in query_service_health.invoke({"service_name": "database"})
    assert "Service not found." in query_service_health.invoke({"service_name": "unknown_service"})

@patch("agent.GoogleGenerativeAIEmbeddings")
def test_search_remediation_runbooks_no_results(mock_embeddings, mock_postgres):
    mock_emb_inst = MagicMock()
    mock_emb_inst.embed_query.return_value = [0.1] * 768
    mock_embeddings.return_value = mock_emb_inst

    mock_conn = mock_postgres["conn"]
    mock_cur = mock_conn.cursor.return_value.__enter__.return_value
    mock_cur.fetchall.return_value = []

    res = search_remediation_runbooks.invoke({"query": "obscure error"})
    assert res == "No relevant runbooks found."

def test_agent_tool_routing_and_health_first():
    checkpointer = MemorySaver()
    mock_llm = MagicMock()
    
    # Simulates agent: first health check, then final text
    def llm_side_effect(msgs):
        if len(msgs) == 2:  # System message + Human message
            return AIMessage(
                content="",
                tool_calls=[{"name": "query_service_health", "args": {"service_name": "auth"}, "id": "tc1"}]
            )
        elif len(msgs) > 2:  # After tool response
            return AIMessage(content="Auth service is degraded. Checked health first.")
    
    mock_llm.invoke.side_effect = llm_side_effect
    app = get_agent_app(checkpointer=checkpointer, custom_llm=mock_llm)
    config = {"configurable": {"thread_id": "thread-health-first"}}
    
    res = app.invoke({"messages": [HumanMessage(content="Auth timing out")]}, config)
    final_content = extract_text(res["messages"][-1].content)
    assert "Auth service is degraded. Checked health first." in final_content

def test_state_persistence_across_instances():
    checkpointer = MemorySaver()
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content="Response saved in state")
    
    app1 = get_agent_app(checkpointer=checkpointer, custom_llm=mock_llm)
    config = {"configurable": {"thread_id": "persistent-thread-1"}}
    app1.invoke({"messages": [HumanMessage(content="Initial message")]}, config)
    
    # Recreate app context with same checkpointer instance
    app2 = get_agent_app(checkpointer=checkpointer, custom_llm=mock_llm)
    state = app2.get_state(config)
    assert len(state.values["messages"]) >= 2
    assert extract_text(state.values["messages"][-1].content) == "Response saved in state"
