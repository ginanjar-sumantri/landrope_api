from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from models.checklist_kelengkapan_dokumen_model import ChecklistKelengkapanDokumenHd, ChecklistKelengkapanDokumenDt
from models.worker_model import Worker
from schemas.checklist_kelengkapan_dokumen_hd_sch import (ChecklistKelengkapanDokumenHdCreateSch, ChecklistKelengkapanDokumenHdSch, 
                                                          ChecklistKelengkapanDokumenHdUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, 
                                  GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException, ContentNoChangeException)
from common.enum import StatusHasilPetaLokasiEnum
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
        detail = ChecklistKelengkapanDokumenDt(
            jenis_bayar=master.jenis_bayar,
            dokumen_id=master.dokumen_id
        )
        
    new_obj = await crud.checklist_kelengkapan_dokumen_hd.create(obj_in=sch, created_by_id=current_worker.id, db_session=db_session, with_commit=False)
    
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

@router.get("/{id}", response_model=GetResponseBaseSch[ChecklistKelengkapanDokumenHdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.checklist_kelengkapan_dokumen_hd.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(ChecklistKelengkapanDokumenHd, id)

@router.put("/{id}", response_model=PutResponseBaseSch[ChecklistKelengkapanDokumenHdSch])
async def update(id:UUID, sch:ChecklistKelengkapanDokumenHdUpdateSch,
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