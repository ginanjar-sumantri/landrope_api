from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, or_, and_
from models.tahap_model import Tahap, TahapDetail
from models.bidang_model import Bidang
from models.worker_model import Worker
from models.planing_model import Planing
from models.skpt_model import Skpt
from models.ptsk_model import Ptsk
from schemas.tahap_sch import (TahapSch, TahapByIdSch, TahapCreateSch, TahapUpdateSch)
from schemas.tahap_detail_sch import TahapDetailCreateSch, TahapDetailUpdateSch, TahapDetailExtSch
from schemas.section_sch import SectionUpdateSch
from schemas.bidang_sch import BidangSrcSch, BidangForTahapByIdSch, BidangUpdateSch
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException)
from common.enum import StatusBidangEnum, JenisBidangEnum
from shapely import wkb, wkt
import crud
import json

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[TahapSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: TahapCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    db_session = db.session

    obj_planing = await crud.planing.get(id=sch.planing_id)
    obj_section = obj_planing.project.section

    new_last_tahap = (obj_section.last_tahap or 0) + 1

    updated_section = SectionUpdateSch(last_tahap=new_last_tahap)
    await crud.section.update(obj_current=obj_section, obj_new=updated_section, 
                              db_session=db_session, with_commit=False, updated_by_id=current_worker.id)
    
    sch.nomor_tahap = new_last_tahap

    new_obj = await crud.tahap.create(obj_in=sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)

    for dt in sch.details:
        dt_sch = TahapDetailCreateSch(tahap_id=new_obj.id, bidang_id=dt.bidang_id, is_void=False)
        await crud.tahap_detail.create(obj_in=dt_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)

        bidang_current = await crud.bidang.get(id=dt.bidang_id)
        if bidang_current.geom :
            bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))
        bidang_updated = bidang_current
        bidang_updated.luas_bayar = dt.luas_bayar
        bidang_updated.harga_akta = dt.harga_akta
        bidang_updated.harga_transaksi = dt.harga_transaksi

        await crud.bidang.update(obj_current=bidang_current, obj_new=bidang_updated,
                                  with_commit=False, db_session=db_session, 
                                  updated_by_id=current_worker.id)
    
    await db_session.commit()
    await db_session.refresh(new_obj)

    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[TahapSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(Tahap).select_from(Tahap
                                    ).outerjoin(Planing, Planing.id == Tahap.planing_id,
                                    ).outerjoin(Ptsk, Ptsk.id == Tahap.ptsk_id
                                    ).outerjoin(TahapDetail, TahapDetail.tahap_id == Tahap.id
                                    ).outerjoin(Bidang, Bidang.id == TahapDetail.bidang_id)
    
    if keyword:
        query = query.filter(
            or_(
                Tahap.nomor_tahap == int(keyword),
                Bidang.id_bidang.ilike(f'%{keyword}%'),
                Bidang.alashak.ilike(f'%{keyword}%'),
                Tahap.group.ilike(f'%{keyword}%')
            )
        )

    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
                query = query.where(getattr(Tahap, key) == value)


    objs = await crud.tahap.get_multi_paginated(params=params, query=query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[TahapByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.tahap.get_by_id(id=id)
    if obj is None:
        raise IdNotFoundException(Tahap, id)
    
    tahap_details = await crud.tahap_detail.get_multi_by_tahap_id(tahap_id=id)
    
    obj_return = TahapByIdSch(**dict(obj))

    details = [TahapDetailExtSch(**dict(dt)) for dt in tahap_details]
    
    obj_return.details = details

    return create_response(data=obj_return)
    
    
    
@router.put("/{id}", response_model=PutResponseBaseSch[TahapSch])
async def update(
            id:UUID, 
            sch:TahapUpdateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    db_session = db.session

    obj_current = await crud.tahap.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Tahap, id)
    
    obj_updated = await crud.tahap.update(obj_current=obj_current, obj_new=sch, 
                                          db_session=db_session, with_commit=False, 
                                          updated_by_id=current_worker.id)

    #remove bidang
    list_id = [dt.id for dt in sch.details if dt.id is not None]
    if len(list_id) > 0:
        list_detail = await crud.tahap_detail.get_multi_removed_detail(list_ids=list_id, tahap_id=id)
        if list_detail:
            await crud.tahap_detail.remove_multiple_data(list_obj=list_detail, db_session=db_session)
    
    if len(list_id) == 0 and len(obj_current.details) > 0:
        await crud.tahap_detail.remove_multiple_data(list_obj=obj_current.details, db_session=db_session)

    #updated details
    for dt in sch.details:
        if dt.id is None:
            dt_sch = TahapDetailCreateSch(tahap_id=id, bidang_id=dt.bidang_id, is_void=False)
            await crud.tahap_detail.create(obj_in=dt_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)
        else:
            dt_current = await crud.tahap_detail.get(id=dt.id)
            dt_updated = TahapDetailUpdateSch(**dt_current.dict())

            await crud.tahap_detail.update(obj_current=dt_current, obj_new=dt_updated, 
                                           with_commit=False, db_session=db_session,
                                             updated_by_id=current_worker.id)
        
        bidang_current = await crud.bidang.get(id=dt.bidang_id)
        if bidang_current.geom :
            bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))
        bidang_updated = BidangUpdateSch(**bidang_current.dict())
        bidang_updated.luas_bayar = dt.luas_bayar
        bidang_updated.harga_akta = dt.harga_akta
        bidang_updated.harga_transaksi = dt.harga_transaksi
        await crud.bidang.update(obj_current=bidang_current, obj_new=bidang_updated,
                                  with_commit=False, db_session=db_session, 
                                  updated_by_id=current_worker.id)

    await db_session.commit()
    await db_session.refresh(obj_updated)

    return create_response(data=obj_updated)

@router.get("/search/bidang", response_model=GetResponsePaginatedSch[BidangSrcSch])
async def get_list(
                planing_id:UUID,
                ptsk_id:UUID,
                keyword:str = None,
                params: Params=Depends(),
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    status_ = [StatusBidangEnum.Deal]
    query = select(Bidang.id, Bidang.id_bidang).select_from(Bidang
                    ).outerjoin(TahapDetail, TahapDetail.bidang_id == Bidang.id
                    ).outerjoin(Skpt, Skpt.id == Bidang.skpt_id
                    ).where(and_(
                                Bidang.status.in_(status_),
                                Bidang.jenis_bidang != JenisBidangEnum.Bintang,
                                Bidang.hasil_peta_lokasi != None,
                                Bidang.planing_id == planing_id,
                                or_(
                                    TahapDetail.bidang == None,
                                    TahapDetail.is_void == True),
                                or_(
                                    Skpt.ptsk_id == ptsk_id,
                                    Bidang.penampung_id == ptsk_id
                                )
                            ))  
    
    if keyword:
        query = query.filter(Bidang.id_bidang.ilike(f'%{keyword}%'))


    objs = await crud.bidang.get_multi_paginated(params=params, query=query)
    return create_response(data=objs)

@router.get("/search/bidang/{id}", response_model=GetResponseBaseSch[BidangForTahapByIdSch])
async def get_by_id(id:UUID,
                    current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Get an object by id"""

    obj = await crud.bidang.get(id=id)

    obj_return = BidangForTahapByIdSch(**obj.dict())
    obj_return.project_name, obj_return.desa_name, obj_return.planing_name, obj_return.planing_id, obj_return.ptsk_name, obj_return.ptsk_id = [obj.project_name, 
                                                                                                    obj.desa_name, 
                                                                                                    obj.planing_name,
                                                                                                    obj.planing_id,
                                                                                                    obj.ptsk_name or (f'{obj.penampung_name} (PENAMPUNG)'),
                                                                                                    (obj.skpt.ptsk_id if obj.skpt is not None else obj.penampung_id)]
    
    if obj_return:
        return create_response(data=obj_return)
    else:
        raise IdNotFoundException(Bidang, id)
