from fastapi import APIRouter, Depends, status, UploadFile, File, HTTPException, Response, Request
from fastapi_pagination import Params
from models.desa_model import Desa
from models.import_log_model import ImportLog
from models.worker_model import Worker
from models.code_counter_model import CodeCounterEnum
from schemas.desa_sch import (DesaSch, DesaRawSch, DesaCreateSch, DesaUpdateSch, DesaExportSch)
from schemas.import_log_sch import (ImportLogCreateSch, ImportLogSch, ImportLogCloudTaskSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, NameNotFoundException)
from common.generator import generate_code
from common.rounder import RoundTwo
from common.enum import TaskStatusEnum
from services.geom_service import GeomService
from services.gcloud_task_service import GCloudTaskService
from shapely.geometry import shape
from decimal import Decimal
from datetime import datetime
from shapely import wkt, wkb
from uuid import UUID
import crud

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[DesaRawSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: DesaCreateSch = Depends(DesaCreateSch.as_form), 
            file:UploadFile = File(),
            current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Create a new object"""
    
    obj_current = await crud.desa.get_by_name(name=sch.name)
    if obj_current:
        raise NameExistException(Desa, name=sch.name)

    if file:
        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry
        
        sch = DesaSch(**sch.dict())
        sch.geom = GeomService.single_geometry_to_wkt(geo_dataframe.geometry)
    
    new_obj = await crud.desa.create(obj_in=sch, created_by_id=current_worker.id)

    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[DesaRawSch])
async def get_list(
            params:Params = Depends(), 
            order_by:str=None, 
            keyword:str=None, 
            filter_query:str=None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.desa.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
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
async def update(id:UUID, sch:DesaUpdateSch = Depends(DesaUpdateSch.as_form), file:UploadFile = None,
                 current_worker:Worker = Depends(crud.worker.get_current_user)):
    
    """Update a obj by its id"""

    obj_current = await crud.desa.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Desa, id)
    
    if obj_current.geom :
        obj_current.geom = wkt.dumps(wkb.loads(obj_current.geom.data, hex=True))
    
    
    if file:
        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry
        
        sch = DesaSch(name=sch.name, 
                      code=sch.code,
                      kecamatan=sch.kecamatan,
                      kota=sch.kota, 
                      luas=RoundTwo(sch.luas), 
                      geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
    obj_updated = await crud.desa.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)

@router.post("/bulk")
async def bulk(file:UploadFile=File(),
               current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Create bulk or import data"""
    try:
        datas = []
        current_datetime = datetime.now()
        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)
        
        
        for i, geo_data in geo_dataframe.iterrows():
            code:str = geo_data['code']
            name:str = geo_data['name']
            kota:str = geo_data['kota']
            kecamatan:str = geo_data['kecamatan']
            luas:Decimal = RoundTwo(Decimal(geo_data['luas']))

            obj_current = await crud.desa.get_by_name(name=name)
            
            if obj_current:
                obj_current.geom = wkt.dumps(wkb.loads(obj_current.geom.data, hex=True))
                sch_update = DesaSch(name=obj_current.name, 
                      code=obj_current.code,
                      kecamatan=kecamatan,
                      kota=kota, 
                      luas=luas, 
                      geom=GeomService.single_geometry_to_wkt(geo_data.geometry))
                
                await crud.desa.update(obj_current=obj_current, obj_new=sch_update, updated_by_id=current_worker.id)
                continue

            code = await generate_code(entity=CodeCounterEnum.Desa)

            sch = Desa(
                          name=name,
                          code=code,
                          kecamatan=kecamatan,
                          kota=kota, 
                          luas=luas,
                          geom=GeomService.single_geometry_to_wkt(geo_data.geometry),
                          created_at=current_datetime,
                          updated_at=current_datetime,
                          created_by_id=current_worker.id,
                          updated_by_id=current_worker.id
                          )
            
            datas.append(sch)

        if len(datas) > 0:    
            await crud.desa.create_all(obj_ins=datas)

    except:
        raise HTTPException(status_code=422, detail="Failed import data")
    
    return {"result" : status.HTTP_200_OK, "message" : "Successfully upload"}

@router.get("/export/shp", response_class=Response)
async def export_shp(
                filter_query:str = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):

    schemas = []
    
    results = await crud.desa.get_multi_by_dict(filter_query=filter_query)

    for data in results:
        sch = DesaExportSch(
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
    

