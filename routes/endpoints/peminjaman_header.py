from fastapi import APIRouter, status, Depends, Response, HTTPException
from sqlmodel import select, or_
from models.bidang_model import Bidang
from models.peminjaman_header_model import PeminjamanHeader
from schemas.peminjaman_header_sch import (PeminjamanHeaderSch, PeminjamanHeaderCreateSch, PeminjamanHeaderUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from schemas.bidang_sch import BidangPeminjamanSch
from common.exceptions import (IdNotFoundException)
from models.worker_model import Worker
import crud
from common.exceptions import (IdNotFoundException, DocumentFileNotFoundException)
from datetime import datetime
from fastapi.responses import StreamingResponse
from sqlalchemy.sql import text
from fastapi_async_sqlalchemy import db




router = APIRouter()

@router.post("", response_model=PostResponseBaseSch[PeminjamanHeaderSch], status_code=status.HTTP_201_CREATED)
async def create(sch: PeminjamanHeaderCreateSch, current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Create a new object"""
    db_session = db.session

    obj_nomor = await crud.peminjaman_header.generate_nomor_perjanjian()

    sch.nomor_perjanjian = obj_nomor

    new_obj = await crud.peminjaman_header.create_peminjaman_header(obj_in=sch, created_by_id=current_worker.id, db_session=db_session)
    
    return create_response(data=new_obj)


@router.get("/no-page", response_model=GetResponseBaseSch[list[PeminjamanHeader]])
async def get_no_page(search:str | None = None):
    
    """Gets a all list objects"""

    query = select(PeminjamanHeader)

    if search:
         query = query.filter(
             or_(
                PeminjamanHeader.nomor_perjanjian.ilike(f"%{search}%"),
                PeminjamanHeader.tanggal_perjanjian.ilike(f"%{search}%")
                )
            )

    objs = await crud.peminjaman_header.get_multi_no_page(query=query)
    
    return create_response(data=objs)

@router.put("/{id}", response_model=PutResponseBaseSch[PeminjamanHeaderSch])
async def update(id:str, sch:PeminjamanHeaderUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.peminjaman_header.get(id=id)

    if not obj_current:
        raise IdNotFoundException(PeminjamanHeader, id)
    
    obj_updated = await crud.peminjaman_header.update(obj_current=obj_current, obj_new=sch)

    return create_response(data=obj_updated)


@router.delete("/delete", response_model=DeleteResponseBaseSch[PeminjamanHeaderSch], status_code=status.HTTP_200_OK)
async def delete(id:str):
    
    """Delete a object"""

    obj_current = await crud.peminjaman_header.get(id=id)

    if not obj_current:
        raise IdNotFoundException(PeminjamanHeader, id)
    
    obj_deleted = await crud.peminjaman_header.remove(id=id)

    return create_response(data=obj_deleted)


# @router.get("/list-peminjaman", response_model=GetResponsePaginatedSch[PeminjamanHeaderListSch])
# async def get_list_peminjaman():
    
#     """Gets a paginated list peminjaman objects"""

#     query = select(PeminjamanHeader)

#     objs = await crud.peminjaman_header.get_multi_paginated_ordered(query=query)
    
#     return create_response(data=objs)


@router.get("/list-bidang", response_model=GetResponsePaginatedSch[BidangPeminjamanSch])
async def get_list_bidang(keyword:str):
    
    """Gets a paginated list bidang objects"""
    #tambahkan parameters keyword = id bidang dan alashak sesuai dengan planing id dan ptsk id nya
    # dan tidak muncul jika tanggal berahkirnya belum selesai
    

    query = (
        select(Bidang)
        .filter(Bidang.status == 'Bebas')
        .order_by(Bidang.updated_at.desc())
    )

    objs = await crud.bidang.get_multi_paginated_ordered(query=query)
    
    return create_response(data=objs)


@router.get("/{search}", response_model=GetResponseBaseSch[BidangPeminjamanSch])
async def get_by_id_bidang_dan_alashak(search:str = None):

    """Get an object by id bidang dan alas hak"""

    obj = await crud.bidang.get_by_id_bidang_dan_alashak(search=search)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(BidangPeminjamanSch, search)
    


   