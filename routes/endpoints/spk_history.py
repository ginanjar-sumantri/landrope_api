from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select
from models import SpkHistory, Worker
from schemas.spk_history_sch import (SpkHistorySch, SpkHistoryCreateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException)
import crud
import json

router = APIRouter()

@router.get("", response_model=GetResponsePaginatedSch[SpkHistorySch])
async def get_list(
                params: Params=Depends(),
                keyword:str|None = None,
                filter_query:str=None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(SpkHistory).join(SpkHistory.spk)

    if keyword:
         query = query.filter(SpkHistory.meta_data.ilike(f"%{keyword}%"))

    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
                query = query.where(getattr(SpkHistory, key) == value)

    objs = await crud.spk_history.get_multi_paginated_ordered(params=params, query=query)
    return create_response(data=objs)


   