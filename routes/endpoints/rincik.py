from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, File
from fastapi_pagination import Params
import crud
from models.rincik_model import Rincik
from schemas.rincik_sch import (RincikSch, RincikCreateSch, RincikUpdateSch, RincikRawSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException)
from services.geom_service import GeomService
from shapely.geometry import shape
from geoalchemy2.shape import to_shape

router = APIRouter()

@router.post("", response_model=PostResponseBaseSch[RincikRawSch], status_code=status.HTTP_201_CREATED)
async def create(sch: RincikCreateSch = Depends(RincikCreateSch.as_form), file:UploadFile = None):
    
    """Create a new object"""
    
    obj_current = await crud.rincik.get_by_id_rincik(name=sch.id_rincik)
    if obj_current:
        raise NameExistException(Rincik, name=sch.id_rincik)
    
    if file:
        buffer = await file.read()

        geo_dataframe = GeomService.file_to_geo_dataframe(buffer)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry

        sch = RincikSch(id_rincik=sch.id_rincik,
                        estimasi_nama_pemilik=sch.estimasi_nama_pemilik,
                        luas=sch.luas,
                        category=sch.category,
                        alas_hak=sch.alas_hak,
                        jenis_dokumen=sch.jenis_dokumen,
                        no_peta=sch.no_peta,
                        jenis_lahan_id=sch.jenis_lahan_id,
                        planing_id=sch.planing_id,
                        ptsk_id=sch.ptsk_id,
                        geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
    new_obj = await crud.rincik.create(obj_in=sch)
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[RincikRawSch])
async def get_list(params:Params = Depends()):
    
    """Gets a paginated list objects"""

    objs = await crud.rincik.get_multi_paginated(params=params)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[RincikRawSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.rincik.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Rincik, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[RincikRawSch])
async def update(id:UUID, sch:RincikUpdateSch = Depends(RincikUpdateSch.as_form), file:UploadFile = None):
    
    """Update a obj by its id"""

    obj_current = await crud.rincik.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Rincik, id)
    
    if obj_current.geom:
        obj_current.geom = to_shape(obj_current.geom).__str__()
    
    if file:
        buffer = await file.read()

        geo_dataframe = GeomService.file_to_geo_dataframe(buffer)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry

        sch = RincikSch(id_rincik=sch.id_rincik,
                        estimasi_nama_pemilik=sch.estimasi_nama_pemilik,
                        luas=sch.luas,
                        category=sch.category,
                        alas_hak=sch.alas_hak,
                        jenis_dokumen=sch.jenis_dokumen,
                        no_peta=sch.no_peta,
                        jenis_lahan_id=sch.jenis_lahan_id,
                        planing_id=sch.planing_id,
                        ptsk_id=sch.ptsk_id,
                        geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
    obj_updated = await crud.rincik.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

