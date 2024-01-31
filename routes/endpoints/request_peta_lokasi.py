from uuid import UUID
from fastapi import APIRouter, status, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from models.request_peta_lokasi_model import RequestPetaLokasi
from models.kjb_model import KjbDt
from models.worker_model import Worker
from schemas.request_peta_lokasi_sch import (RequestPetaLokasiSch, RequestPetaLokasiHdSch, 
                                             RequestPetaLokasiCreateSch, RequestPetaLokasiCreatesSch, 
                                             RequestPetaLokasiUpdateSch, RequestPetaLokasiUpdateExtSch,
                                             RequestPetaLokasiHdbyCodeSch, RequestPetaLokasiPdfSch,
                                             RequestPetaLokasiForInputHasilSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.generator import generate_code, CodeCounterEnum
from services.pdf_service import PdfService
from datetime import datetime, date
from jinja2 import Environment, FileSystemLoader
import pdfkit
import crud
import string
import random
import os


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[RequestPetaLokasiSch], status_code=status.HTTP_201_CREATED)
async def create(sch: RequestPetaLokasiCreateSch):
    
    """Create a new object"""

    kjb_dt = await crud.kjb_dt.get(id=sch.kjb_dt_id)

    if kjb_dt is None:
        raise IdNotFoundException(KjbDt, sch.kjb_dt_id)
        
    exists = await crud.request_peta_lokasi.get_by_kjb_dt_id(id=kjb_dt.id)
    if exists:
        raise HTTPException(status_code=409, detail="Resource already exists")
        
    new_obj = await crud.request_peta_lokasi.create(obj_in=sch)
    
    return create_response(data=new_obj)

@router.post("/creates")
async def creates(sch: RequestPetaLokasiCreatesSch,
                  current_worker:Worker = Depends(crud.worker.get_current_user)):

    datas = []
    db_session = db.session
    today_date = date.today()
    counter = await generate_code(CodeCounterEnum.RequestPetaLokasi, db_session=db_session, with_commit=False)
    code = f"SO/{counter}/REQ-PETLOK/{str(today_date.month)}/{str(today_date.year)}"
   
    for id in sch.datas:
        kjb_dt = await crud.kjb_dt.get(id=id)

        if kjb_dt is None:
            raise IdNotFoundException(KjbDt, id)
        
        exists = await crud.request_peta_lokasi.get_by_kjb_dt_id(id=kjb_dt.id)
        if exists:
            raise HTTPException(status_code=409, detail="Resource already exists")
        
        data = RequestPetaLokasiCreateSch(code=str(code),
                                 kjb_dt_id=kjb_dt.id,
                                 remark=sch.remark,
                                 tanggal=sch.tanggal,
                                 is_disabled=False,
                                 tanggal_terima_berkas=sch.tanggal_terima_berkas,
                                 tanggal_pengukuran=id.tanggal_pengukuran,
                                 tanggal_kirim_ukur=id.tanggal_kirim_ukur,
                                 penunjuk_batas=id.penunjuk_batas,
                                 surveyor=id.surveyor
                                 )
        
        await crud.request_peta_lokasi.create(obj_in=data, created_by_id=current_worker.id, db_session=db_session, with_commit=False)
    
    await db_session.commit()
    

    return {"result" : status.HTTP_200_OK, "message" : "Data created correctly"}

