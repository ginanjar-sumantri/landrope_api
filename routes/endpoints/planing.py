from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, status, UploadFile, File, HTTPException, Response
from fastapi_pagination import Params
from models.planing_model import Planing
from models.project_model import Project
from models.desa_model import Desa
from schemas.planing_sch import (PlaningSch, PlaningCreateSch, PlaningUpdateSch, PlaningRawSch, PlaningExtSch, PlaningShpSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, CodeExistException, NameNotFoundException)
from services.geom_service import GeomService
from shapely  import wkt, wkb
from shapely.geometry import shape
from geoalchemy2.shape import to_shape
from common.rounder import RoundTwo
from decimal import Decimal
from datetime import datetime
import crud
import json

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[PlaningRawSch], status_code=status.HTTP_201_CREATED)
async def create(sch: PlaningCreateSch = Depends(PlaningCreateSch.as_form), file:UploadFile = None):
    
    """Create a new object"""
    
    obj_current = await crud.planing.get_by_project_id_desa_id(project_id=sch.project_id, desa_id=sch.desa_id)
    if obj_current:
        raise NameExistException(Planing, name=sch.name)

    project = await crud.project.get(id=sch.project_id)
    if project is None:
        raise IdNotFoundException(Project, id=sch.project_id)
    
    desa = await crud.desa.get(id=sch.desa_id)
    if desa is None:
        raise IdNotFoundException(Desa, id=sch.desa_id)
    
    code = project.section.code + project.code + desa.code
    sch.code = code
    sch.name = project.name + "-" + desa.name + "-" + code
    
    if file:
        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry
        
        sch = PlaningSch(code=sch.code, 
                        project_id=sch.project_id, 
                        desa_id=sch.desa_id,
                        luas=RoundTwo(sch.luas), 
                        name=sch.name, 
                        geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
        
    new_obj = await crud.planing.create(obj_in=sch)
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[PlaningRawSch])
async def get_list(params:Params = Depends(), order_by:str=None, keyword:str=None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.planing.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
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
    
    if obj_current.geom :
        obj_current.geom = wkt.dumps(wkb.loads(obj_current.geom.data, hex=True))
    
    if file:
        buffer = await file.read()

        geo_dataframe = GeomService.file_to_geo_dataframe(buffer)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry

        sch.geom = GeomService.single_geometry_to_wkt(geo_dataframe.geometry)
    
    obj_updated = await crud.planing.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

@router.post("/bulk")
async def bulk(file:UploadFile=File()):

    """Create bulk or import data"""

    try:
        file = await file.read()
        geo_dataframe = GeomService.file_to_geo_dataframe(file)
        datas = []
        current_datetime = datetime.now()

        errors = []

        for i, geo_data in geo_dataframe.iterrows():
            name:str = geo_data['name']
            code:str = geo_data['code']
            project_name:str = geo_data['project']
            desa_name:str = geo_data['desa']

            luas:Decimal = RoundTwo(Decimal(geo_data['luas']))

            project = await crud.project.get_by_name(name=project_name)
            if project is None:
                raise NameNotFoundException(Project, name=project_name)
            
            desa = await crud.desa.get_by_name(name=desa_name)
            if desa is None:
                raise NameNotFoundException(Desa, name=desa_name)
            
            code_combine = project.section.code + project.code + desa.code
            name_combine = project.name + "-" + desa.name + "-" + code_combine
            
            obj_current = await crud.planing.get_by_project_id_desa_id(project_id=project.id, desa_id=desa.id)

            if obj_current:
                obj_current.geom = wkt.dumps(wkb.loads(obj_current.geom.data, hex=True))
                sch_update = PlaningSch(code=obj_current.code,
                            name=obj_current.name,
                            project_id=project.id,
                            desa_id=desa.id,
                            geom=GeomService.single_geometry_to_wkt(geo_data.geometry),
                            luas=luas)

                await crud.planing.update(obj_current=obj_current, obj_new=sch_update)
                continue

            sch = Planing(code=code_combine,
                            name=name_combine,
                            project_id=project.id,
                            desa_id=desa.id,
                            geom=GeomService.single_geometry_to_wkt(geo_data.geometry),
                            luas=luas,
                            created_at=current_datetime,
                            updated_at=current_datetime)
            
            datas.append(sch)
        
        if len(datas) > 0:
            await crud.planing.create_all(obj_ins=datas)  

    except:
        raise HTTPException(status_code=422, detail="Failed import data")
    
    if len(errors) > 0:
        return {"result" : status.HTTP_207_MULTI_STATUS, "message" : "Some data can't imported", "errors" : errors}
    
    return {"result" : status.HTTP_200_OK, "message" : "Successfully upload"}

@router.get("/export/shp", response_class=Response)
async def export_shp(filter_query:str = None):

    schemas = []
    
    results = await crud.planing.get_multi_by_dict(filter_query=filter_query)

    for data in results:
        sch = PlaningShpSch(
                      geom=wkt.dumps(wkb.loads(data.geom.data, hex=True)),
                      luas=data.luas,
                      name=data.name,
                      code=data.code,
                      project=data.project_name,
                      desa=data.desa_name,
                      section=data.section_name)

        schemas.append(sch)

    if results:
        obj_name = results[0].__class__.__name__
        if len(results) == 1:
            obj_name = f"{obj_name}-{results[0].name}"

    return GeomService.export_shp_zip(data=schemas, obj_name=obj_name)

    