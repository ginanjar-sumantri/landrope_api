from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, func, or_, and_, case
from models.checklist_kelengkapan_dokumen_model import ChecklistKelengkapanDokumenHd, ChecklistKelengkapanDokumenDt
from models.worker_model import Worker
from models.bidang_model import Bidang
from models.bundle_model import BundleHd, BundleDt
from models.kjb_model import KjbHd, KjbDt, KjbHarga, KjbTermin
from schemas.checklist_kelengkapan_dokumen_hd_sch import (ChecklistKelengkapanDokumenHdCreateSch, ChecklistKelengkapanDokumenHdSch, 
                                                          ChecklistKelengkapanDokumenHdUpdateSch, ChecklistKelengkapanDokumenHdByIdSch)
from schemas.bundle_dt_sch import BundleDtCreateSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, 
                                  GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException, ContentNoChangeException)
from common.enum import StatusHasilPetaLokasiEnum, JenisBayarEnum
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[ChecklistKelengkapanDokumenHdSch], status_code=status.HTTP_201_CREATED)
async def create(sch: ChecklistKelengkapanDokumenHdCreateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    db_session = db.session

    hasil_peta_lokasi_current = await crud.hasil_peta_lokasi.get_by_bidang_id(bidang_id=sch.bidang_id)
    if not hasil_peta_lokasi_current:
        raise ContentNoChangeException(detail="Bidang belum mempunyai hasil peta lokasi!")
    
    if hasil_peta_lokasi_current.status_hasil_peta_lokasi == StatusHasilPetaLokasiEnum.Batal:
        raise ContentNoChangeException(detail="Hasil Peta Lokasi Bidang BATAL! tidak dapat dibuat checklist kelengkapan dokumen!")
    
    bidang_current = hasil_peta_lokasi_current.bidang
    kjb_dt_current = hasil_peta_lokasi_current.kjb_dt
    kjb_hd_current = kjb_dt_current.kjb_hd

    master_checklist_dokumens = await crud.checklistdokumen.get_multi_by_jenis_alashak_and_kategori_penjual(
        jenis_alashak=bidang_current.jenis_alashak,
        kategori_penjual=kjb_hd_current.kategori_penjual)
    
    details = []
    for master in master_checklist_dokumens:
        bundle_dt_current = await crud.bundledt.get_by_bundle_hd_id_and_dokumen_id(bundle_hd_id=bidang_current.bundle_hd_id, dokumen_id=master.dokumen_id)
        if not bundle_dt_current:
            code = bidang_current.bundlehd.code + master.dokumen.code
            bundle_dt_current = BundleDtCreateSch(code=code, 
                                          dokumen_id=master.dokumen_id,
                                          bundle_hd_id=bidang_current.bundle_hd_id)
            
            bundle_dt_current = await crud.bundledt.create(obj_in=bundle_dt_current, db_session=db_session, with_commit=False)

        detail = ChecklistKelengkapanDokumenDt(
            jenis_bayar=master.jenis_bayar,
            dokumen_id=master.dokumen_id,
            bundle_dt_id=bundle_dt_current.id,
            created_by_id=current_worker.id,
            updated_by_id=current_worker.id)
        
        details.append(detail)
    
    obj_in = ChecklistKelengkapanDokumenHd(bidang_id=sch.bidang_id, details=details)
        
    new_obj = await crud.checklist_kelengkapan_dokumen_hd.create_and_generate(obj_in=obj_in, created_by_id=current_worker.id, db_session=db_session)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[ChecklistKelengkapanDokumenHdSch])
async def get_list(
        params: Params=Depends(), 
        order_by:str = None, 
        keyword:str = None, 
        filter_query:str = None,
        current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.checklist_kelengkapan_dokumen_hd.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[ChecklistKelengkapanDokumenHdByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.checklist_kelengkapan_dokumen_hd.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(ChecklistKelengkapanDokumenHd, id)
    
    # bundle_hd_id = obj.bidang.bundle_hd_id
    
    # meta_data_case = case(
    #     [(BundleDt.meta_data != None or BundleDt.meta_data != "", True)],
    #     else_=False
    # )

    # subquery_meta_data = select(meta_data_case).subquery()
    # subquery_dp = select(KjbTermin).where(KjbTermin.jenis_bayar == JenisBayarEnum.DP)
    # subquery_lunas = select(KjbTermin).where(KjbTermin.jenis_bayar == JenisBayarEnum.LUNAS)
    # query = select(ChecklistKelengkapanDokumenDt
    #                ).add_columns(
    #                              subquery_meta_data.label("has_meta_data")
    #                              ).select_from(ChecklistKelengkapanDokumenDt
    #                                             ).outerjoin(BundleDt, BundleDt.id == ChecklistKelengkapanDokumenDt.bundle_dt_id
    #                                             ).outerjoin(BundleHd, BundleHd.id == BundleDt.bundle_hd_id
    #                                             ).outerjoin(KjbDt, KjbDt.bundle_hd_id == BundleHd.id
    #                                             ).outerjoin(KjbHd, KjbHd.id == KjbDt.kjb_hd_id
    #                                             ).outerjoin(KjbHarga, KjbHarga.kjb_hd_id == KjbHd.id
    #                                             ).outerjoin(KjbTermin, KjbTermin.kjb_harga_id == KjbHarga.id
    #                                             ).where(
    #                                                     and_(KjbHd.ada_utj == True,
    #                                                          subquery_dp.exists(),
    #                                                          subquery_lunas.exists(),
    #                                                          BundleHd.id == bundle_hd_id))
    
    
    # obj_details = await crud.checklist_kelengkapan_dokumen_dt.get_all(query=query)

@router.put("/{id}", response_model=PutResponseBaseSch[ChecklistKelengkapanDokumenHdSch])
async def update(id:UUID, sch:list[ChecklistKelengkapanDokumenHdUpdateSch],
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.checklist_kelengkapan_dokumen_hd.get(id=id)

    if not obj_current:
        raise IdNotFoundException(ChecklistKelengkapanDokumenHd, id)
    
    obj_updated = await crud.checklistdokumen.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[ChecklistKelengkapanDokumenHdSch], status_code=status.HTTP_200_OK)
async def delete(
            id:UUID, 
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Delete a object"""

    obj_current = await crud.checklist_kelengkapan_dokumen_hd.get(id=id)
    if not obj_current:
        raise IdNotFoundException(ChecklistKelengkapanDokumenHd, id)
    
    obj_deleted = await crud.checklist_kelengkapan_dokumen_hd.remove(id=id)

    return obj_deleted