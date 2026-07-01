import os
import glob
from pathlib import Path
from typing import Optional
import chromadb
from chromadb.utils import embedding_functions
from app.config import get_settings
from app.utils.observability import get_logger

settings = get_settings()
logger = get_logger(__name__)

KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent.parent / "knowledge_base"
COLLECTION_NAME = "telanova_support_kb"


class KnowledgeBaseLoader:
    def __init__(self):
        self._client: Optional[chromadb.Client] = None
        self._collection: Optional[chromadb.Collection] = None
        self._embedding_fn = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
            api_key=os.environ.get("GOOGLE_API_KEY", ""),
            model_name="models/gemini-embedding-001"

        )

    def _get_client(self) -> chromadb.Client:
        if self._client is None:
            self._client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        return self._client

    def _get_collection(self) -> chromadb.Collection:
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=self._embedding_fn,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def _chunk_document(self, text: str, chunk_size: int = 600, overlap: int = 100) -> list[str]:
        words = text.split()
        chunks = []
        i = 0
        while i < len(words):
            chunk = " ".join(words[i: i + chunk_size])
            chunks.append(chunk)
            i += chunk_size - overlap
        return chunks

    def load_knowledge_base(self, force_reload: bool = False) -> int:
        collection = self._get_collection()
        if collection.count() > 0 and not force_reload:
            logger.info("knowledge_base_already_loaded", count=collection.count())
            return collection.count()

        if force_reload:
            client = self._get_client()
            client.delete_collection(COLLECTION_NAME)
            self._collection = None
            collection = self._get_collection()

        md_files = glob.glob(str(KNOWLEDGE_BASE_PATH / "*.md"))
        all_chunks = []
        all_ids = []
        all_metadatas = []

        for filepath in md_files:
            doc_name = Path(filepath).stem
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            chunks = self._chunk_document(content)
            for idx, chunk in enumerate(chunks):
                chunk_id = f"{doc_name}_{idx}"
                all_chunks.append(chunk)
                all_ids.append(chunk_id)
                all_metadatas.append({
                    "source": doc_name,
                    "filepath": filepath,
                    "chunk_index": idx,
                })

        if all_chunks:
            batch_size = 50
            for i in range(0, len(all_chunks), batch_size):
                collection.add(
                    documents=all_chunks[i: i + batch_size],
                    ids=all_ids[i: i + batch_size],
                    metadatas=all_metadatas[i: i + batch_size],
                )

        logger.info("knowledge_base_loaded", document_count=len(md_files), chunk_count=len(all_chunks))
        return len(all_chunks)

    def retrieve(self, query: str, n_results: int = 4, intent_filter: Optional[str] = None) -> list[dict]:
        collection = self._get_collection()
        where_filter = None
        if intent_filter:
            source_map = {
                "billing": "billing_faq",
                "network": "network_troubleshooting",
                "plan": "plan_comparison",
                "escalation": "escalation_sop",
                "account": "customer_support_handbook",
            }
            source = source_map.get(intent_filter)
            if source:
                where_filter = {"source": {"$eq": source}}

        query_params = {
            "query_texts": [query],
            "n_results": min(n_results, collection.count() or 1),
            "include": ["documents", "metadatas", "distances"],
        }
        if where_filter:
            query_params["where"] = where_filter

        results = collection.query(**query_params)
        retrieved = []
        if results["documents"] and results["documents"][0]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                retrieved.append({
                    "content": doc,
                    "source": meta.get("source", "unknown"),
                    "relevance_score": round(1 - dist, 4),
                })
        logger.info("rag_retrieval", query_preview=query[:80], results_count=len(retrieved))
        return retrieved


knowledge_base = KnowledgeBaseLoader()
