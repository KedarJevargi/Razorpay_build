import json
from typing import Dict, Any, Optional
from datetime import datetime
from backend.db.pool import get_pool

class AuditLogger:
    """
    Immutable audit trail for agent actions.
    Logs every significant decision, intent parsing, and policy check.
    """
    
    @staticmethod
    async def log_event(
        session_id: str,
        event_type: str,
        agent: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        policy_check: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Appends an event to the audit_trail table.
        """
        pool = await get_pool()
        async with pool.acquire() as conn:
            query = """
                INSERT INTO audit_trail 
                (session_id, event_type, agent, action, details, policy_check, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """
            
            details_json = json.dumps(details) if details else None
            policy_json = json.dumps(policy_check) if policy_check else None
            
            record_id = await conn.fetchval(
                query,
                session_id,
                event_type,
                agent,
                action,
                details_json,
                policy_json,
                datetime.utcnow()
            )
            return record_id
