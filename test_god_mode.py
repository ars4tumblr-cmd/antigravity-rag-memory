
import unittest
import uuid
from chroma_client import AntigravityRAGClient

class TestGodMode(unittest.TestCase):
    def setUp(self):
        self.client = AntigravityRAGClient()
        self.test_id = str(uuid.uuid4())[:8]
        self.secret_project = f"SECRET_PROJECT_{self.test_id}"
        self.secret_data = f"Super Secret Data {self.test_id}"
        
        # Store data in a completely different project
        print(f"\n[SETUP] Hiding secret '{self.secret_data}' in '{self.secret_project}' (local scope)")
        self.client.store(
            content=self.secret_data,
            project_id=self.secret_project,
            scope="local"
        )

    def test_god_mode_search(self):
        """Verify that we can find the secret data using project_id='*'"""
        print(f"[TEST] Attempting to find secret using God Mode (project_id='*')")
        
        results = self.client.search(
            query=f"Super Secret {self.test_id}", 
            project_id="*"
        )
        
        found = any(r['content'] == self.secret_data for r in results)
        if found:
            print("✅ FOUND! God mode successfully retrieved cross-project local data.")
        else:
            print("❌ FAILED. God mode did not find the data.")
            
        self.assertTrue(found, "God Mode failed to find hidden local data")

if __name__ == '__main__':
    unittest.main()
