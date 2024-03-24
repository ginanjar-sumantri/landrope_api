from uuid import UUID
from fastapi import APIRouter, status, Depends, BackgroundTasks, HTTPException
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, or_, func, and_, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from models import Payment, Worker, Giro, PaymentDetail, Invoice, Bidang, Termin, InvoiceDetail, Skpt, BidangKomponenBiaya, Workflow
from schemas.payment_sch import (PaymentSch, PaymentCreateSch, PaymentUpdateSch, PaymentByIdSch, PaymentVoidSch, PaymentVoidExtSch)
from schemas.payment_detail_sch import PaymentDetailCreateSch, PaymentDetailUpdateSch
from schemas.invoice_sch import InvoiceSch, InvoiceByIdSch, InvoiceSearchSch, InvoiceUpdateSch, InvoiceOnMemoSch
from schemas.giro_sch import GiroSch, GiroCreateSch, GiroUpdateSch
from schemas.bidang_sch import BidangUpdateSch
from schemas.termin_sch import TerminSearchSch
from schemas.beban_biaya_sch import BebanBiayaGroupingSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException, ContentNoChangeException)
from common.generator import generate_code
from common.enum import StatusBidangEnum, PaymentMethodEnum, JenisBayarEnum, WorkflowLastStatusEnum, PaymentStatusEnum
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

    bidang_ids = []
    invoice_ids = []
    for dt in sch.details:
        invoice_current = await crud.invoice.get_by_id(id=dt.invoice_id)
        if (invoice_current.invoice_outstanding - dt.amount) < 0:
            raise ContentNoChangeException(detail="Invalid Amount: Amount payment tidak boleh lebih besar dari invoice outstanding!!")
        
        bidang_ids.append(invoice_current.bidang_id)
        if invoice_current.jenis_bayar not in [JenisBayarEnum.UTJ, JenisBayarEnum.UTJ_KHUSUS]:
            invoice_ids.append(invoice_current.id)

    new_obj = await crud.payment.create(obj_in=sch, created_by_id=current_worker.id)
    new_obj = await crud.payment.get_by_id(id=new_obj.id)

    background_task.add_task(bidang_update_status, bidang_ids)
    background_task.add_task(invoice_update_payment_status, new_obj.id)
    
    return create_response(data=new_obj)

#backup
# @router.post("/create", response_model=PostResponseBaseSch[PaymentSch], status_code=status.HTTP_201_CREATED)
# async def create(
#             sch: PaymentCreateSch,
#             background_task:BackgroundTasks,
#             current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
#     """Create a new object"""
#     db_session = db.session

#     amount_dtls = [dt.amount for dt in sch.details]

#     if (sch.amount - sum(amount_dtls)) < 0:
#             raise ContentNoChangeException(detail=f"Invalid Amount: Amount payment detail tidak boleh lebih besar dari payment!!")

#     giro_current = None

#     if sch.giro_id is None and sch.payment_method != PaymentMethodEnum.Tunai:
#         giro_current = await crud.giro.get_by_nomor_giro_and_payment_method(nomor_giro=sch.nomor_giro, payment_method=sch.payment_method)
#         if giro_current is None:
#             entity = CodeCounterEnum.Giro if sch.payment_method == PaymentMethodEnum.Giro else CodeCounterEnum.Cek
#             last_number_giro = await generate_code(entity=entity, db_session=db_session, with_commit=False)
#             code_giro = f"{sch.payment_method.value}/{last_number_giro}"
#             sch_giro = GiroCreateSch(**sch.dict(exclude={"code"}), code=code_giro, is_active=True, from_master=False)
            
#             giro_current = await crud.giro.create(obj_in=sch_giro, created_by_id=current_worker.id, db_session=db_session, with_commit=False)
#         else:
#             sch_giro = GiroUpdateSch(**giro_current.dict())
#             sch_giro.tanggal_buka = sch.tanggal_buka
#             sch_giro.tanggal_cair = sch.tanggal_cair

#             giro_current = await crud.giro.update(obj_current=giro_current, obj_new=sch_giro, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)
        
#         sch.giro_id = giro_current.id      
    
#     if sch.giro_id and sch.payment_method == PaymentMethodEnum.Giro:
#         giro_current = await crud.giro.get(id=sch.giro_id)
#         sch_giro = GiroUpdateSch(**giro_current.dict())
#         sch_giro.tanggal_buka = sch.tanggal_buka
#         sch_giro.tanggal_cair = sch.tanggal_cair

