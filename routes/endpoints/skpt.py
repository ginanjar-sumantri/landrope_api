from uuid import UUID
from fastapi import APIRouter, Depends, status
from fastapi_pagination import Params
from sqlmodel import select
from sqlalchemy.orm import selectinload
import crud
from models.skpt_model import Skpt
from models.worker_model import Worker
from schemas.skpt_sch import (SkptSch, SkptCreateSch, SkptUpdateSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, ImportResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, ImportFailedException)


router = APIRouter()

@router.post("", response_model=PostResponseBaseSch[SkptSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: SkptCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    
    obj_current = await crud.skpt.get_by_sk_number(number=sch.nomor_sk)
    if obj_current:
        raise NameExistException(Skpt, name=sch.nomor_sk)
    
    new_obj = await crud.skpt.create(obj_in=sch, created_by_id=current_worker.id)

    query = select(Skpt).where(Skpt.id == new_obj.id
                            ).options(selectinload(Skpt.ptsk))
    
    new_obj = await crud.skpt.get(query=query)

    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[SkptSch])
async def get_list(
            params:Params = Depends(), 
            order_by:str = None, 
            keyword:str = None, filter_query:str = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.skpt.get_multi_paginate_ordered_with_keyword_dict(params=params, 
                                                                        order_by=order_by, 
                                                                        keyword=keyword, 
                                                                        filter_query=filter_query,
                                                                        join=True)
    
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[SkptSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    query = select(Skpt).where(Skpt.id == id
                            ).options(selectinload(Skpt.ptsk))

    obj = await crud.skpt.get(query=query)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Skpt, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[SkptSch])
async def update(
            id:UUID, 
            sch:SkptUpdateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.skpt.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Skpt, id)
    
    obj_updated = await crud.skpt.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)

    query = select(Skpt).where(Skpt.id == id
                            ).options(selectinload(Skpt.ptsk))
    
    obj_updated = await crud.skpt.get(query=query)
    
    return create_response(data=obj_updated)