@router.get("/header", response_model=GetResponsePaginatedSch[RequestPetaLokasiHdSch])
async def get_list_header(
                    params: Params=Depends(), 
                    keyword:str|None = None,
                    current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""
    

    objs = await crud.request_peta_lokasi.get_multi_header_paginated(params=params, keyword=keyword)
    return create_response(data=objs)

@router.get("", response_model=GetResponsePaginatedSch[RequestPetaLokasiForInputHasilSch])
async def get_list_for_input_hasil_petlok(
            params: Params = Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str = None,
            outstanding:bool|None = False,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.request_peta_lokasi.get_multi_detail_paginated(outstanding=outstanding, params=params, keyword=keyword)
    
    return create_response(data=objs)

@router.get("/has-input-petlok", response_model=GetResponsePaginatedSch[RequestPetaLokasiForInputHasilSch])
async def get_list_for_input_hasil_petlok(
            code:str|None = None,
            params: Params = Depends(), 
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.request_peta_lokasi.get_multi_detail_has_input_petlok_paginated(params=params, code=code)
    
    return create_response(data=objs)

@router.get("/by/code", response_model=GetResponseBaseSch[RequestPetaLokasiHdbyCodeSch])
async def get_by_code(code:str = None):

    """Get an object by id"""

    objs = await crud.request_peta_lokasi.get_all_by_code(code=code)
    if objs:
        
        data = objs[0]
        kjb_dt_ids:list[RequestPetaLokasiSch] = []
        for i in objs:
            request = RequestPetaLokasiSch.from_orm(i)
            request.created_at = None
            request.updated_at = None
            kjb_dt_ids.append(request)

        obj = RequestPetaLokasiHdbyCodeSch(code=data.code,
                                           desa_name=data.desa_hd_name,
                                           mediator=data.mediator,
                                           group=data.group,
                                           tanggal=data.tanggal,
                                           remark=data.remark,
                                           kjb_hd_code=data.kjb_hd_code,
                                           kjb_hd_id=data.kjb_dt.kjb_hd_id,
                                           kjb_dt_ids=kjb_dt_ids)
        return create_response(data=obj)
    else:
        raise IdNotFoundException(RequestPetaLokasi, id)

@router.get("/{id}", response_model=GetResponseBaseSch[RequestPetaLokasiSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.request_peta_lokasi.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(RequestPetaLokasi, id)

# @router.put("", response_model=PutResponseBaseSch[RequestPetaLokasiSch])
# async def update(sch:RequestPetaLokasiUpdateExtSch,
#                  current_worker:Worker=Depends(crud.worker.get_current_user)):
    
#     """Update a obj by its id"""
#     db_session = db.session
#     obj_currents = await crud.request_peta_lokasi.get_all_by_code(code=sch.code)

#     list_removed = []
#     for i in obj_currents:
#         if i.kjb_dt_id not in sch.kjb_dt_ids:
#             request_removed = await crud.request_peta_lokasi.get_by_kjb_dt_id(id=i.kjb_dt_id)
#             list_removed.append(request_removed)
    
#     if len(list_removed) > 0:
#         await crud.request_peta_lokasi.remove_multiple_data(list_obj=list_removed, db_session=db_session)

#     ids = [x.kjb_dt_id for x in obj_currents]  

#     for j in sch.kjb_dt_ids:
#         if j not in ids:
#             new_obj = RequestPetaLokasi(code=sch.code,
#                                  kjb_dt_id=j,
#                                  remark=sch.remark,
#                                  tanggal=sch.tanggal,
#                                  tanggal_kirim_ukur=sch.tanggal_kirim_ukur,
#                                  tanggal_pengukuran=sch.tanggal_pengukuran,
#                                  tanggal_terima_berkas=sch.tanggal_terima_berkas,
#                                  penunjuk_batas=sch.penunjuk_batas,
#                                  surveyor=sch.surveyor,
#                                  dibuat_oleh="Land Adm Acquisition Officer",
#                                  diperiksa_oleh="Land Adm & Verification Section Head",
#                                  diterima_oleh="Land Measurement Analyst",
#                                  is_disabled=False)
#             obj = await crud.request_peta_lokasi.create(obj_in=new_obj, created_by_id=current_worker.id, db_session=db_session, with_commit=False)
#         else:
#             obj_current = next((x for x in obj_currents if x.kjb_dt_id == j), None)
#             obj_updated = RequestPetaLokasiUpdateSch(code=sch.code,
#                                                      tanggal=sch.tanggal,
#                                                      remark=sch.remark,
#                                                      tanggal_kirim_ukur=sch.tanggal_kirim_ukur,
#                                                      tanggal_pengukuran=sch.tanggal_pengukuran,
#                                                      tanggal_terima_berkas=sch.tanggal_terima_berkas,
#                                                      penunjuk_batas=sch.penunjuk_batas,
#                                                      surveyor=sch.surveyor,
#                                                      kjb_dt_id=j)
            
#             obj = await crud.request_peta_lokasi.update(obj_current=obj_current, obj_new=obj_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

#     await db_session.commit()

#     obj = await crud.request_peta_lokasi.get_by_id(id=obj.id)

#     return create_response(data=obj)


@router.put("", response_model=PutResponseBaseSch[RequestPetaLokasiSch])
async def update(sch:RequestPetaLokasiUpdateExtSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_currents = await crud.request_peta_lokasi.get_all_by_code(code=sch.code)

    obj_updated = await crud.request_peta_lokasi.updates_(obj_currents=obj_currents, obj_new=sch, code=sch.code, updated_by_id=current_worker.id)
    obj_updated = await crud.request_peta_lokasi.get_by_id(id=obj_updated.id)
    return create_response(data=obj_updated)


@router.get("/perintah/pengukuran")
async def perintah_pengukuran(
                        code:str = None,
                        current_worker:Worker = Depends(crud.worker.get_active_worker)):
    """Print out Perintah Pengukuran Tanah"""

    objs = await crud.request_peta_lokasi.get_all_by_code(code=code)

    data_list = []
    no = 1
    nomor = ""
    for obj in objs:
        data = RequestPetaLokasiPdfSch(no=no,
                                       mediator=obj.mediator,
                                       group=obj.group,
                                       pemilik=obj.nama_pemilik_tanah,
                                       no_pemilik=obj.nomor_pemilik_tanah,
                                       alashak=obj.alashak,
                                       luas="{:,.2f}".format(obj.luas),
                                       desa=obj.desa_name,
                                       project=obj.project_name,
                                       remark=obj.remark)
        no = no + 1
        nomor = obj.code
        data_list.append(data)

    
    # template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("request_peta_lokasi.html")

    render_template = template.render(data=data_list, nomor=nomor, tanggal=str(date.today()))

    try:
        doc = await PdfService().get_pdf(render_template)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed generate document")
    
    response = Response(doc, media_type='application/pdf')
    response.headers["Content-Disposition"] = f"attachment; filename={nomor}.pdf"
    return response

@router.delete("/delete", response_model=DeleteResponseBaseSch[RequestPetaLokasiSch], status_code=status.HTTP_200_OK)
async def delete(
            id:UUID,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Delete a object"""

    obj_current = await crud.request_peta_lokasi.get(id=id)
    if not obj_current:
        raise IdNotFoundException(RequestPetaLokasi, id)
    
    obj_deleted = await crud.request_peta_lokasi.remove(id=id)

    return obj_deleted


@router.get("/search/has-input-petlok", response_model=GetResponsePaginatedSch[RequestPetaLokasiHdSch])
async def get_list_header_has_input_petlok(
                    params: Params=Depends(), 
                    keyword:str|None = None,
                    current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""
    

    objs = await crud.request_peta_lokasi.get_multi_header_has_input_petlok_paginated(params=params, keyword=keyword)
    return create_response(data=objs)