from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from services.dependencies.dependencies import get_lead_service
from services.dependencies.dependencies_repo import request_context
from services.leads.lead_services import LeadClient

from .handle_webhook import handle_bitrix24_webhook

lead_router = APIRouter(
    prefix="/entities", dependencies=[Depends(request_context)]
)


@lead_router.post("/handle-webhook/lead")  # type: ignore
async def handle_bitrix24_webhook_lead(
    request: Request,
    lead_client: LeadClient = Depends(get_lead_service),
) -> JSONResponse:
    """
    Обработчик вебхуков Bitrix24 для лидов
    """
    return await handle_bitrix24_webhook(request, lead_client)
