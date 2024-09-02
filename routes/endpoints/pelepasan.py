from fastapi import APIRouter, status, Depends, Response, HTTPException, UploadFile
from fastapi_pagination import Params
from sqlmodel import select, or_, cast, String, and_
from models import (PelepasanHeader, PelepasanBidang, Bidang, Worker, Planing)
from schemas.pelepasan_header_sch import (PelepasanHeaderSch, PelepasanHeaderCreateSch, PelepasanHeaderUpdateSch, 
                                        PelepasanHeaderEditSch, PelepasanHeaderByIdSch, BidangSearchSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)

from services.gcloud_storage_service import GCStorageService
from services.pdf_service import PdfService

from common.exceptions import (IdNotFoundException)
from common.exceptions import (IdNotFoundException, DocumentFileNotFoundException)
from datetime import datetime
from uuid import UUID
import crud



router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[PelepasanHeaderSch], status_code=status.HTTP_201_CREATED)
async def create(sch: PelepasanHeaderCreateSch, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    new_obj = await crud.pelepasan_header.create(obj_in=sch, created_by_id=current_worker.id)

    response_obj = await crud.pelepasan_header.get(id=new_obj.id, with_select_in_load=True)
    
    return create_response(data=response_obj)

@router.put("/{id}/edit", response_model=PutResponseBaseSch[PelepasanHeaderSch])
async def edit(id:UUID, sch:PelepasanHeaderEditSch, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.pelepasan_header.get(id=id)

    if not obj_current:
        raise IdNotFoundException(PelepasanHeader, id)
    
    if obj_current.is_lock:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pelepasan sudah terkunci")
    
    obj_updated = await crud.pelepasan_header.edit(obj_current=obj_current, obj_new=sch)

    response_obj = await crud.pelepasan_header.get(id=obj_updated.id, with_select_in_load=True)

    return create_response(data=response_obj)

@router.put("/{id}/update", response_model=PutResponseBaseSch[PelepasanHeaderSch])
async def update(id:UUID, sch:PelepasanHeaderUpdateSch = Depends(PelepasanHeaderUpdateSch.as_form), 
                file:UploadFile | None = None, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.pelepasan_header.get(id=id)

    if not obj_current:
        raise IdNotFoundException(PelepasanHeader, id)
    
    if obj_current.is_lock:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pelepasan sudah terkunci")
    
    obj_updated = await crud.pelepasan_header.update(obj_current=obj_current, obj_new=sch, file=file, updated_by_id=current_worker.id)

    response_obj = await crud.pelepasan_header.get(id=obj_updated.id, with_select_in_load=True)

    return create_response(data=response_obj)

@router.get("/no-page", response_model=GetResponseBaseSch[list[PelepasanHeaderSch]])
async def get_no_page(keyword:str | None = None, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a all list objects"""

    query = select(PelepasanHeader)

    if keyword:
         query = query.filter(
             or_(
                cast(PelepasanHeader.nomor_pelepasan, String).ilike(f"%{keyword}%"),
                cast(PelepasanHeader.alashak, String).ilike(f"%{keyword}%"),
                cast(PelepasanHeader.nama_pemilik, String).ilike(f"%{keyword}%"),
                cast(PelepasanHeader.nomor_ktp_pemilik, String).ilike(f"%{keyword}%"),
                cast(PelepasanHeader.nomor_telepon_pemilik, String).ilike(f"%{keyword}%")
                )
            )

    objs = await crud.pelepasan_header.get_multi_no_page(query=query)
    
    return create_response(data=objs)

@router.get("", response_model=GetResponsePaginatedSch[PelepasanHeaderSch])
async def get_list(keyword:str | None = None, params:Params = Depends(), current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(PelepasanHeader)

    if keyword:
        query = query.outerjoin(PelepasanBidang, PelepasanHeader.id == PelepasanBidang.pelepasan_header_id
                    ).outerjoin(Bidang, Bidang.id == PelepasanBidang.bidang_id
                    ).filter(or_(
                        cast(PelepasanHeader.nomor_pelepasan, String).ilike(f"%{keyword}%"),
                        cast(PelepasanHeader.alashak, String).ilike(f"%{keyword}%"),
                        cast(PelepasanHeader.nama_pemilik, String).ilike(f"%{keyword}%"),
                        cast(PelepasanHeader.nomor_ktp_pemilik, String).ilike(f"%{keyword}%"),
                        cast(PelepasanHeader.nomor_telepon_pemilik, String).ilike(f"%{keyword}%"),
                        cast(Bidang.id_bidang, String).ilike(f"%{keyword}%"),
                        cast(Bidang.alashak, String).ilike(f"%{keyword}%")
                    ))
    
    query = query.distinct()

    objs = await crud.pelepasan_header.get_multi_paginated_ordered(query=query)
    
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[PelepasanHeaderByIdSch])
async def get_by_id(id:UUID, current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Get an object by id bidang"""

    obj = await crud.pelepasan_header.get(id=id, with_select_in_load=True)

    if not obj:
        raise IdNotFoundException(PelepasanHeader, id)

    return create_response(data=obj)

@router.get("/{id}/download_file" )
async def download_file(id:UUID):
    """Download File Dokumen"""

    obj_current = await crud.pelepasan_header.get(id=id)
    if not obj_current:
        raise IdNotFoundException(PelepasanHeader, id)
    
    if obj_current.file_path is None:
        raise DocumentFileNotFoundException(dokumenname=obj_current.nomor_pelepasan)
    try:
        file_bytes = await GCStorageService().download_dokumen(file_path=obj_current.file_path)
    except Exception as e:
        raise DocumentFileNotFoundException(dokumenname=obj_current.nomor_pelepasan)
    
    ext = obj_current.file_path.split('.')[-1]

    response = Response(content=file_bytes, media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename={obj_current.nomor_pelepasan}.{ext}"
    return response

@router.get("/{id}/printout")
async def printout_file(id:UUID):

    obj_current = await crud.pelepasan_header.get(id=id, with_select_in_load=True)
    if not obj_current:
        raise IdNotFoundException(PelepasanHeader, id)
    
    data = {
        "filename": "landrope_form_pelepasan",
        "template_file": "landrope_form_pelepasan.docx",
        "data": {
            "nama_pemilik": obj_current.nama_pemilik,
            "total_luas_bayar": obj_current.total_luas_bayar,
            "desa_name": obj_current.desa_name,

        },
        "images": []
    }

    file_bytes = await PdfService().get_pdf_from_report_service(data=data)
    
    response = Response(content=file_bytes, media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename={obj_current.nomor_pelepasan.replace('/', '_')}.pdf"
    return response


@router.get("/search/bidang", response_model=GetResponsePaginatedSch[BidangSearchSch])
async def search_bidang(project_id: UUID, desa_id: UUID, pelepasan_header_id: UUID | None = None, keyword:str | None = None, params:Params = Depends(), current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(Bidang).join(Planing, Bidang.planing_id == Planing.id
                   ).outerjoin(PelepasanBidang, Bidang.id == PelepasanBidang.bidang_id)

    if pelepasan_header_id:
        query = query.where(
            or_(PelepasanBidang.pelepasan_header_id == pelepasan_header_id, 
                PelepasanBidang.id == None,
                and_(
                    Planing.project_id == project_id,
                    Planing.desa_id == desa_id
                )
            )
        )
    else:
        query = query.where(
            and_(
                    PelepasanBidang.id == None,
                    Planing.project_id == project_id,
                    Planing.desa_id == desa_id
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








   