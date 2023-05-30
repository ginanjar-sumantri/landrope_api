from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from models.dokumen_model import BundleDt
from schemas.bundle_dt_sch import (BundleDtSch, BundleDtUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.generator import generate_code
from models.code_counter_model import CodeCounterEnum
import crud

router = APIRouter()

@router.get("", response_model=GetResponsePaginatedSch[BundleDtSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.bundledt.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[BundleDtSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.bundledt.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(BundleDt, id)

@router.put("/{id}", response_model=PutResponseBaseSch[BundleDtSch])
async def update(id:UUID, sch:BundleDtUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.bundledt.get(id=id)

    if not obj_current:
        raise IdNotFoundException(BundleDt, id)
    
    for_keyword = ["AJB", "PBB"]
    
    if obj_current.dokumen.name in for_keyword:
        pass
    
    obj_updated = await crud.bundledt.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

   