from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, or_, func, and_
from sqlalchemy.orm import selectinload
from models import Payment, Worker, Giro, PaymentDetail, Invoice, Bidang, Termin, InvoiceDetail, Skpt, BidangKomponenBiaya
from schemas.payment_sch import (PaymentSch, PaymentCreateSch, PaymentUpdateSch, PaymentByIdSch, PaymentVoidSch, PaymentVoidExtSch)
from schemas.payment_detail_sch import PaymentDetailCreateSch, PaymentDetailUpdateSch
from schemas.invoice_sch import InvoiceSch, InvoiceByIdSch, InvoiceSearchSch
from schemas.giro_sch import GiroSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException, ContentNoChangeException)
from common.generator import generate_code
from models.code_counter_model import CodeCounterEnum
import crud
import json

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[PaymentSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: PaymentCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    db_session = db.session

    if sch.giro_id:
        giro_current = await crud.giro.get_by_id(id=sch.giro_id)
        if (giro_current.giro_outstanding - sch.amount) < 0:
            raise ContentNoChangeException(detail=f"Invalid Amount: Amount payment tidak boleh lebih besar dari giro outstanding {giro_current.giro_outstanding}!!")
    
    new_obj = await crud.payment.create(obj_in=sch, created_by_id=current_worker.id, with_commit=False, db_session=db_session)

    for dt in sch.details:
        invoice_current = await crud.invoice.get_by_id(id=dt.invoice_id)
        if (invoice_current.invoice_outstanding - dt.amount) < 0:
            raise ContentNoChangeException(detail="Invalid Amount: Amount payment tidak boleh lebih besar dari invoice outstanding!!")
        
        detail = PaymentDetailCreateSch(payment_id=new_obj.id, invoice_id=dt.invoice_id, amount=dt.amount, is_void=False)
        await crud.payment_detail.create(obj_in=detail, created_by_id=current_worker.id, db_session=db_session, with_commit=False)

    await db_session.commit()

    new_obj = await crud.payment.get_by_id(id=new_obj.id)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[PaymentSch])
