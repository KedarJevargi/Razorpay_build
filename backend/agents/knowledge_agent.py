import logging
import asyncpg
from typing import Dict, Any, List
from google import genai
from backend.agents.base_agent import BaseAgent
from a2a.types import AgentCard

logger = logging.getLogger(__name__)

class KnowledgeAgent(BaseAgent):
    """
    Merchant Specialist: Knowledge Agent
    Responsible for answering queries about merchant policies, documentation, and FAQs.
    Uses pgvector for RAG (Retrieval-Augmented Generation).
    """
    def __init__(self, db_pool: asyncpg.Pool):
        agent_card = AgentCard(
            name="Knowledge Agent",
            description="You are the specialist agent for store policies (returns, shipping, sizing)."
        )
        super().__init__(agent_card=agent_card)
        self.db_pool = db_pool
        # We use a separate client for embeddings (or the same one)
        self.embedding_client = genai.Client()
        self.embedding_model = "gemini-embedding-2"
        
        # Register the vector search tool
        self.register_tool(self.search_knowledge_base)

    async def search_knowledge_base(self, merchant_id: str, query: str) -> List[Dict[str, Any]]:
        """
        Search the merchant's knowledge base using semantic search (RAG).
        Returns the top matching documents.
        """
        try:
            # 1. Generate embedding for the query
            # We must run the synchronous SDK call in an async-friendly way if necessary,
            # but since it's blocking and fast, we can just call it, or better yet, run in executor.
            # Using the native async client to be completely non-blocking:
            response = await self.embedding_client.aio.models.embed_content(
                model=self.embedding_model,
                contents=query
            )
            query_vector = response.embeddings[0].values

            # Format vector as string for pgvector '[1.0, 2.0, ...]'
            vector_str = "[" + ",".join(str(v) for v in query_vector) + "]"

            # 2. Perform cosine similarity search using pgvector (<=> operator)
            # We return the top 3 closest documents
            sql_query = """
                SELECT id, doc_type, title, content, 
                       1 - (embedding <=> $1::vector) as similarity
                FROM knowledge_documents 
                WHERE merchant_id = $2
                ORDER BY embedding <=> $1::vector
                LIMIT 3
            """
            
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(sql_query, vector_str, merchant_id)
                results = []
                for r in rows:
                    row_dict = dict(r)
                    # We might want to filter out low similarity matches if needed
                    results.append({
                        "title": row_dict["title"],
                        "doc_type": row_dict["doc_type"],
                        "content": row_dict["content"],
                        "similarity": float(row_dict["similarity"])
                    })
                return results

        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}", exc_info=True)
            return [{"error": "Failed to retrieve documents."}]
