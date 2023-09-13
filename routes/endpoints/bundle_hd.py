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
    
    return create_response(data=new_obj)

# @router.get("", response_model=GetResponsePaginatedSch[BundleHdSch])
# async def get_list(
#             params: Params=Depends(), 
#             order_by:str = None, 
#             keyword:str = None, 
#             filter_query:str = None,
#             current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
#     """Gets a paginated list objects"""

#     objs = await crud.bundlehd.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
#     return create_response(data=objs)

@router.get("", response_model=GetResponsePaginatedSch[BundleHdSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(BundleHd).select_from(BundleHd
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

    objs = await crud.bundlehd.get_multi_paginated(params=params, query=query)

    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[BundleHdByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.bundlehd.get(id=id)
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
    return create_response(data=obj_updated)

@router.put("regenerate/{id}", response_model=PutResponseBaseSch[BundleHdSch])
async def regenerate(id:UUID,
                     current_worker: Worker = Depends(crud.worker.get_active_worker)):

    """Get an object by id"""

    obj = await crud.bundlehd.get(id=id)
    if obj is None:
        raise IdNotFoundException(BundleHd, id)
    
    db_session = db.session
    dokumens = await crud.dokumen.get_all()
    for doc in dokumens:
        bundle_dt = await crud.bundledt.get_by_bundle_hd_id_and_dokumen_id(bundle_hd_id=id, dokumen_id=doc.id)
        if bundle_dt is None:
            code = obj.code + doc.code
            bundle_dt_create = BundleDtCreateSch(code=code, 
                                          dokumen_id=doc.id,
                                          bundle_hd_id=obj.id)
            
            await crud.bundledt.create(obj_in=bundle_dt_create, db_session=db_session, with_commit=False)
    
    obj_new = BundleHd(**obj.dict())

    obj_updated = await crud.bundlehd.update(obj_current=obj, 
                                             obj_new=obj_new, 
                                             db_session=db_session, 
                                             updated_by_id=current_worker.id,
                                             with_commit=True)
    
    return create_response(data=obj_updated)

@router.get("/test/query/first")
async def test_query(keyword:str):
    bundle = await crud.bundlehd.get_by_keyword(keyword=keyword)
    # bundle = await crud.bundlehd.get(id=keyword)

    return bundle.dict()

   