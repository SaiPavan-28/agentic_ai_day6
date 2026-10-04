import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import gradio as gr
from langchain_core.messages import HumanMessage, ToolMessage
from agent import get_agent_app, extract_text

app = FastAPI()
_agent_app = None

def get_shared_agent_app():
    global _agent_app
    if _agent_app is None:
        _agent_app = get_agent_app()
    return _agent_app

def set_shared_agent_app(agent_instance):
    global _agent_app
    _agent_app = agent_instance

# Shared Service Layer
def service_chat(thread_id: str, message: str, agent_instance=None) -> dict:
    if not thread_id or not message:
        raise ValueError("Both thread_id and message are required.")
    agent = agent_instance or get_shared_agent_app()
    config = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke({"messages": [HumanMessage(content=message)]}, config)
    state = agent.get_state(config)
    
    if state.next and "sensitive_tools" in state.next:
        last_msg = state.values["messages"][-1]
        sensitive_calls = [tc for tc in last_msg.tool_calls if tc["name"] == "escalate_ticket"]
        return {
            "status": "AWAITING_APPROVAL",
            "pending_action": {"calls": sensitive_calls},
            "response": extract_text(result["messages"][-1].content)
        }
    return {
        "status": "COMPLETED",
        "pending_action": None,
        "response": extract_text(result["messages"][-1].content)
    }

def service_approve(thread_id: str, approved: bool, rejection_reason: str = "", agent_instance=None) -> dict:
    if not thread_id:
        raise ValueError("thread_id is required.")
    agent = agent_instance or get_shared_agent_app()
    config = {"configurable": {"thread_id": thread_id}}
    state = agent.get_state(config)
    
    if not state.next or "sensitive_tools" not in state.next:
        raise ValueError("No pending actions for this thread.")
        
    if approved:
        result = agent.invoke(None, config)
        return {
            "status": "RESOLVED",
            "response": extract_text(result["messages"][-1].content)
        }
    else:
        last_msg = state.values["messages"][-1]
        tool_messages = [
            ToolMessage(
                content=f"Rejected by engineer: {rejection_reason}",
                tool_call_id=tc["id"]
            )
            for tc in last_msg.tool_calls
        ]
        agent.update_state(config, {"messages": tool_messages}, as_node="sensitive_tools")
        result = agent.invoke(None, config)
        return {
            "status": "REJECTED_AND_RESUMED",
            "response": extract_text(result["messages"][-1].content)
        }

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

class ChatRequest(BaseModel):
    thread_id: str
    message: str

class ChatResponse(BaseModel):
    status: str
    pending_action: dict | None = None
    response: str | None = None

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    try:
        res = service_chat(req.thread_id, req.message)
        return ChatResponse(**res)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

class ApproveRequest(BaseModel):
    thread_id: str
    approved: bool
    rejection_reason: str = ""

@app.post("/approve")
def approve_endpoint(req: ApproveRequest):
    try:
        return service_approve(req.thread_id, req.approved, req.rejection_reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Gradio Callbacks using Shared Service Layer
def gradio_chat(thread_id, message):
    if not thread_id or not message:
        return "Please provide both Thread ID and Incident Description.", "", gr.update(visible=False)
    try:
        res = service_chat(thread_id, message)
        if res["status"] == "AWAITING_APPROVAL":
            calls = res["pending_action"]["calls"]
            return f"AWAITING_APPROVAL: Pending escalation -> {calls}", res["response"], gr.update(visible=True)
        return res["status"], res["response"], gr.update(visible=False)
    except Exception as e:
        return f"ERROR: {str(e)}", "", gr.update(visible=False)

def gradio_approve(thread_id):
    if not thread_id:
        return "Thread ID is required.", ""
    try:
        res = service_approve(thread_id, approved=True)
        return res["status"], res["response"]
    except Exception as e:
        return f"ERROR: {str(e)}", ""

def gradio_reject(thread_id, reason):
    if not thread_id:
        return "Thread ID is required.", ""
    try:
        res = service_approve(thread_id, approved=False, rejection_reason=reason)
        return res["status"], res["response"]
    except Exception as e:
        return f"ERROR: {str(e)}", ""

with gr.Blocks() as ui:
    gr.Markdown("# Autonomous Incident Triage Agent")
    with gr.Row():
        thread_input = gr.Textbox(label="Thread ID", value="thread-1")
        msg_input = gr.Textbox(label="Incident Description", value="Auth service is timing out")
    trigger_btn = gr.Button("Trigger Triage")
    
    status_label = gr.Label(label="Workflow State")
    agent_log = gr.Markdown(label="Agent Log")
    
    with gr.Group(visible=False) as approval_group:
        gr.Markdown("### Escalation Requires Approval")
        approve_btn = gr.Button("Approve Escalation", variant="primary")
        reason_input = gr.Textbox(label="Rejection Reason", value="Not severe enough")
        reject_btn = gr.Button("Reject Action", variant="stop")
        
    trigger_btn.click(gradio_chat, inputs=[thread_input, msg_input], outputs=[status_label, agent_log, approval_group])
    approve_btn.click(gradio_approve, inputs=[thread_input], outputs=[status_label, agent_log])
    reject_btn.click(gradio_reject, inputs=[thread_input, reason_input], outputs=[status_label, agent_log])

app = gr.mount_gradio_app(app, ui, path="/")

