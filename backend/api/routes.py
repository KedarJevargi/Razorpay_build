import asyncio
import logging
import uuid
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, AsyncGenerator

from a2a.server.request_handlers.request_handler import RequestHandler, Event
from a2a.server.context import ServerCallContext
from a2a.types import (
    GetTaskRequest, Task, ListTasksRequest, ListTasksResponse,
    CancelTaskRequest, SendMessageRequest, Message,
    TaskPushNotificationConfig, GetTaskPushNotificationConfigRequest,
    SubscribeToTaskRequest, ListTaskPushNotificationConfigsRequest,
    ListTaskPushNotificationConfigsResponse, DeleteTaskPushNotificationConfigRequest,
    GetExtendedAgentCardRequest, AgentCard, Role, Part, UnsupportedOperationError
)

from backend.db.pool import get_pool
from backend.audit.service import AuditLogger
from backend.revenue.tracker import RevenueTracker

from backend.agents.catalog_agent import CatalogAgent
from backend.agents.knowledge_agent import KnowledgeAgent
from backend.agents.recommendation_agent import RecommendationAgent
from backend.agents.checkout_agent import CheckoutAgent
from backend.agents.merchant_orchestrator import MerchantOrchestratorAgent
from backend.agents.exceptions import PaymentVerificationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Observability"])

_orchestrator = None

async def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        pool = await get_pool()
        catalog = CatalogAgent(db_pool=pool)
        knowledge = KnowledgeAgent(db_pool=pool)
        recommendation = RecommendationAgent(db_pool=pool)
        checkout = CheckoutAgent(db_pool=pool)
        _orchestrator = MerchantOrchestratorAgent(
            catalog_agent=catalog,
            knowledge_agent=knowledge,
            recommendation_agent=recommendation,
            checkout_agent=checkout
        )
    return _orchestrator

class MerchantRequestHandler(RequestHandler):
    
    async def on_get_task(self, params: GetTaskRequest, context: ServerCallContext) -> Task | None:
        raise UnsupportedOperationError()

    async def on_list_tasks(self, params: ListTasksRequest, context: ServerCallContext) -> ListTasksResponse:
        raise UnsupportedOperationError()

    async def on_cancel_task(self, params: CancelTaskRequest, context: ServerCallContext) -> Task | None:
        raise UnsupportedOperationError()

    async def on_message_send(self, params: SendMessageRequest, context: ServerCallContext) -> Task | Message:
        orchestrator = await get_orchestrator()
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        # Extract intent text
        intent = "".join([p.text for p in params.message.parts if p.HasField("text")])
        session_id = dict(params.metadata).get("session_id", "unknown_session") if params.HasField("metadata") else "unknown_session"
        
        internal_task = Task(
            id=task_id,
            history=[params.message]
        )
        
        # Fire and forget audit log
        asyncio.create_task(
            AuditLogger.log_event(
                session_id=session_id,
                event_type="task_received",
                agent="merchant_orchestrator",
                action=f"Received task: {intent}",
                details={"task_id": task_id}
            )
        )
        
        try:
            result = await orchestrator.process_task(internal_task)
            
            asyncio.create_task(
                AuditLogger.log_event(
                    session_id=session_id,
                    event_type="task_completed",
                    agent="merchant_orchestrator",
                    action=f"Task completed with status: {result.status}",
                    details={"task_id": task_id, "result": result.result_data}
                )
            )
            
            response_text = result.result_data.get("response", "") if result.result_data else "Done"
            return Message(
                role=Role.ROLE_AGENT,
                parts=[Part(text=response_text)]
            )
        except PaymentVerificationError as e:
            # Deterministic override: abort conversation and return strict message
            asyncio.create_task(
                AuditLogger.log_event(
                    session_id=session_id,
                    event_type="payment_failed",
                    agent="merchant_orchestrator",
                    action=f"Deterministic payment rejection: {str(e)}",
                    details={"task_id": task_id}
                )
            )
            return Message(
                role=Role.ROLE_AGENT,
                parts=[Part(text=f"I'm sorry, but your payment verification failed. {str(e)}")]
            )
        except Exception as e:
            asyncio.create_task(
                AuditLogger.log_event(
                    session_id=session_id,
                    event_type="task_failed",
                    agent="merchant_orchestrator",
                    action=f"Task failed with error: {str(e)}",
                    details={"task_id": task_id}
                )
            )
            raise e

    async def on_message_send_stream(self, params: SendMessageRequest, context: ServerCallContext) -> AsyncGenerator[Event, None]:
        raise UnsupportedOperationError()
        yield

    async def on_create_task_push_notification_config(self, params: TaskPushNotificationConfig, context: ServerCallContext) -> TaskPushNotificationConfig:
        raise UnsupportedOperationError()

    async def on_get_task_push_notification_config(self, params: GetTaskPushNotificationConfigRequest, context: ServerCallContext) -> TaskPushNotificationConfig:
        raise UnsupportedOperationError()

    async def on_subscribe_to_task(self, params: SubscribeToTaskRequest, context: ServerCallContext) -> AsyncGenerator[Event, None]:
        raise UnsupportedOperationError()
        yield

    async def on_list_task_push_notification_configs(self, params: ListTaskPushNotificationConfigsRequest, context: ServerCallContext) -> ListTaskPushNotificationConfigsResponse:
        raise UnsupportedOperationError()

    async def on_delete_task_push_notification_config(self, params: DeleteTaskPushNotificationConfigRequest, context: ServerCallContext) -> None:
        raise UnsupportedOperationError()

    async def on_get_extended_agent_card(self, params: GetExtendedAgentCardRequest, context: ServerCallContext) -> AgentCard:
        orchestrator = await get_orchestrator()
        return orchestrator.agent_card

@router.get("/audit", response_model=List[Dict[str, Any]])
async def get_audit_trail(limit: int = 50):
    pool = await get_pool()
    async with pool.acquire() as conn:
        records = await conn.fetch(
            "SELECT * FROM audit_trail ORDER BY timestamp DESC LIMIT $1", limit
        )
        return [dict(record) for record in records]

@router.get("/revenue", response_model=Dict[str, Any])
async def get_revenue_metrics():
    try:
        metrics = await RevenueTracker.get_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