#         giro_current = await crud.giro.update(obj_current=giro_current, obj_new=sch_giro, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

#     last_number = await generate_code(entity=CodeCounterEnum.Payment, db_session=db_session, with_commit=False)
#     sch.code = f"PAY/{last_number}"

#     new_obj = await crud.payment.create(obj_in=sch, created_by_id=current_worker.id, with_commit=False, db_session=db_session)
    
#     bidang_ids = []
#     invoice_ids = []
#     for dt in sch.details:
#         invoice_current = await crud.invoice.get_by_id(id=dt.invoice_id)
#         if (invoice_current.invoice_outstanding - dt.amount) < 0:
#             raise ContentNoChangeException(detail="Invalid Amount: Amount payment tidak boleh lebih besar dari invoice outstanding!!")
        
#         # if invoice_current.jenis_bayar == JenisBayarEnum.BIAYA_LAIN:
#         #     await bidang_komponen_biaya_add_pay_update_is_paid()
        
#         bidang_ids.append(invoice_current.bidang_id)
#         invoice_ids.append(invoice_current.id)

#         detail = PaymentDetailCreateSch(payment_id=new_obj.id, invoice_id=dt.invoice_id, amount=dt.amount, is_void=False, allocation_date=dt.allocation_date)
#         await crud.payment_detail.create(obj_in=detail, created_by_id=current_worker.id, db_session=db_session, with_commit=False)

#     await db_session.commit()

#     new_obj = await crud.payment.get_by_id(id=new_obj.id)

#     background_task.add_task(bidang_update_status, bidang_ids)
#     background_task.add_task(invoice_update_payment_status, new_obj.id)
    
