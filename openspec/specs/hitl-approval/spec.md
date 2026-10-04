# Spec: hitl-approval

## Purpose
Enforce Human-in-the-Loop approval for sensitive incident escalation actions.

## Requirements

### Requirement: Sensitive tool interruption
The agent MUST pause before executing a model message if ANY of its tool calls is sensitive, and MUST NOT execute any sensitive tool without explicit approval for that thread.

#### Scenario: Escalation pauses
- GIVEN an incident prompt that causes the LLM to request `escalate_ticket`
- WHEN the agent graph runs
- THEN execution pauses before `sensitive_tools` node
- AND state status is set to `AWAITING_APPROVAL`
- AND `escalate_ticket` is NOT executed

#### Scenario: Approval resumes execution
- GIVEN a thread paused before `sensitive_tools`
- WHEN an engineer explicitly approves the pending action
- THEN `escalate_ticket` executes exactly once
- AND the graph resumes to produce the final response

#### Scenario: Rejection stops execution
- GIVEN a thread paused before `sensitive_tools`
- WHEN an engineer rejects the action with a reason
- THEN `escalate_ticket` is NOT executed
- AND a `ToolMessage` with the rejection reason is passed to the agent
- AND the graph resumes reasoning safely

#### Scenario: Approval state survives application restart
- GIVEN a thread paused before `sensitive_tools`
- WHEN the application process restarts
- THEN querying the thread state shows approval is still pending and can be resumed

#### Scenario: Mixed safe and sensitive tool calls
- GIVEN the model returns `[query_service_health, escalate_ticket]` in a single message
- WHEN the agent graph runs `route_tools`
- THEN execution pauses for approval at `sensitive_tools`
- AND the pending approval action lists `escalate_ticket`

#### Scenario: Rejection answers every pending tool call
- GIVEN a paused thread containing multiple tool calls in the pending message
- WHEN an engineer rejects the action with a reason
- THEN each tool call receives a corresponding `ToolMessage`
- AND no sensitive tool executes
- AND the agent resumes reasoning with the rejection messages
