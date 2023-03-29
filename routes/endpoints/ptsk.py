from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, File
from fastapi_pagination import Params
import crud
from models.ptsk_model import Ptsk
from schemas.ptsk_sch import (PtskSch, PtskCreateSch, PtskUpdateSch, PtskRawSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException)
from services.geom_service import GeomService
from shapely.geometry import shape
from geoalchemy2.shape import to_shape

router = APIRouter()

@router.post("", response_model=PostResponseBaseSch[PtskRawSch], status_code=status.HTTP_201_CREATED)
async def create(sch: PtskCreateSch = Depends(PtskCreateSch.as_form), file:UploadFile = None):
    
    """Create a new object"""
    
    obj_current = await crud.ptsk.get_by_name(name=sch.name)
    if obj_current:
        raise NameExistException(Ptsk, name=sch.name)
    
    if file:
        buffer = await file.read()

        geo_dataframe = GeomService.file_to_geo_dataframe(buffer)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry

        sch = PtskSch(name=sch.name, 
                      code=sch.code,
                      status=sch.status,
                      kategori=sch.kategori,
                      luas=sch.luas,
                      nomor_sk=sch.nomor_sk,
                      tanggal_tahun_SK=sch.tanggal_tahun_SK,
                      tanggal_jatuh_tempo=sch.tanggal_jatuh_tempo,
                      geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
    new_obj = await crud.ptsk.create(obj_in=sch)
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[PtskRawSch])
async def get_list(params:Params = Depends()):
    
    """Gets a paginated list objects"""

    objs = await crud.ptsk.get_multi_paginated(params=params)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[PtskRawSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.ptsk.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Ptsk, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[PtskRawSch])
async def update(id:UUID, sch:PtskUpdateSch, file:UploadFile = None):
    
    """Update a obj by its id"""

    obj_current = await crud.planing.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Ptsk, id)
    
    if obj_current.geom:
        obj_current.geom = to_shape(obj_current.geom).__str__()
    
    if file:
        buffer = await file.read()

        geo_dataframe = GeomService.file_to_geo_dataframe(buffer)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry
        
        sch = PtskSch(name=sch.name, 
                      code=sch.code,
                      status=sch.status,
                      kategori=sch.kategori,
                      luas=sch.luas,
                      nomor_sk=sch.nomor_sk,
                      tanggal_tahun_SK=sch.tanggal_tahun_SK,
                      tanggal_jatuh_tempo=sch.tanggal_jatuh_tempo,
                      geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
    obj_updated = await crud.ptsk.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

