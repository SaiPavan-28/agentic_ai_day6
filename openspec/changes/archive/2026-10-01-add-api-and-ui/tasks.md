# Tasks: add-api-and-ui

- [x] Create shared service layer functions `service_chat` and `service_approve` in `app.py`
- [x] Implement FastAPI endpoints `POST /chat` and `POST /approve`
- [x] Mount Gradio UI at `/` in `app.py`
- [x] Implement HTTP 400 response when approving a thread without pending action
- [x] Create tests in `tests/test_api.py` covering endpoints and shared service integration
