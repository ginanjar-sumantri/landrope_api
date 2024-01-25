from uuid import UUID
from fastapi import APIRouter, status, Depends, HTTPException, UploadFile, Request, Response
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, or_
from models import KjbHd, KjbDt, KjbPenjual, WorkflowTemplate
from models.worker_model import Worker
from models.marketing_model import Manager, Sales
from models.pemilik_model import Pemilik
from models.code_counter_model import CodeCounterEnum
from schemas.kjb_hd_sch import (KjbHdSch, KjbHdCreateSch, KjbHdUpdateSch, KjbHdByIdSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from schemas.workflow_sch import WorkflowCreateSch, WorkflowSystemCreateSch, WorkflowSystemAttachmentSch
from common.exceptions import (IdNotFoundException, ImportFailedException, DocumentFileNotFoundException)
from common.generator import generate_code
from common.enum import WorkflowEntityEnum
from datetime import datetime
from typing import Dict, Any
from services.gcloud_storage_service import GCStorageService
from services.helper_service import BidangHelper, BundleHelper
import crud
import json
import time


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[KjbHdSch], status_code=status.HTTP_201_CREATED)
async def create(sch: KjbHdCreateSch,
                 request:Request,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    db_session = db.session
    sch.code = await generate_code(CodeCounterEnum.Kjb, db_session=db_session, with_commit=False)

    new_obj = await crud.kjb_hd.create_(obj_in=sch, created_by_id=current_worker.id, db_session=db_session, request=request)
    new_obj = await crud.kjb_hd.get_by_id_cu(id=new_obj.id)

    return create_response(data=new_obj)

@router.put("/upload-dokumen/{id}", response_model=PutResponseBaseSch[KjbHdSch])
async def upload_dokumen(
            id:UUID, 
            file: UploadFile,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.kjb_hd.get_by_id(id=id)
    if not obj_current:
        raise IdNotFoundException(KjbHd, id)

    if file:
        file_path = await GCStorageService().upload_file_dokumen(file=file, file_name=f'KJB-{id}', is_public=True)
        object_updated = KjbHdUpdateSch(file_path=file_path)
    
    obj_updated = await crud.kjb_hd.update(obj_current=obj_current, obj_new=object_updated, updated_by_id=current_worker.id)
    obj_updated = await crud.kjb_hd.get_by_id(id=obj_updated.id)

    return create_response(data=obj_updated)

@router.get("/download-file/{id}")
async def download_file(id:UUID):
    """Download File Dokumen"""

    obj_current = await crud.kjb_hd.get(id=id)
    if not obj_current:
        raise IdNotFoundException(KjbHd, id)
    if obj_current.file_path is None:
        raise DocumentFileNotFoundException(dokumenname=obj_current.code)
    try:
        file_bytes = await GCStorageService().download_dokumen(file_path=obj_current.file_path)
    except Exception as e:
        raise DocumentFileNotFoundException(dokumenname=obj_current.alashak_kjb_dt)
    
    ext = obj_current.file_path.split('.')[-1]

    # return FileResponse(file, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={obj_current.id}.{ext}"})
    response = Response(content=file_bytes, media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename=Hasil Peta Lokasi-{id}-{obj_current.code}.{ext}"
    return response

@router.post("/cloud-task-workflow")
async def create_workflow(payload:Dict):
    id = payload.get("id", None)
    is_create = payload.get("is_create", None)
    additional_info = payload.get("additional_info", None)

    obj = await crud.kjb_hd.get(id=id)

    if not obj:
        raise IdNotFoundException(KjbHd, id)
    
    trying:int = 0
    if is_create:
        while obj.file_path is None:
            if trying > 7:
                raise HTTPException(status_code=409, detail="File not found")
            obj = await crud.kjb_hd.get(id=id)
            time.sleep(2)
            trying = trying + 1
    

    
    public_url = await GCStorageService().public_url(file_path=obj.file_path)
    flow = await crud.workflow_template.get_by_entity(entity=WorkflowEntityEnum.KJB)
    wf_sch = WorkflowCreateSch(reference_id=id, entity=WorkflowEntityEnum.KJB, flow_id=flow.flow_id)
    wf_system_attachment = WorkflowSystemAttachmentSch(name=f"KJB", url=public_url)
    wf_system_sch = WorkflowSystemCreateSch(client_ref_no=str(id), 
                                            flow_id=flow.flow_id, 
                                            descs=f"""Dokumen KJB {obj.code} ini membutuhkan Approval dari Anda:<br><br>
                                                    Tanggal: {obj.created_at.date()}<br>
                                                    Dokumen: {obj.code}""", 
                                            additional_info={"approval_number" : str(additional_info)}, 
                                            attachments=[vars(wf_system_attachment)])
    
    wf_current = await crud.workflow.get_by_reference_id(reference_id=id)
    if wf_current:
        wf_sch.version = wf_current.version + 1 if wf_current.version else 1
        wf_system_sch.version = wf_current.version + 1 if wf_current.version else 1
    
    await crud.workflow.create_(obj_in=wf_sch, obj_wf=wf_system_sch, created_by_id=obj.created_by_id)

    return {"message" : "successfully"}

@router.get("", response_model=GetResponsePaginatedSch[KjbHdSch])
async def get_list(
        params: Params=Depends(), 
        order_by: str = None, 
        keyword: str = None, 
        filter_query: str= None,
        current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""
    search_date = None

    query = select(KjbHd).select_from(KjbHd
                        ).outerjoin(Manager, KjbHd.manager_id == Manager.id
                        ).outerjoin(Sales, KjbHd.sales_id == Sales.id
                        ).outerjoin(KjbPenjual, KjbHd.id == KjbPenjual.kjb_hd_id
                        ).outerjoin(Pemilik, KjbPenjual.pemilik_id == Pemilik.id
                        ).outerjoin(KjbDt, KjbHd.id == KjbDt.kjb_hd_id)
    
    try:
        # Mengonversi string tanggal menjadi objek datetime
        search_date = datetime.strptime(keyword, "%d-%m-%Y").date()
    except:
        pass
    
    if keyword and search_date is None:
        query = query.filter(
            or_(
                KjbHd.code.ilike(f'%{keyword}%'),
                KjbHd.nama_group.ilike(f'%{keyword}%'),
                Pemilik.name.ilike(f'%{keyword}%'),
                Manager.name.ilike(f'%{keyword}%'),
                Sales.name.ilike(f'%{keyword}%'),
                KjbDt.alashak.ilike(f'%{keyword}%')
            )
        )
    
    if search_date:
        query = query.filter(KjbHd.tanggal_kjb == search_date)
    
    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
                query = query.where(getattr(KjbHd, key) == value)

    query = query.distinct()

    objs = await crud.kjb_hd.get_multi_paginated_ordered(params=params, query=query)
    return create_response(data=objs)

@router.get("/not-draft", response_model=GetResponsePaginatedSch[KjbHdSch])
async def get_list_not_draft(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.kjb_hd.get_multi_kjb_not_draft(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[KjbHdByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.kjb_hd.get_by_id(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(KjbHd, id)

@router.put("/{id}", response_model=PutResponseBaseSch[KjbHdSch])
async def update(id:UUID, sch:KjbHdCreateSch, request:Request,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.kjb_hd.get_by_id(id=id)

    if not obj_current:
        raise IdNotFoundException(KjbHd, id)

    try:
        obj_updated = await crud.kjb_hd.update_(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id, request=request)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"{str(e)}")
    
    obj_updated = await crud.kjb_hd.get_by_id_cu(id=obj_updated.id)
    return create_response(data=obj_updated)

@router.post("/task/update-alashak")
async def update_alashak_bidang_bundle(payload:Dict):

    db_session = db.session

    id = payload.get("id", None)
    obj = await crud.kjb_hd.get_by_id(id=id)

    if not obj:
        raise IdNotFoundException(KjbHd, id)
    
    for kjb_dt in obj.kjb_dts:
        if kjb_dt.hasil_peta_lokasi:
            await BidangHelper().update_alashak(bidang_id=kjb_dt.hasil_peta_lokasi.bidang_id, alashak=kjb_dt.alashak, db_session=db_session, worker_id=obj.updated_by_id)

        if kjb_dt.bundlehd:
            await BundleHelper().merge_alashak(bundle=kjb_dt.bundlehd, worker_id=obj.updated_by_id, alashak=kjb_dt.alashak, db_session=db_session)
    
    await db_session.commit()

    return {"message" : "successfully"}



