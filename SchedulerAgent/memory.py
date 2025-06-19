import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document

load_dotenv()

FAISS_INDEX_PATH = os.getenv("VECTOR_STORE_PATH", "faiss_index")
embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

_vector_store_instance = None

def get_vector_store() -> FAISS:
    global _vector_store_instance
    if _vector_store_instance is not None:
        return _vector_store_instance

    try:
        _vector_store_instance = FAISS.load_local(
            folder_path=FAISS_INDEX_PATH,
            embeddings=embedding_model,
            allow_dangerous_deserialization=True
        )
        print(f"✅ Loaded FAISS index from '{FAISS_INDEX_PATH}'")
    except Exception as e:
        print(f"⚠️ Could not load FAISS index: {e}. Initializing a new, empty index.")
        dummy_documents = [
            Document(
                page_content="I am Debajyoti. Creator of Agent.",
                metadata={"user_id": "owner", "user_name": "Debajyoti"}
            )
        ]
        _vector_store_instance = FAISS.from_documents(
            documents=dummy_documents,
            embedding=embedding_model
        )
        save_vector_store(_vector_store_instance)

    return _vector_store_instance

def save_vector_store(store_to_save: FAISS):
    store_to_save.save_local(FAISS_INDEX_PATH)
    print(f"✅ FAISS index saved to '{FAISS_INDEX_PATH}'")
