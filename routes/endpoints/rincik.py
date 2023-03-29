from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, File
from fastapi_pagination import Params
import crud
from models.rincik_model import Rincik
from schemas.rincik_sch import (RincikSch, RincikCreateSch, RincikUpdateSch, RincikRawSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException)
from services.geom_service import GeomService
from shapely.geometry import shape

router = APIRouter()

@router.post("", response_model=PostResponseBaseSch[RincikRawSch], status_code=status.HTTP_201_CREATED)
async def create(sch: RincikCreateSch, file:UploadFile = None):
    
    """Create a new object"""
    
    obj_current = await crud.rincik.get_by_id_rincik(name=sch.id_rincik)
    if obj_current:
        raise NameExistException(Rincik, name=sch.id_rincik)
    
    if file is not None:
        buffer = await file.read()

        geo_dataframe = GeomService.file_to_geo_dataframe(buffer)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry

        sch.geom = GeomService.single_geometry_to_wkt(geo_dataframe.geometry)
    
    new_obj = await crud.rincik.create(obj_in=sch)
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[RincikRawSch])
async def get_list(params:Params = Depends()):
    
    """Gets a paginated list objects"""

    objs = await crud.rincik.get_multi_paginated(params=params)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[RincikRawSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.rincik.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Rincik, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[RincikRawSch])
async def update(id:UUID, sch:RincikUpdateSch, file:UploadFile = None):
    
    """Update a obj by its id"""

    obj_current = await crud.rincik.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Rincik, id)
    
    if file is not None:
        content_type = await file.content_type
        buffer = await file.read()
        geom = GeomService.from_map_to_wkt(buffer=buffer, content_type=content_type)

        sch.geom = geom
    
    obj_updated = await crud.rincik.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

