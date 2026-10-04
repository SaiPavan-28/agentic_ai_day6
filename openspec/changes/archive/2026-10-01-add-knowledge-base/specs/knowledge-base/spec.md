# Delta for knowledge-base

## ADDED Requirements

### Requirement: Runbook storage
The system SHALL store runbooks in the `incident_docs` table with text content, JSON metadata, and a 768-dimension vector embedding.

#### Scenario: Schema matches embedding size
- GIVEN the SQL migration `001_incident_docs.sql` has been applied
- WHEN a 768-dimension vector embedding is inserted into `incident_docs`
- THEN the insert operation succeeds

### Requirement: Idempotent seeding
Running `seed_rag.py` multiple times SHALL NOT create duplicate runbook entries in the database.

#### Scenario: Re-running the seed script
- GIVEN runbooks have already been inserted into the database
- WHEN `seed_rag.py` is executed again
- THEN existing records are preserved without duplication using `ON CONFLICT (md5(content)) DO NOTHING`

### Requirement: Semantic retrieval function
The database SHALL expose `match_incident_docs(query_embedding, match_count, filter)` to return relevant runbooks ordered by cosine similarity.

#### Scenario: Filter by metadata
- GIVEN runbooks for auth, database, and payment services stored in `incident_docs`
- WHEN `match_incident_docs` is called with a service filter JSONB object
- THEN only matching runbooks conforming to the metadata filter are returned