#     return create_response(data=new_obj)

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
                Payment.pay_to.ilike(f"%{keyword}%"),
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
    db_session = db.session

    obj_current = await crud.payment.get_by_id(id=id)

    if obj_current.is_void:
        raise ContentNoChangeException(detail="Payment telah di void")

    if not obj_current:
        raise IdNotFoundException(Payment, id)
    
    amount_dtls = []

    for dt in sch.details:
        if dt.id:
            dt_current = next((x for x in obj_current.details if x.id == dt.id), None)
            if dt_current.is_void != True:
                amount_dtls.append(dt_current.amount)
        else:
            amount_dtls.append(dt.amount)
    
    if (sch.amount - sum(amount_dtls)) < 0:
            raise ContentNoChangeException(detail=f"Invalid Amount: Amount payment detail tidak boleh lebih besar dari payment!!")
    
    giro_current = None
    if sch.giro_id is None and sch.payment_method != PaymentMethodEnum.Tunai:
        giro_current = await crud.giro.get_by_nomor_giro(code=sch.nomor_giro)
        if giro_current is None:
            entity = CodeCounterEnum.Giro if sch.payment_method == PaymentMethodEnum.Giro else CodeCounterEnum.Cek
            last_number_giro = await generate_code(entity=entity, db_session=db_session, with_commit=False)
            code_giro = f"{sch.payment_method.value}/{last_number_giro}"
            sch_giro = GiroCreateSch(**sch.dict(exclude={"code"}), code=code_giro, is_active=True, from_master=False)
            giro_current = await crud.giro.create(obj_in=sch_giro, created_by_id=current_worker.id, db_session=db_session, with_commit=False)
        else:
            sch_giro = GiroUpdateSch(**giro_current.dict())
            sch_giro.tanggal_buka = sch.tanggal_buka
            sch_giro.tanggal_cair = sch.tanggal_cair

            giro_current = await crud.giro.update(obj_current=giro_current, obj_new=sch_giro, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)
        sch.giro_id = giro_current.id    
    
    if sch.giro_id and sch.payment_method == PaymentMethodEnum.Giro:
        giro_current = await crud.giro.get(id=sch.giro_id)
        sch_giro = GiroUpdateSch(**giro_current.dict())
        sch_giro.tanggal_buka = sch.tanggal_buka
        sch_giro.tanggal_cair = sch.tanggal_cair

        giro_current = await crud.giro.update(obj_current=giro_current, obj_new=sch_giro, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

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
    await db_session.refresh(obj_updated)
    
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
    
    obj_updated = obj_current
    obj_updated.is_void = True
    obj_updated.void_reason = sch.void_reason
    obj_updated.void_by_id = current_worker.id
    obj_updated.void_at = date.today()

    obj_updated = await crud.payment.update(obj_current=obj_current, obj_new=obj_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

    bidang_ids = []
    for dt in obj_current.details:
        payment_dtl_updated = dt
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
    objs = [inv for inv in objs if inv.invoice_outstanding > 0 
            and ((inv.termin.status_workflow == WorkflowLastStatusEnum.COMPLETED 
                  and inv.jenis_bayar not in [JenisBayarEnum.UTJ, JenisBayarEnum.UTJ_KHUSUS]) or inv.jenis_bayar in [JenisBayarEnum.UTJ, JenisBayarEnum.UTJ_KHUSUS])]
    
    return create_response(data=objs)

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

    if obj.termin.status_workflow != WorkflowLastStatusEnum.COMPLETED and obj.jenis_bayar not in [JenisBayarEnum.UTJ, JenisBayarEnum.UTJ_KHUSUS]:
        raise HTTPException(status_code=422, detail="Memo bayar must completed approval")
    
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Invoice, id)

@router.get("/search/giro", response_model=GetResponseBaseSch[list[GiroSch]])
async def get_list(
                keyword:str = None,
                payment_id:UUID = None, 
                filter_query:str=None,
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
        query = query.outerjoin(Giro.payment).filter(or_(Giro.payment == None, Payment.is_void == True))
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

    invoice_outstandings = await crud.invoice.get_multi_outstanding_invoice(keyword=keyword)
    list_id = [invoice.termin_id for invoice in invoice_outstandings]

    query = select(Termin).where(and_(Termin.status_workflow == WorkflowLastStatusEnum.COMPLETED,
                                    Termin.id.in_(list_id)))
    
    query = query.options(selectinload(Termin.tahap))

    objs = await crud.termin.get_multi_no_page(query=query)
    
    return create_response(data=objs)

@router.get("/search/invoice/by-termin/{id}", response_model=GetResponseBaseSch[list[InvoiceOnMemoSch]])
async def get_invoice_by_id(id:UUID):

    """Get an object by id"""

    termin_current = await crud.termin.get_by_id(id=id)
    if termin_current.status_workflow != WorkflowLastStatusEnum.COMPLETED and termin_current.jenis_bayar not in [JenisBayarEnum.UTJ, JenisBayarEnum.UTJ_KHUSUS]:
        raise HTTPException(status_code=422, detail="Memo bayar must completed approval")

    memo_bayar_invoices = await crud.invoice.get_multi_by_termin_id(termin_id=id)

    bidang_ids = [inv.bidang_id for inv in memo_bayar_invoices if inv.use_utj == True and inv.is_void != True]
    utj_invoices = await crud.invoice.get_multi_by_bidang_ids(bidang_ids=bidang_ids)

    merge_invoices = memo_bayar_invoices + utj_invoices

    invoices:list[InvoiceOnMemoSch] = []
    for inv in merge_invoices:
        inv_in = InvoiceOnMemoSch.from_orm(inv)
        if inv_in.jenis_bayar in [JenisBayarEnum.UTJ, JenisBayarEnum.UTJ_KHUSUS]:
            inv_in.realisasi = True
        else:
            inv_in.realisasi = False
        
        invoices.append(inv_in)

    return create_response(data=invoices)

@router.get("/search/komponen/by-termin/{id}", response_model=GetResponseBaseSch[list[BebanBiayaGroupingSch]])
async def get_invoice_by_id(id:UUID):

    """Get an object by id"""

    termin_current = await crud.termin.get_by_id(id=id)
    if termin_current.status_workflow != WorkflowLastStatusEnum.COMPLETED and termin_current.jenis_bayar not in [JenisBayarEnum.UTJ, JenisBayarEnum.UTJ_KHUSUS]:
        raise HTTPException(status_code=422, detail="Memo bayar must completed approval")

    komponens = await crud.bebanbiaya.get_multi_grouping_beban_biaya_by_termin_id(termin_id=id)

    return create_response(data=komponens)

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
            if payment_current.tanggal_buka is None and payment_current.tanggal_cair is None:
                invoice_updated.payment_status = None
            if payment_current.tanggal_buka:
                invoice_updated.payment_status = PaymentStatusEnum.BUKA_GIRO
            if payment_current.tanggal_cair:
                invoice_updated.payment_status = PaymentStatusEnum.CAIR_GIRO
        
        await crud.invoice.update(obj_current=invoice_current, obj_new=invoice_updated, db_session=db_session, with_commit=False)
    
    await db_session.commit()



