from uuid import UUID
from fastapi import APIRouter, status, Depends, HTTPException, Request
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, or_, and_, func
from sqlalchemy.orm import selectinload
from models import KjbDt, KjbHd, Pemilik, Manager, Sales, KjbPenjual, BundleHd, BundleDt
from models.request_peta_lokasi_model import RequestPetaLokasi
from models.worker_model import Worker
from schemas.kjb_dt_sch import (KjbDtSch, KjbDtCreateSch, KjbDtUpdateSch, KjbDtListSch, KjbDtListRequestPetlokSch)
from schemas.bidang_sch import BidangUpdateSch
from schemas.hasil_peta_lokasi_sch import HasilPetaLokasiUpdateSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.enum import StatusPetaLokasiEnum, WorkflowEntityEnum, JenisBayarEnum
from services.helper_service import BundleHelper, BidangHelper
from services.gcloud_task_service import GCloudTaskService
from shapely import wkt, wkb
from typing import Dict
import crud
import json


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[KjbDtSch], status_code=status.HTTP_201_CREATED)
async def create(sch: KjbDtCreateSch,
                 current_worker:Worker = Depends(crud.worker.get_current_user)):
    
    """Create a new object"""

    # alashak = await crud.kjb_dt.get_by_alashak(alashak=sch.alashak)
    # if alashak:
    #     raise HTTPException(status_code=409, detail=f"alashak {sch.alashak} ada di KJB lain ({alashak.kjb_code})")
        
    new_obj = await crud.kjb_dt.create(obj_in=sch, created_by_id=current_worker.id)
    new_obj = await crud.kjb_dt.get_by_id(id=new_obj.id)
    
    return create_response(data=new_obj)

# @router.get("", response_model=GetResponsePaginatedSch[KjbDtSch])
# async def get_list(
#             params: Params=Depends(), 
#             order_by:str = None, 
#             keyword:str = None, 
#             filter_query:str = None,
#             current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
#     """Gets a paginated list objects"""

#     query = select(KjbDt).select_from(KjbDt
#                     ).join(KjbHd, KjbHd.id == KjbDt.kjb_hd_id)
    
#     if keyword:
#         query = query.filter(
#             or_(
#                 KjbDt.alashak.ilike(f'%{keyword}%'),
#                 KjbHd.code.ilike(f'%{keyword}%')
#             )
#         )

#     if filter_query:
#         filter_query = json.loads(filter_query)
#         for key, value in filter_query.items():
#                 query = query.where(getattr(KjbDt, key) == value)

#     objs = await crud.kjb_dt.get_multi_paginated_ordered(params=params, query=query)
#     return create_response(data=objs)

