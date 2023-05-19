from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, File, Form, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi_pagination import Params
import crud
from models.desa_model import Desa
from models.code_counter_model import CodeCounterEnum
from schemas.desa_sch import (DesaSch, DesaRawSch, DesaCreateSch, DesaUpdateSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, NameNotFoundException)
from services.geom_service import GeomService
from shapely.geometry import shape
from geoalchemy2.shape import to_shape
from common.generator import generate_code
from common.rounder import RoundTwo
from decimal import Decimal
from shapely import wkt, wkb

import json

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[DesaRawSch], status_code=status.HTTP_201_CREATED)
async def create(sch: DesaCreateSch = Depends(DesaCreateSch.as_form), file:UploadFile = File()):
    
    """Create a new object"""
    
    obj_current = await crud.desa.get_by_name(name=sch.name)
    if obj_current:
        raise NameExistException(Desa, name=sch.name)
    
    sch.code = await generate_code(CodeCounterEnum.Desa)
    sch.last = 1

    if file:
        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry

        sch = DesaSch(name=sch.name, 
                      code=sch.code, 
                      luas=RoundTwo(sch.luas),
                      last=sch.last, 
                      geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
    new_obj = await crud.desa.create(obj_in=sch)

    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[DesaRawSch])
async def get_list(params:Params = Depends(), order_by:str=None, keyword:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.desa.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword)
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
        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry
        
        sch = DesaSch(name=sch.name, 
                      code=sch.code, 
                      luas=RoundTwo(sch.luas), 
                      geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
    obj_updated = await crud.desa.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)


@router.post("/bulk")
async def bulk_create(file:UploadFile=File()):

    """Create bulk or import data"""
    try:
        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)
        print(geo_dataframe.head())
        desas = await crud.desa.get_all()
        
        for i, geo_data in geo_dataframe.iterrows():
            name:str | None = geo_data['NAMOBJ']

            obj_current = next((obj for obj in desas 
                           if obj.name.replace(" ", "").lower() == name.replace(" ", "").lower()),None)
            
            if obj_current:
                continue
            
            g_code = await generate_code(entity=CodeCounterEnum.Desa)
            luas:Decimal = RoundTwo(Decimal(geo_data['SHAPE_Area']))

            sch = DesaSch(name=geo_data['NAMOBJ'], 
                          code=g_code, 
                          luas=luas, 
                          geom=GeomService.single_geometry_to_wkt(geo_data.geometry))
            
            await crud.desa.create(obj_in=sch)

    except:
        raise HTTPException(status_code=422, detail="Failed import data")
    
    return {"result" : status.HTTP_200_OK, "message" : "Successfully upload"}

@router.get("/export/shp", response_class=Response)
async def export_shp(filter_query:str = None):
    if filter_query:
        filter_query = json.loads(filter_query)

    schemas = []
    
    results = await crud.desa.get_by_dict(filter_query=filter_query)

    for data in results:
        sch = DesaSch(id=data.id,
                      geom=wkt.dumps(wkb.loads(data.geom.data, hex=True)),
                      name=data.name,
                      code=data.code,
                      kecamatan=data.kecamatan,
                      kota=data.kota,
                      luas=data.luas)

        schemas.append(sch)

    if results:
        obj_name = results[0].__class__.__name__
        if len(results) == 1:
            obj_name = f"{obj_name}-{results[0].name}"

    return GeomService.export_shp_zip(data=schemas, obj_name=obj_name)
    

