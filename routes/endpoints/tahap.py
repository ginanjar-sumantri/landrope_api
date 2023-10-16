from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi.responses import FileResponse
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, or_, and_
from models import Tahap, TahapDetail, Bidang, Worker, Planing, Skpt, Ptsk, Project, Desa, Termin
from schemas.tahap_sch import (TahapSch, TahapByIdSch, TahapCreateSch, TahapUpdateSch)
from schemas.tahap_detail_sch import TahapDetailCreateSch, TahapDetailUpdateSch, TahapDetailExtSch
from schemas.main_project_sch import MainProjectUpdateSch
from schemas.bidang_sch import BidangSrcSch, BidangByIdForTahapSch, BidangUpdateSch
from schemas.bidang_overlap_sch import BidangOverlapForTahap
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, ContentNoChangeException)
from common.enum import StatusBidangEnum, JenisBidangEnum
from shapely import wkb, wkt
from io import BytesIO
from datetime import date
import crud
import json
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[TahapSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: TahapCreateSch,
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
        
        for ov in dt.overlaps:
            bidang_overlap_current = await crud.bidangoverlap.get(id=ov.id)
            if bidang_overlap_current.geom :
                bidang_overlap_current.geom = wkt.dumps(wkb.loads(bidang_overlap_current.geom.data, hex=True))
            
            bidang_overlap_updated = bidang_overlap_current
            bidang_overlap_updated.kategori = ov.kategori
            bidang_overlap_updated.harga_transaksi = ov.harga_transaksi or 0
            bidang_overlap_updated.luas_bayar = ov.luas_bayar or 0

            await crud.bidangoverlap.update(obj_current=bidang_overlap_current, obj_new=bidang_overlap_updated,
                                            with_commit=False, db_session=db_session,
                                            updated_by_id=current_worker.id)
    
    await db_session.commit()
    await db_session.refresh(new_obj)

    new_obj = await crud.tahap.get_by_id(id=new_obj.id)

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
                                    ).outerjoin(Tahap.sub_project)
    
    if filter_list is not None and filter_list == "with_termin":
        query = query.join(Tahap.termins)
    
    if filter_list is not None and filter_list == "without_termin":
        query = query.outerjoin(Tahap.termins).where(Termin.id == None)
    
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

    if project_id:
        query = query.filter(Project.id == project_id)
    
    if ptsk_id:
        query = query.filter(Ptsk.id == ptsk_id)


    objs = await crud.tahap.get_multi_paginated(params=params, query=query)

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
        
        for ov in dt.overlaps:
            bidang_overlap_current = await crud.bidangoverlap.get(id=ov.id)
            if bidang_overlap_current.geom :
                bidang_overlap_current.geom = wkt.dumps(wkb.loads(bidang_overlap_current.geom.data, hex=True))
            
            bidang_overlap_updated = bidang_overlap_current
            bidang_overlap_updated.kategori = ov.kategori
            bidang_overlap_updated.harga_transaksi = ov.harga_transaksi or 0
            bidang_overlap_updated.luas_bayar = ov.luas_bayar or 0

            await crud.bidangoverlap.update(obj_current=bidang_overlap_current, obj_new=bidang_overlap_updated,
                                            with_commit=False, db_session=db_session,
                                            updated_by_id=current_worker.id)
        

    await db_session.commit()
    await db_session.refresh(obj_updated)

    obj_updated = await crud.tahap.get_by_id(id=obj_updated.id)

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

@router.get("/export_excel/")
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

    

    objs = await crud.tahap.get_multi_no_page(query=query)

    data = [{"Nomor" : tahap.nomor_tahap, "Project" : tahap.project_name,
             "Desa" : tahap.desa_name, "PTSK" : tahap.ptsk_name,
             "Group" : tahap.group, "JumlahBidang" : tahap.jumlah_bidang,
             "DP" : tahap.dp_count, "Lunas" : tahap.lunas_count} for tahap in objs]

    
    df = pd.DataFrame(data=data)

    # Buat file Excel menggunakan openpyxl
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Data", index=False)
        searchby = searchby[0:-2]
        # Tambahkan judul ke cell pertama
        workbook = writer.book
        worksheet = writer.sheets["Data"]
        worksheet.title = "Data"
        worksheet.cell(row=1, column=1, value=f'Search by : {searchby}').font = Font(bold=True)

    output.seek(0)

    filename:str = f'Report Tahap {str(date.today())}'
    # Simpan file sementara ke disk dan kirimkan sebagai FileResponse
    with open("temp_excel.xlsx", "wb") as temp_file:
        temp_file.write(output.read())
    return FileResponse("temp_excel.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"})
