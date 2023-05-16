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
from io import BytesIO
import zipfile
from typing import List
import geopandas as gpd
from shapely.wkb import loads
import tempfile
import os

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

@router.get("export-all", response_class=Response)
async def export_shp():
    objs = await crud.desa.get_all_()
    return export_shp_zip(data=objs, obj_name="desa")
    

def export_shp_zip(data:List[DesaSch]| None, obj_name:str):
        my_objects=[]

        ent = data[0].dict()
        obj_columns = list(ent.keys())

        geom:str='geom'
        geometry:str = 'geometry'
        
        for row in data:
            dict_object = dict(row)
            dict_object['geometry'] = loads(dict_object['geom'].data)
            dict_object['id'] = str(dict_object['id'])
            my_objects.append(dict_object)
        
        for key in obj_columns:
            if key == "created_at":
                obj_columns.remove(key)
            if key == "updated_at":
                obj_columns.remove(key)
        
        obj_columns.append(geometry)
        obj_columns.remove(geom)

        gdf = gpd.GeoDataFrame(my_objects, columns=obj_columns)

        tempdir = tempfile.mkdtemp()

        # mengekspor GeoDataFrame ke dalam file shapefile
        output_folder = os.path.join(tempdir, 'shapefile')
        gdf.to_file(filename=output_folder, driver='ESRI Shapefile')

        # membuat file zip dan menambahkan file shapefile ke dalamnya
        output_zip = os.path.join(tempdir, f'{obj_name}.zip')
        with zipfile.ZipFile(output_zip, 'w') as zip:
            zip.write(os.path.join(output_folder, 'shapefile.shp'), 'shapefile.shp')
            zip.write(os.path.join(output_folder, 'shapefile.shx'), 'shapefile.shx')
            zip.write(os.path.join(output_folder, 'shapefile.dbf'), 'shapefile.dbf')

        return FileResponse(output_zip, media_type='application/zip', filename=f'{obj_name}.zip')