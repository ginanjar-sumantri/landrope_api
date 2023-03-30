from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, status, UploadFile, File, HTTPException
from fastapi_pagination import Params
from models.planing_model import Planing
from models.project_model import Project
from models.desa_model import Desa
from schemas.planing_sch import (PlaningSch, PlaningCreateSch, PlaningUpdateSch, PlaningRawSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, NameNotFoundException)
from services.geom_service import GeomService
from shapely.geometry import shape
from datetime import datetime
from geoalchemy2.shape import to_shape
import crud
from typing import List

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[PlaningRawSch], status_code=status.HTTP_201_CREATED)
async def create(sch: PlaningCreateSch = Depends(PlaningCreateSch.as_form), file:UploadFile = None):
    
    """Create a new object"""
    
    obj_current = await crud.planing.get_by_name(name=sch.name)
    if obj_current:
        raise NameExistException(Planing, name=sch.name)
    
    if file is not None:
        buffer = await file.read()

        geo_dataframe = GeomService.file_to_geo_dataframe(buffer)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry
        
        sch = PlaningSch(code=sch.code, project_id=sch.project_id, 
                          desa_id=sch.desa_id, luas=sch.luas, 
                          name=sch.name, geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry)
                          )
        
    new_obj = await crud.planing.create(obj_in=sch)
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[PlaningRawSch])
async def get_list(params:Params = Depends()):
    
    """Gets a paginated list objects"""

    objs = await crud.planing.get_multi_paginated(params=params)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[PlaningSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.planing.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Planing, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[PlaningCreateSch])
async def update(id:UUID, sch:PlaningUpdateSch = Depends(PlaningUpdateSch.as_form), file:UploadFile = None):
    
    """Update a obj by its id"""

    obj_current = await crud.planing.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Planing, id)
    
    if obj_current.geom:
        obj_current.geom = to_shape(obj_current.geom).__str__()
    
    if file is not None:
        buffer = await file.read()

        geo_dataframe = GeomService.file_to_geo_dataframe(buffer)

        

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry

        sch.geom = GeomService.single_geometry_to_wkt(geo_dataframe.geometry)
    
    obj_updated = await crud.planing.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

@router.post("/bulk")
async def bulk_create(file:UploadFile=File()):

    """Create bulk or import data"""

    try:
        file = await file.read()
        geo_dataframe = GeomService.file_to_geo_dataframe(file)

        projects = await crud.project.get_by_names(list_names=geo_dataframe["PROJECT"])
        desas = await crud.desa.get_by_names(list_names=geo_dataframe["DESA"])

        for i, geo_data in geo_dataframe.iterrows():

            project = next((obj for obj in projects if obj.name == geo_data['PROJECT']), None) 
            desa = next((obj for obj in desas if obj.name == geo_data['DESA']), None) 

            sch = Planing(code="",
                            name="",
                            project_id=project.id,
                            desa_id=desa.id,
                            geom=GeomService.single_geometry_to_wkt(geo_data.geometry),
                            luas=geo_data['LUAS'])
            
            new_obj = await crud.planing.create_planing(obj_in=sch)  

    except:
        raise HTTPException(status_code=13, detail="Failed import data")
    
    return {"result" : status.HTTP_200_OK, "message" : "Successfully upload"}

    