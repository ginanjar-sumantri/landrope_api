from uuid import UUID
from fastapi import APIRouter, Depends
from sqlmodel import text, select
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from fastapi_async_sqlalchemy import db
from common.rounder import RoundTwo

from models import Worker
from schemas.report_pembebasan_sch import SummaryProjectSch
from schemas.response_sch import create_response, GetResponseBaseSch

from services.report_pembebasan_service import ReportPembebasanService

from decimal import Decimal
from datetime import date
import crud

router = APIRouter()


@router.get("/summary_project", response_model=GetResponseBaseSch[list[SummaryProjectSch]])
async def report_pembebasan_summary_project(period_date:date, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    objs = await ReportPembebasanService().summary_project(period_date=period_date)
    return create_response(data=objs)