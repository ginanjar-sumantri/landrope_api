from fastapi import APIRouter, status, Depends, Response, HTTPException
from sqlmodel import select, or_
from models.bidang_model import Bidang
from models import Project, Desa, Planing, Skpt, Ptsk
from models.peminjaman_bidang_model import PeminjamanBidang
from models.peminjaman_header_model import PeminjamanHeader
from schemas.peminjaman_header_sch import (PeminjamanHeaderSch, PeminjamanHeaderCreateSch, PeminjamanHeaderUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from schemas.bidang_sch import BidangPeminjamanSch
from common.exceptions import (IdNotFoundException)
from models.worker_model import Worker
import crud
from common.exceptions import (IdNotFoundException, DocumentFileNotFoundException)
from datetime import datetime
from sqlalchemy.sql import text
from fastapi_async_sqlalchemy import db
from uuid import UUID




router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[PeminjamanHeaderSch], status_code=status.HTTP_201_CREATED)
async def create(sch: PeminjamanHeaderCreateSch, current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Create a new object"""
    db_session = db.session

    obj_nomor = await crud.peminjaman_header.generate_nomor_perjanjian()

    sch.nomor_perjanjian = obj_nomor

    new_obj = await crud.peminjaman_header.create_peminjaman_header(obj_in=sch, created_by_id=current_worker.id, db_session=db_session)
    
    return create_response(data=new_obj)


@router.get("", response_model=GetResponsePaginatedSch[PeminjamanHeaderSch])
async def get_list_peminjaman():
    
    """Gets a paginated list peminjaman objects"""

    query = select(PeminjamanHeader)

    objs = await crud.peminjaman_header.get_multi_paginated_ordered(query=query)
    
    return create_response(data=objs)



@router.get("/no-page", response_model=GetResponseBaseSch[list[PeminjamanHeader]])
async def get_no_page(keyword:str | None = None):
    
    """Gets a all list objects"""

    query = select(PeminjamanHeader)

    if keyword:
         query = query.filter(
             or_(
                PeminjamanHeader.nomor_perjanjian.ilike(f"%{keyword}%"),
                PeminjamanHeader.tanggal_perjanjian.ilike(f"%{keyword}%")
                )
            )

    objs = await crud.peminjaman_header.get_multi_no_page(query=query)
    
    return create_response(data=objs)

@router.put("/peminjaman-header/{id}", response_model=GetResponseBaseSch[PeminjamanHeaderSch])
async def edit_pinjam(id: str | None, sch:PeminjamanHeaderUpdateSch, current_worker:Worker = Depends(crud.worker.get_active_worker)):


    obj = await crud.peminjaman_header.get(id=id)

    if not obj:
        raise HTTPException(status_code=404, detail="Pinjaman not found")
    
    # if not obj.is_lock:
    #     raise HTTPException(status_code=422, detail="The loan has been approved")

    obj_updated = await crud.peminjaman_header.edit(obj_current=obj, obj_new=sch, updated_by_id=current_worker.id)
    
    return create_response(data=obj_updated)


@router.put("/peminjaman-header/update/{id}", response_model=GetResponseBaseSch[PeminjamanHeaderSch])
async def update_pinjam(id: UUID):

    #update is lock

    obj = await crud.peminjaman_header.update_islock(id=id)

    if not obj:
        raise HTTPException(status_code=404, detail="Peminjaman not found")
    
    return create_response(data=obj)



@router.delete("/delete", response_model=DeleteResponseBaseSch[PeminjamanHeaderSch], status_code=status.HTTP_200_OK)
async def delete(id:str):
    
    """Delete a object"""

    obj_current = await crud.peminjaman_header.get(id=id)

    if not obj_current:
        raise IdNotFoundException(PeminjamanHeader, id)
    
    obj_deleted = await crud.peminjaman_header.remove(id=id)

    return create_response(data=obj_deleted)


@router.get("/bidang", response_model=GetResponsePaginatedSch[BidangPeminjamanSch])
async def get_list_bidang(keyword:str = None):
    
    """Gets a paginated list bidang objects"""
    
    current_date = datetime.now()
    
    query = select(Bidang)
    query = query.outerjoin(PeminjamanBidang, PeminjamanBidang.bidang_id == Bidang.id)
    query = query.outerjoin(PeminjamanHeader, PeminjamanHeader.id == PeminjamanBidang.peminjaman_header_id)
    query = query.filter(Bidang.status == 'Bebas')
    query = query.filter(
            or_(
                PeminjamanBidang.bidang_id == None,
                or_(
                    PeminjamanHeader.tanggal_berakhir == None,
                    PeminjamanHeader.tanggal_berakhir <= current_date
                )
            )
        )

    if keyword:
        query = query.filter(
            or_(
                Bidang.id_bidang == keyword,      
                Bidang.alashak.ilike(f"%{keyword}%")  
            )
        )
    
    query = query.order_by(Bidang.updated_at.desc())
    
    objs = await crud.bidang.get_multi_paginated_ordered(query=query)

    return create_response(data=objs)


# @router.get("/list-bidang-3", response_model=GetResponsePaginatedSch[BidangPeminjamanSch])
# async def get_list_bidang(
#                             project_id: str, 
#                             desa_id: str, 
#                             ptsk_id: str, 
#                             keyword:str = None
#                         ):
    
#     """Gets a paginated list bidang objects"""
#     #tambahkan parameters keyword = id bidang dan alashak sesuai dengan planing id dan ptsk id nya
#     # dan tidak muncul jika tanggal berahkirnya belum selesai
    
#     current_date = datetime.now()
    
#     query = select(Bidang)
#     query = query.outerjoin(PeminjamanBidang, PeminjamanBidang.bidang_id == Bidang.id)
#     query = query.outerjoin(PeminjamanHeader, PeminjamanHeader.id == PeminjamanBidang.peminjaman_header_id)
#     query = query.outerjoin(Planing, Planing.id == Bidang.planing_id)
#     query = query.outerjoin(Project, Project.id == Planing.project_id)
#     query = query.outerjoin(Desa, Desa.id == Planing.desa_id)
#     query = query.outerjoin(Skpt, Skpt.id == Bidang.skpt_id)
#     query = query.outerjoin(Ptsk, Ptsk.id == Skpt.ptsk_id)
#     query = query.filter(Bidang.status == 'Bebas')
#     query = query.filter(
#             or_(
#                 PeminjamanBidang.bidang_id == None,
#                 or_(
#                     PeminjamanHeader.tanggal_berakhir == None,
#                     PeminjamanHeader.tanggal_berakhir <= current_date
#                 )
#             )
#         )

#     if not project_id:
#         raise HTTPException(status_code=400, detail="Parameter 'project' is required.")
    
#     if not desa_id:
#         raise HTTPException(status_code=400, detail="Parameter 'desa' is required.")
    
#     if not ptsk_id:
#         raise HTTPException(status_code=400, detail="Parameter 'ptsk' is required.")
    
#     if keyword:
#         query = query.filter(
#             or_(
#                 Bidang.id_bidang == keyword,      
#                 Bidang.alashak.ilike(f"%{keyword}%")  
#             )
#         )
    
#     query = query.order_by(Bidang.updated_at.desc())
    
#     objs = await crud.bidang.get_multi_paginated_ordered(query=query)

#     if not objs:
#         raise HTTPException(status_code=404, detail="No bidang found with the given criteria.")
    
#     return create_response(data=objs)


# @router.get("/{search}", response_model=GetResponseBaseSch[BidangPeminjamanSch])
# async def get_by_id_bidang_dan_alashak(search:str = None):

#     """Get an object by id bidang dan alas hak"""

#     obj = await crud.bidang.get_by_id_bidang_dan_alashak(search=search)
#     if obj:
#         return create_response(data=obj)
#     else:
#         raise IdNotFoundException(BidangPeminjamanSch, search)
    


   