# Autonomous Incident Triage Agent

This is an autonomous LangGraph agent powered by Gemini, a Supabase pgvector RAG system, and Human-in-the-Loop (HITL) execution.

## Deployment to Render

To deploy this agent to Render's free tier:

1. Commit all your changes and push to a GitHub repository.
2. In the Render Dashboard, create a **New Blueprint** or **New Web Service**.
3. Connect your GitHub repository.
4. Set the Instance Type to **Free**.
5. Set `PYTHON_VERSION` to `3.11.9`.
6. Add the following environment variables (do not commit them to Git):
   - `GEMINI_API_KEY`: Your Google AI Studio API key.
   - `DATABASE_URL`: Your Supabase Postgres transaction pooler URL (port 6543) with `?sslmode=require`.

### Free-tier Notes
- **Spin-down**: Render's free tier spins down the web service after 15 minutes of inactivity.
- **Cold starts**: Because of the spin-down, the next request might take 30-60 seconds to cold start.
- **State persistence**: Since the agent uses a Postgres checkpointer (`PostgresSaver`) running on Supabase, any paused approval (Human-in-the-Loop) will perfectly survive a cold start! You can leave an incident escalated, go to sleep, the server will spin down, and you can approve it the next day when the server wakes up.
