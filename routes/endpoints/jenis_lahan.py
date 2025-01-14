from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
import crud
from models.master_model import JenisLahan
from models.worker_model import Worker
from schemas.jenis_lahan_sch import (JenisLahanSch, JenisLahanCreateSch, JenisLahanUpdateSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException)

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[JenisLahanSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: JenisLahanCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    obj_current = await crud.jenislahan.get_by_name(name=sch.name)
    if obj_current:
        raise NameExistException(JenisLahan, name=sch.name)
    
    new_obj = await crud.jenislahan.create(obj_in=sch, created_by_id=current_worker.id)
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[JenisLahanSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str=None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.jenislahan.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[JenisLahanSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.jenislahan.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(JenisLahan, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[JenisLahanSch])
async def update(
            id:UUID, 
            sch:JenisLahanUpdateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.jenislahan.get(id=id)
    if not obj_current:
        raise IdNotFoundException(JenisLahan, id)
    
    obj_updated = await crud.jenislahan.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)
