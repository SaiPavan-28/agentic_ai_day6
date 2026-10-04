# Delta for triage-agent

## ADDED Requirements

### Requirement: Health-first investigation
The agent SHALL check the health of affected backend services using `query_service_health` before searching runbooks for remediation steps.

#### Scenario: Investigation sequence
- GIVEN an engineer describes an incident affecting a service
- WHEN the agent graph runs
- THEN `query_service_health` is called before `search_remediation_runbooks`

### Requirement: Runbook retrieval
The agent SHALL search internal runbooks using `search_remediation_runbooks` and return relevant remediation steps or "No relevant runbooks found."

#### Scenario: No matching runbooks
- GIVEN a query for an unknown incident pattern
- WHEN `search_remediation_runbooks` is invoked and returns empty results
- THEN the tool returns "No relevant runbooks found."

### Requirement: Unknown service health query
Querying health for an unknown service name SHALL return a structured error message rather than raising an unhandled exception.

#### Scenario: Querying missing service
- GIVEN a query for service "unknown_service"
- WHEN `query_service_health` is executed
- THEN it returns "Service not found."

### Requirement: State persistence across sessions
The agent graph SHALL persist conversation state keyed by `thread_id` so process restarts can reload the conversation.

#### Scenario: Conversation resumption
- GIVEN a conversation stored under thread ID "thread-1"
- WHEN the application process restarts and queries state for "thread-1"
- THEN the existing messages and history are preserved and reloaded

### Requirement: Content normalization
The system SHALL normalize model message content (strings, dicts, or lists) into plain text strings.

#### Scenario: List or dict content normalization
- GIVEN model output containing list-structured or dict content
- WHEN `extract_text` is called
- THEN it returns a unified plain text string
