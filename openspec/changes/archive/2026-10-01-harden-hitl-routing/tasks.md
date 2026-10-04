# Tasks: harden-hitl-routing

- [x] Update `route_tools` in `agent.py` to route to `sensitive_tools` if ANY tool call is sensitive
- [x] Update `service_approve` in `app.py` to generate `ToolMessage` for every tool call on rejection
- [x] Add regression tests for mixed safe+sensitive tool calls in `tests/test_hitl.py`
- [x] Add regression tests for mixed tool call rejection in `tests/test_hitl.py`
