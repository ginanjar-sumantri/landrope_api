from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from models.dokumen_model import KategoriDokumen
from models.worker_model import Worker
from schemas.kategori_dokumen_sch import (KategoriDokumenSch, KategoriDokumenCreateSch, KategoriDokumenUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[KategoriDokumenSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: KategoriDokumenCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    new_obj = await crud.kategori_dokumen.create(obj_in=sch)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[KategoriDokumenSch])
async def get_list(
                params: Params=Depends(), 
                order_by:str = None, 
                keyword:str = None, 
                filter_query:str = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.kategori_dokumen.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[KategoriDokumenSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.kategori_dokumen.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(KategoriDokumen, id)

@router.put("/{id}", response_model=PutResponseBaseSch[KategoriDokumenSch])
async def update(
            id:UUID, 
            sch:KategoriDokumenUpdateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.kategori_dokumen.get(id=id)

    if not obj_current:
        raise IdNotFoundException(KategoriDokumen, id)
    
    obj_updated = await crud.kategori_dokumen.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[KategoriDokumenSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Delete a object"""

    obj_current = await crud.kategori_dokumen.get(id=id)
    if not obj_current:
        raise IdNotFoundException(KategoriDokumen, id)
    
    obj_deleted = await crud.kategori_dokumen.remove(id=id)

    return obj_deleted

   