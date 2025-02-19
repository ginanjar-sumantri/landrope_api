from uuid import UUID
from fastapi import APIRouter, status, Depends, BackgroundTasks, HTTPException
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, or_, func, and_, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from models import Payment, Worker, Giro, PaymentDetail, Invoice, Bidang, Termin, InvoiceDetail, Skpt, BidangKomponenBiaya, Workflow, PaymentGiroDetail
from schemas.payment_sch import (PaymentSch, PaymentCreateSch, PaymentUpdateSch, PaymentByIdSch, PaymentVoidSch, PaymentVoidExtSch)
from schemas.payment_detail_sch import PaymentDetailCreateSch, PaymentDetailUpdateSch
from schemas.invoice_sch import InvoiceSch, InvoiceByIdSch, InvoiceSearchSch, InvoiceUpdateSch, InvoiceOnMemoSch, InvoiceOnUTJSch
from schemas.giro_sch import GiroSch, GiroCreateSch, GiroUpdateSch
from schemas.bidang_sch import BidangUpdateSch
from schemas.termin_sch import TerminSearchSch
from schemas.beban_biaya_sch import BebanBiayaGroupingSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException, ContentNoChangeException)
from common.generator import generate_code
from common.enum import StatusBidangEnum, PaymentMethodEnum, JenisBayarEnum, WorkflowLastStatusEnum, PaymentStatusEnum, ActivityEnum, WorkflowEntityEnum
from models.code_counter_model import CodeCounterEnum
from shapely import wkt, wkb
from datetime import date
from collections import defaultdict
import crud
import json

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[PaymentSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: PaymentCreateSch,
            background_task:BackgroundTasks,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    
    sum_amount_giro = sum([giro.amount for giro in sch.giros])
    sum_amount_invoice = sum([invoice.amount for invoice in sch.details])
    sum_amount_komponen = sum([komponen.amount for komponen in sch.komponens])

    if (sum_amount_invoice + sum_amount_komponen) != sum_amount_giro:
        HTTPException(status_code=422, detail="Total semua pembayaran tidak boleh lebih besar dari Total Giro/Cek")

    bidang_ids = []
    invoice_ids = []
    for dt in sch.details:
        if dt.realisasi != True:
            invoice_current = await crud.invoice.get_by_id(id=dt.invoice_id)
            dt_amount = sum([new_dt.amount for new_dt in sch.details if new_dt.invoice_id == dt.invoice_id]) #handle dalam satu payment ada 2 row invoice yg sama, yg split giro/cek nya.
            if (invoice_current.invoice_outstanding - dt_amount) < 0:
                raise ContentNoChangeException(detail="Invalid Amount: Amount payment tidak boleh lebih besar dari invoice outstanding!!")
            
            bidang_ids.append(invoice_current.bidang_id)
            invoice_ids.append(invoice_current.id)

    new_obj = await crud.payment.create(obj_in=sch, created_by_id=current_worker.id)
    new_obj = await crud.payment.get_by_id(id=new_obj.id)

    background_task.add_task(bidang_update_status, bidang_ids)
    background_task.add_task(invoice_update_payment_status, new_obj.id)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[PaymentSch])
