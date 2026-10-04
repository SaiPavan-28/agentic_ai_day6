import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from app import (
    app,
    set_shared_agent_app,
    service_chat,
    service_approve,
    gradio_chat,
    gradio_approve,
    gradio_reject
)
from agent import get_agent_app

client = TestClient(app)

@pytest.fixture
def mock_agent_service():
    checkpointer = MemorySaver()
    mock_llm = MagicMock()
    test_agent = get_agent_app(checkpointer=checkpointer, custom_llm=mock_llm)
    set_shared_agent_app(test_agent)
    return test_agent, mock_llm

def test_7_api_completed(mock_agent_service):
    _, mock_llm = mock_agent_service
    mock_llm.invoke.return_value = AIMessage(content="Triage complete. Health is normal.")
    
    response = client.post("/chat", json={"thread_id": "api-thread-1", "message": "Database latency"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert "Triage complete" in data["response"]

def test_7_api_awaiting_approval(mock_agent_service):
    _, mock_llm = mock_agent_service
    mock_llm.invoke.return_value = AIMessage(
        content="",
        tool_calls=[{"name": "escalate_ticket", "args": {"ticket_title": "DB latency", "severity": "High"}, "id": "tc1"}]
    )
    
    response = client.post("/chat", json={"thread_id": "api-thread-2", "message": "Escalate DB latency"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "AWAITING_APPROVAL"
    assert len(data["pending_action"]["calls"]) == 1
    assert data["pending_action"]["calls"][0]["name"] == "escalate_ticket"

def test_7_api_approve(mock_agent_service):
    _, mock_llm = mock_agent_service
    
    def llm_side_effect(msgs):
        if len(msgs) > 2:
            return AIMessage(content="Ticket escalated and resolved.")
        return AIMessage(
            content="",
            tool_calls=[{"name": "escalate_ticket", "args": {"ticket_title": "DB latency", "severity": "High"}, "id": "tc1"}]
        )
    mock_llm.invoke.side_effect = llm_side_effect
    
    client.post("/chat", json={"thread_id": "api-thread-3", "message": "Escalate"})
    
    response = client.post("/approve", json={"thread_id": "api-thread-3", "approved": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "RESOLVED"
    assert "Ticket escalated and resolved" in data["response"]

def test_7_api_reject(mock_agent_service):
    _, mock_llm = mock_agent_service
    
    def llm_side_effect(msgs):
        if len(msgs) > 2:
            return AIMessage(content="Escalation rejected. Resumed investigation.")
        return AIMessage(
            content="",
            tool_calls=[{"name": "escalate_ticket", "args": {"ticket_title": "DB latency", "severity": "High"}, "id": "tc1"}]
        )
    mock_llm.invoke.side_effect = llm_side_effect
    
    client.post("/chat", json={"thread_id": "api-thread-4", "message": "Escalate"})
    
    response = client.post("/approve", json={"thread_id": "api-thread-4", "approved": False, "rejection_reason": "Not urgent"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "REJECTED_AND_RESUMED"
    assert "Escalation rejected" in data["response"]

def test_7_api_http_400_no_pending(mock_agent_service):
    response = client.post("/approve", json={"thread_id": "api-thread-5", "approved": True})
    assert response.status_code == 400
    assert "No pending actions" in response.json()["detail"]

def test_8_ui_service_layer_integration(mock_agent_service):
    # Verify that Gradio callbacks use the exact same shared service functions
    with patch("app.service_chat", wraps=service_chat) as spy_service_chat, \
         patch("app.service_approve", wraps=service_approve) as spy_service_approve:
        
        _, mock_llm = mock_agent_service
        mock_llm.invoke.return_value = AIMessage(content="Gradio UI response")
        
        status, log, group_update = gradio_chat("ui-thread-1", "Auth timeout")
        assert spy_service_chat.called
        assert status == "COMPLETED"
        assert "Gradio UI response" in log
        assert group_update.get("visible") is False
        
        # Test gradio approval call invokes service_approve
        mock_llm.invoke.return_value = AIMessage(
            content="",
            tool_calls=[{"name": "escalate_ticket", "args": {"ticket_title": "Auth timeout", "severity": "High"}, "id": "tc1"}]
        )
        service_chat("ui-thread-2", "Escalate Auth")
        
        mock_llm.invoke.side_effect = None
        mock_llm.invoke.return_value = AIMessage(content="Approved via UI")
        
        status, log, group_update = gradio_approve("ui-thread-2")
        assert spy_service_approve.called
        assert status == "RESOLVED"
        assert "Approved via UI" in log
        assert group_update.get("visible") is False

def test_9_gradio_ui_approval_controls_visibility(mock_agent_service):
    _, mock_llm = mock_agent_service
    
    # 1. AWAITING_APPROVAL -> approval_group visible=True
    mock_llm.invoke.return_value = AIMessage(
        content="",
        tool_calls=[{"name": "escalate_ticket", "args": {"ticket_title": "Auth timeout", "severity": "High"}, "id": "tc1"}]
    )
    status_text, log_text, group_update = gradio_chat("vis-thread-1", "Auth timeout")
    assert "AWAITING_APPROVAL" in status_text
    assert group_update.get("visible") is True
    
    # 2. RESOLVED via gradio_approve -> approval_group visible=False
    mock_llm.invoke.return_value = AIMessage(content="Approved escalation response")
    status, log, group_update = gradio_approve("vis-thread-1")
    assert status == "RESOLVED"
    assert "Approved escalation response" in log
    assert group_update.get("visible") is False

    # 3. REJECTED_AND_RESUMED via gradio_reject -> approval_group visible=False
    mock_llm.invoke.return_value = AIMessage(
        content="",
        tool_calls=[{"name": "escalate_ticket", "args": {"ticket_title": "DB issue", "severity": "High"}, "id": "tc2"}]
    )
    gradio_chat("vis-thread-2", "DB issue")
    
    mock_llm.invoke.return_value = AIMessage(content="Rejected response")
    status, log, group_update = gradio_reject("vis-thread-2", "Not severe")
    assert status == "REJECTED_AND_RESUMED"
    assert "Rejected response" in log
    assert group_update.get("visible") is False

