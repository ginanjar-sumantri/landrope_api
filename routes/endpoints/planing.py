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
async def get_list(params:Params = Depends(), order_by:str=None, keyword:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.planing.get_multi_paginated_ordered_with_keyword(params=params, order_by=order_by, keyword=keyword)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[PlaningRawSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.planing.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Planing, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[PlaningRawSch])
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

        projects = await crud.project.get_all()
        desas = await crud.desa.get_all()
        planings = await crud.planing.get_all()

        for i, geo_data in geo_dataframe.iterrows():
            p:str = geo_data['PROJECT']
            d:str = geo_data['DESA']
            kode:str = geo_data['kode']

            project = next((obj for obj in projects 
                            if obj.name.replace(" ", "").lower() == p.replace(" ", "").lower()), None) 
            if project is None:
                continue
                # raise HTTPException(status_code=404, detail=f"{p} Not Exists in Project Data Master")
            
            desa = next((obj for obj in desas 
                         if obj.name.replace(" ", "").lower() == d.replace(" ", "").lower()), None)
            if desa is None:
                continue
                # raise HTTPException(status_code=404, detail=f"{d} Not Exists in Desa Data Master")
            
            planing = next((obj for obj in planings 
                         if obj.project_id == project.id and obj.desa_id == desa.id), None)
            if planing:
                continue

            sch = PlaningSch(code=kode,
                            name=project.name + "-" + desa.name + "-" + kode,
                            project_id=project.id,
                            desa_id=desa.id,
                            geom=GeomService.single_geometry_to_wkt(geo_data.geometry),
                            luas=geo_data['LUAS'])
            
            await crud.planing.create_planing(obj_in=sch)  

    except:
        raise HTTPException(status_code=422, detail="Failed import data")
    
    return {"result" : status.HTTP_200_OK, "message" : "Successfully upload"}

    