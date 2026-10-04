# Delta for triage-api

## ADDED Requirements

### Requirement: Triage chat endpoint
The API SHALL provide `POST /chat` taking `{thread_id, message}` and returning status `COMPLETED` (with text response) or `AWAITING_APPROVAL` (with pending tool call details).

#### Scenario: Normal triage query completes
- GIVEN a valid thread ID and incident prompt requiring safe tools
- WHEN `POST /chat` is called
- THEN status `COMPLETED` is returned with the agent's triage analysis

#### Scenario: Sensitive action returns awaiting approval
- GIVEN an incident prompt requesting escalation
- WHEN `POST /chat` is called
- THEN status `AWAITING_APPROVAL` is returned containing the pending tool call parameters

### Requirement: Approval endpoint
The API SHALL provide `POST /approve` taking `{thread_id, approved, rejection_reason}` to resume or reject paused escalation workflows.

#### Scenario: Approve pending escalation
- GIVEN a thread currently in state `AWAITING_APPROVAL`
- WHEN `POST /approve` is called with `approved=true`
- THEN status `RESOLVED` is returned and the action executes

#### Scenario: Reject pending escalation
- GIVEN a thread currently in state `AWAITING_APPROVAL`
- WHEN `POST /approve` is called with `approved=false` and a rejection reason
- THEN status `REJECTED_AND_RESUMED` is returned and the action is cancelled

#### Scenario: Approve without pending action returns HTTP 400
- GIVEN a thread ID with no pending approval actions
- WHEN `POST /approve` is called
- THEN the endpoint returns HTTP 400 with detail "No pending actions for this thread."
