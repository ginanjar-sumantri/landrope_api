from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from sqlmodel import select
from models.checklist_dokumen_model import ChecklistDokumen
from models import Worker, Dokumen
from schemas.checklist_dokumen_sch import (ChecklistDokumenSch, ChecklistDokumenCreateSch, ChecklistDokumenBulkCreateSch, ChecklistDokumenUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.generator import generate_code
from models.code_counter_model import CodeCounterEnum
import crud
import json


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[ChecklistDokumenSch], status_code=status.HTTP_201_CREATED)
async def create(sch: ChecklistDokumenBulkCreateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    
    for dokumen in sch.dokumens:
        new_obj = await crud.checklistdokumen.get_single(dokumen_id=dokumen, 
                                                 jenis_alashak=sch.jenis_alashak, 
                                                 jenis_bayar=sch.jenis_bayar, 
                                                 kategori_penjual=sch.kategori_penjual)
        if new_obj:
            continue

        obj_new = ChecklistDokumen(jenis_alashak=sch.jenis_alashak,
                                   kategori_penjual=sch.kategori_penjual,
                                   jenis_bayar=sch.jenis_bayar,
                                   dokumen_id=dokumen)
        
        new_obj = await crud.checklistdokumen.create(obj_in=obj_new, created_by_id=current_worker.id)
        
    new_obj = await crud.checklistdokumen.get_by_id(id=new_obj.id)
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[ChecklistDokumenSch])
async def get_list(
        params: Params=Depends(), 
        order_by:str = None, 
        keyword:str = None, 
        filter_query:str = None,
        current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(ChecklistDokumen).join(ChecklistDokumen.dokumen).where(Dokumen.is_active != False)

    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
            query = query.where(getattr(ChecklistDokumen, key) == value)

    objs = await crud.checklistdokumen.get_multi_paginated(params=params, query=query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[ChecklistDokumenSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.checklistdokumen.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(ChecklistDokumen, id)

@router.put("/{id}", response_model=PutResponseBaseSch[ChecklistDokumenSch])
async def update(id:UUID, sch:ChecklistDokumenUpdateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.checklistdokumen.get(id=id)

    if not obj_current:
        raise IdNotFoundException(ChecklistDokumen, id)
    
    obj_updated = await crud.checklistdokumen.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    obj_updated = await crud.checklistdokumen.get_by_id(id=obj_updated.id)
    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[ChecklistDokumenSch], status_code=status.HTTP_200_OK)
async def delete(
            id:UUID, 
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Delete a object"""

    obj_current = await crud.checklistdokumen.get(id=id)
    if not obj_current:
        raise IdNotFoundException(ChecklistDokumen, id)
    
    obj_deleted = await crud.checklistdokumen.remove(id=id)

    return obj_deleted