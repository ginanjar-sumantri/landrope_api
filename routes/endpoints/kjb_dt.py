from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from models.kjb_model import KjbDt
from schemas.kjb_dt_sch import (KjbDtSch, KjbDtCreateSch, KjbDtUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[KjbDtSch], status_code=status.HTTP_201_CREATED)
async def create(sch: KjbDtCreateSch):
    
    """Create a new object"""
        
    new_obj = await crud.kjb_dt.create(obj_in=sch)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[KjbDtSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.kjb_dt.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/request/petlok", response_model=GetResponsePaginatedSch[KjbDtSch])
async def get_list_for_petlok(kjb_hd_id:UUID):
    
    """Gets a paginated list objects"""

    objs = await crud.kjb_dt.get_for_petlok(kjb_hd_id=kjb_hd_id)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[KjbDtSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.kjb_dt.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(KjbDt, id)

@router.put("/{id}", response_model=PutResponseBaseSch[KjbDtSch])
async def update(id:UUID, sch:KjbDtUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.kjb_dt.get(id=id)

    if not obj_current:
        raise IdNotFoundException(KjbDt, id)
    
    obj_updated = await crud.kjb_dt.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)


   