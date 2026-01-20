
import chromadb
from pathlib import Path
import sys
import shutil

def verify_fix():
    # Define a test directory separate from the main one to avoid messing up real data
    test_dir = Path("./verify_persistence_db").resolve()
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    print(f"Verifying persistence in: {test_dir}")
    print(f"Chroma version: {chromadb.__version__}")
    
    try:
        # The Fix: Use PersistentClient
        print("Initializing using PersistentClient(path=...)")
        client = chromadb.PersistentClient(path=str(test_dir))
        
        collection = client.create_collection("verification_collection")
        collection.add(
            documents=["verification_doc"],
            metadatas=[{"source": "verification"}],
            ids=["verify_1"]
        )
        print("Added document.")
        
        # Check if files exist
        files = list(test_dir.glob("**/*"))
        # Filter out directories
        files = [f for f in files if f.is_file()]
        
        print(f"Found {len(files)} files in storage.")
        if not files:
            print("FAILURE: No files created in directory!")
        else:
            print("SUCCESS: Files created. Persistence is working.")
            for f in files[:3]:
                print(f" - {f.name}")
            if len(files) > 3:
                print(" ... and more")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    # Clean up (optional, maybe keep it to inspect manually if needed, but for auto script usually clean up)
    # shutil.rmtree(test_dir)

if __name__ == "__main__":
    verify_fix()
