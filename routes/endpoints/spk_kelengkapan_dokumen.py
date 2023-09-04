from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from models.spk_model import SpkKelengkapanDokumen
from models.worker_model import Worker
from schemas.spk_kelengkapan_dokumen_sch import (SpkKelengkapanDokumenSch, SpkKelengkapanDokumenCreateSch, SpkKelengkapanDokumenUpdateSch, SpkKelengkapanDokumenByIdSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[SpkKelengkapanDokumenSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: SpkKelengkapanDokumenCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
        
    new_obj = await crud.spk_kelengkapan_dokumen.create(obj_in=sch, created_by_id=current_worker.id)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[SpkKelengkapanDokumenSch])
async def get_list(
                params: Params=Depends(), 
                order_by:str = None, 
                keyword:str = None, 
                filter_query:str=None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.spk_kelengkapan_dokumen.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[SpkKelengkapanDokumenByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.spk_kelengkapan_dokumen.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(SpkKelengkapanDokumen, id)

@router.put("/{id}", response_model=PutResponseBaseSch[SpkKelengkapanDokumenSch])
async def update(id:UUID, sch:SpkKelengkapanDokumenUpdateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.spk_kelengkapan_dokumen.get(id=id)

    if not obj_current:
        raise IdNotFoundException(SpkKelengkapanDokumen, id)
    
    obj_updated = await crud.spk_kelengkapan_dokumen.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[SpkKelengkapanDokumenSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Delete a object"""

    obj_current = await crud.spk_kelengkapan_dokumen.get(id=id)
    if not obj_current:
        raise IdNotFoundException(SpkKelengkapanDokumen, id)
    
    obj_deleted = await crud.spk_beban_biaya.remove(id=id)

    return obj_deleted

   