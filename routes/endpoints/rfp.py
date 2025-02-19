
from fastapi import APIRouter, Request
from services.rfp_service import RfpService

router = APIRouter()

@router.post("/notification")
async def notification(payload: dict, request:Request):

    result = await RfpService().notification_center(payload=payload)

    return {"result" : result}