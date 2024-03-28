from uuid import UUID
from fastapi import APIRouter, status, Depends, HTTPException
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, or_, and_, func
from models import KjbDt, KjbHd, Pemilik, Manager, Sales, KjbPenjual
from models.request_peta_lokasi_model import RequestPetaLokasi
from models.worker_model import Worker
from schemas.kjb_dt_sch import (KjbDtSch, KjbDtCreateSch, KjbDtUpdateSch, KjbDtListSch, KjbDtListRequestPetlokSch)
from schemas.bidang_sch import BidangUpdateSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.enum import StatusPetaLokasiEnum
from services.helper_service import BundleHelper, BidangHelper
from shapely import wkt, wkb
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
async def get_list_for_petlok(keyword:str | None, kjb_hd_id:UUID | None, no_order:str | None = None, params: Params=Depends()):
    
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

    objs = await crud.kjb_dt.get_multi_paginated(params=params, query=query)
    return create_response(data=objs)

@router.get("/request/petlok/no-page", response_model=GetResponseBaseSch[list[KjbDtListRequestPetlokSch]])
async def get_list_for_petlok_no_page(keyword:str | None, kjb_hd_id:UUID | None, no_order:str | None = None):
    
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

    objs = await crud.kjb_dt.get_multi_no_page(query=query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[KjbDtSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.kjb_dt.get_by_id(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(KjbDt, id)

@router.put("/{id}", response_model=PutResponseBaseSch[KjbDtSch])
async def update(id:UUID, sch:KjbDtUpdateSch,
                 current_worker:Worker = Depends(crud.worker.get_current_user)):
    
    """Update a obj by its id"""
    
    db_session = db.session
    obj_current = await crud.kjb_dt.get_by_id(id=id)

    # alashak = await crud.kjb_dt.get_by_alashak_and_kjb_hd_id(alashak=sch.alashak, kjb_hd_id=sch.kjb_hd_id)
    # if alashak :
    #     raise HTTPException(status_code=409, detail=f"alashak {sch.alashak} ada di KJB lain ({alashak.kjb_code})")

    if not obj_current:
        raise IdNotFoundException(KjbDt, id)

    if obj_current.hasil_peta_lokasi:
        # tahap_detail_current = await crud.tahap_detail.get_by_bidang_id(bidang_id=obj_current.hasil_peta_lokasi.bidang_id)
        if obj_current.hasil_peta_lokasi.bidang:
            bidang_current = await crud.bidang.get_by_id(id=obj_current.hasil_peta_lokasi.bidang_id)

            if bidang_current.geom :
                bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))

            if bidang_current.geom :
                if isinstance(bidang_current.geom, str):
                    pass
                else:
                    bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))
            if bidang_current.geom_ori :
                if isinstance(bidang_current.geom_ori, str):
                    pass
                else:
                    bidang_current.geom_ori = wkt.dumps(wkb.loads(bidang_current.geom_ori.data, hex=True))
            
            if bidang_current.harga_akta != sch.harga_akta or bidang_current.harga_transaksi != sch.harga_transaksi or bidang_current.alashak != sch.alashak:
                if len([inv for inv in bidang_current.invoices if inv.is_void == False]) == 0:
                    bidang_updated = BidangUpdateSch(harga_akta=sch.harga_akta, harga_transaksi=sch.harga_transaksi, alashak=sch.alashak)
                    await crud.bidang.update(obj_current=bidang_current, obj_new=bidang_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)
                else:
                    if bidang_current.alashak != sch.alashak:
                        bidang_updated = BidangUpdateSch(alashak=sch.alashak)
                        await crud.bidang.update(obj_current=bidang_current, obj_new=bidang_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)
                        bundle = await crud.bundlehd.get_by_id(id=obj_current.bundle_hd_id)
                        await BundleHelper().merge_alashak(bundle=bundle, alashak=sch.alashak, worker_id=current_worker.id, db_session=db_session)
    
    obj_updated = await crud.kjb_dt.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)
    await db_session.commit()

    obj_updated = await crud.kjb_dt.get_by_id(id=obj_updated.id)
    return create_response(data=obj_updated)
