import asyncio
import glob
from pathlib import Path
from typing import Optional, List

from google import genai
from google.cloud import aiplatform
from google.cloud.aiplatform.matching_engine.matching_engine_index import MatchingEngineIndex
from google.cloud.aiplatform.matching_engine.matching_engine_index_endpoint import (
    MatchingEngineIndexEndpoint,
)
from google.cloud.aiplatform_v1.types.index import IndexDatapoint

from app.config import get_settings
from app.db.container import repositories
from app.utils.observability import get_logger

settings = get_settings()
logger = get_logger(__name__)

KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent.parent / "knowledge_base"


class KnowledgeBaseLoader:
    def __init__(self):
        aiplatform.init(
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )
        
        self._genai_client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )
        self._embedding_model = "gemini-embedding-001"

        self._index: Optional[MatchingEngineIndex] = None
        self._index_endpoint: Optional[MatchingEngineIndexEndpoint] = None

    def _run_sync(self, coro):
        try:
            return asyncio.run(coro)
        except RuntimeError:
            return asyncio.get_event_loop().run_until_complete(coro)

    def _get_index(self) -> MatchingEngineIndex:
        if self._index is None:
            self._index = MatchingEngineIndex(index_name=settings.vertex_index_id)
        return self._index

    def _get_index_endpoint(self) -> MatchingEngineIndexEndpoint:
        if self._index_endpoint is None:
            self._index_endpoint = MatchingEngineIndexEndpoint(
                index_endpoint_name=settings.vertex_index_endpoint_id
            )
        return self._index_endpoint

    def _chunk_document(self, text: str, chunk_size: int = 600, overlap: int = 100) -> list[str]:
        words = text.split()
        chunks = []
        i = 0
        while i < len(words):
            chunk = " ".join(words[i: i + chunk_size])
            chunks.append(chunk)
            i += chunk_size - overlap
        return chunks

    def _generate_embedding(self, text: str) -> list[float]:
        response = self._genai_client.models.embed_content(
            model=self._embedding_model,
            contents=text,
        )
        return list(response.embeddings[0].values)

    def load_knowledge_base(self, force_reload: bool = False) -> int:
        repo = repositories.knowledge
        current_db_count = self._run_sync(repo.count_chunks())

        if current_db_count > 0 and not force_reload:
            logger.info("knowledge_base_already_loaded", count=current_db_count)
            return current_db_count

        if force_reload:
            logger.info("force_reloading_knowledge_base")
            all_existing_ids = self._run_sync(repo.get_all_chunk_ids())
            if all_existing_ids:
                index = self._get_index()
                index.remove_datapoints(datapoint_ids=all_existing_ids)
            
            self._run_sync(repo.delete_all_chunks())

        md_files = glob.glob(str(KNOWLEDGE_BASE_PATH / "*.md"))
        all_chunks = []
        all_metadatas = []
        datapoints = []

        for filepath in md_files:
            doc_name = Path(filepath).stem
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            chunks = self._chunk_document(content)
            for idx, chunk in enumerate(chunks):
                chunk_id = f"{doc_name}_{idx}"
                all_chunks.append(chunk)
                all_metadatas.append({
                    "id": chunk_id,
                    "chunk_text": chunk,
                    "source": doc_name,
                    "filepath": filepath,
                    "chunk_index": idx,
                })

                vector = self._generate_embedding(chunk)
                datapoints.append(
                    IndexDatapoint(datapoint_id=chunk_id, feature_vector=vector)
                )

        if all_chunks:
            index = self._get_index()
            batch_size = 50
            for i in range(0, len(datapoints), batch_size):
                batch_datapoints = datapoints[i : i + batch_size]
                try:
                    index.upsert_datapoints(
                        datapoints=batch_datapoints
                    )
                except Exception as exc:
                    logger.exception(
                        "vertex_upsert_failed",
                        error=str(exc),
                    )
                    raise

            self._run_sync(repo.save_chunks(all_metadatas))

        logger.info("knowledge_base_loaded", document_count=len(md_files), chunk_count=len(all_chunks))
        return len(all_chunks)

    def retrieve(self, query: str, n_results: int = 4, intent_filter: Optional[str] = None) -> list[dict]:
        repo = repositories.knowledge
        
        query_vector = self._generate_embedding(query)
        endpoint = self._get_index_endpoint()

        try:
            response = endpoint.find_neighbors(
                deployed_index_id=settings.vertex_deployed_index_id,
                queries=[query_vector],
                num_neighbors=n_results * 3 if intent_filter else n_results,
            )
        except Exception as exc:
            logger.exception(
                "vertex_retrieval_failed",
                error=str(exc),
            )
            raise

        retrieved = []
        if not response or not response[0]:
            return retrieved

        neighbors = response[0]
        neighbor_ids = [n.id for n in neighbors]
        distance_map = {n.id: n.distance for n in neighbors}

        db_chunks = self._run_sync(repo.get_chunks_by_ids(neighbor_ids))
        
        chunk_map = {
            chunk["id"]: chunk
            for chunk in db_chunks
        }
        
        source_target = None
        if intent_filter:
            source_map = {
                "billing": "billing_faq",
                "network": "network_troubleshooting",
                "plan": "plan_comparison",
                "escalation": "escalation_sop",
                "account": "customer_support_handbook",
            }
            source_target = source_map.get(intent_filter)

        for chunk_id in neighbor_ids:
            chunk = chunk_map.get(chunk_id)
            if not chunk:
                continue
                
            chunk_source = chunk.get("source", "unknown")
            
            if source_target and chunk_source != source_target:
                continue

            distance = distance_map.get(chunk_id, 1.0)
            retrieved.append({
                "content": chunk.get("chunk_text", ""),
                "source": chunk_source,
                "relevance_score": round(1.0 - distance, 4),
            })

            if len(retrieved) >= n_results:
                break

        logger.info("rag_retrieval", query_preview=query[:80], results_count=len(retrieved))
        return retrieved


knowledge_base = KnowledgeBaseLoader()