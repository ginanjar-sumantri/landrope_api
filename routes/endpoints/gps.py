from uuid import UUID
from fastapi import APIRouter, status, Depends, UploadFile, File, HTTPException, Response
from fastapi_pagination import Params
from sqlmodel import select
from sqlalchemy.orm import selectinload
import crud
from models.gps_model import Gps, StatusGpsEnum
from models.worker_model import Worker
from schemas.gps_sch import (GpsSch, GpsRawSch, GpsCreateSch, GpsUpdateSch, GpsValidator, GpsShpSch, GpsParamSch)
from schemas.bidang_sch import BidangGpsValidator
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, ImportFailedException)
from services.geom_service import GeomService
from services.helper_service import HelperService
from shapely.geometry import shape
from geoalchemy2.shape import to_shape
from common.rounder import RoundTwo
from decimal import Decimal
from shapely import wkt, wkb
from datetime import date


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[GpsRawSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch:GpsCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    draft = await crud.draft.get(id=sch.draft_id)
    
    geom = None
    if draft:
        geom = wkt.dumps(wkb.loads(draft.geom.data, hex=True))

    obj_new = GpsSch(**sch.dict(), geom=geom)
        
    new_obj = await crud.gps.create(obj_in=obj_new, created_by_id=current_worker.id)
    new_obj = await crud.gps.get_by_id(id=new_obj.id)

    if draft:
        await crud.draft.remove(id=draft.id)

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

    obj = await crud.gps.get_by_id(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Gps, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[GpsRawSch])
async def update(id:UUID, 
                sch:GpsUpdateSch,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Update a obj by its id"""

    obj_current = await crud.gps.get_by_id(id=id)

    if not obj_current:
        raise IdNotFoundException(Gps, id)
    
    if obj_current.geom :
        obj_current.geom = wkt.dumps(wkb.loads(obj_current.geom.data, hex=True))

    obj_updated = GpsSch(**sch.dict(), geom=obj_current.geom)
    
    draft = await crud.draft.get(id=sch.draft_id)
    if draft:
        if draft.geom:
            obj_updated.geom = wkt.dumps(wkb.loads(draft.geom.data, hex=True)) 

        
    obj_updated = await crud.gps.update(obj_current=obj_current, obj_new=obj_updated, updated_by_id=current_worker.id)
    obj_updated = await crud.gps.get_by_id(id=obj_updated.id)

    if draft:
        await crud.draft.remove(id=draft.id)
    
    return create_response(data=obj_updated)

@router.get("/validasi/alashak", response_model=GetResponseBaseSch[GpsValidator])
async def get_by_alashak(alashak:str | None = None):

    """Get an object by id"""

    gps_objs = await crud.gps.get_multi_by_alashak(alashak=alashak)
    gps_objs = [GpsRawSch.from_orm(gps) for gps in gps_objs]

    bidang_objs = await crud.bidang.get_multi_by_alashak(alashak=alashak)
    bidang_objs = [BidangGpsValidator.from_orm(bidang) for bidang in bidang_objs]

    obj = GpsValidator(bidang=bidang_objs, gps=gps_objs)
    
    return create_response(data=obj)

@router.get("/export/shp", response_class=Response)
async def export_shp(id:UUID):
    
    """Export SHP"""

    data = []
    obj_current = await crud.gps.get_by_id(id=id)

    if not obj_current:
        raise IdNotFoundException(Gps, id)

    gps = GpsShpSch(**obj_current.dict(exclude={"geom"}),
                    ptsk_name=obj_current.ptsk_name,
                    nomor_sk=obj_current.nomor_sk,
                    desa_name=obj_current.desa_name,
                    project_name=obj_current.project_name,
                    geom=wkt.dumps(wkb.loads(obj_current.geom.data, hex=True)))
    
    data.append(gps)

    return GeomService.export_shp_zip(data=data, obj_name=f"gps-{date.today()}")

@router.post("/export/bulk/shp", response_class=Response)
async def export_bulk_shp(param:GpsParamSch):
    
    """Export SHP"""
    data = []
    objs = await crud.gps.get_multi_export_shp(param=param)

    data = [GpsShpSch(**obj.dict(exclude={"geom"}),
                    ptsk_name=obj.ptsk_name,
                    nomor_sk=obj.nomor_sk,
                    desa_name=obj.desa_name,
                    project_name=obj.project_name,
                    geom=wkt.dumps(wkb.loads(obj.geom.data, hex=True))) for obj in objs]

    return GeomService.export_shp_zip(data=data, obj_name=f"gps-{date.today()}")




