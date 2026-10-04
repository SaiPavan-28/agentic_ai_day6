import os
import pytest
from unittest.mock import patch, MagicMock
from seed_rag import seed
from agent import search_remediation_runbooks

def test_schema_and_embedding_dimension():
    # Verify migration file schema expectation for 3072 dimensions
    sql_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "migrations", "001_incident_docs.sql")
    with open(sql_path, "r") as f:
        sql_content = f.read()
    assert "VECTOR(3072)" in sql_content or "vector(3072)" in sql_content
    assert "match_incident_docs" in sql_content

@patch("seed_rag.GoogleGenerativeAIEmbeddings")
def test_seed_idempotent_and_3072_dim(mock_embeddings, mock_postgres):
    mock_emb_inst = MagicMock()
    mock_emb_inst.embed_query.return_value = [0.1] * 3072
    mock_embeddings.return_value = mock_emb_inst
    
    mock_conn = mock_postgres["conn"]
    mock_cur = mock_conn.cursor.return_value.__enter__.return_value
    
    # Run seed
    seed()
    
    # Verify GoogleGenerativeAIEmbeddings was initialized
    mock_embeddings.assert_called_once_with(
        model="models/gemini-embedding-001",
        task_type="RETRIEVAL_DOCUMENT"
    )
    
    # Verify 3 items inserted
    assert mock_cur.execute.call_count == 3
    
    # Verify idempotent SQL construct
    call_args = mock_cur.execute.call_args_list[0][0]
    sql_query = call_args[0]
    assert "ON CONFLICT (md5(content)) DO NOTHING" in sql_query

@patch("agent.GoogleGenerativeAIEmbeddings")
def test_retrieval_and_metadata_filtering(mock_embeddings, mock_postgres):
    mock_emb_inst = MagicMock()
    mock_emb_inst.embed_query.return_value = [0.1] * 3072
    mock_embeddings.return_value = mock_emb_inst

    mock_conn = mock_postgres["conn"]
    mock_cur = mock_conn.cursor.return_value.__enter__.return_value
    mock_cur.fetchall.return_value = [("Auth service runbook content",)]

    res = search_remediation_runbooks.invoke({"query": "Auth issue"})
    assert "Auth service runbook content" in res
    
    # Check that query executed match_incident_docs function
    mock_cur.execute.assert_called_once()
    executed_sql = mock_cur.execute.call_args[0][0]
    assert "match_incident_docs" in executed_sql