async def get_list(
                params: Params=Depends(), 
                order_by:str = None, 
                keyword:str = None, 
                filter_query:str=None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(Payment).outerjoin(PaymentDetail, PaymentDetail.payment_id == Payment.id
                            ).outerjoin(Invoice, Invoice.id == PaymentDetail.invoice_id
                            ).outerjoin(Bidang, Bidang.id == Invoice.bidang_id
                            ).outerjoin(Termin, Termin.id == Invoice.termin_id
                            ).outerjoin(PaymentGiroDetail, PaymentGiroDetail.id == PaymentDetail.payment_giro_detail_id
                            ).outerjoin(Giro, Giro.id == PaymentGiroDetail.giro_id)
    
    if keyword:
        query = query.filter(
            or_(
                Payment.code.ilike(f"%{keyword}%"),
                Giro.code.ilike(f"%{keyword}%"),
                Bidang.id_bidang.ilike(f"%{keyword}%"),
                Bidang.alashak.ilike(f"%{keyword}%"),
                Termin.code.ilike(f"%{keyword}%"),
                Termin.nomor_memo.ilike(f"%{keyword}%"),
                Payment.pay_to.ilike(f"%{keyword}%"),
                PaymentGiroDetail.pay_to.ilike(f"%{keyword}%"),
                Giro.nomor_giro.ilike(f'%{keyword}%'),
                Payment.remark.ilike(f'%{keyword}%')
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

        result = PaymentByIdSch.from_orm(obj)
        komponens = result.komponens

        new_komponens: list[BebanBiayaGroupingSch] = []
        for group_komponen in komponens:
            existing_komponen = next((bb for bb in new_komponens if bb.beban_biaya_id == group_komponen.beban_biaya_id and bb.termin_id == group_komponen.termin_id), None)
            if existing_komponen:
                continue

            total_amount = sum([kompo.amount for kompo in komponens if kompo.beban_biaya_id == group_komponen.beban_biaya_id and kompo.termin_id == group_komponen.termin_id])
            
            group_komponen.amount = total_amount
            new_komponens.append(group_komponen)

        result.komponens = new_komponens


        return create_response(data=result)
    else:
        raise IdNotFoundException(Payment, id)

@router.put("/{id}", response_model=PutResponseBaseSch[PaymentSch])
async def update(id:UUID, sch:PaymentUpdateSch,
                 background_task:BackgroundTasks,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    sum_amount_giro = sum([giro.amount for giro in sch.giros])
    sum_amount_invoice = sum([invoice.amount for invoice in sch.details])
    sum_amount_komponen = sum([komponen.amount for komponen in sch.komponens])

    if (sum_amount_invoice + sum_amount_komponen) > sum_amount_giro:
        HTTPException(status_code=422, detail="Total semua pembayaran tidak boleh lebih besar dari Total Giro/Cek")

    obj_current = await crud.payment.get_by_id(id=id)

    if obj_current.is_void:
        raise ContentNoChangeException(detail="Payment telah di void")

    if not obj_current:
        raise IdNotFoundException(Payment, id)
    
    bidang_ids = []
    invoice_ids = []
    for dt in sch.details:
        if dt.realisasi != True:
            invoice_current = await crud.invoice.get_by_id(id=dt.invoice_id)
            if dt.id is None:
                dt_amount = sum([new_dt.amount for new_dt in sch.details if new_dt.invoice_id == dt.invoice_id]) #handle dalam satu payment ada 2 row invoice yg sama, yg split giro/cek nya.
                if (invoice_current.invoice_outstanding - dt_amount) < 0:
                    raise ContentNoChangeException(detail="Invalid Amount: Amount payment tidak boleh lebih besar dari invoice outstanding!!")
                
            else:
                dt_current = next((x for x in obj_current.details if x.id == dt.id), None)
                if dt_current.is_void != True:
                    dt_current_amount = sum([new_dt.amount for new_dt in obj_current.details if new_dt.invoice_id == dt.invoice_id]) #handle dalam satu payment ada 2 row invoice yg sama, yg split giro/cek nya.
                    dt_amount = sum([new_dt.amount for new_dt in sch.details if new_dt.invoice_id == dt.invoice_id]) #handle dalam satu payment ada 2 row invoice yg sama, yg split giro/cek nya.
                    if ((invoice_current.invoice_outstanding + dt_current_amount) - dt_amount) < 0:
                        raise ContentNoChangeException(detail="Invalid Amount: Amount payment tidak boleh lebih besar dari invoice outstanding!!")

            bidang_ids.append(invoice_current.bidang_id)
            invoice_ids.append(invoice_current.id)

    
    obj_updated = await crud.payment.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    obj_updated = await crud.payment.get_by_id(id=obj_updated.id)

    background_task.add_task(bidang_update_status, bidang_ids)
    background_task.add_task(invoice_update_payment_status, obj_updated.id)

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
    
    obj_updated = PaymentUpdateSch.from_orm(obj_current)
    obj_updated.is_void = True
    obj_updated.void_reason = sch.void_reason
    obj_updated.void_by_id = current_worker.id
    obj_updated.void_at = date.today()

    obj_updated = await crud.payment.update(obj_current=obj_current, obj_new=obj_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

    bidang_ids = []
    for dt in obj_current.details:
        payment_dtl_updated = PaymentDetailUpdateSch.from_orm(dt)
        payment_dtl_updated.is_void = True
        payment_dtl_updated.void_reason = sch.void_reason
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
    
    items = []
    reference_ids = [invoice.termin_id for invoice in objs]
    workflows = await crud.workflow.get_by_reference_ids(reference_ids=reference_ids, entity=WorkflowEntityEnum.TERMIN)

    for inv in objs:
        workflow = next((wf for wf in workflows if wf.reference_id == inv.termin_id), None)

        if inv.invoice_outstanding > 0 and ((workflow.last_status == WorkflowLastStatusEnum.COMPLETED and inv.jenis_bayar not in [JenisBayarEnum.UTJ, JenisBayarEnum.UTJ_KHUSUS]) or inv.jenis_bayar in [JenisBayarEnum.UTJ, JenisBayarEnum.UTJ_KHUSUS]):
            items.append(inv)

    return create_response(data=items)

@router.get("/search/invoiceExt", response_model=GetResponseBaseSch[list[InvoiceSearchSch]])
async def get_list(
                keyword:str = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets all list objects"""

    objs = await crud.invoice.get_multi_outstanding_invoice(keyword=keyword)
    
    return create_response(data=objs)

@router.get("/search/invoice/{id}", response_model=GetResponseBaseSch[InvoiceByIdSch])
async def get_invoice_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.invoice.get_by_id(id=id)
    if obj is None:
        raise HTTPException(status_code=404, detail="invoice not found!!")
    
    workflow = await crud.workflow.get_by_reference_id(reference_id=obj.termin_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="workflow not found!!")

    if workflow.last_status != WorkflowLastStatusEnum.COMPLETED and obj.jenis_bayar not in [JenisBayarEnum.UTJ, JenisBayarEnum.UTJ_KHUSUS]:
        raise HTTPException(status_code=422, detail="Memo bayar must completed approval")
    
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Invoice, id)

@router.get("/search/giro", response_model=GetResponseBaseSch[list[GiroSch]])
async def get_list(
                keyword:str | None = None,
                payment_id:UUID | None = None, 
                filter_query:str | None = None,
                payment_method:PaymentMethodEnum|None = None,
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
        query = query.outerjoin(Giro.payment
                    ).outerjoin(Giro.payment_giros
                    ).filter(and_(or_(Giro.payment == None, Payment.is_void == True),
                                  Giro.payment_giros == None))
    else:
        query = query.outerjoin(Giro.payment).filter(or_(Giro.payment == None, Payment.is_void == True, Payment.id == payment_id))

    if payment_method:
        query = query.filter(Giro.payment_method == payment_method)
    
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
    
    query = query.options(selectinload(Giro.payment
                                    ).options(selectinload(Payment.details))
                    )
    query = query.distinct()

    objs = await crud.giro.get_multi_no_page(query=query)
    return create_response(data=objs)

@router.get("/search/termin", response_model=GetResponseBaseSch[list[TerminSearchSch]])
async def get_list(
                keyword:str = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets all list objects"""

    # invoice_outstandings = await crud.invoice.get_multi_outstanding_invoice(keyword=keyword)
    # list_id = [invoice.termin_id for invoice in invoice_outstandings]

    query = select(Termin).join(Workflow, Workflow.reference_id == Termin.id
                        ).outerjoin(Invoice, Invoice.termin_id == Termin.id
                        ).outerjoin(PaymentDetail, PaymentDetail.invoice_id == Invoice.id
                        ).where(and_(Workflow.last_status == WorkflowLastStatusEnum.COMPLETED,
                                    PaymentDetail.id == None))
    
    if keyword:
        query = query.filter(or_(
            Termin.nomor_memo.ilike(f"%{keyword}%"),
            Termin.code.ilike(f"%{keyword}%")
        ))
    
    query = query.order_by(Termin.created_at.desc()).distinct()

    query = query.options(selectinload(Termin.tahap))

    objs = await crud.termin.get_multi_no_page(query=query)
    
    return create_response(data=objs)

@router.get("/search/invoice/by-termin/{id}", response_model=GetResponseBaseSch[list[InvoiceOnMemoSch]])
async def get_invoice_by_id(id:UUID):

    """Get an object by id"""

    termin_current = await crud.termin.get_by_id(id=id)

    if termin_current is None:
        raise HTTPException(status_code=404, detail="termin not found!!")
    
    workflow = await crud.workflow.get_by_reference_id(reference_id=termin_current.id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="workflow not found!!")

    if workflow.last_status != WorkflowLastStatusEnum.COMPLETED and termin_current.jenis_bayar not in [JenisBayarEnum.UTJ, JenisBayarEnum.UTJ_KHUSUS]:
        raise HTTPException(status_code=422, detail="Memo bayar must completed approval")

    invoices = await crud.invoice.get_multi_by_termin_id(termin_id=id)
    
    bidang_ids = [inv.bidang_id for inv in invoices if inv.is_void != True]
    utj_invoices = await crud.invoice.get_multi_by_bidang_ids(bidang_ids=bidang_ids)
    
    invoice_bayars = await crud.invoice_bayar.get_multi_by_termin_id(termin_id=id)

    invoices_in:list[InvoiceOnMemoSch] = []
    for invoice_bayar in invoice_bayars:
        if (invoice_bayar.amount or 0) == 0:
            continue
        if invoice_bayar.termin_bayar.activity == ActivityEnum.BEBAN_BIAYA:
            continue
        elif invoice_bayar.termin_bayar.activity == ActivityEnum.UTJ:
            utj_invoice = next((utj for utj in utj_invoices if utj.bidang_id == invoice_bayar.invoice.bidang_id), None)
            if utj_invoice is None:
                continue

            inv_in = InvoiceOnMemoSch.from_orm(utj_invoice)
            inv_in.realisasi = True
            inv_in.invoice_bayar_amount = invoice_bayar.amount
            inv_in.termin_bayar_id = invoice_bayar.termin_bayar_id
        else:
            regular_invoice = next((inv for inv in invoices if inv.id == invoice_bayar.invoice_id), None)
            if regular_invoice is None:
                continue

            inv_in = InvoiceOnMemoSch.from_orm(regular_invoice)
            inv_in.realisasi = False
            inv_in.invoice_bayar_amount = invoice_bayar.amount
            inv_in.termin_bayar_id = invoice_bayar.termin_bayar_id

        invoices_in.append(inv_in)

    return create_response(data=invoices_in)

@router.get("/search/komponen/by-termin/{id}", response_model=GetResponseBaseSch[list[BebanBiayaGroupingSch]])
async def get_invoice_by_id(id:UUID):

    """Get an object by id"""

    termin_current = await crud.termin.get_by_id(id=id)
    workflow = await crud.workflow.get_by_reference_id(reference_id=termin_current.id)
    if workflow.last_status != WorkflowLastStatusEnum.COMPLETED and termin_current.jenis_bayar not in [JenisBayarEnum.UTJ, JenisBayarEnum.UTJ_KHUSUS]:
        raise HTTPException(status_code=422, detail="Memo bayar must completed approval")

    komponens = await crud.bebanbiaya.get_multi_grouping_beban_biaya_by_termin_id(termin_id=id)

    return create_response(data=komponens)

@router.get("/search/termin/utj", response_model=GetResponseBaseSch[list[TerminSearchSch]])
async def get_list_termin_utj(
                keyword:str = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets all list objects"""

    invoice_outstandings = await crud.invoice.get_multi_outstanding_utj_invoice(keyword=keyword)
    list_id = [invoice.termin_id for invoice in invoice_outstandings]

    query = select(Termin).where(Termin.id.in_(list_id))
    
    query = query.options(selectinload(Termin.tahap))

    objs = await crud.termin.get_multi_no_page(query=query)
    
    return create_response(data=objs)

@router.get("/search/utj/invoice/by-termin/{id}", response_model=GetResponseBaseSch[list[InvoiceOnUTJSch]])
async def get_invoice_by_id(id:UUID):

    """Get an object by id"""

    memo_bayar_invoices = await crud.invoice.get_multi_by_termin_id(termin_id=id)

    # bidang_ids = [inv.bidang_id for inv in memo_bayar_invoices if inv.use_utj == True and inv.is_void != True]
    # utj_invoices = await crud.invoice.get_multi_by_bidang_ids(bidang_ids=bidang_ids)

    # merge_invoices = memo_bayar_invoices + utj_invoices

    invoices:list[InvoiceOnUTJSch] = []
    for inv in memo_bayar_invoices:
        if inv.invoice_outstanding == 0:
            continue
        inv_in = InvoiceOnUTJSch.from_orm(inv)
        inv_in.realisasi = False
        
        invoices.append(inv_in)

    return create_response(data=invoices)


async def bidang_update_status(bidang_ids:list[UUID]):
    for id in bidang_ids:
        payment_details = await crud.payment_detail.get_payment_detail_by_bidang_id(bidang_id=id)
        if len(payment_details) > 0:
            bidang_current = await crud.bidang.get_by_id(id=id)
            if bidang_current.geom :
                bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))
            bidang_updated = BidangUpdateSch(status=StatusBidangEnum.Bebas)
            await crud.bidang.update(obj_current=bidang_current, obj_new=bidang_updated)
        else:
            bidang_current = await crud.bidang.get_by_id(id=id)
            if bidang_current.geom :
                bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))
            bidang_updated = BidangUpdateSch(status=StatusBidangEnum.Deal)
            await crud.bidang.update(obj_current=bidang_current, obj_new=bidang_updated)

async def invoice_update_payment_status(payment_id:UUID):
    
    db_session = db.session
    payment_current = await crud.payment.get_by_id(id=payment_id)
    payment_details_current = await crud.payment_detail.get_by_payment_id(payment_id=payment_id)

    for payment_detail in payment_details_current:
        if payment_detail.is_void:
            payment_detais = await crud.payment_detail.get_multi_payment_actived_by_invoice_id()
            continue
        else:
            invoice_current = await crud.invoice.get(id=payment_detail.invoice_id)
            invoice_updated = InvoiceUpdateSch.from_orm(invoice_current)
            if payment_current.giro_id:
                if payment_current.tanggal_buka is None and payment_current.tanggal_cair is None:
                    invoice_updated.payment_status = None
                if payment_current.tanggal_buka:
                    invoice_updated.payment_status = PaymentStatusEnum.BUKA_GIRO
                if payment_current.tanggal_cair:
                    invoice_updated.payment_status = PaymentStatusEnum.CAIR_GIRO
            else:
                payment_giro_detail = await crud.payment_giro_detail.get(id=payment_detail.payment_giro_detail_id)
                if payment_giro_detail.payment_method == PaymentMethodEnum.Giro:
                    giro = await crud.giro.get(id=payment_giro_detail.giro_id)
                    if giro:
                        if giro.tanggal_buka:
                            invoice_updated.payment_status = PaymentStatusEnum.BUKA_GIRO
                        if giro.tanggal_cair:
                            invoice_updated.payment_status = PaymentStatusEnum.CAIR_GIRO
                        if giro.tanggal_buka is None and giro.tanggal_cair is None:
                            invoice_updated.payment_status = None
        
        await crud.invoice.update(obj_current=invoice_current, obj_new=invoice_updated, db_session=db_session, with_commit=False)
    
    await db_session.commit()



