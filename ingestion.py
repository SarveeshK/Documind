import os
import time
from typing import List
from dotenv import load_dotenv
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone, ServerlessSpec
from langchain_core.documents import Document

# Load environment variables
load_dotenv()

# Configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

class DocumentLoader:
    def __init__(self, directory_path: str):
        self.directory_path = directory_path

    def load_documents(self) -> List[Document]:
        """
        Step 1: Document Loading
        Loads PDFs using Unstructured to extract text & page numbers.
        """
        documents = []
        if not os.path.exists(self.directory_path):
            print(f"Directory {self.directory_path} does not exist.")
            return []

        for filename in os.listdir(self.directory_path):
            if filename.endswith(".pdf"):
                file_path = os.path.join(self.directory_path, filename)
                print(f"Loading {filename}...")
                try:
                    # 'elements' mode helps preserve structure often
                    loader = UnstructuredPDFLoader(file_path, mode="elements", strategy="fast")
                    docs = loader.load()
                    
                    # Normalize metadata and consolidate
                    # Unstructured often returns many small elements. For this pipeline, 
                    # we often want to aggregate them per page or process them as a stream.
                    # Here we will simplify: merge text but ensure page numbers are tracked.
                    # Ideally, Unstructured returns 'page_number' in metadata.
                    
                    for doc in docs:
                        # Ensure source is just the filename for cleaner display
                        doc.metadata["source"] = filename
                        # Ensure page_number exists
                        if "page_number" not in doc.metadata:
                             doc.metadata["page_number"] = 1 # Default if not found
                        documents.append(doc)
                        
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
        
        print(f"Loaded {len(documents)} raw document elements.")
        return documents

class ContentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            add_start_index=True,
            separators=["\n\n", "\n", " ", ""]
        )

    def clean_text(self, text: str) -> str:
        """
        Step 2: Document Cleaning
        Simple normalization: remove excessive whitespace.
        """
        # Collapse multiple spaces and newlines
        return " ".join(text.split())

    def process_documents(self, documents: List[Document]) -> List[Document]:
        """
        Step 2 & 3: Clean and Chunk
        """
        cleaned_docs = []
        for doc in documents:
            # Clean content
            doc.page_content = self.clean_text(doc.page_content)
            if doc.page_content: # Filter empty
                cleaned_docs.append(doc)

        print(f"Splitting {len(cleaned_docs)} elements into chunks...")
        chunks = self.text_splitter.split_documents(cleaned_docs)
        
        # Add parent ID and ensure strict metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = f"{chunk.metadata.get('source', 'doc')}_{i}"
            # Ensure mandatory fields
            chunk.metadata.setdefault("page_number", 0)
            chunk.metadata.setdefault("source", "unknown")

        print(f"Generated {len(chunks)} chunks.")
        return chunks

class VectorStoreManager:
    def __init__(self):
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index_name = INDEX_NAME
        # Use Local Embeddings (Free)
        print(f"Loading local embedding model: {EMBEDDING_MODEL}...")
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    def ensure_index_exists(self):
        """
        Step 5: Index Creation
        """
        existing_indexes = [i.name for i in self.pc.list_indexes()]
        
        # Check if we need to delete existing index (due to dimension change)
        if self.index_name in existing_indexes:
            print(f"Checking index {self.index_name}...")
            desc = self.pc.describe_index(self.index_name)
            if desc.dimension != 384:
                print(f"Dimension mismatch (Found {desc.dimension}, Need 384). Deleting old index...")
                self.pc.delete_index(self.index_name)
                while self.index_name in [i.name for i in self.pc.list_indexes()]:
                    time.sleep(1)
                print("Old index deleted.")
                existing_indexes = [i.name for i in self.pc.list_indexes()]

        if self.index_name not in existing_indexes:
            print(f"Creating index {self.index_name} with dimension 384...")
            self.pc.create_index(
                name=self.index_name,
                dimension=384, # HuggingFace MiniLM dimension
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=os.getenv("PINECONE_ENV", "us-east-1"))
            )
            while not self.pc.describe_index(self.index_name).status["ready"]:
                time.sleep(1)
            print("Index created.")
        else:
            print(f"Index {self.index_name} exists.")

    def upsert_chunks(self, chunks: List[Document]):
        """
        Step 4 & 5: Embed and Upsert
        """
        index = self.pc.Index(self.index_name)
        
        # Prepare vectors: (id, embedding, metadata)
        # LangChain's Pinecone wrapper is easier, but using raw Pinecone client 
        # gives us more control for this exercise as per requirements to explain Steps.
        
        batch_size = 100
        print(f"Upserting {len(chunks)} chunks to Pinecone...")
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            
            # Step 4: Generate Embeddings
            texts = [c.page_content for c in batch]
            ids = [str(hash(c.page_content)) for c in batch] # Simple hash ID for demo, usually UUID
            embeddings = self.embeddings.embed_documents(texts)
            
            vectors = []
            for j, text in enumerate(texts):
                metadata = batch[j].metadata
                metadata["text"] = text # Store text in metadata for retrieval
                
                # SANITIZE METADATA: Pinecone only allows str, int, float, bool, List[str]
                clean_metadata = {}
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        clean_metadata[key] = value
                    elif isinstance(value, list) and all(isinstance(x, str) for x in value):
                        clean_metadata[key] = value
                    else:
                        # Drop complex types like 'coordinates' (dict) or 'languages' (List[str] sometimes fails if mixed)
                        # specifically 'coordinates' causes the reported crash
                        pass
                
                vectors.append({
                    "id": ids[j],
                    "values": embeddings[j],
                    "metadata": clean_metadata
                })
            
            # Step 5: Upsert
            index.upsert(vectors=vectors)
            print(f"Upserted batch {i} - {i + len(batch)}")

def run_ingestion_pipeline():
    # Define source directory
    source_dir = "data"
    os.makedirs(source_dir, exist_ok=True)
    
    # Initialize components
    loader = DocumentLoader(source_dir)
    processor = ContentProcessor()
    vector_manager = VectorStoreManager()
    
    # Run Pipeline
    raw_docs = loader.load_documents()
    if not raw_docs:
        print("No documents found. Please add PDFs to the 'data' folder.")
        return

    processed_chunks = processor.process_documents(raw_docs)
    
    vector_manager.ensure_index_exists()
    vector_manager.upsert_chunks(processed_chunks)
    print("Ingestion Pipeline Complete.")

if __name__ == "__main__":
    run_ingestion_pipeline()
