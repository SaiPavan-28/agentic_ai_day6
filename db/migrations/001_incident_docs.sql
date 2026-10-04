CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS incident_docs (
    id SERIAL PRIMARY KEY,
    content TEXT,
    metadata JSONB,
    embedding VECTOR(768)
);
CREATE UNIQUE INDEX IF NOT EXISTS incident_docs_content_hash_idx ON incident_docs (md5(content));

CREATE OR REPLACE FUNCTION match_incident_docs (
  query_embedding vector(768),
  match_count int DEFAULT null,
  filter jsonb DEFAULT '{}'
) RETURNS TABLE (
  id int,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    incident_docs.id,
    incident_docs.content,
    incident_docs.metadata,
    1 - (incident_docs.embedding <=> query_embedding) AS similarity
  FROM incident_docs
  WHERE incident_docs.metadata @> filter
  ORDER BY incident_docs.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
