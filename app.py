import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import gradio as gr
from langchain_core.messages import HumanMessage, ToolMessage
from agent import get_agent_app

app = FastAPI()
agent_app = get_agent_app()

class ChatRequest(BaseModel):
    thread_id: str
    message: str

class ChatResponse(BaseModel):
    status: str
    pending_action: dict | None = None
    response: str | None = None

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    result = agent_app.invoke({"messages": [HumanMessage(content=req.message)]}, config)
    
    state = agent_app.get_state(config)
    if state.next and "sensitive_tools" in state.next:
        last_msg = state.values["messages"][-1]
        sensitive_calls = [tc for tc in last_msg.tool_calls if tc["name"] == "escalate_ticket"]
        return ChatResponse(
            status="AWAITING_APPROVAL",
            pending_action={"calls": sensitive_calls}
        )
        
    return ChatResponse(status="COMPLETED", response=result["messages"][-1].content)

class ApproveRequest(BaseModel):
    thread_id: str
    approved: bool
    rejection_reason: str = ""

@app.post("/approve")
def approve_endpoint(req: ApproveRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    state = agent_app.get_state(config)
    
    if not state.next or "sensitive_tools" not in state.next:
        raise HTTPException(status_code=400, detail="No pending actions for this thread.")
        
    if req.approved:
        result = agent_app.invoke(None, config)
        return {"status": "RESOLVED", "response": result["messages"][-1].content}
    else:
        last_msg = state.values["messages"][-1]
        tool_messages = []
        for tc in last_msg.tool_calls:
            tool_messages.append(ToolMessage(
                content=f"Rejected by engineer: {req.rejection_reason}",
                tool_call_id=tc["id"]
            ))
        agent_app.update_state(config, {"messages": tool_messages}, as_node="sensitive_tools")
        result = agent_app.invoke(None, config)
        return {"status": "REJECTED_AND_RESUMED", "response": result["messages"][-1].content}

def gradio_chat(thread_id, message):
    if not thread_id or not message:
        return "Please provide both Thread ID and Incident Description.", "", gr.update(visible=False)
        
    config = {"configurable": {"thread_id": thread_id}}
    result = agent_app.invoke({"messages": [HumanMessage(content=message)]}, config)
    state = agent_app.get_state(config)
    
    if state.next and "sensitive_tools" in state.next:
        last_msg = state.values["messages"][-1]
        calls = [f"{tc['name']}: {tc['args']}" for tc in last_msg.tool_calls if tc["name"] == "escalate_ticket"]
        return f"AWAITING_APPROVAL: Pending escalation -> {calls}", result["messages"][-1].content, gr.update(visible=True)
        
    return "COMPLETED", result["messages"][-1].content, gr.update(visible=False)

def gradio_approve(thread_id):
    if not thread_id:
        return "Thread ID is required.", ""
    config = {"configurable": {"thread_id": thread_id}}
    result = agent_app.invoke(None, config)
    return "RESOLVED", result["messages"][-1].content

def gradio_reject(thread_id, reason):
    if not thread_id:
        return "Thread ID is required.", ""
    config = {"configurable": {"thread_id": thread_id}}
    state = agent_app.get_state(config)
    
    if not state.next or "sensitive_tools" not in state.next:
        return "No pending actions.", ""
        
    last_msg = state.values["messages"][-1]
    tool_messages = []
    for tc in last_msg.tool_calls:
        tool_messages.append(ToolMessage(
            content=f"Rejected by engineer: {reason}",
            tool_call_id=tc["id"]
        ))
    agent_app.update_state(config, {"messages": tool_messages}, as_node="sensitive_tools")
    result = agent_app.invoke(None, config)
    return "REJECTED_AND_RESUMED", result["messages"][-1].content

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
