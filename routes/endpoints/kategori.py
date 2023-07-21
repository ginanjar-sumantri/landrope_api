from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from models.kategori_model import Kategori
from schemas.kategori_sch import (KategoriSch, KategoriCreateSch, KategoriUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException)
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[KategoriSch], status_code=status.HTTP_201_CREATED)
async def create(sch: KategoriCreateSch):
    
    """Create a new object"""
        
    new_obj = await crud.kategori.create(obj_in=sch)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[KategoriSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.kategori.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[KategoriSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.kategori.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Kategori, id)

@router.put("/{id}", response_model=PutResponseBaseSch[KategoriSch])
async def update(id:UUID, sch:KategoriUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.kategori.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Kategori, id)
    
    obj_updated = await crud.kategori.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

   