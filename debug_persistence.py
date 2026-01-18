
import chromadb
from chromadb.config import Settings
from pathlib import Path
import sys
import shutil

def test_persistence():
    test_dir = Path("./test_chroma_db").resolve()
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    print(f"Testing persistence in: {test_dir}")
    print(f"Chroma version: {chromadb.__version__}")
    
    # Try the current method
    print("Initializing using Client(Settings(persist_directory=...))")
    try:
        client = chromadb.Client(Settings(
            persist_directory=str(test_dir),
            anonymized_telemetry=False
        ))
        
        collection = client.create_collection("test_collection")
        collection.add(
            documents=["test_doc"],
            metadatas=[{"source": "test"}],
            ids=["test_1"]
        )
        print("Added document.")
        
        # Check if files exist
        files = list(test_dir.glob("*"))
        print(f"Files in dir: {[f.name for f in files]}")
        
        if not files:
            print("FAILURE: No files created in directory!")
        else:
            print("SUCCESS: Files created.")
            
    except Exception as e:
        print(f"Error: {e}")

    # Clean up
    # shutil.rmtree(test_dir)

if __name__ == "__main__":
    test_persistence()
