from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, File
from fastapi_pagination import Params
import crud
from models.ptsk_model import Ptsk
from schemas.ptsk_sch import (PtskSch, PtskCreateSch, PtskUpdateSch, PtskRawSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, ImportResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, ImportFailedException)
from services.geom_service import GeomService
from shapely.geometry import shape
from geoalchemy2.shape import to_shape

router = APIRouter()

@router.post("", response_model=PostResponseBaseSch[PtskRawSch], status_code=status.HTTP_201_CREATED)
async def create(sch: PtskCreateSch):
    
    """Create a new object"""
    
    obj_current = await crud.ptsk.get_by_name(name=sch.name)
    if obj_current:
        raise NameExistException(Ptsk, name=sch.name)
    
    new_obj = await crud.ptsk.create(obj_in=sch)
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[PtskRawSch])
async def get_list(params:Params = Depends(), order_by:str=None, keyword:str=None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.ptsk.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[PtskRawSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.ptsk.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Ptsk, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[PtskRawSch])
async def update(id:UUID, sch:PtskUpdateSch, file:UploadFile = None):
    
    """Update a obj by its id"""

    obj_current = await crud.ptsk.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Ptsk, id)
    
    obj_updated = await crud.ptsk.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)
