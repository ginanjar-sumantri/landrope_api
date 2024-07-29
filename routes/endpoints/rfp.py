
from fastapi import APIRouter, Request, BackgroundTasks
from services.rfp_service import RfpService

router = APIRouter()

@router.post("/notification")
async def notification(payload: dict, background_task:BackgroundTasks, request:Request):

    result = await RfpService().notification_center(payload=payload, background_task=background_task)

    return {"result" : result}