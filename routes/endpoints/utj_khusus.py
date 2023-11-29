from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from models import UtjKhusus, Worker
from schemas.utj_khusus_sch import (UtjKhususSch, UtjKhususCreateSch, UtjKhususUpdateSch)
from schemas.payment_sch import PaymentCreateSch, PaymentUpdateSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException)
from common.generator import generate_code
from common.enum import PaymentMethodEnum
from models.code_counter_model import CodeCounterEnum
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[UtjKhususSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: UtjKhususCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    db_session = db.session
    
    last_number = await generate_code(entity=CodeCounterEnum.Payment, db_session=db_session, with_commit=False)
    sch_payment = PaymentCreateSch(**sch.dict(exclude={"code"}),
                            code=f"PAY-UTJ-KHUSUS/{last_number}",
                            payment_method=PaymentMethodEnum.Tunai
                        )
    
    payment = await crud.payment.create(obj_in=sch_payment, created_by_id=current_worker.id, db_session=db_session, with_commit=False)

    sch.payment_id = payment.id
        
    new_obj = await crud.utj_khusus.create(obj_in=sch, created_by_id=current_worker.id, db_session=db_session)
    new_obj = await crud.utj_khusus.get_by_id(id=new_obj.id)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[UtjKhususSch])
async def get_list(
                params: Params=Depends(), 
                order_by:str = None, 
                keyword:str = None, 
                filter_query:str=None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.utj_khusus.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[UtjKhususSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.utj_khusus.get_by_id(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(UtjKhusus, id)

@router.put("/{id}", response_model=PutResponseBaseSch[UtjKhususSch])
async def update(id:UUID, sch:UtjKhususUpdateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""
    db_session = db.session
    obj_current = await crud.utj_khusus.get(id=id)

    if not obj_current:
        raise IdNotFoundException(UtjKhusus, id)
    
    payment_current = await crud.payment.get_by_id(id=obj_current.payment_id)

    sch_payment = PaymentUpdateSch(**sch.dict(exclude={"code"}),
                            code=payment_current.code,
                            payment_method=PaymentMethodEnum.Tunai
                        )

    payment = await crud.payment.update(obj_current=payment_current, obj_new=sch_payment, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

    obj_updated = await crud.utj_khusus.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id, db_session=db_session)
    obj_updated = await crud.utj_khusus.get_by_id(id=obj_updated.id)
    return create_response(data=obj_updated)

   