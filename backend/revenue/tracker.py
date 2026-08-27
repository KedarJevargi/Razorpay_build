import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from backend.db.pool import get_pool

class RevenueTracker:
    """
    Tracks AI-driven upsells and cross-sells to measure revenue growth ("The Bar").
    """
    
    @staticmethod
    async def log_revenue_event(
        session_id: str,
        event_type: str,
        original_value: float,
        ai_suggested_value: float,
        final_value: float,
        product_id: Optional[str] = None
    ) -> int:
        """
        Logs a revenue event to calculate the uplift from AI suggestions.
        """
        delta = final_value - original_value
        
        pool = await get_pool()
        async with pool.acquire() as conn:
            query = """
                INSERT INTO revenue_events 
                (session_id, event_type, original_value, ai_suggested_value, final_value, delta, product_id, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """
            
            record_id = await conn.fetchval(
                query,
                session_id,
                event_type,
                original_value,
                ai_suggested_value,
                final_value,
                delta,
                product_id,
                datetime.utcnow()
            )
            return record_id

    @staticmethod
    async def get_metrics() -> Dict[str, Any]:
        """
        Retrieves aggregate revenue metrics.
        """
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Total original revenue (without AI suggestions)
            original_query = "SELECT COALESCE(SUM(original_value), 0) FROM revenue_events WHERE event_type = 'checkout'"
            total_original = await conn.fetchval(original_query)
            
            # Total final revenue (with AI suggestions)
            final_query = "SELECT COALESCE(SUM(final_value), 0) FROM revenue_events WHERE event_type = 'checkout'"
            total_final = await conn.fetchval(final_query)
            
            # Total uplift
            delta_query = "SELECT COALESCE(SUM(delta), 0) FROM revenue_events WHERE event_type = 'checkout' AND delta > 0"
            total_uplift = await conn.fetchval(delta_query)
            
            uplift_percentage = (total_uplift / total_original * 100) if total_original > 0 else 0.0
            
            return {
                "baseline_revenue": float(total_original),
                "ai_driven_revenue": float(total_final),
                "total_uplift": float(total_uplift),
                "uplift_percentage": round(float(uplift_percentage), 2)
            }
