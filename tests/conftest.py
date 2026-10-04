import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
import pytest
from unittest.mock import patch, MagicMock
from langgraph.checkpoint.memory import MemorySaver

os.environ["DATABASE_URL"] = "postgresql://postgres:password@localhost:5432/test_db"
os.environ["GEMINI_API_KEY"] = "fake-key"

@pytest.fixture(autouse=True)
def mock_postgres():
    with patch("psycopg_pool.ConnectionPool") as mock_pool, \
         patch("langgraph.checkpoint.postgres.PostgresSaver") as mock_saver, \
         patch("psycopg.connect") as mock_connect, \
         patch("seed_rag.register_vector", create=True) as mock_reg1, \
         patch("agent.register_vector", create=True) as mock_reg2:
        
        mock_saver_inst = MagicMock()
        mock_saver.return_value = mock_saver_inst
        
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        
        yield {
            "pool": mock_pool,
            "saver": mock_saver,
            "psycopg_connect": mock_connect,
            "saver_inst": mock_saver_inst,
            "conn": mock_conn,
            "reg1": mock_reg1,
            "reg2": mock_reg2
        }

@pytest.fixture
def memory_checkpointer():
    return MemorySaver()
