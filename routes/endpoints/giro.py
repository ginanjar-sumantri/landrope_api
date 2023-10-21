from uuid import UUID
from fastapi import APIRouter, status, Depends, UploadFile, File, HTTPException
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, or_
from sqlalchemy import exc
from sqlalchemy.orm import selectinload
from models.giro_model import Giro
from models.worker_model import Worker
from schemas.giro_sch import (GiroSch, GiroCreateSch, GiroUpdateSch)
from schemas.payment_sch import PaymentUpdateSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, ContentNoChangeException)
from common.generator import generate_code
from models.code_counter_model import CodeCounterEnum
from decimal import Decimal
import crud
import pandas
import json


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[GiroSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: GiroCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    db_session = db.session

    obj_current = await crud.giro.get_by_nomor_giro(code=sch.nomor_giro)
    if obj_current:
        raise NameExistException(name=sch.nomor_giro, model=Giro)
    
    last_number = await generate_code(entity=CodeCounterEnum.Payment, db_session=db_session, with_commit=False)
    sch.code = f"GIRO/{last_number}"
    sch.from_master = True
    
    new_obj = await crud.giro.create(obj_in=sch, created_by_id=current_worker.id, db_session=db_session)
    new_obj = await crud.giro.get_by_id(id=new_obj.id)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[GiroSch])
async def get_list(
                params: Params=Depends(), 
                order_by:str = None, 
                keyword:str = None, 
                filter_query:str=None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(Giro).options(selectinload(Giro.payment))

    if keyword:
        query = query.filter(or_(
                            Giro.code.ilike(f"%{keyword}%"),
                            Giro.nomor_giro.ilike(f"%{keyword}%")
                            ))
    
    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
            query = query.where(getattr(Giro, key) == value)

    objs = await crud.giro.get_multi_paginated(params=params, query=query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[GiroSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.giro.get_by_id(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Giro, id)

@router.put("/{id}", response_model=PutResponseBaseSch[GiroSch])
async def update(id:UUID, sch:GiroUpdateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""
    db_session = db.session
    obj_current = await crud.giro.get_by_id(id=id)

    if not obj_current:
        raise IdNotFoundException(Giro, id)
    
    if obj_current.payment:
        payment_current = obj_current.payment
        if len(payment_current.details) > 0:
            amount_payment_detail = [payment_detail.amount for payment_detail in payment_current.details if payment_detail.is_void != True]
            total_amount_payment_detail = sum(amount_payment_detail)

            if (sch.amount - total_amount_payment_detail) < 0 :
                raise ContentNoChangeException(detail=f"Giro {sch.code} eksis di database dan telah terpakai payment, namun amount saat ini lebih kecil dari total paymentnya. Harap dicek kembali")
            
        payment_updated = PaymentUpdateSch(amount=sch.amount)
        await crud.payment.update(obj_current=payment_current, obj_new=payment_updated, with_commit=False, db_session=db_session)

    
    obj_updated = await crud.giro.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id, db_session=db_session)
    obj_updated = await crud.giro.get_by_id(id=obj_updated.id)
    
    return create_response(data=obj_updated)

# @router.delete("/delete", response_model=DeleteResponseBaseSch[GiroSch], status_code=status.HTTP_200_OK)
# async def delete(id:UUID, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
#     """Delete a object"""

#     obj_current = await crud.giro.get(id=id)
#     if not obj_current:
#         raise IdNotFoundException(Giro, id)
    
#     obj_deleted = await crud.giro.remove(id=id)

#     return obj_deleted

@router.post("/import-giro")
async def extract_excel(file:UploadFile,
                        current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Import Excel object"""

    db_session = db.session

    file_content = await file.read()
    df = pandas.read_excel(file_content)
    rows, commit, row = [len(df), False, 1]

    for i, data in df.iterrows():
        sch = GiroCreateSch(code=str(data["code"]), 
                            amount=Decimal(int(data["amount"])), 
                            is_active=True)

        if row == rows:
            commit = True
        
        obj_current = await crud.giro.get_by_nomor_giro(nomor_giro=sch.code)

        if obj_current:
            amount_payment_detail = [payment_detail.amount for payment_detail in obj_current.payment.details if payment_detail.is_void != True]
            total_amount_payment_detail = sum(amount_payment_detail)

            if (sch.amount - total_amount_payment_detail) < 0 :
                raise ContentNoChangeException(detail=f"Giro {sch.code} eksis di database dan telah terpakai payment, namun amount saat ini lebih kecil dari total paymentnya. Harap dicek kembali")

            await crud.giro.update(obj_current=obj_current, obj_new=sch, with_commit=commit, db_session=db_session, updated_by_id=current_worker.id)

        await crud.giro.create(obj_in=sch, created_by_id=current_worker.id, with_commit=commit, db_session=db_session)

        row = row + 1
    
    return {'message' : 'successfully import'}


   