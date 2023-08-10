from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from models.kjb_model import KjbPenjual
from models.worker_model import Worker
from schemas.kjb_penjual_sch import (KjbPenjualSch, KjbPenjualCreateSch, KjbPenjualUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException)
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[KjbPenjualSch], status_code=status.HTTP_201_CREATED)
async def create(sch: KjbPenjualCreateSch,
                 current_worker:Worker = Depends(crud.worker.get_current_user)):
    
    """Create a new object"""
        
    new_obj = await crud.kjb_penjual.create(obj_in=sch)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[KjbPenjualSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.kjb_penjual.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[KjbPenjualSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.kjb_penjual.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(KjbPenjual, id)

@router.put("/{id}", response_model=PutResponseBaseSch[KjbPenjualSch])
async def update(id:UUID, sch:KjbPenjualUpdateSch,
                 current_worker:Worker = Depends(crud.worker.get_current_user)):
    
    """Update a obj by its id"""

    obj_current = await crud.kjb_penjual.get(id=id)

    if not obj_current:
        raise IdNotFoundException(KjbPenjual, id)

    obj_updated = await crud.kjb_penjual.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[KjbPenjualSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID):
    
    """Delete a object"""

    obj_current = await crud.kjb_penjual.get(id=id)
    if not obj_current:
        raise IdNotFoundException(KjbPenjual, id)
    
    obj_deleted = await crud.kjb_penjual.remove(id=id)

    return obj_deleted

   