async def get_list(
                params: Params=Depends(), 
                order_by:str = None, 
                keyword:str = None, 
                filter_query:str=None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(Payment).outerjoin(Giro, Giro.id == Payment.giro_id
                            ).outerjoin(PaymentDetail, PaymentDetail.payment_id == Payment.id
                            ).outerjoin(Invoice, Invoice.id == PaymentDetail.invoice_id
                            ).outerjoin(Bidang, Bidang.id == Invoice.bidang_id
                            ).outerjoin(Termin, Termin.id == Invoice.termin_id)
    
    if keyword:
        query = query.filter(
            or_(
                Payment.code.ilike(f"%{keyword}%"),
                Giro.code.ilike(f"%{keyword}%"),
                Bidang.id_bidang.ilike(f"%{keyword}%"),
                Bidang.alashak.ilike(f"%{keyword}%"),
                Termin.code.ilike(f"%{keyword}%"),
                Termin.nomor_memo.ilike(f"%{keyword}%"),
            )
        )

    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
            query = query.where(getattr(Payment, key) == value)

    objs = await crud.payment.get_multi_paginated(params=params, query=query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[PaymentByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.payment.get_by_id(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Payment, id)

@router.put("/{id}", response_model=PutResponseBaseSch[PaymentSch])
async def update(id:UUID, sch:PaymentUpdateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""
    db_session = db.session

    obj_current = await crud.payment.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Payment, id)
    
    sch.is_void = obj_current.is_void
    
    obj_updated = await crud.payment.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)
    
    #delete detail
    id_dtls = [dt.id for dt in sch.details if dt.id is not None]
    removed_dtls = await crud.payment_detail.get_payment_not_in_by_ids(list_ids=id_dtls, payment_id=obj_updated.id)
    if len(removed_dtls) > 0:
        await crud.payment_detail.remove_multiple_data(removed_dtls, db_session=db_session)

    for dt in sch.details:
        if dt.id is None:
            invoice_current = await crud.invoice.get_by_id(id=dt.invoice_id)
            if (invoice_current.invoice_outstanding - dt.amount) < 0:
                raise ContentNoChangeException(detail="Invalid Amount: Amount payment tidak boleh lebih besar dari invoice outstanding!!")
            
            detail = PaymentDetailCreateSch(payment_id=obj_current.id, invoice_id=dt.invoice_id, amount=dt.amount, is_void=False)
            await crud.payment_detail.create(obj_in=detail, created_by_id=current_worker.id, db_session=db_session, with_commit=False)
        else:
            payment_dtl_current = await crud.payment_detail.get(id=dt.id)
            invoice_current = await crud.invoice.get_by_id(id=dt.invoice_id)
            if (invoice_current.invoice_outstanding + payment_dtl_current.amount) - dt.amount < 0 and payment_dtl_current.invoice_id == dt.invoice_id:
                raise ContentNoChangeException(detail="Invalid Amount: Amount payment tidak boleh lebih besar dari invoice outstanding!!")
            elif (invoice_current.invoice_outstanding - dt.amount) < 0:
                raise ContentNoChangeException(detail="Invalid Amount: Amount payment tidak boleh lebih besar dari invoice outstanding!!")
            
            payment_dtl_updated = PaymentDetailUpdateSch(payment_id=obj_updated.id, invoice_id=dt.invoice_id, amount=dt.amount)
            await crud.payment_detail.update(obj_current=payment_dtl_current, obj_new=payment_dtl_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

    await db_session.commit()
    
    obj_updated = await crud.payment.get_by_id(id=obj_updated.id)
    return create_response(data=obj_updated)

@router.put("/void/{id}", response_model=GetResponseBaseSch[PaymentSch])
async def void(id:UUID, sch:PaymentVoidSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """void a obj by its ids"""
    db_session = db.session

    obj_current = await crud.payment.get_by_id(id=id)

    if not obj_current:
        raise IdNotFoundException(Payment, id)
    
    obj_updated = obj_current
    obj_updated.is_void = True
    obj_updated.remark = sch.remark
    obj_updated.void_by_id = current_worker.id

    obj_updated = await crud.payment.update(obj_current=obj_current, obj_new=obj_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

    for dt in obj_current.details:
        payment_dtl_updated = dt
        payment_dtl_updated.is_void = True
        payment_dtl_updated.remark = sch.remark
        payment_dtl_updated.void_by_id = current_worker.id

        await crud.payment_detail.update(obj_current=dt, obj_new=payment_dtl_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

    await db_session.commit()

    obj_updated = await crud.payment.get_by_id(id=obj_current.id)
    return create_response(data=obj_updated) 

@router.put("/void/detail/{id}", response_model=GetResponseBaseSch[PaymentSch])
async def void_detail(
                id:UUID,
                sch:PaymentVoidExtSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """void a obj by its ids"""
    db_session = db.session

    obj_current = await crud.payment.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Payment, id)

    for dt in sch.details:
        payment_dtl_current = await crud.payment_detail.get(id=dt.id)
        payment_dtl_updated = payment_dtl_current
        payment_dtl_updated.is_void = True
        payment_dtl_updated.remark = dt.remark
        payment_dtl_updated.void_by_id = current_worker.id

        await crud.payment_detail.update(obj_current=payment_dtl_current, obj_new=payment_dtl_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

    await db_session.commit()

    obj_updated = await crud.payment.get_by_id(id=obj_current.id)
    return create_response(data=obj_updated) 

@router.get("/search/invoice", response_model=GetResponseBaseSch[list[InvoiceSearchSch]])
async def get_list(
                keyword:str = None, 
                filter_query:str=None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(Invoice)
    query = query.outerjoin(Invoice.bidang)
    query = query.outerjoin(Invoice.termin)
    query = query.filter(Invoice.is_void != True)

    subquery = (
    select(func.coalesce(func.sum(PaymentDetail.amount), 0))
    .filter(and_(PaymentDetail.invoice_id == Invoice.id, PaymentDetail.is_void != True))
    .scalar_subquery()  # Menggunakan scalar_subquery untuk hasil subquery sebagai skalar
    )

    query = query.filter(Invoice.amount - subquery != 0)  
    
    query = query.options(selectinload(Invoice.bidang)
                            ).options(selectinload(Invoice.termin
                                                ).options(selectinload(Termin.tahap))
                            ).options(selectinload(Invoice.payment_details))  

    if keyword:
        query = query.filter(
            or_(
                Bidang.id_bidang.ilike(f'%{keyword}%'),
                Bidang.alashak.ilike(f'%{keyword}%'),
                Invoice.code.ilike(f'%{keyword}%')
            )
        )
    
    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
                query = query.where(getattr(Invoice, key) == value)


    objs = await crud.invoice.get_multi_no_page(query=query)
    return create_response(data=objs)

@router.get("/search/giro", response_model=GetResponseBaseSch[list[GiroSch]])
async def get_list(
                keyword:str = None, 
                filter_query:str=None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(Giro)
    # query = query.outerjoin(Payment, Payment.giro_id == Giro.id)
    # query = query.filter(Payment.is_void != True)

    subquery = (
    select(func.coalesce(func.sum(Payment.amount), 0))
    .filter(and_(Payment.giro_id == Giro.id, Payment.is_void != True))
    .scalar_subquery()  # Menggunakan scalar_subquery untuk hasil subquery sebagai skalar
    )

    query = query.filter(Giro.amount - subquery != 0)  
     
    if keyword:
        query = query.filter(
            or_(
                Giro.code.ilike(f'%{keyword}%'),
                # Payment.code.ilike(f'%{keyword}%')
            )
        )
    
    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
                query = query.where(getattr(Invoice, key) == value)
    
    query = query.options(selectinload(Giro.payments))
    query = query.distinct()

    objs = await crud.giro.get_multi_no_page(query=query)
    return create_response(data=objs)

@router.get("/search/invoice/{id}", response_model=GetResponseBaseSch[InvoiceByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.invoice.get_by_id(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Invoice, id)
