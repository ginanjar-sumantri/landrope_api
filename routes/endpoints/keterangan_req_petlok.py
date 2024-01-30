from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from models.master_model import KeteranganReqPetlok
from models.worker_model import Worker
from schemas.keterangan_req_petlok_sch import (KeteranganReqPetlokSch, KeteranganReqPetlokCreateSch, KeteranganReqPetlokUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[KeteranganReqPetlokSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: KeteranganReqPetlokCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    db_session = db.session
        
    new_obj = await crud.keterangan_req_petlok.create(obj_in=sch, created_by_id=current_worker.id, db_session=db_session)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[KeteranganReqPetlokSch])
async def get_list(
                params: Params=Depends(), 
                order_by:str = None, 
                keyword:str = None, 
                filter_query:str=None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.keterangan_req_petlok.get_multi_paginated_ordered(params=params, order_by=order_by)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[KeteranganReqPetlokSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.keterangan_req_petlok.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(KeteranganReqPetlok, id)

@router.put("/{id}", response_model=PutResponseBaseSch[KeteranganReqPetlokSch])
async def update(id:UUID, sch:KeteranganReqPetlokUpdateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.keterangan_req_petlok.get(id=id)

    if not obj_current:
        raise IdNotFoundException(KeteranganReqPetlok, id)
    
    obj_updated = await crud.keterangan_req_petlok.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)

   