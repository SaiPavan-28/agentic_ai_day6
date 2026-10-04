# Delta for hitl-approval

## ADDED Requirements

### Requirement: Sensitive tool interruption
The system MUST interrupt execution and pause before executing any sensitive tool such as `escalate_ticket`.

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
