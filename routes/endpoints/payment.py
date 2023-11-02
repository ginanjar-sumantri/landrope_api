from uuid import UUID
from fastapi import APIRouter, status, Depends, BackgroundTasks
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, or_, func, and_, text
from sqlalchemy.orm import selectinload
from models import Payment, Worker, Giro, PaymentDetail, Invoice, Bidang, Termin, InvoiceDetail, Skpt, BidangKomponenBiaya
from schemas.payment_sch import (PaymentSch, PaymentCreateSch, PaymentUpdateSch, PaymentByIdSch, PaymentVoidSch, PaymentVoidExtSch)
from schemas.payment_detail_sch import PaymentDetailCreateSch, PaymentDetailUpdateSch
from schemas.invoice_sch import InvoiceSch, InvoiceByIdSch, InvoiceSearchSch
from schemas.giro_sch import GiroSch, GiroCreateSch
from schemas.bidang_sch import BidangUpdateSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException, ContentNoChangeException)
from common.generator import generate_code
from common.enum import StatusBidangEnum, PaymentMethodEnum
from models.code_counter_model import CodeCounterEnum
from shapely import wkt, wkb
from datetime import date
import crud
import json

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[PaymentSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: PaymentCreateSch,
            background_task:BackgroundTasks,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    db_session = db.session

    giro_current = None
    if sch.giro_id is None and sch.payment_method == PaymentMethodEnum.Giro:
        giro_current = await crud.giro.get_by_nomor_giro(nomor_giro=sch.nomor_giro)
        if giro_current is None:
            last_number_giro = await generate_code(entity=CodeCounterEnum.Giro, db_session=db_session, with_commit=False)
            code_giro = f"BG/{last_number_giro}"
            sch_giro = GiroCreateSch(code=code_giro, nomor_giro=sch.nomor_giro, amount=sch.amount, is_active=True, from_master=False)
            giro_current = await crud.giro.create(obj_in=sch_giro, created_by_id=current_worker.id, db_session=db_session, with_commit=False)
        
        sch.giro_id = giro_current.id      

    amount_dtls = [dt.amount for dt in sch.details]
    if giro_current:
        if giro_current.amount - sum(amount_dtls) < 0:
            raise ContentNoChangeException(detail=f"Invalid Amount: Amount payment detail tidak boleh lebih besar dari payment!!")
    else:
        if (sch.amount - sum(amount_dtls)) < 0:
            raise ContentNoChangeException(detail=f"Invalid Amount: Amount payment detail tidak boleh lebih besar dari payment!!")

    last_number = await generate_code(entity=CodeCounterEnum.Payment, db_session=db_session, with_commit=False)
    sch.code = f"PAY/{last_number}"

    new_obj = await crud.payment.create(obj_in=sch, created_by_id=current_worker.id, with_commit=False, db_session=db_session)
    
    bidang_ids = []
    for dt in sch.details:
        invoice_current = await crud.invoice.get_by_id(id=dt.invoice_id)
        if (invoice_current.invoice_outstanding - dt.amount) < 0:
            raise ContentNoChangeException(detail="Invalid Amount: Amount payment tidak boleh lebih besar dari invoice outstanding!!")
        
        bidang_ids.append(invoice_current.bidang_id)

        detail = PaymentDetailCreateSch(payment_id=new_obj.id, invoice_id=dt.invoice_id, amount=dt.amount, is_void=False, allocation_date=dt.allocation_date)
        await crud.payment_detail.create(obj_in=detail, created_by_id=current_worker.id, db_session=db_session, with_commit=False)

    await db_session.commit()

    background_task.add_task(bidang_update_status, bidang_ids)

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

    query = query.distinct()

    objs = await crud.payment.get_multi_paginated_ordered(params=params, query=query)
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
                 background_task:BackgroundTasks,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""
    db_session = db.session

    obj_current = await crud.payment.get_by_id(id=id)

    if obj_current.is_void:
        raise ContentNoChangeException(detail="Payment telah di void")

    if not obj_current:
        raise IdNotFoundException(Payment, id)
    
    giro_current = None
    if sch.giro_id is None and sch.payment_method == PaymentMethodEnum.Giro:
        giro_current = await crud.giro.get_by_nomor_giro(code=sch.nomor_giro)
        if giro_current is None:
            last_number_giro = await generate_code(entity=CodeCounterEnum.Giro, db_session=db_session, with_commit=False)
            code_giro = f"BG/{last_number_giro}"
            sch_giro = GiroCreateSch(code=code_giro, nomor_giro=sch.nomor_giro, amount=sch.amount, is_active=True, from_master=False)
            giro_current = await crud.giro.create(obj_in=sch_giro, created_by_id=current_worker.id, db_session=db_session, with_commit=False)
        
        sch.giro_id = giro_current.id 
    elif sch.giro_id:
        giro_current = await crud.giro.get_by_id(id=sch.giro_id)     
    
    amount_dtls = []
    for dt in sch.details:
        if dt.id:
            dt_current = await crud.payment_detail.get(id=dt.id)
            if dt_current.is_void != True:
                amount_dtls.append(dt_current.amount)
        else:
            amount_dtls.append(dt.amount)

    if giro_current:
        if giro_current.amount - sum(amount_dtls) < 0:
            raise ContentNoChangeException(detail=f"Invalid Amount: Amount payment detail tidak boleh lebih besar dari payment!!")
    else:
        if (sch.amount - sum(amount_dtls)) < 0:
            raise ContentNoChangeException(detail=f"Invalid Amount: Amount payment detail tidak boleh lebih besar dari payment!!")
    
    sch.is_void = obj_current.is_void
    
    obj_updated = await crud.payment.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)
    
    bidang_ids = []

    #delete detail
    id_dtls = [dt.id for dt in sch.details if dt.id is not None]
    if len(id_dtls) > 0:
        removed_dtls = await crud.payment_detail.get_payment_not_in_by_ids(list_ids=id_dtls, payment_id=obj_updated.id)
        if len(removed_dtls) > 0:
            r_dtl = [rm.invoice.bidang_id for rm in removed_dtls]
            bidang_ids = bidang_ids + r_dtl
            await crud.payment_detail.remove_multiple_data(list_obj=removed_dtls, db_session=db_session)
            
    
    if len(id_dtls) == 0 and len(obj_current.details) > 0:
        r_dtl = [rm.invoice.bidang_id for rm in obj_current.details]
        bidang_ids = bidang_ids + r_dtl
        await crud.payment_detail.remove_multiple_data(list_obj=obj_current.details, db_session=db_session)

    for dt in sch.details:
        if dt.id is None:
            invoice_current = await crud.invoice.get_by_id(id=dt.invoice_id)
            if (invoice_current.invoice_outstanding - dt.amount) < 0:
                raise ContentNoChangeException(detail="Invalid Amount: Amount payment tidak boleh lebih besar dari invoice outstanding!!")
            
            bidang_ids.append(invoice_current.bidang_id)
            detail = PaymentDetailCreateSch(payment_id=obj_current.id, invoice_id=dt.invoice_id, amount=dt.amount, is_void=False, allocation_date=dt.allocation_date)
            await crud.payment_detail.create(obj_in=detail, created_by_id=current_worker.id, db_session=db_session, with_commit=False)
        else:
            payment_dtl_current = await crud.payment_detail.get(id=dt.id)
            invoice_current = await crud.invoice.get_by_id(id=dt.invoice_id)
            if (invoice_current.invoice_outstanding + payment_dtl_current.amount) - dt.amount < 0 and payment_dtl_current.invoice_id == dt.invoice_id:
                raise ContentNoChangeException(detail="Invalid Amount: Amount payment tidak boleh lebih besar dari invoice outstanding!!")
            # elif (invoice_current.invoice_outstanding - dt.amount) < 0:
            #     raise ContentNoChangeException(detail="Invalid Amount: Amount payment tidak boleh lebih besar dari invoice outstanding!!")
            
            bidang_ids.append(invoice_current.bidang_id)
            payment_dtl_updated = PaymentDetailUpdateSch(payment_id=obj_updated.id, invoice_id=dt.invoice_id, amount=dt.amount, allocation_date=dt.allocation_date)
            await crud.payment_detail.update(obj_current=payment_dtl_current, obj_new=payment_dtl_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

    await db_session.commit()

    background_task.add_task(bidang_update_status, bidang_ids)
    
    obj_updated = await crud.payment.get_by_id(id=obj_updated.id)
    return create_response(data=obj_updated)

@router.put("/void/{id}", response_model=GetResponseBaseSch[PaymentSch])
async def void(id:UUID, sch:PaymentVoidSch,
               background_task:BackgroundTasks,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """void a obj by its ids"""
    db_session = db.session

    obj_current = await crud.payment.get_by_id(id=id)

    if not obj_current:
        raise IdNotFoundException(Payment, id)
    
    obj_updated = obj_current
    obj_updated.is_void = True
    obj_updated.remark = sch.void_reason
    obj_updated.void_by_id = current_worker.id

    obj_updated = await crud.payment.update(obj_current=obj_current, obj_new=obj_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

    bidang_ids = []
    for dt in obj_current.details:
        payment_dtl_updated = dt
        payment_dtl_updated.is_void = True
        payment_dtl_updated.remark = sch.void_reason
        payment_dtl_updated.void_by_id = current_worker.id
        payment_dtl_updated.void_at = date.today()

        bidang_ids.append(dt.invoice.bidang_id)
        await crud.payment_detail.update(obj_current=dt, obj_new=payment_dtl_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

    await db_session.commit()

    background_task.add_task(bidang_update_status, bidang_ids)

    obj_updated = await crud.payment.get_by_id(id=obj_current.id)
    return create_response(data=obj_updated) 

@router.put("/void/detail/{id}", response_model=GetResponseBaseSch[PaymentSch])
async def void_detail(
                id:UUID,
                sch:PaymentVoidExtSch,
                background_task:BackgroundTasks,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """void a obj by its ids"""
    db_session = db.session

    obj_current = await crud.payment.get_by_id(id=id)

    if not obj_current:
        raise IdNotFoundException(Payment, id)

    bidang_ids = []
    for dt in sch.details:
        payment_dtl_current = await crud.payment_detail.get(id=dt.id)
        invoice_current = await crud.invoice.get(id=payment_dtl_current.invoice_id)
        payment_dtl_updated = payment_dtl_current
        payment_dtl_updated.is_void = True
        payment_dtl_updated.void_reason = dt.void_reason
        payment_dtl_updated.void_by_id = current_worker.id
        payment_dtl_updated.void_at = date.today()

        bidang_ids.append(invoice_current.bidang_id)

        await crud.payment_detail.update(obj_current=payment_dtl_current, obj_new=payment_dtl_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

    await db_session.commit()
    background_task.add_task(bidang_update_status, bidang_ids)
    obj_updated = await crud.payment.get_by_id(id=obj_current.id)
    return create_response(data=obj_updated) 

@router.get("/search/invoice", response_model=GetResponseBaseSch[list[InvoiceSearchSch]])
async def get_list(
                keyword:str = None, 
                filter_query:str=None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(Invoice)
    query = query.join(Invoice.bidang)
    query = query.join(Invoice.termin)
    query = query.filter(Invoice.is_void != True)

    # subquery_payment = (
    # select(func.coalesce(func.sum(PaymentDetail.amount), 0))
    # .filter(and_(PaymentDetail.invoice_id == Invoice.id, PaymentDetail.is_void != True))
    # .scalar_subquery()  # Menggunakan scalar_subquery untuk hasil subquery sebagai skalar
    # )

    # subquery_beban_biaya = (
    #             select(func.coalesce(func.sum(InvoiceDetail.amount), 0)
    #                 ).join(BidangKomponenBiaya, BidangKomponenBiaya.id == InvoiceDetail.bidang_komponen_biaya_id
    #                 ).filter(and_(InvoiceDetail.invoice_id == Invoice.id, 
    #                               BidangKomponenBiaya.is_void != True, 
    #                               BidangKomponenBiaya.beban_pembeli == False))
    #                 .scalar_subquery()
    #         )
    
    # subquery_utj_amount = (
    #             select(Invoice
    #                 ).join()
    # )

    # query = query.filter(Invoice.amount - (subquery_payment + subquery_beban_biaya) != 0)  
    
    query = query.options(selectinload(Invoice.bidang)
                            ).options(selectinload(Invoice.termin
                                                ).options(selectinload(Termin.tahap))
                            ).options(selectinload(Invoice.payment_details)
                            ).options(selectinload(Invoice.details
                                                ).options(selectinload(InvoiceDetail.bidang_komponen_biaya
                                                                    ).options(selectinload(BidangKomponenBiaya.beban_biaya))
                                                )
                            ).options(selectinload(Invoice.bidang
                                                ).options(selectinload(Bidang.invoices
                                                                    ).options(selectinload(Invoice.termin)
                                                                    ).options(selectinload(Invoice.payment_details))
                                                )
                            )

    if keyword:
        query = query.filter(
            or_(
                Bidang.id_bidang.ilike(f'%{keyword}%'),
                Bidang.alashak.ilike(f'%{keyword}%'),
                Invoice.code.ilike(f'%{keyword}%'),
                Termin.nomor_memo.ilike(f'%{keyword}%')
            )
        )
    
    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
                query = query.where(getattr(Invoice, key) == value)
    
    query = query.distinct()
    query = query.order_by(text("created_at desc"))

    objs = await crud.invoice.get_multi_no_page(query=query)
    objs = [inv for inv in objs if inv.invoice_outstanding > 0]
    return create_response(data=objs)

@router.get("/search/invoice/{id}", response_model=GetResponseBaseSch[InvoiceByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.invoice.get_by_id(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Invoice, id)

@router.get("/search/giro", response_model=GetResponseBaseSch[list[GiroSch]])
async def get_list(
                keyword:str = None,
                payment_id:UUID = None, 
                filter_query:str=None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    # query = select(Giro)
    # query = query.outerjoin(Payment, Payment.giro_id == Giro.id)
    # query = query.filter(Payment.is_void != True)

    # subquery = (
    # select(func.coalesce(func.sum(Payment.amount), 0))
    # .filter(and_(Payment.giro_id == Giro.id, Payment.is_void != True))
    # .scalar_subquery()  # Menggunakan scalar_subquery untuk hasil subquery sebagai skalar
    # )

    # query = query.filter(Giro.amount - subquery != 0)  
     
    query = select(Giro)

    if payment_id is None:
        query = query.outerjoin(Giro.payment).filter(or_(Giro.payment == None, Payment.is_void == True))
    else:
        query = query.outerjoin(Giro.payment).filter(or_(Giro.payment == None, Payment.is_void == True, Payment.id == payment_id))
    
    if keyword:
        query = query.filter(
            or_(
                Giro.code.ilike(f'%{keyword}%'),
                Giro.nomor_giro.ilike(f'%{keyword}%'),
            )
        )
    
    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
                query = query.where(getattr(Giro, key) == value)
    
    query = query.options(selectinload(Giro.payment))
    query = query.distinct()

    objs = await crud.giro.get_multi_no_page(query=query)
    return create_response(data=objs)

async def bidang_update_status(bidang_ids:list[UUID]):
    for id in bidang_ids:
        payment_details = await crud.payment_detail.get_payment_detail_by_bidang_id(bidang_id=id)
        if len(payment_details) > 0:
            bidang_current = await crud.bidang.get(id=id)
            if bidang_current.geom :
                bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))
            bidang_updated = BidangUpdateSch(status=StatusBidangEnum.Bebas)
            await crud.bidang.update(obj_current=bidang_current, obj_new=bidang_updated)
        else:
            bidang_current = await crud.bidang.get(id=id)
            if bidang_current.geom :
                bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))
            bidang_updated = BidangUpdateSch(status=StatusBidangEnum.Deal)
            await crud.bidang.update(obj_current=bidang_current, obj_new=bidang_updated)

