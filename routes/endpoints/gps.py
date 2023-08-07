from uuid import UUID
from fastapi import APIRouter, status, Depends, UploadFile, File, HTTPException
from fastapi_pagination import Params
import crud
from models.gps_model import Gps, StatusGpsEnum
from models.worker_model import Worker
from schemas.gps_sch import (GpsSch, GpsRawSch, GpsCreateSch, GpsUpdateSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, ImportFailedException)
from services.geom_service import GeomService
from shapely.geometry import shape
from geoalchemy2.shape import to_shape
from common.rounder import RoundTwo
from decimal import Decimal
from shapely import wkt, wkb


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[GpsRawSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch:GpsCreateSch=Depends(GpsCreateSch.as_form), 
            file:UploadFile = File(),
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    if file is None:
        ImportFailedException()

    geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

    if geo_dataframe.geometry[0].geom_type == "LineString":
        polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
        geo_dataframe['geometry'] = polygon.geometry


    sch = GpsSch(nama=geo_dataframe['pemilik'][0],
                alas_hak=geo_dataframe['alas_hak'][0],
                luas=RoundTwo(Decimal(geo_dataframe['luas_surat'][0])),
                desa=geo_dataframe['desa'][0],
                petunjuk=geo_dataframe['penunjuk_b'][0],
                pic=geo_dataframe['pic'][0],
                group=geo_dataframe['group'][0],
                status=sch.status,
                skpt_id=sch.skpt_id,
                geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry)
        )
        
    new_obj = await crud.gps.create(obj_in=sch, created_by_id=current_worker.id)
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[GpsRawSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str = None,
            current_user:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.gps.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[GpsRawSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.gps.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Gps, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[GpsRawSch])
async def update(id:UUID, sch:GpsUpdateSch=Depends(GpsUpdateSch.as_form), file:UploadFile = None,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.gps.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Gps, id)
    
    if obj_current.geom :
        obj_current.geom = wkt.dumps(wkb.loads(obj_current.geom.data, hex=True))
    
    if file:
        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry

        sch = GpsSch(nama=sch.nama,
                alas_hak=sch.alas_hak,
                luas=RoundTwo(Decimal(sch.luas)),
                desa=sch.desa,
                petunjuk=sch.petunjuk,
                pic=sch.pic,
                group=sch.group,
                status=sch.status,
                skpt_id=sch.skpt_id,
                geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry)
        )
    
    obj_updated = await crud.gps.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)
