from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from models.giro_model import Giro
from models.worker_model import Worker
from schemas.giro_sch import (GiroSch, GiroCreateSch, GiroUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException)
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[GiroSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: GiroCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    
    obj_current = await crud.giro.get_by_code(code=sch.code)
    if obj_current:
        raise NameExistException(name=sch.code, model=Giro)
    
    new_obj = await crud.giro.create(obj_in=sch, created_by_id=current_worker.id)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[GiroSch])
async def get_list(
                params: Params=Depends(), 
                order_by:str = None, 
                keyword:str = None, 
                filter_query:str=None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.giro.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[GiroSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.giro.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Giro, id)

@router.put("/{id}", response_model=PutResponseBaseSch[GiroSch])
async def update(id:UUID, sch:GiroUpdateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.giro.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Giro, id)
    
    obj_updated = await crud.giro.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[GiroSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Delete a object"""

    obj_current = await crud.giro.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Giro, id)
    
    obj_deleted = await crud.giro.remove(id=id)

    return obj_deleted

   