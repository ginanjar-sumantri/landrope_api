from fastapi import APIRouter, status, Depends, UploadFile, HTTPException, Response
from sqlmodel import select, or_, cast, String, and_
from fastapi_pagination import Params

from common.enum import KategoriTipeTanahEnum


from schemas.peminjaman_header_sch import (PeminjamanHeaderSch, PeminjamanHeaderCreateSch, PeminjamanHeaderUpdateSch, PeminjamanHeaderEditSch, PeminjamanHeaderByIdSch, BidangSearchListSch)
from schemas.peminjaman_bidang_sch import (PeminjamanBidangSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)

from models.peminjaman_header_model import PeminjamanHeader
from models import Bidang, PeminjamanBidang, Planing, Project, Ptsk, Desa, Skpt
from models.worker_model import Worker

from common.exceptions import (IdNotFoundException)

import crud
from common.exceptions import (IdNotFoundException, DocumentFileNotFoundException)
from uuid import UUID
from datetime import datetime

from services.pdf_service import PdfService
from services.gcloud_storage_service import GCStorageService


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[PeminjamanHeaderSch], status_code=status.HTTP_201_CREATED)
async def create(sch: PeminjamanHeaderCreateSch, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    new_obj = await crud.peminjaman_header.create(obj_in=sch, created_by_id=current_worker.id)

    response_obj = await crud.peminjaman_header.get(id=new_obj.id, with_select_in_load=True)
    
    return create_response(data=response_obj)

@router.get("/no-page", response_model=GetResponseBaseSch[list[PeminjamanHeaderSch]])
async def get_no_page(keyword:str | None = None, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a all list objects"""

    query = select(PeminjamanHeader)

    if keyword:
         query = query.filter(
             or_(
                cast(PeminjamanHeader.nomor_perjanjian, String).ilike(f"%{keyword}%"),
                cast(PeminjamanHeader.alashak, String).ilike(f"%{keyword}%")
                )
            )

    objs = await crud.peminjaman_header.get_multi_no_page(query=query)
    
    return create_response(data=objs)


@router.get("", response_model=GetResponsePaginatedSch[PeminjamanHeaderSch])
async def get_list(keyword:str | None = None, params:Params = Depends()):
    
    """Gets a paginated list objects"""

    query = select(PeminjamanHeader)

    if keyword:
        query = query.outerjoin(PeminjamanBidang, PeminjamanHeader.id == PeminjamanBidang.peminjaman_header_id
                    ).outerjoin(Bidang, Bidang.id == PeminjamanBidang.bidang_id
                    ).filter(or_(
                        cast(PeminjamanHeader.nomor_perjanjian, String).ilike(f"%{keyword}%"),
                        cast(Bidang.id_bidang, String).ilike(f"%{keyword}%"),
                        cast(Bidang.alashak, String).ilike(f"%{keyword}%")
                    ))
        
    #tambah query untuk search id bidangnya / join bidang id untuk searching id_bidangnya
    
    query = query.distinct()

    objs = await crud.peminjaman_header.get_multi_paginated_ordered(query=query)
    
    return create_response(data=objs)
    
@router.put("/{id}/edit", response_model=PutResponseBaseSch[PeminjamanHeaderSch])
async def edit(id:UUID, sch:PeminjamanHeaderEditSch, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.peminjaman_header.get(id=id)

    if not obj_current:
        raise IdNotFoundException(PeminjamanHeader, id)
    
    if obj_current.is_lock:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Peminjaman sudah terkunci")
    
    obj_updated = await crud.peminjaman_header.edit(obj_current=obj_current, obj_new=sch)

    response_obj = await crud.peminjaman_header.get(id=obj_updated.id, with_select_in_load=True)

    return create_response(data=response_obj)

@router.put("/{id}/upload", response_model=PutResponseBaseSch[PeminjamanHeaderSch])
async def upload(id:UUID, 
                file:UploadFile | None = None, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.peminjaman_header.get(id=id)

    if not obj_current:
        raise IdNotFoundException(PeminjamanHeader, id)
    
    if not file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload dokumen terlebih dahulu")

    
    obj_updated = await crud.peminjaman_header.upload(obj_current=obj_current, file=file, updated_by_id=current_worker.id)

    response_obj = await crud.peminjaman_header.get(id=obj_updated.id, with_select_in_load=True)

    return create_response(data=response_obj)


@router.put("/{id}/update", response_model=PutResponseBaseSch[PeminjamanHeaderSch])
async def update(id:UUID, sch:PeminjamanHeaderUpdateSch, 
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.peminjaman_header.get(id=id)

    if not obj_current:
        raise IdNotFoundException(PeminjamanHeader, id)
    
    if obj_current.is_lock:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Peminjaman sudah terkunci")
    
    obj_updated = await crud.peminjaman_header.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)

    response_obj = await crud.peminjaman_header.get(id=obj_updated.id, with_select_in_load=True)

    return create_response(data=response_obj)

@router.get("/{id}", response_model=GetResponseBaseSch[PeminjamanHeaderByIdSch])
async def get_by_id(id:UUID, current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Get an object by id bidang"""

    obj = await crud.peminjaman_header.get(id=id, with_select_in_load=True)

    if not obj:
        raise IdNotFoundException(PeminjamanHeader, id)

    return create_response(data=obj)

@router.get("/{id}/download_file" )
async def download_file(id:UUID):
    """Download File Dokumen"""

    obj_current = await crud.peminjaman_header.get(id=id)
    if not obj_current:
        raise IdNotFoundException(PeminjamanHeader, id)
    
    if obj_current.file_path is None:
        raise DocumentFileNotFoundException(dokumenname=obj_current.nomor_perjanjian)
    try:
        file_bytes = await GCStorageService().download_dokumen(file_path=obj_current.file_path)
    except Exception as e:
        raise DocumentFileNotFoundException(dokumenname=obj_current.nomor_perjanjian)
    
    ext = obj_current.file_path.split('.')[-1]

    response = Response(content=file_bytes, media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename={obj_current.nomor_perjanjian}.{ext}"
    return response

@router.get("/{id}/printout")
async def printout_file(id:UUID):

    obj_current = await crud.peminjaman_header.get(id=id, with_select_in_load=True)
    if not obj_current:
        raise IdNotFoundException(PeminjamanHeader, id)
    
    tahun_berakhir = obj_current.tanggal_berakhir.year if obj_current.tanggal_berakhir else "...."

    # penggarap_details = []
    # for penggarap in obj_current.peminjaman_penggaraps:
    #     penggarap_details.append({
    #         "name": penggarap.name,
    #         "alamat": penggarap.alamat,
    #         "nomor_ktp": penggarap.nomor_ktp,
    #         "nomor_handphone": penggarap.nomor_handphone
    #     })
    
    data = {
        "filename": "landrope_form_peminjaman",
        "template_file": "landrope_form_peminjaman.docx",
        "data": {
            "nomor_perjanjian": obj_current.nomor_perjanjian,
            "desa_name": obj_current.desa_name,
            "ptsk_name": obj_current.ptsk_name,
            "kategori": obj_current.kategori,
            "kabupaten_name": obj_current.kabupaten_name,
            "kecamatan_name": obj_current.kecamatan_name,
            "total_luas_bayar": obj_current.total_luas_bayar,
            "tahun_berakhir": tahun_berakhir
            # "penggaraps": penggarap_details
        },
        "images": []
    }

    file_bytes = await PdfService().get_pdf_from_report_service(data=data)
    
    response = Response(content=file_bytes, media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename={obj_current.nomor_perjanjian.replace('/', '_')}.pdf"
    return response


@router.get("/search/bidang", response_model=GetResponsePaginatedSch[BidangSearchListSch])
async def search_bidang(project_id: UUID, desa_id: UUID, ptsk_id: UUID, peminjaman_header_id: UUID | None = None, keyword:str | None = None, params:Params = Depends(), current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(Bidang).join(Planing, Bidang.planing_id == Planing.id
                   ).outerjoin(PeminjamanBidang, Bidang.id == PeminjamanBidang.bidang_id
                    ).outerjoin(Skpt, Skpt.id == Bidang.skpt_id)

    if peminjaman_header_id:
        query = query.where(
            or_(PeminjamanBidang.peminjaman_header_id == peminjaman_header_id, 
                PeminjamanBidang.id == None,
                and_(
                    Planing.project_id == project_id,
                    Planing.desa_id == desa_id,
                    Skpt.ptsk_id == ptsk_id
                )
            )
        )
    else:
        query = query.where(
            and_(
                    PeminjamanBidang.id == None,
                    Planing.project_id == project_id,
                    Planing.desa_id == desa_id,
                    Skpt.ptsk_id == ptsk_id
                )
        )

    if keyword:
        query = query.filter(or_(
                        cast(Bidang.id_bidang, String).ilike(f"%{keyword}%"),
                        cast(Bidang.alashak, String).ilike(f"%{keyword}%")
                    ))
    
    query = query.filter(Bidang.status == "Bebas").distinct()

    objs = await crud.bidang.get_multi_paginated_ordered(query=query)
    
    return create_response(data=objs)

   