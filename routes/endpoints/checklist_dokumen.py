from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from models.checklist_dokumen_model import ChecklistDokumen
from schemas.checklist_dokumen_sch import (ChecklistDokumenSch, ChecklistDokumenCreateSch, ChecklistDokumenBulkCreateSch, ChecklistDokumenUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.generator import generate_code
from models.code_counter_model import CodeCounterEnum
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[ChecklistDokumenBulkCreateSch], status_code=status.HTTP_201_CREATED)
async def create(sch: ChecklistDokumenBulkCreateSch):
    
    """Create a new object"""
    
    for dokumen in sch.dokumens:
        obj_new = ChecklistDokumen(jenis_alashak=sch.jenis_alashak,
                                   kategori_penjual=sch.kategori_penjual,
                                   jenis_bayar=sch.jenis_bayar,
                                   dokumen_id=dokumen)
        
        new_obj = await crud.checklistdokumen.create(obj_in=obj_new)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[ChecklistDokumenSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.checklistdokumen.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
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
async def update(id:UUID, sch:ChecklistDokumenUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.checklistdokumen.get(id=id)

    if not obj_current:
        raise IdNotFoundException(ChecklistDokumen, id)
    
    obj_updated = await crud.checklistdokumen.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[ChecklistDokumenSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID):
    
    """Delete a object"""

    obj_current = await crud.checklistdokumen.get(id=id)
    if not obj_current:
        raise IdNotFoundException(ChecklistDokumen, id)
    
    obj_deleted = await crud.checklistdokumen.remove(id=id)

    return obj_deleted