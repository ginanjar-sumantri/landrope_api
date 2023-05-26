from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from models.dokumen_model import Dokumen
from schemas.dokumen_sch import (DokumenSch, DokumenCreateSch, DokumenUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.generator import generate_code
from models.code_counter_model import CodeCounterEnum
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[DokumenSch], status_code=status.HTTP_201_CREATED)
async def create(sch: DokumenCreateSch):
    
    """Create a new object"""

    sch.code = await generate_code(entity=CodeCounterEnum.Dokumen)
        
    new_obj = await crud.dokumen.create(obj_in=sch)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[DokumenSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.dokumen.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.put("/{id}", response_model=PutResponseBaseSch[DokumenSch])
async def update(id:UUID, sch:DokumenUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.dokumen.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Dokumen, id)
    
    obj_updated = await crud.dokumen.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[DokumenSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID):
    
    """Delete a object"""

    obj_current = await crud.dokumen.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Dokumen, id)
    
    obj_deleted = await crud.dokumen.remove(id=id)

    return obj_deleted

   