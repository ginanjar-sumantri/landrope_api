from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from models.kjb_model import KjbTermin
from models.worker_model import Worker
from schemas.kjb_termin_sch import (KjbTerminSch, KjbTerminCreateSch, KjbTerminUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[KjbTerminSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: KjbTerminCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
        
    new_obj = await crud.kjb_termin.create(obj_in=sch, created_by_id=current_worker.id)
    new_obj = await crud.kjb_termin.get_by_id(id=new_obj.id)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[KjbTerminSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.kjb_termin.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[KjbTerminSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.kjb_termin.get_by_id(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(KjbTermin, id)

@router.put("/{id}", response_model=PutResponseBaseSch[KjbTerminSch])
async def update(
            id:UUID, 
            sch:KjbTerminUpdateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.kjb_termin.get(id=id)

    if not obj_current:
        raise IdNotFoundException(KjbTermin, id)
    
    obj_updated = await crud.kjb_termin.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    obj_updated = await crud.kjb_termin.get_by_id(id=obj_updated.id)
    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[KjbTerminSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Delete a object"""

    obj_current = await crud.kjb_termin.get(id=id)
    if not obj_current:
        raise IdNotFoundException(KjbTermin, id)
    
    obj_deleted = await crud.kjb_termin.remove(id=id)

    return obj_deleted

   