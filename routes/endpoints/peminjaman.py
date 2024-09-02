from fastapi import APIRouter, status, Depends, UploadFile, HTTPException
from sqlmodel import select, or_, cast, String
from fastapi_pagination import Params
from models.peminjaman_header_model import PeminjamanHeader
from schemas.peminjaman_header_sch import (PeminjamanHeaderSch, PeminjamanHeaderCreateSch, PeminjamanHeaderUpdateSch, PeminjamanHeaderEditSch)
from schemas.bidang_sch import BidangPeminjamanSch
from models import Bidang, PeminjamanBidang, Planing, Project, Ptsk, Desa
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException)
from models.worker_model import Worker
import crud
from common.exceptions import (IdNotFoundException, DocumentFileNotFoundException)
from uuid import UUID
from datetime import datetime



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
                        cast(PeminjamanHeader.alashak, String).ilike(f"%{keyword}%"),
                        cast(Bidang.id_bidang, String).ilike(f"%{keyword}%")
                    ))
    
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


@router.put("/{id}/update", response_model=PutResponseBaseSch[PeminjamanHeaderSch])
async def update(id:UUID, sch:PeminjamanHeaderUpdateSch = Depends(PeminjamanHeaderUpdateSch.as_form), 
                file:UploadFile | None = None, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.peminjaman_header.get(id=id)

    if not obj_current:
        raise IdNotFoundException(PeminjamanHeader, id)
    
    if obj_current.is_lock:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Peminjaman sudah terkunci")
    
    obj_updated = await crud.peminjaman_header.update(obj_current=obj_current, obj_new=sch, file=file, updated_by_id=current_worker.id)

    response_obj = await crud.peminjaman_header.get(id=obj_updated.id, with_select_in_load=True)

    return create_response(data=response_obj)


@router.get("/list-bidang", response_model=GetResponsePaginatedSch[BidangPeminjamanSch])
async def get_list_bidang(
    project_id: str,  
    desa_id: str,   
    ptsk_id: str,     
    keyword: str | None = None
):
    """Gets a paginated list of bidang objects"""

    if not project_id:
        raise HTTPException(status_code=400, detail="Parameter 'project' is required.")
    if not desa_id:
        raise HTTPException(status_code=400, detail="Parameter 'desa' is required.")
    if not ptsk_id:
        raise HTTPException(status_code=400, detail="Parameter 'ptsk' is required.")
    
    current_date = datetime.now()
    
    query = (
        select(Bidang)
        .outerjoin(PeminjamanBidang, PeminjamanBidang.bidang_id == Bidang.id)
        .outerjoin(PeminjamanHeader, PeminjamanHeader.id == PeminjamanBidang.peminjaman_header_id)
        .outerjoin(Project, Project.id == PeminjamanHeader.project_id)
        .outerjoin(Desa, Desa.id == PeminjamanHeader.desa_id)
        .outerjoin(Ptsk, Ptsk.id == PeminjamanHeader.ptsk_id)
        .filter(Bidang.status == 'Bebas')
        .filter(Project.id == project_id)  
        .filter(Desa.id == desa_id)        
        .filter(Ptsk.id == ptsk_id)        
        .filter(
            or_(
                PeminjamanBidang.bidang_id == None,
                or_(
                    PeminjamanHeader.tanggal_berakhir == None,
                    PeminjamanHeader.tanggal_berakhir <= current_date
                )
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

    if not objs:
        raise HTTPException(status_code=404, detail="No bidang found with the given criteria.")
    
    return create_response(data=objs)

# @router.get("/print-out/{id}")
# async def printout(id:str):

#     """Print out"""

#     obj_current = await crud.Peminjaman_header.get(id=id)

#     if not obj_current:
#         raise IdNotFoundException(PeminjamanHeader, id)
    
#     obj_bytes = await PeminjamanHeaderService().generate_printout(obj=obj_current)
    
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

#     objs = await crud.Peminjaman_header.get_sql_function(query=query)

#     headers = ["Category", "Jenis", "Total"]
#     attributes = ["category", "jenis", "total"]

#     excel_data = await ExportExcelService().generate_excel_report(objs, headers, attributes, report_title="Report Perpanjangan Peminjaman")
    
#     return StreamingResponse(excel_data,
#                              media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
#                              headers={"Content-Disposition": "attachment; filename=report_Peminjaman.xlsx"})






   