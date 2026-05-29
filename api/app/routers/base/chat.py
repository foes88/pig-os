"""
POST /api/v1/farms/{farm_id}/chat/query

Base tier: Rule Engine + Template Renderer (no LLM cost).
Addon #1 (AI Insight): LLM renderer activated via active subscription.

Follows the same /farms/{farm_id}/... pattern as kpi and events routers.
"""
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_farm_context
from app.db.models.platform import Farm
from app.schemas.chat import ChatQuery, ChatResponse
from app.services.chat_service import handle_query

router = APIRouter(prefix="/farms", tags=["Q&A"])


@router.post("/{farm_id}/chat/query", response_model=ChatResponse)
async def query(
    farm_id: UUID,
    body: ChatQuery,
    farm: Farm = Depends(get_farm_context),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """
    Natural language query about farm KPIs.

    Base tier: structured template answer.
    Upgrade to Addon #1 (AI Insight) for LLM-powered natural language answers.
    """
    return await handle_query(db, farm, body)
