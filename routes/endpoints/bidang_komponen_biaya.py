from uuid import UUID
from fastapi import APIRouter, status, Depends, HTTPException
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from models.bidang_komponen_biaya_model import BidangKomponenBiaya
from models.worker_model import Worker
from schemas.bidang_komponen_biaya_sch import (BidangKomponenBiayaSch, BidangKomponenBiayaCreateSch, BidangKomponenBiayaUpdateSch, BidangKomponenBiayaListSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.generator import generate_code
from models.code_counter_model import CodeCounterEnum
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[BidangKomponenBiayaSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: BidangKomponenBiayaCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    db_session = db.session
    sch.is_void = False
        
    new_obj = await crud.bidang_komponen_biaya.create(obj_in=sch, created_by_id=current_worker.id, db_session=db_session)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[BidangKomponenBiayaListSch])
async def get_list(
                params: Params=Depends(), 
                order_by:str = None, 
                keyword:str = None, 
                filter_query:str=None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.bidang_komponen_biaya.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[BidangKomponenBiayaSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.bidang_komponen_biaya.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(BidangKomponenBiaya, id)

@router.put("/{id}", response_model=PutResponseBaseSch[BidangKomponenBiayaSch])
async def update(id:UUID, sch:BidangKomponenBiayaUpdateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.bidang_komponen_biaya.get(id=id)

    if not obj_current:
        raise IdNotFoundException(BidangKomponenBiaya, id)
    
    # sch.is_void = obj_current.is_void
    obj_updated = await crud.bidang_komponen_biaya.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)

@router.post("/cloud-task-is-use")
async def update_komponen_is_use(id:UUID):

    """Task Update Komponen Biaya Is Use"""

    obj_current = await crud.bidang_komponen_biaya.get(id=id)

    if not obj_current:
        raise IdNotFoundException(BidangKomponenBiaya, id)
    
    sch = BidangKomponenBiayaUpdateSch(**obj_current.dict())
    sch.is_use = True
    
    await crud.bidang_komponen_biaya.update(obj_current=obj_current, obj_new=sch)
    
    return {"message" : "successfully remove link bidang and kelengkapan dokumen"}

@router.post("/cloud-task-is-not-use")
async def update_komponen_is_use(id:UUID):

    """Task Update Komponen Biaya Is Use"""

    obj_current = await crud.bidang_komponen_biaya.get(id=id)

    if not obj_current:
        raise IdNotFoundException(BidangKomponenBiaya, id)
    
    sch = BidangKomponenBiayaUpdateSch(**obj_current.dict())
    sch.is_use = False
    
    await crud.bidang_komponen_biaya.update(obj_current=obj_current, obj_new=sch)
    
    return {"message" : "successfully remove link bidang and kelengkapan dokumen"} 
   