# Spec: triage-ui

## Purpose
Provide a web user interface for engineers to trigger triage and approve or reject sensitive actions.

## Requirements

### Requirement: Gradio web interface
The system SHALL serve an interactive Gradio UI mounted at `/` with inputs for Thread ID and Incident Description, workflow state display, and approval buttons.

#### Scenario: Display pending approval UI
- GIVEN an incident execution that triggers sensitive action approval
- WHEN the Gradio UI callback receives `AWAITING_APPROVAL` status from the shared service
- THEN the approval group UI components become visible with Approve and Reject buttons

#### Scenario: Shared service layer usage
- GIVEN a user interacting through Gradio UI buttons
- WHEN Trigger Triage, Approve, or Reject buttons are clicked
- THEN the callbacks execute the exact same underlying `service_chat` and `service_approve` functions as the REST API
