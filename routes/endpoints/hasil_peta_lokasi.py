from uuid import UUID
from fastapi import APIRouter, status, Depends, UploadFile
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
import crud
from models.hasil_peta_lokasi_model import HasilPetaLokasi
from models.worker_model import Worker
from models.bidang_overlap_model import BidangOverlap
from schemas.hasil_peta_lokasi_sch import (HasilPetaLokasiSch, HasilPetaLokasiCreateSch, 
                                           HasilPetaLokasiCreateExtSch, HasilPetaLokasiByIdSch, HasilPetaLokasiUpdateSch)
from schemas.hasil_peta_lokasi_detail_sch import HasilPetaLokasiDetailCreateSch, HasilPetaLokasiDetailCreateExtSch
from schemas.bidang_overlap_sch import BidangOverlapCreateSch
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, ContentNoChangeException)
from common.generator import generate_code, CodeCounterEnum
from services.gcloud_storage_service import GCStorageService

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[HasilPetaLokasiSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: HasilPetaLokasiCreateExtSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    db_session = db.session
    obj_current = await crud.hasil_peta_lokasi.get_by_kjb_dt_id(kjb_dt_id=sch.kjb_dt_id)
    if obj_current:
        raise ContentNoChangeException(detail="Alashak Sudah input hasil peta lokasi")
    
    obj_current = await crud.hasil_peta_lokasi.get_by_bidang_id(bidang_id=sch.bidang_id)
    if obj_current:
        raise ContentNoChangeException(detail="Bidang Sudah input hasil peta lokasi")

    new_obj = await crud.hasil_peta_lokasi.create(obj_in=sch, created_by_id=current_worker.id, db_session=db_session, with_commit=False)

    draft_header_id = None  
    for dt in sch.hasilpetalokasidetails:

        bidang_overlap_id = None
        if dt.draft_detail_id is not None:
            #input bidang overlap dari hasil analisa

            draft_detail = await crud.draft_detail.get(id=dt.draft_detail_id)
            if draft_detail is None:
                raise ContentNoChangeException(detail="Bidang Overlap tidak exists di Draft Detail")
            
            draft_header_id = draft_detail.draft_id
            
            code = await generate_code(entity=CodeCounterEnum.BidangOverlap)
            bidang_overlap_sch = BidangOverlapCreateSch(
                                    code=code,
                                    parent_bidang_id=sch.bidang_id,
                                    parent_bidang_intersect_id=dt.bidang_id,
                                    luas=dt.luas_overlap)
            
            new_obj_bidang_overlap = await crud.bidangoverlap.create(obj_in=bidang_overlap_sch, db_session=db_session, with_commit=False)
            bidang_overlap_id = new_obj_bidang_overlap.id
        
        #input detail hasil peta lokasi

        detail_sch = HasilPetaLokasiDetailCreateSch(
            tipe_overlap=dt.tipe_overlap,
            bidang_id=dt.bidang_id,
            hasil_peta_lokasi_id=new_obj.id,
            luas_overlap=dt.luas_overlap,
            keterangan=dt.keterangan,
            bidang_overlap_id=bidang_overlap_id
        )

        await crud.hasil_peta_lokasi_detail.create(obj_in=detail_sch, created_by_id=current_worker.id, db_session=db_session, with_commit=False)

    #remove draft
    draft = await crud.draft.get(id=draft_header_id)
    if draft:
        await crud.draft.remove(id=draft.id, db_session=db_session)
    else:
        await db_session.commit()

    await db_session.refresh(new_obj)
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[HasilPetaLokasiSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str=None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.hasil_peta_lokasi.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[HasilPetaLokasiByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.hasil_peta_lokasi.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(HasilPetaLokasi, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[HasilPetaLokasiSch])
async def update(
            id:UUID, 
            sch:HasilPetaLokasiUpdateSch = Depends(HasilPetaLokasiUpdateSch.as_form),
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.hasil_peta_lokasi.get(id=id)
    if not obj_current:
        raise IdNotFoundException(HasilPetaLokasi, id)
    
    obj_updated = await crud.hasil_peta_lokasi.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)
