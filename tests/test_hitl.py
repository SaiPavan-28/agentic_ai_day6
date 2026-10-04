import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from agent import get_agent_app, extract_text, escalate_ticket

def test_1_sensitive_action_pauses():
    checkpointer = MemorySaver()
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(
        content="",
        tool_calls=[{"name": "escalate_ticket", "args": {"ticket_title": "Auth outage", "severity": "High"}, "id": "call_1"}]
    )
    
    app = get_agent_app(checkpointer=checkpointer, custom_llm=mock_llm)
    config = {"configurable": {"thread_id": "hitl-thread-1"}}
    
    with patch.object(escalate_ticket, "func") as mock_escalate:
        app.invoke({"messages": [HumanMessage(content="Auth is failing completely")]}, config)
        state = app.get_state(config)
        
        # Verify execution paused at sensitive_tools
        assert state.next == ("sensitive_tools",)
        # Verify escalate_ticket NOT executed yet
        mock_escalate.assert_not_called()

def test_2_approval():
    checkpointer = MemorySaver()
    mock_llm = MagicMock()
    
    def llm_side_effect(msgs):
        if len(msgs) > 2:
            return AIMessage(content="Escalation ticket created successfully and team paged.")
        return AIMessage(
            content="",
            tool_calls=[{"name": "escalate_ticket", "args": {"ticket_title": "Database outage", "severity": "CRITICAL"}, "id": "call_2"}]
        )
    mock_llm.invoke.side_effect = llm_side_effect
    
    app = get_agent_app(checkpointer=checkpointer, custom_llm=mock_llm)
    config = {"configurable": {"thread_id": "hitl-thread-2"}}
    
    app.invoke({"messages": [HumanMessage(content="DB down")]}, config)
    state = app.get_state(config)
    assert state.next == ("sensitive_tools",)
    
    # Approve pending action
    res = app.invoke(None, config)
    final_text = extract_text(res["messages"][-1].content)
    assert "Escalation ticket created successfully" in final_text

def test_3_rejection():
    checkpointer = MemorySaver()
    mock_llm = MagicMock()
    
    def llm_side_effect(msgs):
        if len(msgs) > 2:
            # Verify rejection reason reached agent
            last_msg = msgs[-1]
            assert "Rejected by engineer: False alarm" in str(last_msg.content)
            return AIMessage(content="Understood. Escalation cancelled per engineer request.")
        return AIMessage(
            content="",
            tool_calls=[{"name": "escalate_ticket", "args": {"ticket_title": "Flaky test", "severity": "Low"}, "id": "call_3"}]
        )
    mock_llm.invoke.side_effect = llm_side_effect
    
    app = get_agent_app(checkpointer=checkpointer, custom_llm=mock_llm)
    config = {"configurable": {"thread_id": "hitl-thread-3"}}
    
    with patch.object(escalate_ticket, "func") as mock_escalate:
        app.invoke({"messages": [HumanMessage(content="Escalate test failure")]}, config)
        state = app.get_state(config)
        assert state.next == ("sensitive_tools",)
        
        # Reject with reason
        last_msg = state.values["messages"][-1]
        tool_messages = [ToolMessage(content="Rejected by engineer: False alarm", tool_call_id=last_msg.tool_calls[0]["id"])]
        app.update_state(config, {"messages": tool_messages}, as_node="sensitive_tools")
        
        res = app.invoke(None, config)
        
        # Verify escalate_ticket was NOT executed
        mock_escalate.assert_not_called()
        # Verify workflow resumed appropriately
        assert "Escalation cancelled per engineer request" in extract_text(res["messages"][-1].content)

def test_4_restart_persistence():
    checkpointer = MemorySaver()
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(
        content="",
        tool_calls=[{"name": "escalate_ticket", "args": {"ticket_title": "Memory leak", "severity": "High"}, "id": "call_4"}]
    )
    
    app1 = get_agent_app(checkpointer=checkpointer, custom_llm=mock_llm)
    config = {"configurable": {"thread_id": "hitl-thread-4"}}
    app1.invoke({"messages": [HumanMessage(content="Memory leaking")]}, config)
    
    # Recreate app context / restart
    app2 = get_agent_app(checkpointer=checkpointer, custom_llm=mock_llm)
    state = app2.get_state(config)
    
    assert state.next == ("sensitive_tools",)
    assert len(state.values["messages"]) > 0

def test_5_mixed_tool_calls():
    checkpointer = MemorySaver()
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(
        content="",
        tool_calls=[
            {"name": "query_service_health", "args": {"service_name": "payments"}, "id": "call_safe"},
            {"name": "escalate_ticket", "args": {"ticket_title": "Payments down", "severity": "CRITICAL"}, "id": "call_sens"}
        ]
    )
    
    app = get_agent_app(checkpointer=checkpointer, custom_llm=mock_llm)
    config = {"configurable": {"thread_id": "hitl-thread-5"}}
    
    app.invoke({"messages": [HumanMessage(content="Check payments and escalate")]}, config)
    state = app.get_state(config)
    
    # Because ANY call is sensitive, execution pauses for approval
    assert state.next == ("sensitive_tools",)

def test_6_mixed_call_rejection():
    checkpointer = MemorySaver()
    mock_llm = MagicMock()
    
    def llm_side_effect(msgs):
        if len(msgs) > 2:
            return AIMessage(content="Continuing without performing sensitive action.")
        return AIMessage(
            content="",
            tool_calls=[
                {"name": "query_service_health", "args": {"service_name": "auth"}, "id": "c1"},
                {"name": "escalate_ticket", "args": {"ticket_title": "Auth timeout", "severity": "High"}, "id": "c2"}
            ]
        )
    mock_llm.invoke.side_effect = llm_side_effect
    
    app = get_agent_app(checkpointer=checkpointer, custom_llm=mock_llm)
    config = {"configurable": {"thread_id": "hitl-thread-6"}}
    
    with patch.object(escalate_ticket, "func") as mock_escalate:
        app.invoke({"messages": [HumanMessage(content="Check and escalate")]}, config)
        state = app.get_state(config)
        assert state.next == ("sensitive_tools",)
        
        # Reject mixed tool calls
        last_msg = state.values["messages"][-1]
        tool_messages = [
            ToolMessage(content="Rejected by engineer: Action rejected", tool_call_id=tc["id"])
            for tc in last_msg.tool_calls
        ]
        app.update_state(config, {"messages": tool_messages}, as_node="sensitive_tools")
        
        res = app.invoke(None, config)
        
        # Every pending call received a ToolMessage
        assert len(tool_messages) == 2
        # Sensitive tool never executed
        mock_escalate.assert_not_called()
        assert "Continuing without performing sensitive action" in extract_text(res["messages"][-1].content)