@router.get("", response_model=GetResponsePaginatedSch[KjbDtListSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str = None,
            filter:str = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.kjb_dt.get_multi_paginated_ordered(params=params, keyword=keyword, filter=filter)

    items = []
    reference_ids = [kjb_dt.kjb_hd_id for kjb_dt in objs.data.items]
    workflows = await crud.workflow.get_by_reference_ids(reference_ids=reference_ids, entity=WorkflowEntityEnum.KJB)

    for obj in objs.data.items:
        workflow = next((wf for wf in workflows if wf.reference_id == obj.kjb_hd_id), None)
        if workflow:
            obj.status_workflow = workflow.last_status
            obj.step_name_workflow = workflow.step_name

        items.append(obj)

    objs.data.items = items

    return create_response(data=objs)

@router.get("/tanda-terima/notaris", response_model=GetResponsePaginatedSch[KjbDtSch])
async def get_list(
                params: Params=Depends(),
                keyword: str = None):
    
    """Gets a paginated list objects"""
    query = select(KjbDt)

    query = query.select_from(KjbDt)
    query = query.outerjoin(RequestPetaLokasi, KjbDt.id == RequestPetaLokasi.kjb_dt_id
                ).join(KjbHd, KjbHd.id == KjbDt.kjb_hd_id
                ).outerjoin(KjbPenjual, KjbHd.id == KjbPenjual.kjb_hd_id
                ).outerjoin(Pemilik, Pemilik.id == KjbPenjual.pemilik_id
                ).join(Manager, Manager.id == KjbHd.manager_id
                ).join(Sales, Sales.id == KjbHd.sales_id
                ).where(or_(KjbHd.is_draft != True, KjbHd.is_draft is None))
    
    if keyword and keyword != "":
        query = query.filter(
            or_(
                KjbDt.alashak.ilike(f'%{keyword}%'),
                Pemilik.name.ilike(f'%{keyword}%'),
                KjbHd.code.ilike(f'%{keyword}%'),
                KjbHd.nama_group.ilike(f'%{keyword}%'),
                KjbHd.mediator.ilike(f'%{keyword}%'),
                Manager.name.ilike(f'%{keyword}%'),
                Sales.name.ilike(f'%{keyword}%')
            )
        )
    
    query = query.where(KjbDt.request_peta_lokasi == None)
    
    objs = await crud.kjb_dt.get_multi_paginated(params=params, query=query)
    return create_response(data=objs)

@router.get("/request/petlok", response_model=GetResponsePaginatedSch[KjbDtListRequestPetlokSch])
async def get_list_for_petlok(kjb_hd_id:UUID | None, keyword:str | None = None, no_order:str | None = None, params: Params=Depends()):
    
    """Gets a paginated list objects"""

    query = select(KjbDt).select_from(KjbDt
                                     ).outerjoin(RequestPetaLokasi, KjbDt.id == RequestPetaLokasi.kjb_dt_id
                                     ).where(and_(
                                                    KjbDt.kjb_hd_id == kjb_hd_id,
                                                    KjbDt.status_peta_lokasi == StatusPetaLokasiEnum.Lanjut_Peta_Lokasi,
                                                    or_(
                                                        RequestPetaLokasi.code == no_order,
                                                        KjbDt.request_peta_lokasi == None
                                                    )
                                                )
                                            )
    if keyword:
            query = query.filter(
                or_(
                    RequestPetaLokasi.code.ilike(f'%{keyword}%'),
                    KjbDt.alashak.ilike(f'%{keyword}%')
                )
            )

    query = query.distinct()

    query = query.options(selectinload(KjbDt.kjb_hd))

    objs = await crud.kjb_dt.get_multi_paginated(params=params, query=query)
    return create_response(data=objs)

@router.get("/request/petlok/no-page", response_model=GetResponseBaseSch[list[KjbDtListRequestPetlokSch]])
async def get_list_for_petlok_no_page(kjb_hd_id:UUID | None, keyword:str | None = None, no_order:str | None = None):
    
    """Gets a paginated list objects"""

    query = select(KjbDt).select_from(KjbDt
                                     ).outerjoin(RequestPetaLokasi, KjbDt.id == RequestPetaLokasi.kjb_dt_id
                                     ).where(and_(
                                                    KjbDt.kjb_hd_id == kjb_hd_id,
                                                    KjbDt.status_peta_lokasi == StatusPetaLokasiEnum.Lanjut_Peta_Lokasi,
                                                    or_(
                                                        RequestPetaLokasi.code == no_order,
                                                        KjbDt.request_peta_lokasi == None
                                                    )
                                                )
                                            )
    if keyword:
            query = query.filter(
                or_(
                    RequestPetaLokasi.code.ilike(f'%{keyword}%'),
                    KjbDt.alashak.ilike(f'%{keyword}%')
                )
            )

    query = query.distinct()
    query = query.options(selectinload(KjbDt.kjb_hd)
                ).options(selectinload(KjbDt.pemilik)
                ).options(selectinload(KjbDt.jenis_surat)
                ).options(selectinload(KjbDt.bundlehd
                            ).options(selectinload(BundleHd.bundledts
                                        ).options(selectinload(BundleDt.dokumen))
                            )
                ).options(selectinload(KjbDt.tanda_terima_notaris_hd)
                ).options(selectinload(KjbDt.request_peta_lokasi)
                ).options(selectinload(KjbDt.hasil_peta_lokasi))

    objs = await crud.kjb_dt.get_multi_no_page(query=query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[KjbDtSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.kjb_dt.get_by_id(id=id)
    if obj:
        obj = KjbDtSch.from_orm(obj)
        workflow = await crud.workflow.get_by_reference_id(reference_id=obj.kjb_hd_id)
        if workflow:
            obj = KjbDtSch.from_orm(obj)
            obj.status_workflow = workflow.last_status
            obj.step_name_workflow = workflow.step_name

        return create_response(data=obj)
    else:
        raise IdNotFoundException(KjbDt, id)

@router.put("/{id}", response_model=PutResponseBaseSch[KjbDtSch])
async def update(id:UUID,
                 sch:KjbDtUpdateSch,
                 request:Request,
                 current_worker:Worker = Depends(crud.worker.get_current_user)):
    
    """Update a obj by its id"""
    
    db_session = db.session
    obj_current = await crud.kjb_dt.get_by_id(id=id)

    if not obj_current:
        raise IdNotFoundException(KjbDt, id)
    
    obj_updated = await crud.kjb_dt.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id, db_session=db_session)
    obj_updated = await crud.kjb_dt.get_by_id(id=obj_updated.id)

    url = f'{request.base_url}landrope/kjbdt/task/update-to-bidang'
    GCloudTaskService().create_task(payload={"id":str(obj_updated.id)}, base_url=url)

    return create_response(data=obj_updated)

@router.post("/task/update-to_bidang")
async def update_alashak_bidang_bundle(payload:Dict):

    db_session = db.session

    id = payload.get("id", None)
    obj = await crud.kjb_dt.get(id=id)

    if not obj:
        raise IdNotFoundException(KjbHd, id)
    
    hasil_peta_lokasi = await crud.hasil_peta_lokasi.get_by_kjb_dt_id(kjb_dt_id=obj.id)
    
    if hasil_peta_lokasi:
        await BidangHelper().update_from_kjb_to_bidang(kjb_dt_id=obj.id, db_session=db_session, worker_id=obj.updated_by_id)

    if obj.bundle_hd_id:
        bundle_hd = await crud.bundlehd.get_by_id(id=obj.bundle_hd_id)
        await BundleHelper().merge_alashak(bundle=bundle_hd, worker_id=obj.updated_by_id, alashak=obj.alashak, db_session=db_session)
    
    await db_session.commit()

    return {"message" : "successfully"}
