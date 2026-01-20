
import sys
import os
import time
import uuid
import unittest
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chroma_client import AntigravityRAGClient

class TestRAGScenarios(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Initialize client once for all tests."""
        cls.client = AntigravityRAGClient()
        print(f"\n[SETUP] RAG Client initialized.")
        
    def setUp(self):
        """Generate unique IDs for test isolation."""
        self.test_id = str(uuid.uuid4())[:8]
        self.project_a = f"project_A_{self.test_id}"
        self.project_b = f"project_B_{self.test_id}"
        
    def test_global_scope_persistence(self):
        """Test that global facts are accessible from any project."""
        fact = f"Global Fact {self.test_id}: Sky is blue."
        print(f"\n[TEST] Storing Global Fact: '{fact}'")
        
        doc_id = self.client.store(
            content=fact,
            project_id="any_project", # project_id required by signature but ignored for global validity? No, metadata stores it.
            scope="global",
            entity_type="fact",
            manual_save=True
        )
        
        # Search without project_id
        results = self.client.search(query=f"Global Fact {self.test_id}", project_id=None)
        self.assertTrue(any(r['content'] == fact for r in results), "Failed to find global fact without project_id")
        
        # Search FROM project B
        results_b = self.client.search(query=f"Global Fact {self.test_id}", project_id=self.project_b)
        self.assertTrue(any(r['content'] == fact for r in results_b), "Failed to find global fact from Project B")
        
        print("✅ Global scope test passed")

    def test_local_scope_isolation(self):
        """Test that local facts are isolated between projects."""
        fact_a = f"Project A Secret {self.test_id}: We use Python."
        
        print(f"\n[TEST] Storing Local Fact for {self.project_a}: '{fact_a}'")
        self.client.store(
            content=fact_a,
            project_id=self.project_a,
            scope="local",
            entity_type="fact"
        )
        
        # Verify Project A can see it
        results_a = self.client.search(query=f"Project A Secret {self.test_id}", project_id=self.project_a)
        self.assertTrue(any(r['content'] == fact_a for r in results_a), "Project A failed to find its own secret")
        
        # Verify Project B CANNOT see it
        results_b = self.client.search(query=f"Project A Secret {self.test_id}", project_id=self.project_b)
        self.assertFalse(any(r['content'] == fact_a for r in results_b), "Project B SHOULD NOT see Project A's secret")
        
        # Verify Global search CANNOT see it (without project_id)
        results_global = self.client.search(query=f"Project A Secret {self.test_id}", project_id=None)
        self.assertFalse(any(r['content'] == fact_a for r in results_global), "Global search SHOULD NOT see local secret")
        
        print("✅ Local scope isolation test passed")

    def test_private_scope_isolation(self):
        """Test that private notes are not returned in standard searches."""
        note = f"Private Note {self.test_id}: My password is 123."
        
        print(f"\n[TEST] Storing Private Note: '{note}'")
        self.client.store(
            content=note,
            project_id=self.project_a,
            scope="private",
            entity_type="fact"
        )
        
        # Search from Project A (standard search defaults)
        # Assuming standard search doesn't explicitly filter OUT private, but logic in server.py/client.py 
        # usually constructs queries. Let's check `search` implementation.
        # In `chroma_client.py`:
        # if project_id: queries (project_id & local) OR (global). 
        # Private is NOT included in this OR logic.
        
        results = self.client.search(query=f"Private Note {self.test_id}", project_id=self.project_a)
        self.assertFalse(any(r['content'] == note for r in results), "Private note should NOT appear in standard project search")
        
        print("✅ Private scope isolation test passed")
        
    def test_cross_session_simulation(self):
        """Simulate a new session by re-instantiating the client."""
        fact = f"Session Persist {self.test_id}: Data survives restart."
        
        self.client.store(content=fact, project_id=self.project_a, scope="global")
        
        print(f"\n[TEST] Simulating client restart...")
        # Force new client instance
        new_client = AntigravityRAGClient()
        
        results = new_client.search(query=f"Session Persist {self.test_id}", project_id=None)
        self.assertTrue(any(r['content'] == fact for r in results), "Data failed to persist across client instances")
        
        print("✅ Cross-session persistence test passed")

if __name__ == '__main__':
    unittest.main()
