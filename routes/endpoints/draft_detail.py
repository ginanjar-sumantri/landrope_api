from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, or_
from models.draft_model import DraftDetail
from models.worker_model import Worker
from schemas.draft_detail_sch import (DraftDetailSch, DraftDetailRawSch, DraftDetailCreateSch, DraftDetailUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, 
                                  DeleteResponseBaseSch, GetResponsePaginatedSch, 
                                  PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from shapely.geometry import shape
from shapely import wkt, wkb
import crud
import json


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[DraftDetailRawSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: DraftDetailCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
        
    new_obj = await crud.draft_detail.create(obj_in=sch, created_by_id=current_worker.id)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[DraftDetailRawSch])
async def get_list(
                params: Params=Depends(), 
                order_by:str = None, 
                keyword:str = None, 
                filter_query:str=None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.draft_detail.get_multi_paginate_ordered_with_keyword_dict(
        params=params, 
        order_by=order_by, 
        keyword=keyword, 
        filter_query=filter_query)
    
    return create_response(data=objs)

@router.get("/all", response_model=GetResponsePaginatedSch[DraftDetailRawSch])
async def get_all(
                keyword:str = None, 
                filter_query:str=None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(DraftDetail)

    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
            query = query.where(getattr(DraftDetail, key) == value)

    objs = await crud.draft_detail.get_multi_no_page(query=query)
    
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[DraftDetailRawSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.draft_detail.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(DraftDetail, id)

@router.put("/{id}", response_model=PutResponseBaseSch[DraftDetailRawSch])
async def update(id:UUID, sch:DraftDetailUpdateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.draft_detail.get(id=id)

    if not obj_current:
        raise IdNotFoundException(DraftDetail, id)
    
    if obj_current.geom :
        obj_current.geom = wkt.dumps(wkb.loads(obj_current.geom.data, hex=True))
    
    obj_updated = await crud.draft_detail.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[DraftDetailSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Delete a object"""

    obj_current = await crud.draft_detail.get(id=id)
    if not obj_current:
        raise IdNotFoundException(DraftDetail, id)
    
    obj_deleted = await crud.draft_detail.remove(id=id)

    return obj_deleted

   