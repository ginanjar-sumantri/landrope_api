from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from models.kjb_model import KjbRekening
from schemas.kjb_rekening_sch import (KjbRekeningSch, KjbRekeningCreateSch, KjbRekeningUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException)
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[KjbRekeningSch], status_code=status.HTTP_201_CREATED)
async def create(sch: KjbRekeningCreateSch):
    
    """Create a new object"""
        
    new_obj = await crud.kjb_rekening.create(obj_in=sch)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[KjbRekeningSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.kjb_rekening.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[KjbRekeningSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.kjb_rekening.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(KjbRekening, id)

@router.put("/{id}", response_model=PutResponseBaseSch[KjbRekeningSch])
async def update(id:UUID, sch:KjbRekeningUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.kjb_rekening.get(id=id)

    if not obj_current:
        raise IdNotFoundException(KjbRekening, id)

    obj_updated = await crud.kjb_rekening.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[KjbRekeningSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID):
    
    """Delete a object"""

    obj_current = await crud.kjb_rekening.get(id=id)
    if not obj_current:
        raise IdNotFoundException(KjbRekening, id)
    
    obj_deleted = await crud.kjb_rekening.remove(id=id)

    return obj_deleted

   