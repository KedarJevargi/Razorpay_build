import logging
import asyncpg
from typing import Dict, Any, List
from backend.agents.base_agent import BaseAgent
from a2a.types import AgentCard

logger = logging.getLogger(__name__)

class RecommendationAgent(BaseAgent):
    """
    Merchant Specialist: Recommendation Agent
    Responsible for suggesting upsells and cross-sells to increase merchant revenue.
    Uses fast SQL-based rules.
    """
    def __init__(self, db_pool: asyncpg.Pool):
        agent_card = AgentCard(
            name="Recommendation Agent",
            description="You are the specialist agent for up-selling and cross-selling based on user context."
        )
        super().__init__(agent_card=agent_card)
        self.db_pool = db_pool
        
        self.register_tool(self.suggest_upsell)
        self.register_tool(self.suggest_cross_sell)

    async def suggest_upsell(self, merchant_id: str, product_id: str) -> List[Dict[str, Any]]:
        """
        Suggest an upsell (a product in the same category but more expensive), ranked by semantic similarity.
        """
        async with self.db_pool.acquire() as conn:
            # 1. Get the current product's category, price, and embedding
            current = await conn.fetchrow(
                "SELECT category, price, embedding::text FROM products WHERE id = $1 AND merchant_id = $2",
                product_id, merchant_id
            )
            
            if not current or not current["embedding"]:
                return []
                
            # 2. Find products in the same category with a higher price, ordered by vector similarity
            upsells = await conn.fetch(
                """
                SELECT id, name, description, price, category 
                FROM products 
                WHERE merchant_id = $1 
                  AND category = $2 
                  AND price > $3
                ORDER BY embedding <=> $4::vector
                LIMIT 3
                """,
                merchant_id, current["category"], current["price"], current["embedding"]
            )
            return [dict(u) for u in upsells]

    async def suggest_cross_sell(self, merchant_id: str, product_id: str) -> List[Dict[str, Any]]:
        """
        Suggest a cross-sell (complementary items) using vector semantic search.
        """
        async with self.db_pool.acquire() as conn:
            # 1. Get the current product's category and embedding
            current = await conn.fetchrow(
                "SELECT category, embedding::text FROM products WHERE id = $1 AND merchant_id = $2",
                product_id, merchant_id
            )
            
            if not current or not current["embedding"]:
                return []
                
            # 2. Find closest matching products in a DIFFERENT category
            cross_sells = await conn.fetch(
                """
                SELECT id, name, description, price, category 
                FROM products 
                WHERE merchant_id = $1 
                  AND category != $2
                ORDER BY embedding <=> $3::vector
                LIMIT 3
                """,
                merchant_id, current["category"], current["embedding"]
            )
            return [dict(c) for c in cross_sells]
