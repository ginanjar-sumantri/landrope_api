from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, File
from fastapi_pagination import Params
import crud
from models.bidang_model import Bidang
from schemas.bidang_sch import (BidangSch, BidangCreateSch, BidangUpdateSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException)
from services.geom_service import GeomService

router = APIRouter()

@router.post("", response_model=PostResponseBaseSch[BidangSch], status_code=status.HTTP_201_CREATED)
async def create(sch: BidangCreateSch, file:UploadFile = None):
    
    """Create a new object"""
    
    obj_current = await crud.bidang.get_by_id_bidang(name=sch.id_bidang)
    if obj_current:
        raise NameExistException(Bidang, name=sch.id_bidang)
    
    if file is not None:
        content_type = await file.content_type
        buffer = await file.read()
        geom = GeomService.from_map_to_wkt(buffer=buffer, content_type=content_type)

        sch.geom = geom
    
    new_obj = await crud.bidang.create(obj_in=sch)
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[BidangSch])
async def get_list(params:Params = Depends()):
    
    """Gets a paginated list objects"""

    objs = await crud.bidang.get_multi_paginated(params=params)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[BidangSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.bidang.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Bidang, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[BidangCreateSch])
async def update(id:UUID, sch:BidangUpdateSch, file:UploadFile = None):
    
    """Update a obj by its id"""

    obj_current = await crud.bidang.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Bidang, id)
    
    if file is not None:
        content_type = await file.content_type
        buffer = await file.read()
        geom = GeomService.from_map_to_wkt(buffer=buffer, content_type=content_type)

        sch.geom = geom
    
    obj_updated = await crud.bidang.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

