from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from sqlmodel import select, or_
from models.master_model import BebanBiaya
from models.worker_model import Worker
from schemas.beban_biaya_sch import (BebanBiayaSch, BebanBiayaCreateSch, BebanBiayaUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.generator import generate_code
from models.code_counter_model import CodeCounterEnum
import crud
import json


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[BebanBiayaSch], status_code=status.HTTP_201_CREATED)
async def create(sch: BebanBiayaCreateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    new_obj = await crud.bebanbiaya.create(obj_in=sch, created_by_id=current_worker.id)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[BebanBiayaSch])
async def get_list(params: Params=Depends(), 
                   order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    query = select(BebanBiaya)

    if keyword:
        query = query.filter(or_(
            BebanBiaya.name.ilike(f"%keyword%")

        ))

    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
                query = query.where(getattr(BebanBiaya, key) == value)
        
    objs = await crud.bebanbiaya.get_multi_paginated_ordered(params=params, query=query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[BebanBiayaSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.bebanbiaya.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(BebanBiaya, id)

@router.put("/{id}", response_model=PutResponseBaseSch[BebanBiayaSch])
async def update(id:UUID, sch:BebanBiayaUpdateSch,
                 current_worker:Worker = Depends(crud.worker.get_current_user)):
    
    """Update a obj by its id"""

    obj_current = await crud.bebanbiaya.get(id=id)

    if not obj_current:
        raise IdNotFoundException(BebanBiaya, id)
    
    obj_updated = await crud.dokumen.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[BebanBiayaSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID):
    
    """Delete a object"""

    obj_current = await crud.bebanbiaya.get(id=id)
    if not obj_current:
        raise IdNotFoundException(BebanBiaya, id)
    
    obj_deleted = await crud.bebanbiaya.remove(id=id)

    return obj_deleted

   