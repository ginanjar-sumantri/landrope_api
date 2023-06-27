from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from models.kjb_model import KjbBebanBiaya
from schemas.beban_biaya_sch import BebanBiayaCreateSch
from schemas.kjb_beban_biaya_sch import (KjbBebanBiayaSch, KjbBebanBiayaCreateSch, KjbBebanBiayaUpdateSch, KjbBebanBiayaCreateExSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[KjbBebanBiayaSch], status_code=status.HTTP_201_CREATED)
async def create(sch: KjbBebanBiayaCreateExSch):
    
    """Create a new object"""

    beban_biaya = await crud.bebanbiaya.get_by_name(name=sch.beban_biaya_name)
    if beban_biaya is None:
        sch_bebanbiaya = BebanBiayaCreateSch(name=sch.beban_biaya_name, is_active=True)
        beban_biaya = await crud.bebanbiaya.create(obj_in=sch_bebanbiaya)

    sch_in = KjbBebanBiayaCreateSch(beban_biaya_id=beban_biaya.id, beban_pembeli=sch.beban_pembeli, kjb_hd_id=UUID(sch.kjb_hd_id))

    new_obj = await crud.kjb_bebanbiaya.create(obj_in=sch_in)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[KjbBebanBiayaSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.kjb_bebanbiaya.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[KjbBebanBiayaSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.kjb_bebanbiaya.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(KjbBebanBiaya, id)

@router.put("/{id}", response_model=PutResponseBaseSch[KjbBebanBiayaSch])
async def update(id:UUID, sch:KjbBebanBiayaUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.kjb_bebanbiaya.get(id=id)

    if not obj_current:
        raise IdNotFoundException(KjbBebanBiaya, id)
    
    obj_updated = await crud.kjb_bebanbiaya.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[KjbBebanBiayaSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID):
    
    """Delete a object"""

    obj_current = await crud.kjb_bebanbiaya.get(id=id)
    if not obj_current:
        raise IdNotFoundException(KjbBebanBiaya, id)
    
    obj_deleted = await crud.kjb_bebanbiaya.remove(id=id)

    return obj_deleted

   