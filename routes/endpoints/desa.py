from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, File, Form, HTTPException
from fastapi_pagination import Params
import crud
from models.desa_model import Desa
from schemas.desa_sch import (DesaSch, DesaRawSch, DesaCreateSch, DesaUpdateSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, NameNotFoundException)
from services.geom_service import GeomService
from shapely.geometry import shape
from geoalchemy2.shape import to_shape

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[DesaRawSch], status_code=status.HTTP_201_CREATED)
async def create(sch: DesaCreateSch = Depends(DesaCreateSch.as_form), file:UploadFile = File()):
    
    """Create a new object"""
    
    obj_current = await crud.desa.get_by_name(name=sch.name)
    if obj_current:
        raise NameExistException(Desa, name=sch.name)

    if file:
        buffer = await file.read()

        geo_dataframe = GeomService.file_to_geo_dataframe(buffer)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry

        sch = DesaSch(name=sch.name, code=sch.code, luas=sch.luas, geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
    new_obj = await crud.desa.create(obj_in=sch)

    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[DesaRawSch])
async def get_list(params:Params = Depends(), keyword:str = None):
    
    """Gets a paginated list objects"""

    objs = await crud.desa.get_multi_paginated_with_keyword(params=params, keyword=keyword)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[DesaRawSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.desa.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Desa, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[DesaRawSch])
async def update(id:UUID, sch:DesaUpdateSch = Depends(DesaUpdateSch.as_form), file:UploadFile = None):
    
    """Update a obj by its id"""

    obj_current = await crud.desa.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Desa, id)
    
    if obj_current.geom:
        obj_current.geom = to_shape(obj_current.geom).__str__()
    
    if file:
        buffer = await file.read()

        geo_dataframe = GeomService.file_to_geo_dataframe(buffer)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry
        
        sch = DesaSch(name=sch.name, code=sch.code, luas=sch.luas, geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
    obj_updated = await crud.desa.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)


@router.post("/bulk")
async def bulk_create(file:UploadFile=File()):

    """Create bulk or import data"""

    try:
        file = await file.read()
        geo_dataframe = GeomService.file_to_geo_dataframe(file)
        
        for i, geo_data in geo_dataframe.iterrows():

            sch = DesaSch(name=geo_data['DESA'], luas=geo_data['LUAS'], geom=GeomService.single_geometry_to_wkt(geo_data.geometry))
            
            new_obj = await crud.desa.create(obj_in=sch)

    except:
        raise HTTPException(status_code=13, detail="Failed import data")
    
    return {"result" : status.HTTP_200_OK, "message" : "Successfully upload"}

