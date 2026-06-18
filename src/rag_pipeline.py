import os
from pathlib import Path
from typing import List, Dict, Any
import chromadb
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.config import Config
from src.utils import logger, DocumentReader

class RAGPipeline:
    """Handles document indexing, embedding generation, vector storage in ChromaDB, and top-k retrieval."""
    
    def __init__(self):
        # Initialize the Sentence Transformer model
        logger.info(f"Initializing embedding model: {Config.EMBEDDING_MODEL_NAME}")
        self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL_NAME)
        
        # Initialize ChromaDB persistent client
        logger.info(f"Initializing ChromaDB persistent storage at: {Config.CHROMA_DB_DIR}")
        self.chroma_client = chromadb.PersistentClient(path=str(Config.CHROMA_DB_DIR))
        
        # Get or create collection using cosine distance metric
        self.collection = self.chroma_client.get_or_create_collection(
            name="support_knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )
        
    def clear_database(self):
        """Clears all indexed documents from ChromaDB."""
        try:
            self.chroma_client.delete_collection(name="support_knowledge_base")
            self.collection = self.chroma_client.get_or_create_collection(
                name="support_knowledge_base",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB collection cleared successfully.")
        except Exception as e:
            logger.error(f"Error clearing ChromaDB collection: {e}")
            raise e

    def index_documents(self, data_dir: Path = None) -> int:
        """
        Scans data_dir for support docs (PDF, TXT, MD), chunks them, 
        generates embeddings, and stores them in ChromaDB.
        Returns the total number of chunks indexed.
        """
        target_dir = data_dir or Config.DATA_DIR
        if not target_dir.exists():
            logger.warning(f"Data directory {target_dir} does not exist. No files indexed.")
            return 0
            
        logger.info(f"Scanning directory {target_dir} for support files...")
        
        # Supported extensions
        extensions = [".pdf", ".txt", ".md", ".markdown"]
        files = [p for p in target_dir.glob("**/*") if p.suffix.lower() in extensions]
        
        if not files:
            logger.warning("No support documents found in data directory.")
            return 0
            
        logger.info(f"Found {len(files)} files to index.")
        
        all_chunks_text = []
        all_chunks_metadata = []
        all_chunks_ids = []
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=80,
            length_function=len
        )
        
        chunk_counter = 0
        for file_path in files:
            try:
                # Load document segments
                segments = DocumentReader.load_document(file_path)
                
                for idx, segment in enumerate(segments):
                    text = segment["text"]
                    base_metadata = segment["metadata"]
                    
                    # Split into smaller chunks
                    split_texts = text_splitter.split_text(text)
                    
                    for split_idx, split_text in enumerate(split_texts):
                        chunk_id = f"{file_path.name}_s{idx}_c{split_idx}"
                        
                        # Prepare detailed metadata
                        metadata = base_metadata.copy()
                        metadata["chunk_index"] = split_idx
                        # Convert all metadata values to string/int/float for Chroma compatibility
                        for key in list(metadata.keys()):
                            if metadata[key] is None:
                                metadata[key] = ""
                                
                        all_chunks_text.append(split_text)
                        all_chunks_metadata.append(metadata)
                        all_chunks_ids.append(chunk_id)
                        chunk_counter += 1
                        
            except Exception as e:
                logger.error(f"Error preparing file {file_path.name} for indexing: {e}")
                
        if not all_chunks_text:
            logger.warning("No chunks generated from documents.")
            return 0
            
        logger.info(f"Generating embeddings and indexing {len(all_chunks_text)} chunks...")
        
        # Batch encode in chunks of 64 to avoid memory spikes
        batch_size = 64
        for i in range(0, len(all_chunks_text), batch_size):
            batch_texts = all_chunks_text[i:i+batch_size]
            batch_metadatas = all_chunks_metadata[i:i+batch_size]
            batch_ids = all_chunks_ids[i:i+batch_size]
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(batch_texts).tolist()
            
            # Upsert into ChromaDB
            self.collection.upsert(
                ids=batch_ids,
                embeddings=embeddings,
                documents=batch_texts,
                metadatas=batch_metadatas
            )
            
        logger.info(f"Successfully indexed {chunk_counter} chunks in ChromaDB.")
        return chunk_counter

    def retrieve(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Retrieves top-k relevant chunks matching the query.
        Converts cosine distances into normalized similarity scores (0.0 to 1.0).
        """
        k = top_k or Config.DEFAULT_TOP_K
        
        # Empty check
        if self.collection.count() == 0:
            logger.warning("Retrieval requested but ChromaDB collection is empty.")
            return []
            
        # Embed query
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Retrieve
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        
        # Format results
        retrieved_items = []
        
        # Verify result content
        if not results or not results["documents"] or not results["documents"][0]:
            return []
            
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]
        
        for doc, meta, dist in zip(documents, metadatas, distances):
            # Calculate cosine similarity score from cosine distance
            # Cosine distance in Chroma ranges [0, 2] (where 0 is identical, 2 is opposite)
            # cosine_similarity = 1 - distance
            # Cap it between 0.0 and 1.0 for user presentation
            similarity = max(0.0, min(1.0, 1.0 - dist))
            
            retrieved_items.append({
                "text": doc,
                "metadata": meta,
                "similarity": round(similarity, 4)
            })
            
        return retrieved_items

    def get_kb_status(self) -> Dict[str, Any]:
        """Returns diagnostic details of the indexed Knowledge Base."""
        count = self.collection.count()
        sources = set()
        
        if count > 0:
            # Query all metadata elements to identify unique documents
            results = self.collection.get(include=["metadatas"])
            for meta in results.get("metadatas", []):
                if meta and "source" in meta:
                    sources.add(meta["source"])
                    
        return {
            "total_chunks": count,
            "document_count": len(sources),
            "documents": list(sources)
        }
