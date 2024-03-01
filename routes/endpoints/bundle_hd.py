from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_, or_
from models.bundle_model import BundleHd
from models.worker_model import Worker
from models.bidang_model import Bidang
from models.kjb_model import KjbHd, KjbDt
from models.planing_model import Planing
from schemas.bundle_hd_sch import (BundleHdSch, BundleHdCreateSch, BundleHdUpdateSch, BundleHdByIdSch)
from schemas.bundle_dt_sch import BundleDtCreateSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.generator import generate_code
from models.code_counter_model import CodeCounterEnum
import crud
import json


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[BundleHdSch], status_code=status.HTTP_201_CREATED)
async def create(sch: BundleHdCreateSch,
                current_worker: Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
        
    new_obj = await crud.bundlehd.create_and_generate(obj_in=sch, created_by_id=current_worker.id)
    new_obj = await crud.bundlehd.get_by_id(id=new_obj.id)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[BundleHdSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(BundleHd
                            ).outerjoin(Bidang, Bidang.bundle_hd_id == BundleHd.id
                            ).outerjoin(KjbDt, KjbDt.bundle_hd_id == BundleHd.id
                            ).outerjoin(Planing, Planing.id == BundleHd.planing_id)
    
    if keyword:
        query = query.filter(
            or_(
                BundleHd.code.ilike(f'%{keyword}%'),
                Planing.name.ilike(f'%{keyword}%'),
                KjbDt.alashak.ilike(f'%{keyword}%'),
                Bidang.id_bidang.ilike(f'%{keyword}%')
            ))
    
    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
            query = query.where(getattr(BundleHd, key) == value)
    
    query = query.distinct()

    objs = await crud.bundlehd.get_multi_paginated_ordered(params=params, query=query, order_by="updated_at")

    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[BundleHdByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.bundlehd.get_by_id(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(BundleHd, id)

@router.put("/{id}", response_model=PutResponseBaseSch[BundleHdSch])
async def update(id:UUID, 
                 sch:BundleHdUpdateSch,
                 current_worker: Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.bundlehd.get(id=id)

    if not obj_current:
        raise IdNotFoundException(BundleHd, id)
    
    obj_updated = await crud.bundlehd.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    obj_updated = await crud.bundlehd.get_by_id(id=obj_updated.id)
    return create_response(data=obj_updated)

@router.put("regenerate/{id}", response_model=PutResponseBaseSch[BundleHdSch])
async def regenerate(id:UUID,
                     current_worker: Worker = Depends(crud.worker.get_active_worker)):

    """Get an object by id"""

    obj = await crud.bundlehd.get(id=id)
    if obj is None:
        raise IdNotFoundException(BundleHd, id)
    
    db_session = db.session

    bundle_dts = await crud.bundledt.get_by_bundle_hd_id(bundle_hd_id=obj.id)
    list_ids = [dt.dokumen_id for dt in bundle_dts]
    dokumens = await crud.dokumen.get_not_in_by_ids(list_ids=list_ids)
    
    if dokumens:
        for doc in dokumens:
            if doc.is_active == False:
                continue
            code = obj.code + doc.code
            bundle_dt_create = BundleDtCreateSch(code=code, 
                                        dokumen_id=doc.id,
                                        bundle_hd_id=obj.id)
            
            await crud.bundledt.create(obj_in=bundle_dt_create, db_session=db_session, with_commit=False)
    
    obj_new = obj

    obj_updated = await crud.bundlehd.update(obj_current=obj, 
                                             obj_new=obj_new, 
                                             db_session=db_session, 
                                             updated_by_id=current_worker.id,
                                             with_commit=True)
    
    obj_updated = await crud.bundlehd.get_by_id(id=obj_updated.id)
    
    return create_response(data=obj_updated)

   