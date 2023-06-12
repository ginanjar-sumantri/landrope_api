from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from models.kjb_model import KjbCaraBayar
from schemas.kjb_cara_bayar_sch import (KjbCaraBayarSch, KjbCaraBayarCreateSch, KjbCaraBayarUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[KjbCaraBayarSch], status_code=status.HTTP_201_CREATED)
async def create(sch: KjbCaraBayarCreateSch):
    
    """Create a new object"""
        
    new_obj = await crud.kjb_carabayar.create(obj_in=sch)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[KjbCaraBayarSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.kjb_carabayar.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[KjbCaraBayarSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.kjb_carabayar.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(KjbCaraBayar, id)

@router.put("/{id}", response_model=PutResponseBaseSch[KjbCaraBayarSch])
async def update(id:UUID, sch:KjbCaraBayarUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.kjb_carabayar.get(id=id)

    if not obj_current:
        raise IdNotFoundException(KjbCaraBayar, id)
    
    obj_updated = await crud.kjb_carabayar.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[KjbCaraBayarSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID):
    
    """Delete a object"""

    obj_current = await crud.kjb_carabayar.get(id=id)
    if not obj_current:
        raise IdNotFoundException(KjbCaraBayar, id)
    
    obj_deleted = await crud.kjb_carabayar.remove(id=id)

    return obj_deleted

   