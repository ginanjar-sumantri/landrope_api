from uuid import UUID
from fastapi import APIRouter, Depends
from fastapi_pagination import Params
from models.import_log_model import ImportLog
from schemas.import_log_sch import (ImportLogSch)
from schemas.response_sch import (GetResponsePaginatedSch, create_response)
import crud


router = APIRouter()

@router.get("", response_model=GetResponsePaginatedSch[ImportLogSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.import_log.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

   