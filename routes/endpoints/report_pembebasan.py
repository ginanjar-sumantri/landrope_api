from uuid import UUID
from fastapi import APIRouter, Depends
from sqlmodel import text, select
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from fastapi_async_sqlalchemy import db
from common.rounder import RoundTwo
from common.enum import StatusReportPembebasanEnum

from models import Worker
from schemas.report_pembebasan_sch import SummaryProjectSch, DetailProjectSch
from schemas.export_log_sch import ExportLogSch
from schemas.response_sch import create_response, GetResponseBaseSch, GetResponsePaginatedSch

from services.report_pembebasan_service import ReportPembebasanService

from decimal import Decimal
from datetime import date
import crud
import math

router = APIRouter()


@router.get("/summary_project", response_model=GetResponseBaseSch[list[SummaryProjectSch]])
async def report_pembebasan_summary_project(period_date:date, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    objs = await ReportPembebasanService().summary_project(period_date=period_date)
    return create_response(data=objs)

@router.get("/detail_project", response_model=GetResponsePaginatedSch[DetailProjectSch])
async def report_pembebasan_detail_project(period_date:date, project_id:UUID, status_pembebasan:StatusReportPembebasanEnum, keyword:str | None = None, params: Params=Depends(), current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    objs = await ReportPembebasanService().detail_project(period_date=period_date, project_id=project_id, status_pembebasan=status_pembebasan, keyword=keyword)

    # SETUP MANUAL PAGINATION
    start = (params.page - 1) * params.size
    end = params.page * params.size
    total_items = len(objs)
    pages = math.ceil(total_items / params.size)

    data = Page(items=objs[start:end], size=params.size, page=params.page, pages=pages, total=total_items)

    return create_response(data=data)

@router.get("/summary_project/export", response_model=GetResponseBaseSch[ExportLogSch])
async def export_report_pembebasan_summary_project(period_date:date, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    export_log = await ReportPembebasanService().export_summary_project(period_date=period_date, created_by_id=current_worker.id)

    return create_response(data=export_log)

@router.get("/detail_project/export", response_model=GetResponseBaseSch[ExportLogSch])
async def export_report_pembebasan_summary_project(period_date:date, project_id:UUID | None = None, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    export_log = await ReportPembebasanService().export_detail_project(period_date=period_date, created_by_id=current_worker.id, project_id=project_id)

    return create_response(data=export_log)