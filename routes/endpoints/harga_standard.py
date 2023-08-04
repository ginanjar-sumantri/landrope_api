from uuid import UUID
from fastapi import APIRouter, status, Depends, HTTPException
from fastapi_pagination import Params
import crud
from models.master_model import HargaStandard
from models.worker_model import Worker
from schemas.harga_standard_sch import (HargaStandardSch, HargaStandardCreateSch, HargaStandardUpdateSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, DeleteResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException)
from decimal import Decimal

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[HargaStandardSch], status_code=status.HTTP_201_CREATED)
async def create(sch: HargaStandardCreateSch,
                 current_worker:Worker = Depends(crud.worker.get_current_user)):
    
    """Create a new object"""

    obj_current = await crud.harga_standard.get_by_planing_id(planing_id=sch.planing_id)
    if obj_current:
        raise NameExistException(HargaStandard, name="harga standard")
    
    new_obj = await crud.harga_standard.create(obj_in=sch, created_by_id=current_worker.id)
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[HargaStandardSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.harga_standard.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[HargaStandardSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.harga_standard.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(HargaStandard, id)

@router.get("/desa/{desa_id}", response_model=GetResponseBaseSch[HargaStandardSch])
async def get_by_desa_id(desa_id:UUID):

    """Get an object by id"""

    obj = await crud.harga_standard.get_by_desa_id(desa_id=desa_id)
    if obj:
        return create_response(data=obj)
    return {}
    
@router.put("/{id}", response_model=PutResponseBaseSch[HargaStandardSch])
async def update(id:UUID, sch:HargaStandardUpdateSch,
                 current_worker:Worker = Depends(crud.worker.get_current_user)):
    
    """Update a obj by its id"""

    obj_current = await crud.harga_standard.get(id=id)
    if not obj_current:
        raise IdNotFoundException(HargaStandard, id)
    
    obj_updated = await crud.harga_standard.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[HargaStandardSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID):
    
    """Delete a object"""

    obj_current = await crud.harga_standard.get(id=id)
    if not obj_current:
        raise IdNotFoundException(HargaStandard, id)
    
    obj_deleted = await crud.harga_standard.remove(id=id)

    return obj_deleted
