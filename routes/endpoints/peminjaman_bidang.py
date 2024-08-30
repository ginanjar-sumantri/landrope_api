from fastapi import APIRouter, status, Depends, Response
from fastapi_pagination import Params
from sqlmodel import select, or_
from models.peminjaman_bidang_model import PeminjamanBidang
from schemas.peminjaman_bidang_sch import (PeminjamanBidangSch, PeminjamanBidangCreateSch, PeminjamanBidangUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException)
# from services.Peminjaman_bidang_service import PeminjamanBidangService
import crud
from common.exceptions import (IdNotFoundException, DocumentFileNotFoundException)
from datetime import datetime
# from services.export_excel_service import ExportExcelService
from fastapi.responses import StreamingResponse
from sqlalchemy.sql import text



router = APIRouter()

@router.post("", response_model=PostResponseBaseSch[PeminjamanBidangSch], status_code=status.HTTP_201_CREATED)
async def create(sch: PeminjamanBidangCreateSch):
    
    """Create a new object"""

    new_obj = await crud.peminjaman_bidang.create(obj_in=sch)
    
    return create_response(data=new_obj)

@router.get("/no-page", response_model=GetResponseBaseSch[list[PeminjamanBidang]])
async def get_no_page(search:str | None = None):
    
    """Gets a all list objects"""

    query = select(PeminjamanBidang)

    if search:
         query = query.filter(
             or_(
                PeminjamanBidang.nomor_perjanjian.ilike(f"%{search}%"),
                PeminjamanBidang.tanggal_perjanjian.ilike(f"%{search}%")
                )
            )

    objs = await crud.peminjaman_bidang.get_multi_no_page(query=query)
    
    return create_response(data=objs)


@router.get("", response_model=GetResponsePaginatedSch[PeminjamanBidangSch])
async def get_list(params: Params=Depends(), search:str = None):
    
    """Gets a paginated list objects"""

    query = select(PeminjamanBidang)

    if search:
         query = query.filter(
             or_(
                PeminjamanBidang.nomor_perjanjian.ilike(f"%{search}%"),
                PeminjamanBidang.tanggal_perjanjian.ilike(f"%{search}%")
                )
            )

    objs = await crud.peminjaman_bidang.get_multi_paginated_ordered(params=params, query=query)
    
    return create_response(data=objs)


@router.get("/{search}", response_model=GetResponseBaseSch[PeminjamanBidangSch])
async def get_by_bidang_id_dan_alashak(search:str = None):

    """Get an object by bidang id dan alas hak"""

    obj = await crud.bidang.get_by_id_bidang_dan_alashak(search=search)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(PeminjamanBidang, search)
    #difilter status bebas
    
@router.put("/{id}", response_model=PutResponseBaseSch[PeminjamanBidangSch])
async def update(id:str, sch:PeminjamanBidangUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.peminjaman_bidang.get(id=id)

    if not obj_current:
        raise IdNotFoundException(PeminjamanBidang, id)
    
    obj_updated = await crud.peminjaman_bidang.update(obj_current=obj_current, obj_new=sch)

    return create_response(data=obj_updated)


@router.delete("/delete", response_model=DeleteResponseBaseSch[PeminjamanBidangSch], status_code=status.HTTP_200_OK)
async def delete(id:str):
    
    """Delete a object"""

    obj_current = await crud.peminjaman_bidang.get(id=id)

    if not obj_current:
        raise IdNotFoundException(PeminjamanBidang, id)
    
    obj_deleted = await crud.peminjaman_bidang.remove(id=id)
    return create_response(data=obj_deleted)

# @router.get("/print-out/{id}")
# async def printout(id:str):

#     """Print out"""

#     obj_current = await crud.Peminjaman_bidang.get(id=id)

#     if not obj_current:
#         raise IdNotFoundException(PeminjamanBidang, id)
    
#     obj_bytes = await PeminjamanBidangService().generate_printout(obj=obj_current)
    
#     headers = {'Content-Disposition': 'inline; filename="Report_Peminjaman.pdf"'}

#     response = Response(obj_bytes.getvalue(), headers=headers, media_type="application/octet-stream")
#     return response
    

# @router.get("/export/excel")
# async def get_report_Peminjaman(periode_date: datetime):

#     """Gets a report"""
#     base_query = "SELECT * FROM public._a_report_Peminjaman(:periode_date)"
#     params = {
#         "periode_date": periode_date
#     }

#     query = text(base_query).params(**params)

#     objs = await crud.Peminjaman_bidang.get_sql_function(query=query)

#     headers = ["Category", "Jenis", "Total"]
#     attributes = ["category", "jenis", "total"]

#     excel_data = await ExportExcelService().generate_excel_report(objs, headers, attributes, report_title="Report Perpanjangan Peminjaman")
    
#     return StreamingResponse(excel_data,
#                              media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
#                              headers={"Content-Disposition": "attachment; filename=report_Peminjaman.xlsx"})






   