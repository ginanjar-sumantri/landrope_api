from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
import crud
from models.master_model import JenisSurat
from schemas.jenis_surat_sch import (JenisSuratSch, JenisSuratCreateSch, JenisSuratUpdateSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException)

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[JenisSuratSch], status_code=status.HTTP_201_CREATED)
async def create(sch: JenisSuratCreateSch):
    
    """Create a new object"""

    obj_current = await crud.jenissurat.get_by_name(name=sch.name)
    if obj_current:
        raise NameExistException(JenisSurat, name=sch.name)
    
    new_obj = await crud.jenissurat.create(obj_in=sch)
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[JenisSuratSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.jenissurat.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[JenisSuratSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.jenissurat.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(JenisSurat, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[JenisSuratSch])
async def update(id:UUID, sch:JenisSuratUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.jenissurat.get(id=id)
    if not obj_current:
        raise IdNotFoundException(JenisSurat, id)
    
    obj_updated = await crud.jenissurat.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)
