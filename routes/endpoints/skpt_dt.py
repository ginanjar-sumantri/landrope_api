from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, File, Response
from fastapi_pagination import Params
import crud
from models.planing_model import Planing
from models.project_model import Project
from models.desa_model import Desa
from models.skpt_model import Skpt, SkptDt
from schemas.skpt_sch import SkptSch, SkptShpSch
from schemas.skpt_dt_sch import SkptDtCreateSch, SkptDtUpdateSch, SkptDtSch, SkptDtRawSch
from schemas.ptsk_sch import (PtskSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, ImportResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameNotFoundException, ImportFailedException)
from services.geom_service import GeomService
from shapely import wkt, wkb
from shapely.geometry import shape
from common.rounder import RoundTwo
from decimal import Decimal
from datetime import datetime
import json

router = APIRouter()

@router.post("", response_model=PostResponseBaseSch[SkptDtRawSch], status_code=status.HTTP_201_CREATED)
async def create(sch: SkptDtCreateSch = Depends(SkptDtCreateSch.as_form), file:UploadFile = None):
    
    """Create a new object"""
    
    skpt_current = await crud.skpt.get(id=sch.skpt_id)
    if skpt_current:
        raise IdNotFoundException(Skpt, id=sch.skpt_id)
    
    planing_current = await crud.planing.get(id=sch.planing_id)
    if planing_current:
        raise IdNotFoundException(Planing, id=sch.planing_id)
    
    if file:
        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry

        sch = SkptDtSch(planing_id=sch.planing_id,
                        skpt_id=sch.skpt_id,
                        luas=RoundTwo(sch.luas),
                      geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
    new_obj = await crud.skptdt.create(obj_in=sch)
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[SkptDtRawSch])
async def get_list(params:Params = Depends(), order_by:str=None, keyword:str=None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.skptdt.get_multi_paginate_ordered_with_keyword_dict(params=params, 
                                                                        order_by=order_by, 
                                                                        keyword=keyword, 
                                                                        filter_query=filter_query,
                                                                        join=True)
    
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[SkptDtRawSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.skptdt.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Skpt, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[SkptDtRawSch])
async def update(id:UUID, sch:SkptDtUpdateSch = Depends(SkptDtUpdateSch.as_form), file:UploadFile=None):
    
    """Update a obj by its id"""

    obj_current = await crud.skpt.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Skpt, id)
    
    if obj_current.geom :
        obj_current.geom = wkt.dumps(wkb.loads(obj_current.geom.data, hex=True))
    
    if file:
        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry
        
        sch = SkptDtSch(planing_id=sch.planing_id,
                        skpt_id=sch.skpt_id,
                        luas=RoundTwo(sch.luas),
                      geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
    obj_updated = await crud.skpt.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

@router.post("/bulk", response_model=ImportResponseBaseSch[SkptDtRawSch], status_code=status.HTTP_201_CREATED)
async def bulk_skpt(file:UploadFile=File()):

    """Create bulk or import data"""

    try:
        datas = [SkptDtSch]
        current_datetime = datetime.now()
        geo_dataframe = GeomService.file_to_geodataframe(file.file)

        for i, geo_data in geo_dataframe.iterrows():

            shp_data = SkptShpSch(geom=GeomService.single_geometry_to_wkt(geo_data.geometry),
                                  code=geo_data['code'],
                                  name=geo_data['name'],
                                  luas=RoundTwo(Decimal(geo_data['luas'])),
                                  no_sk=geo_data['no_sk'],
                                  status=geo_data['status'],
                                  tgl_sk=geo_data['tgl_sk'],
                                  jatuhtempo=geo_data['jatuhtempo'],
                                  project=geo_data['project'],
                                  desa=geo_data['desa'])
            
            project = await crud.project.get_by_name(name=shp_data.project)

            if project is None:
                raise NameNotFoundException(Project, name=shp_data.project)
            
            desa = await crud.desa.get_by_name(name=shp_data.desa)

            if desa is None:
                raise NameNotFoundException(Desa, name=shp_data.desa)
            
            planing = await crud.planing.get_by_project_id_desa_id(project_id=project.id, desa_id=desa.id)
            if planing is None:
                raise NameNotFoundException(Planing, name=f"{project.name} - {desa.name}")

            pt = await crud.ptsk.get_by_name(name=shp_data.name)

            if pt is None:
                new_pt =  PtskSch(name=shp_data.name, code= shp_data.code or "")
                
                pt = await crud.ptsk.create(obj_in=new_pt)
            
            sk = await crud.skpt.get_by_sk_number(number=shp_data.no_sk)

            if sk is None:
                 new_sk = SkptSch(ptsk_id=pt.id,
                          status=shp_data.status,
                          kategori=shp_data.kategori,
                          nomor_sk=shp_data.no_sk,
                          tanggal_tahun_SK=shp_data.tgl_sk,
                          tanggal_jatuh_tempo=shp_data.jatuhtempo)
                 
                 sk = await crud.skpt.create(obj_in=new_sk)
            else:
                update_sk = SkptSch(ptsk_id=pt.id,
                          status=shp_data.status,
                          kategori=shp_data.kategori,
                          nomor_sk=shp_data.no_sk,
                          tanggal_tahun_SK=shp_data.tgl_sk,
                          tanggal_jatuh_tempo=shp_data.jatuhtempo)
                
                sk = await crud.skpt.update(obj_current=sk, obj_new=update_sk)

            data = SkptDtSch(planing_id=planing.id, 
                             skpt_id=sk.id,
                             luas=shp_data.luas,
                             updated_at=current_datetime,
                             created_at=current_datetime,
                             geom=shp_data.geom)
            
            datas.append(data)

        objs = await crud.skptdt.create_all(obj_ins=datas)

    except:
        raise ImportFailedException(filename=file.filename)
    
    return create_response(data=objs)

@router.get("/export/shp", response_class=Response)
async def export_shp(filter_query:str = None):

    schemas = []
    
    results = await crud.skptdt.get_multi_by_dict(filter_query=filter_query)

    for data in results:
        sch = SkptShpSch(geom=wkt.dumps(wkb.loads(data.geom.data, hex=True)),
                      code=data.skpt.ptsk.code,
                      name=data.skpt.ptsk.name,
                      kategori=str(data.skpt.kategori),
                      luas=data.luas,
                      no_sk=data.nomor_sk,
                      status=str(data.skpt.status),
                      tgl_sk=data.skpt.tanggal_tahun_SK,
                      jatuhtempo=data.skpt.tanggal_jatuh_tempo,
                      project=data.project_name,
                      desa=data.desa_name)
        schemas.append(sch)

    if results:
        obj_name = results[0].__class__.__name__
        if len(results) == 1:
            obj_name = f"{obj_name}-{results[0].nomor_sk}"

    return GeomService.export_shp_zip(data=schemas, obj_name=obj_name)

# def StatusSK(status:str|None = None):
#     if status:
#         if status.replace(" ", "").lower() == "belumil":
#             return StatusSKEnum.Belum_Pengajuan_SK
#         elif status.replace(" ", "").lower() == "sudahil":
#             return StatusSKEnum.Final_SK
#         else:
#             return StatusSKEnum.Pengajuan_Awal_SK
#     else:
#         return StatusSKEnum.Belum_Pengajuan_SK