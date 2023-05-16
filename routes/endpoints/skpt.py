from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, File
from fastapi_pagination import Params
import crud
from models.skpt_model import Skpt, StatusSKEnum, KategoriEnum
from schemas.skpt_sch import (SkptSch, SkptCreateSch, SkptUpdateSch, SkptRawSch)
from schemas.ptsk_sch import (PtskSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, ImportResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, ImportFailedException)
from services.geom_service import GeomService
from shapely.geometry import shape
from geoalchemy2.shape import to_shape
from common.rounder import RoundTwo
from decimal import Decimal
import json

router = APIRouter()

@router.post("", response_model=PostResponseBaseSch[SkptRawSch], status_code=status.HTTP_201_CREATED)
async def create(sch: SkptCreateSch = Depends(SkptCreateSch.as_form), file:UploadFile = None):
    
    """Create a new object"""
    
    obj_current = await crud.skpt.get_by_sk_number(number=sch.nomor_sk)
    if obj_current:
        raise NameExistException(Skpt, name=sch.nomor_sk)
    
    if file:
        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry

        sch = SkptSch(ptsk_id=sch.ptsk_id,
                      status=sch.status,
                      kategori=sch.kategori,
                      luas=RoundTwo(sch.luas),
                      nomor_sk=sch.nomor_sk,
                      tanggal_tahun_SK=sch.tanggal_tahun_SK,
                      tanggal_jatuh_tempo=sch.tanggal_jatuh_tempo,
                      geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
    new_obj = await crud.skpt.create(obj_in=sch)
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[SkptRawSch])
async def get_list(params:Params = Depends(), order_by:str=None, keyword:str=None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    if filter_query:
        filter_query = json.loads(filter_query)

    objs = await crud.skpt.get_multi_paginate_ordered_with_keyword_dict(params=params, 
                                                                        order_by=order_by, 
                                                                        keyword=keyword, 
                                                                        filter_query=filter_query,
                                                                        join=True)
    
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[SkptRawSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.skpt.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Skpt, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[SkptRawSch])
async def update(id:UUID, sch:SkptUpdateSch = Depends(SkptUpdateSch.as_form), file:UploadFile = None):
    
    """Update a obj by its id"""

    obj_current = await crud.skpt.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Skpt, id)
    
    if obj_current.geom:
        obj_current.geom = to_shape(obj_current.geom).__str__()
    
    if file:
        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry
        
        sch = SkptSch(ptsk_id=sch.ptsk_id,
                      status=sch.status,
                      kategori=sch.kategori,
                      luas=RoundTwo(sch.luas),
                      nomor_sk=sch.nomor_sk,
                      tanggal_tahun_SK=sch.tanggal_tahun_SK,
                      tanggal_jatuh_tempo=sch.tanggal_jatuh_tempo,
                      geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
    obj_updated = await crud.skpt.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

@router.post("/bulk", response_model=ImportResponseBaseSch[SkptRawSch], status_code=status.HTTP_201_CREATED)
async def bulk_create(file:UploadFile=File()):

    """Create bulk or import data"""

    try:
        geo_dataframe = GeomService.file_to_geodataframe(file.file)

        for i, geo_data in geo_dataframe.iterrows():
            
            pt_name = geo_data['NAMA_PT']
            pt = await crud.ptsk.get_by_name(name=pt_name)

            if pt is None:
                new_pt =  PtskSch(name=geo_data['NAMA_PT'],
                          code="")
                
                pt = await crud.ptsk.create(obj_in=new_pt)

            luas:Decimal = RoundTwo(Decimal(geo_data['LUAS']))
            sch = SkptSch(ptsk_id=pt.id,
                          status=StatusSK(geo_data['STATUS']),
                          kategori=KategoriEnum.SK_ASG,
                          luas=luas,
                          geom=GeomService.single_geometry_to_wkt(geo_data.geometry))

            obj = await crud.skpt.create(obj_in=sch)

    except:
        raise ImportFailedException(filename=file.filename)
    
    return create_response(data=obj)

def StatusSK(status:str|None = None):
    if status:
        if status.replace(" ", "").lower() == "belumil":
            return StatusSKEnum.Belum_Pengajuan_SK
        elif status.replace(" ", "").lower() == "sudahil":
            return StatusSKEnum.Final_SK
        else:
            return StatusSKEnum.Pengajuan_Awal_SK
    else:
        return StatusSKEnum.Belum_Pengajuan_SK