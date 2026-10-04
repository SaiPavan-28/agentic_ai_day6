import os
import hashlib
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import psycopg
from psycopg.types.json import Jsonb
from pgvector.psycopg import register_vector

load_dotenv()

docs = [
    {"content": "Auth service 504 timeouts: Check Redis cache for token refresh. Restart auth pods if Redis is healthy.", "metadata": {"service": "auth"}},
    {"content": "Database high latency: Check for long-running queries in pg_stat_activity. Kill queries older than 5 minutes.", "metadata": {"service": "database"}},
    {"content": "Payment gateway failures: Verify Stripe API keys and connection. Failover to secondary gateway if Stripe is down.", "metadata": {"service": "payments"}},
]

def get_hash(content: str) -> str:
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def seed():
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        task_type="RETRIEVAL_DOCUMENT",
        output_dimensionality=768,
    )
    
    db_url = os.environ["DATABASE_URL"]
    
    with psycopg.connect(db_url) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            for doc in docs:
                emb = embeddings.embed_query(doc["content"])
                # We use ON CONFLICT to make it idempotent, requiring the unique index
                cur.execute("""
                    INSERT INTO incident_docs (content, metadata, embedding)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (md5(content)) DO NOTHING
                """, (doc["content"], Jsonb(doc["metadata"]), emb))
        conn.commit()
    print("Seeding complete.")

if __name__ == "__main__":
    seed()
