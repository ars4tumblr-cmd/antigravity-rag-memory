
from chroma_client import AntigravityRAGClient

def search_everything():
    client = AntigravityRAGClient()
    queries = ["Abahalamaxa", "абабагаламага", "publishing"]
    
    for q in queries:
        print(f"\nSearching for '{q}' in ALL projects (God Mode)...")
        results = client.search(query=q, project_id="*")
        
        if results:
            print(f"✅ Found {len(results)} matches for '{q}':")
            for r in results:
                print(f"- [{r['metadata'].get('project_id')}] {r['content']} (Scope: {r['metadata'].get('scope')})")
        else:
            print(f"❌ Nothing found for '{q}'.")

if __name__ == "__main__":
    search_everything()
