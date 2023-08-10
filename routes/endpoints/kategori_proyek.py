from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from models.kategori_model import KategoriProyek
from models.worker_model import Worker
from schemas.kategori_proyek_sch import (KategoriProyekSch, KategoriProyekCreateSch, KategoriProyekUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException)
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[KategoriProyekSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: KategoriProyekCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
        
    new_obj = await crud.kategori_proyek.create(obj_in=sch, created_by_id=current_worker.id)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[KategoriProyekSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.kategori_proyek.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[KategoriProyekSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.kategori_proyek.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(KategoriProyek, id)

@router.put("/{id}", response_model=PutResponseBaseSch[KategoriProyekSch])
async def update(
            id:UUID, 
            sch:KategoriProyekUpdateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.kategori_proyek.get(id=id)

    if not obj_current:
        raise IdNotFoundException(KategoriProyek, id)
    
    obj_updated = await crud.kategori_proyek.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)

    return create_response(data=obj_updated)

   