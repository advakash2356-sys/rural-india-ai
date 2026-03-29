"""
Vector Database - Local semantic search and embeddings
Phase 3 Feature
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class VectorDatabase:
    """
    Local vector database for semantic search without cloud dependency.
    
    Stores document embeddings for retrieval-augmented generation (RAG).
    Uses simple cosine similarity for edge device compatibility.
    """
    
    def __init__(self, db_path: str = "data/vector_db.json"):
        """
        Initialize vector database.
        
        Args:
            db_path: Path to store vector database
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.embeddings = {}  # Dict[doc_id -> embedding]
        self.documents = {}   # Dict[doc_id -> document]
        self.metadata = {}    # Dict[doc_id -> metadata]
        
        self._load_database()
        logger.info(f"VectorDatabase initialized at {db_path}")
    
    def add_document(self, 
                    text: str, 
                    doc_id: Optional[str] = None,
                    metadata: Optional[Dict] = None,
                    embedding: Optional[List[float]] = None) -> str:
        """
        Add document to vector database.
        
        Args:
            text: Document text
            doc_id: Optional document ID
            metadata: Optional metadata
            embedding: Optional pre-computed embedding
            
        Returns:
            Document ID
        """
        if doc_id is None:
            doc_id = f"doc_{len(self.documents):06d}"
        
        self.documents[doc_id] = text
        self.metadata[doc_id] = {
            "created": datetime.utcnow().isoformat(),
            "language": "hi",
            **(metadata or {})
        }
        
        # Use provided embedding or generate one
        if embedding is not None:
            self.embeddings[doc_id] = embedding
        else:
            self.embeddings[doc_id] = self._compute_embedding(text)
        
        self._save_database()
        logger.info(f"Document added: {doc_id}")
        return doc_id
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float, str]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of (doc_id, similarity_score, document_text) tuples
        """
        if not self.documents:
            return []
        
        query_embedding = self._compute_embedding(query)
        scores = []
        
        for doc_id, doc_embedding in self.embeddings.items():
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            scores.append((doc_id, similarity, self.documents[doc_id]))
        
        # Sort by similarity and return top_k
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        if doc_id not in self.documents:
            return None
        
        return {
            "id": doc_id,
            "text": self.documents[doc_id],
            "metadata": self.metadata.get(doc_id, {}),
            "embedding_dim": len(self.embeddings.get(doc_id, []))
        }
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete document from database."""
        if doc_id not in self.documents:
            return False
        
        del self.documents[doc_id]
        del self.embeddings[doc_id]
        del self.metadata[doc_id]
        
        self._save_database()
        logger.info(f"Document deleted: {doc_id}")
        return True
    
    def clear(self) -> None:
        """Clear entire database."""
        self.documents.clear()
        self.embeddings.clear()
        self.metadata.clear()
        self._save_database()
        logger.info("Vector database cleared")
    
    @staticmethod
    def _compute_embedding(text: str, dim: int = 384) -> List[float]:
        """
        Compute simple embedding (TF-IDF like).
        For production: use sentence-transformers or similar.
        """
        # Simple character-based embedding
        text_lower = text.lower()
        
        # Initialize embedding
        embedding = np.zeros(dim)
        
        # Hash characters into embedding space
        for i, char in enumerate(text_lower):
            if i >= len(text_lower) * 2:
                break
            hash_val = hash(char) % dim
            embedding[hash_val] += 1
        
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding.tolist()
    
    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def _save_database(self) -> None:
        """Persist database to disk."""
        try:
            data = {
                "documents": self.documents,
                "embeddings": self.embeddings,
                "metadata": self.metadata,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            with open(self.db_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save database: {e}")
    
    def _load_database(self) -> None:
        """Load database from disk."""
        if not self.db_path.exists():
            return
        
        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                self.documents = data.get("documents", {})
                self.embeddings = data.get("embeddings", {})
                self.metadata = data.get("metadata", {})
                
            logger.info(f"Loaded {len(self.documents)} documents from database")
            
        except Exception as e:
            logger.error(f"Failed to load database: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        return {
            "total_documents": len(self.documents),
            "embedding_dimension": len(next(iter(self.embeddings.values()), [])),
            "database_size_mb": self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0,
            "last_modified": datetime.fromtimestamp(
                self.db_path.stat().st_mtime
            ).isoformat() if self.db_path.exists() else None
        }


class RAGEngine:
    """
    Retrieval-Augmented Generation engine.
    Combines vector search with inference for knowledge-grounded responses.
    """
    
    def __init__(self, vector_db: VectorDatabase, orchestrator):
        """
        Initialize RAG engine.
        
        Args:
            vector_db: VectorDatabase instance
            orchestrator: EdgeNodeOrchestrator instance
        """
        self.vector_db = vector_db
        self.orchestrator = orchestrator
        
        logger.info("RAGEngine initialized")
    
    async def generate_with_context(self, 
                                   query: str, 
                                   top_k: int = 3) -> Dict[str, Any]:
        """
        Generate response using retrieved context.
        
        Args:
            query: User query
            top_k: Number of context documents
            
        Returns:
            Response with context and generated text
        """
        # Retrieve relevant documents
        search_results = self.vector_db.search(query, top_k=top_k)
        
        context_docs = []
        for doc_id, score, text in search_results:
            context_docs.append({
                "doc_id": doc_id,
                "similarity": float(score),
                "text": text[:200]  # Truncate for context
            })
        
        # Build augmented prompt
        context_str = "\n".join([
            f"[Doc {i+1}] {doc['text']}"
            for i, doc in enumerate(context_docs)
        ])
        
        augmented_query = f"""Context:
{context_str}

Question: {query}

Answer:"""
        
        # Generate response
        result = await self.orchestrator.process_local_query(augmented_query)
        
        return {
            "query": query,
            "response": result.get("response", "Unable to generate response"),
            "context": context_docs,
            "success": result.get("success", False)
        }
    
    def add_knowledge(self, knowledge_items: List[Dict[str, str]]) -> int:
        """
        Add knowledge documents to vector database.
        
        Args:
            knowledge_items: List of dicts with 'text' and optional 'id', 'metadata'
            
        Returns:
            Number of documents added
        """
        count = 0
        for item in knowledge_items:
            self.vector_db.add_document(
                text=item['text'],
                doc_id=item.get('id'),
                metadata=item.get('metadata')
            )
            count += 1
        
        logger.info(f"Added {count} knowledge documents")
        return count
