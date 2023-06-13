from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from models.tanda_terima_notaris_model import TandaTerimaNotarisHd
from schemas.tanda_terima_notaris_hd_sch import (TandaTerimaNotarisHdSch, TandaTerimaNotarisHdCreateSch, TandaTerimaNotarisHdUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.generator import generate_code
from models.code_counter_model import CodeCounterEnum
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[TandaTerimaNotarisHdSch], status_code=status.HTTP_201_CREATED)
async def create(sch: TandaTerimaNotarisHdCreateSch):
    
    """Create a new object"""
        
    new_obj = await crud.tandaterimanotaris_hd.create(obj_in=sch)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[TandaTerimaNotarisHdSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.tandaterimanotaris_hd.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[TandaTerimaNotarisHdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.tandaterimanotaris_hd.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(TandaTerimaNotarisHd, id)

@router.put("/{id}", response_model=PutResponseBaseSch[TandaTerimaNotarisHdSch])
async def update(id:UUID, sch:TandaTerimaNotarisHdUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.tandaterimanotaris_hd.get(id=id)

    if not obj_current:
        raise IdNotFoundException(TandaTerimaNotarisHd, id)
    
    obj_updated = await crud.tandaterimanotaris_hd.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)


   