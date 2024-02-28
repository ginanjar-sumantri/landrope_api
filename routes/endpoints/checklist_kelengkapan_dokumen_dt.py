from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from sqlmodel import select
from models.checklist_kelengkapan_dokumen_model import ChecklistKelengkapanDokumenDt, ChecklistKelengkapanDokumenHd
from models import Worker, Dokumen
from schemas.checklist_kelengkapan_dokumen_dt_sch import (ChecklistKelengkapanDokumenDtCreateSch, ChecklistKelengkapanDokumenDtSch, 
                                                          ChecklistKelengkapanDokumenDtUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException, ContentNoChangeException)
from common.generator import generate_code
from models.code_counter_model import CodeCounterEnum
import crud
import json


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[ChecklistKelengkapanDokumenDtSch], status_code=status.HTTP_201_CREATED)
async def create(sch: ChecklistKelengkapanDokumenDtCreateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    checklist_kelengkapan_hd = await crud.checklist_kelengkapan_dokumen_hd.get_by_id(id=sch.checklist_kelengkapan_dokumen_hd_id)
    if checklist_kelengkapan_hd is None:
        raise IdNotFoundException(ChecklistKelengkapanDokumenHd, sch.checklist_kelengkapan_dokumen_hd_id)
    
    bundle_dt = await crud.bundledt.get_by_bundle_hd_id_and_dokumen_id(bundle_hd_id=checklist_kelengkapan_hd.bidang.bundle_hd_id, dokumen_id=sch.dokumen_id)
    if bundle_dt is None:
        raise ContentNoChangeException(detail="Bundle detail yang dimaksud tidak ditemukan")
    
    sch.bundle_dt_id = bundle_dt.id
    new_obj = await crud.checklist_kelengkapan_dokumen_dt.create(obj_in=sch, created_by_id=current_worker.id)
    new_obj = await crud.checklist_kelengkapan_dokumen_dt.get_by_id(id=new_obj.id)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[ChecklistKelengkapanDokumenDtSch])
async def get_list(
        params: Params=Depends(), 
        order_by:str = None, 
        keyword:str = None, 
        filter_query:str = None,
        current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""
    query = select(ChecklistKelengkapanDokumenDt).join(ChecklistKelengkapanDokumenDt.dokumen).where(Dokumen.is_active != False)

    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
            query = query.where(getattr(ChecklistKelengkapanDokumenDt, key) == value)

    objs = await crud.checklist_kelengkapan_dokumen_dt.get_multi_paginated(params=params, query=query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[ChecklistKelengkapanDokumenDtSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.checklist_kelengkapan_dokumen_dt.get_by_id(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(ChecklistKelengkapanDokumenDt, id)

@router.put("/{id}", response_model=PutResponseBaseSch[ChecklistKelengkapanDokumenDtSch])
async def update(id:UUID, sch:ChecklistKelengkapanDokumenDt,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.checklist_kelengkapan_dokumen_dt.get(id=id)

    if not obj_current:
        raise IdNotFoundException(ChecklistKelengkapanDokumenDt, id)
    
    obj_updated = await crud.checklist_kelengkapan_dokumen_dt.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    obj_updated = await crud.checklist_kelengkapan_dokumen_dt.get_by_id(id=obj_updated.id)
    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[ChecklistKelengkapanDokumenDtSch], status_code=status.HTTP_200_OK)
async def delete(
            id:UUID, 
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Delete a object"""

    obj_current = await crud.checklist_kelengkapan_dokumen_dt.get(id=id)
    if not obj_current:
        raise IdNotFoundException(ChecklistKelengkapanDokumenDt, id)
    
    obj_deleted = await crud.checklist_kelengkapan_dokumen_dt.remove(id=id)

    return obj_deleted