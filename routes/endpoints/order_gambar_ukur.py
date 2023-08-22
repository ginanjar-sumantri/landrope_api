from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from models.order_gambar_ukur_model import OrderGambarUkur, OrderGambarUkurBidang, OrderGambarUkurTembusan
from models.worker_model import Worker
from schemas.order_gambar_ukur_sch import (OrderGambarUkurSch, OrderGambarUkurCreateSch, OrderGambarUkurUpdateSch, OrderGambarUkurByIdSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException)
import crud
import string
import secrets

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[OrderGambarUkurSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: OrderGambarUkurCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    alphabet = string.ascii_letters + string.digits
    sch.code = ''.join(secrets.choice(alphabet) for _ in range(10))
        
    new_obj = await crud.order_gambar_ukur.create_order_gambar_ukur(obj_in=sch, created_by_id=current_worker.id)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[OrderGambarUkurSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.order_gambar_ukur.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[OrderGambarUkurByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.order_gambar_ukur.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(OrderGambarUkur, id)

@router.put("/{id}", response_model=PutResponseBaseSch[OrderGambarUkurSch])
async def update(
            id:UUID, 
            sch:OrderGambarUkurUpdateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    db_session = db.session

    obj_current = await crud.order_gambar_ukur.get(id=id)

    if not obj_current:
        raise IdNotFoundException(OrderGambarUkur, id)
    
    bidang_ids = [bidang.bidang_id for bidang in sch.bidangs]
    order_gu_bidang_will_removed = await crud.order_gambar_ukur_bidang.get_not_in_by_ids(list_ids=bidang_ids)
    if len(order_gu_bidang_will_removed) > 0 :
        await crud.order_gambar_ukur_bidang.remove_multiple_data(list_obj=order_gu_bidang_will_removed, db_session=db_session)
    
    for order_gu_bidang in sch.bidangs:
        if order_gu_bidang.id is None:
            new_order_gu_bidang = OrderGambarUkurBidang(bidang_id=order_gu_bidang.bidang_id)
            await crud.order_gambar_ukur_bidang.create(obj_in=new_order_gu_bidang, created_by_id=current_worker.id, db_session=db_session, with_commit=False)
    
    tembusan_ids = [tembusan.id for tembusan in sch.tembusans]
    order_gu_tembusan_will_removed = await crud.order_gambar_ukur_tembusan.get_not_in_by_ids(list_ids=tembusan_ids)
    if len(order_gu_tembusan_will_removed) > 0:
        await crud.order_gambar_ukur_tembusan.remove_multiple_data(list_obj=order_gu_tembusan_will_removed)
    
    for order_gu_tembusan in sch.tembusans:
        if order_gu_tembusan.id is None:
            new_order_gu_tembusan = OrderGambarUkurTembusan(tembusan_id=order_gu_tembusan.tembusan_id)
            await crud.order_gambar_ukur_tembusan.create(obj_in=new_order_gu_tembusan, created_by_id=current_worker.id, db_session=db_session, with_commit=False)
    
    obj_updated = await crud.order_gambar_ukur.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)

   