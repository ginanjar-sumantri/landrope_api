from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from models.notaris_model import Notaris
from schemas.notaris_sch import (NotarisSch, NotarisCreateSch, NotarisUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException)
from common.generator import generate_code
from models.code_counter_model import CodeCounterEnum
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[NotarisSch], status_code=status.HTTP_201_CREATED)
async def create(sch: NotarisCreateSch):
    
    """Create a new object"""
        
    new_obj = await crud.notaris.create(obj_in=sch)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[NotarisSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.notaris.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[NotarisSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.notaris.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Notaris, id)

@router.put("/{id}", response_model=PutResponseBaseSch[NotarisSch])
async def update(id:UUID, sch:NotarisUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.notaris.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Notaris, id)
    
    obj_updated = await crud.notaris.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[NotarisSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID):
    
    """Delete a object"""

    obj_current = await crud.notaris.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Notaris, id)
    
    obj_deleted = await crud.notaris.remove(id=id)

    return obj_deleted

   