from uuid import UUID
from fastapi import APIRouter, status, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, or_, and_
from sqlalchemy import String, cast
from sqlalchemy.orm import selectinload
from models import Tahap, TahapDetail, Bidang, Worker, Planing, Skpt, Ptsk, Project, Desa, Termin, BidangOverlap
from schemas.tahap_sch import (TahapSch, TahapByIdSch, TahapCreateSch, TahapUpdateSch)
from schemas.tahap_detail_sch import TahapDetailCreateSch, TahapDetailUpdateSch, TahapDetailExtSch
from schemas.main_project_sch import MainProjectUpdateSch
from schemas.bidang_sch import BidangSrcSch, BidangByIdForTahapSch, BidangUpdateSch
from schemas.bidang_overlap_sch import BidangOverlapForTahap, BidangOverlapUpdateSch
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, ContentNoChangeException)
from common.enum import StatusBidangEnum, JenisBidangEnum
from services.helper_service import KomponenBiayaHelper
from shapely import wkb, wkt
from io import BytesIO
import crud
import json
import pandas as pd

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[TahapSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: TahapCreateSch,
            background_task:BackgroundTasks,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    db_session = db.session

    obj_planing = await crud.planing.get_by_id(id=sch.planing_id)
    if not obj_planing:
        raise IdNotFoundException(Planing, sch.planing_id)
    
    new_last_tahap = 0
    mainproject_current = None
    if obj_planing.project.main_project:
        mainproject_current = obj_planing.project.main_project
        new_last_tahap = (mainproject_current.last_tahap or 0) + 1
    else:
        obj_sub_project = await crud.sub_project.get_by_id(id=sch.sub_project_id)
        if not obj_sub_project:
            raise ContentNoChangeException(detail="Sub Project tidak ditemukan")
        mainproject_current = obj_sub_project.main_project
        new_last_tahap = (mainproject_current.last_tahap or 0) + 1

    mainproject_updated = mainproject_current
    mainproject_updated.last_tahap = new_last_tahap
    await crud.section.update(obj_current=mainproject_current, obj_new=mainproject_updated, 
                              db_session=db_session, with_commit=False, updated_by_id=current_worker.id)
    
    sch.nomor_tahap = new_last_tahap

    new_obj = await crud.tahap.create(obj_in=sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)

    for dt in sch.details:
        dt_sch = TahapDetailCreateSch(tahap_id=new_obj.id, bidang_id=dt.bidang_id, is_void=False)
        await crud.tahap_detail.create(obj_in=dt_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)

        bidang_current = await crud.bidang.get_by_id(id=dt.bidang_id)
        if bidang_current.geom :
            bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))
        if bidang_current.geom_ori:
            bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))
        
        bidang_updated = BidangUpdateSch.from_orm(bidang_current)
        bidang_updated.luas_bayar = dt.luas_bayar
        bidang_updated.harga_akta = dt.harga_akta
        bidang_updated.harga_transaksi = dt.harga_transaksi

        await crud.bidang.update(obj_current=bidang_current, obj_new=bidang_updated,
                                  with_commit=False, db_session=db_session, 
                                  updated_by_id=current_worker.id)

        
        for ov in dt.overlaps:
            bidang_overlap_current = await crud.bidangoverlap.get(id=ov.id)
            if bidang_overlap_current.geom :
                geom_ov = wkt.dumps(wkb.loads(bidang_overlap_current.geom.data, hex=True))
                bidang_overlap_current.geom = geom_ov
            if bidang_overlap_current.geom_temp :
                geom_temp_ov = wkt.dumps(wkb.loads(bidang_overlap_current.geom_temp.data, hex=True))
                bidang_overlap_current.geom_temp = geom_temp_ov
        
            bidang_overlap_updated = BidangOverlapUpdateSch(**ov.dict())
            
            await crud.bidangoverlap.update(obj_current=bidang_overlap_current, obj_new=bidang_overlap_updated,
                                            with_commit=False, db_session=db_session,
                                            updated_by_id=current_worker.id)
    
    await db_session.commit()
    await db_session.refresh(new_obj)

    new_obj = await crud.tahap.get_by_id(id=new_obj.id)

    bidang_ids = [dt.bidang_id for dt in new_obj.details]
    background_task.add_task(KomponenBiayaHelper().calculated_all_komponen_biaya, bidang_ids)

    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[TahapSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str = None,
            project_id:UUID|None = None,
            ptsk_id:UUID|None = None,
            filter_list:str = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(Tahap).outerjoin(Planing, Planing.id == Tahap.planing_id,
                                    ).outerjoin(Project, Project.id == Planing.project_id
                                    ).outerjoin(Desa, Desa.id == Planing.desa_id
                                    ).outerjoin(Ptsk, Ptsk.id == Tahap.ptsk_id
                                    ).outerjoin(TahapDetail, TahapDetail.tahap_id == Tahap.id
                                    ).outerjoin(Bidang, Bidang.id == TahapDetail.bidang_id
                                    ).outerjoin(Tahap.sub_project).distinct()
    
    if filter_list is not None and filter_list == "with_termin":
        query = query.join(Tahap.termins)
    
    if filter_list is not None and filter_list == "without_termin":
        query = query.outerjoin(Tahap.termins).where(Termin.id == None)
    
    if keyword:
        query = query.filter(
            or_(
                cast(Tahap.nomor_tahap, String).ilike(f'%{keyword}%'),
                Bidang.id_bidang.ilike(f'%{keyword}%'),
                Bidang.alashak.ilike(f'%{keyword}%'),
                Tahap.group.ilike(f'%{keyword}%'),
                Project.name.ilike(f'%{keyword}%'),
                Desa.name.ilike(f'%{keyword}%'),
                Ptsk.name.ilike(f'%{keyword}%')
            )
        )

    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
                query = query.where(getattr(Tahap, key) == value)

    if project_id:
        query = query.filter(Project.id == project_id)
    
    if ptsk_id:
        query = query.filter(Ptsk.id == ptsk_id)


    objs = await crud.tahap.get_multi_paginated_ordered(params=params, query=query)

    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[TahapByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.tahap.get_by_id(id=id)
    if obj is None:
        raise IdNotFoundException(Tahap, id)

    return create_response(data=obj)
    
@router.put("/{id}", response_model=PutResponseBaseSch[TahapSch])
async def update(
            id:UUID, 
            sch:TahapUpdateSch,
            background_task:BackgroundTasks,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    db_session = db.session

    obj_current = await crud.tahap.get_by_id(id=id)
    if not obj_current:
        raise IdNotFoundException(Tahap, id)
    
    obj_updated = await crud.tahap.update(obj_current=obj_current, obj_new=sch, 
                                          db_session=db_session, with_commit=False, 
                                          updated_by_id=current_worker.id)

    #remove bidang
    list_id = [dt.id for dt in sch.details if dt.id is not None]
    if len(list_id) > 0:
        list_detail = await crud.tahap_detail.get_multi_not_in_id_removed(list_ids=list_id, tahap_id=id)
        for ls in list_detail:
            if len(ls.bidang.invoices) > 0:
                raise ContentNoChangeException(detail=f"bidang {ls.bidang.id_bidang} tidak dapat dihapus karena memiliki invoice")
            
        if list_detail:
            await crud.tahap_detail.remove_multiple_data(list_obj=list_detail, db_session=db_session)
    
    if len(list_id) == 0 and len(obj_current.details) > 0:
        list_id = [dt.id for dt in obj_current.details if dt.id is not None]
        list_detail = await crud.tahap_detail.get_multi_in_id_removed(list_ids=list_id, tahap_id=id)
        for ls in list_detail:
            if len(ls.bidang.invoices) > 0:
                raise ContentNoChangeException(detail=f"bidang {ls.bidang.id_bidang} tidak dapat dihapus karena memiliki invoice")
            
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
        
        bidang_current = await crud.bidang.get_by_id(id=dt.bidang_id)
        if bidang_current.geom :
            bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))
        
        if bidang_current.geom_ori :
            bidang_current.geom_ori = wkt.dumps(wkb.loads(bidang_current.geom_ori.data, hex=True))
        
        bidang_updated = BidangUpdateSch.from_orm(bidang_current)
        bidang_updated.luas_bayar = dt.luas_bayar
        bidang_updated.harga_akta = dt.harga_akta
        bidang_updated.harga_transaksi = dt.harga_transaksi

        await crud.bidang.update(obj_current=bidang_current, obj_new=bidang_updated,
                                  with_commit=False, db_session=db_session, 
                                  updated_by_id=current_worker.id)
        
        for ov in dt.overlaps:
            bidang_overlap_current = await crud.bidangoverlap.get(id=ov.id)
            if bidang_overlap_current.geom :
                geom_ov = wkt.dumps(wkb.loads(bidang_overlap_current.geom.data, hex=True))
                bidang_overlap_current.geom = geom_ov
            if bidang_overlap_current.geom_temp :
                geom_temp_ov = wkt.dumps(wkb.loads(bidang_overlap_current.geom_temp.data, hex=True))
                bidang_overlap_current.geom_temp = geom_temp_ov
        
            bidang_overlap_updated = BidangOverlapUpdateSch(**ov.dict())

            await crud.bidangoverlap.update(obj_current=bidang_overlap_current, obj_new=bidang_overlap_updated,
                                            with_commit=False, db_session=db_session,
                                            updated_by_id=current_worker.id)
        

    await db_session.commit()
    await db_session.refresh(obj_updated)

    obj_updated = await crud.tahap.get_by_id(id=obj_updated.id)

    bidang_ids = [dt.bidang_id for dt in obj_updated.details]
    background_task.add_task(KomponenBiayaHelper().calculated_all_komponen_biaya, bidang_ids)

    return create_response(data=obj_updated)

@router.get("/search/bidang", response_model=GetResponsePaginatedSch[BidangSrcSch])
async def get_list(
                planing_id:UUID,
                ptsk_id:UUID,
                sub_project_id:UUID|None = None,
                keyword:str = None,
                params: Params=Depends(),
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    # status_ = [StatusBidangEnum.Deal]
    query = select(Bidang.id, Bidang.id_bidang).select_from(Bidang
                    ).outerjoin(TahapDetail, TahapDetail.bidang_id == Bidang.id
                    ).outerjoin(Skpt, Skpt.id == Bidang.skpt_id
                    ).where(and_(
                                # Bidang.status.in_(status_),
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
    
    if sub_project_id:
        query = query.filter(Bidang.sub_project_id == sub_project_id)
    
    if keyword:
        query = query.filter(Bidang.id_bidang.ilike(f'%{keyword}%'))


    objs = await crud.bidang.get_multi_paginated(params=params, query=query)
    return create_response(data=objs)
    
@router.get("/search/bidang/{id}", response_model=GetResponseBaseSch[BidangByIdForTahapSch])
async def get_by_id(id:UUID,
                    current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Get an object by id"""

    obj = await crud.bidang.get_by_id_for_tahap(id=id)

    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Bidang, id)

@router.get("/export/excel")
async def export_to_excel(
            keyword:str = None,
            project_id:UUID|None = None,
            ptsk_id:UUID|None = None,
            filter_list:str = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    searchby : str = 'All, '

    query = select(Tahap).outerjoin(Planing, Planing.id == Tahap.planing_id,
                                    ).outerjoin(Project, Project.id == Planing.project_id
                                    ).outerjoin(Desa, Desa.id == Planing.desa_id
                                    ).outerjoin(Ptsk, Ptsk.id == Tahap.ptsk_id
                                    ).outerjoin(TahapDetail, TahapDetail.tahap_id == Tahap.id
                                    ).outerjoin(Bidang, Bidang.id == TahapDetail.bidang_id
                                    ).outerjoin(Tahap.sub_project)
    
    if filter_list is not None and filter_list == "with_termin":
        searchby = "with_termin, "
        query = query.join(Tahap.termins)
    
    if filter_list is not None and filter_list == "without_termin":
        query = query.outerjoin(Tahap.termins).where(Termin.id == None)
        searchby = "with_termin, "
    
    if keyword:
        searchby += f'{keyword}, ' 
        query = query.filter(
            or_(
                Tahap.nomor_tahap == int(keyword),
                Bidang.id_bidang.ilike(f'%{keyword}%'),
                Bidang.alashak.ilike(f'%{keyword}%'),
                Tahap.group.ilike(f'%{keyword}%')
            )
        )

    if project_id:
        query = query.filter(Project.id == project_id)
    
    if ptsk_id:
        query = query.filter(Ptsk.id == ptsk_id)

    query = query.options(selectinload(Tahap.planing
                                    ).options(selectinload(Planing.project)
                                    ).options(selectinload(Planing.desa))
                        ).options(selectinload(Tahap.termins)
                        ).options(selectinload(Tahap.details)
                        ).options(selectinload(Tahap.ptsk))
    
    query = query.distinct()
    

    objs = await crud.tahap.get_multi_no_page(query=query)

    data = [{"Nomor" : tahap.nomor_tahap, "Project" : tahap.project_name,
             "Desa" : tahap.desa_name, "PTSK" : tahap.ptsk_name,
             "Group" : tahap.group, "JumlahBidang" : tahap.jumlah_bidang,
             "DP" : tahap.dp_count, "Lunas" : tahap.lunas_count} for tahap in objs]

    
    df = pd.DataFrame(data=data)

    output = BytesIO()
    df.to_excel(output, index=False, sheet_name=f'SPK')

    output.seek(0)

    return StreamingResponse(BytesIO(output.getvalue()), 
                            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            headers={"Content-Disposition": "attachment;filename=tahap_data.xlsx"})