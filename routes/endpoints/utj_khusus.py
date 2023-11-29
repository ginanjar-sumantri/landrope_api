from uuid import UUID
from fastapi import APIRouter, status, Depends, BackgroundTasks
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from models import UtjKhusus, Worker
from schemas.utj_khusus_sch import (UtjKhususSch, UtjKhususCreateSch, UtjKhususUpdateSch, UtjKhususByIdSch)
from schemas.termin_sch import TerminCreateSch
from schemas.payment_sch import PaymentCreateSch, PaymentUpdateSch
from schemas.payment_detail_sch import PaymentDetailCreateSch, PaymentDetailUpdateSch
from schemas.invoice_sch import InvoiceCreateSch, InvoiceUpdateSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ContentNoChangeException)
from common.generator import generate_code, generate_code_month
from common.enum import PaymentMethodEnum, JenisBayarEnum
from services.helper_service import HelperService
from models.code_counter_model import CodeCounterEnum
from datetime import date
import roman
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[UtjKhususSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: UtjKhususCreateSch,
            background_task:BackgroundTasks,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    db_session = db.session

    today = date.today()
    month = roman.toRoman(today.month)
    year = today.year
    bidang_ids = []

    #region add payment
    last_number_payment = await generate_code(entity=CodeCounterEnum.Payment, db_session=db_session, with_commit=False)
    sch_payment = PaymentCreateSch(**sch.dict(exclude={"code"}),
                            code=f"PAY-UTJ-KHUSUS/{last_number_payment}",
                            payment_method=PaymentMethodEnum.Tunai
                        )
    
    payment = await crud.payment.create(obj_in=sch_payment, created_by_id=current_worker.id, db_session=db_session, with_commit=False)
    #endregion payment

    #region add termin and invoice
    
    jns_byr = JenisBayarEnum.UTJ.value
    last_number_termin = await generate_code_month(entity=CodeCounterEnum.Utj, with_commit=False, db_session=db_session)
    termin_code = f"{last_number_termin}/{jns_byr}/LA/{month}/{year}"

    sch_termin = TerminCreateSch(code=termin_code, kjb_hd_id=sch.kjb_hd_id,
                                jenis_bayar=JenisBayarEnum.UTJ_KHUSUS, 
                                is_void=False)
    
    termin = await crud.termin.create(obj_in=sch_termin, db_session=db_session, with_commit=False, created_by_id=current_worker.id)

    # region add invoice and payment detail
    for invoice in sch.invoices:
        last_number_invoice = await generate_code_month(entity=CodeCounterEnum.Invoice, with_commit=False, db_session=db_session)
        invoice_sch = InvoiceCreateSch(**invoice.dict(), termin_id=termin.id)
        invoice_sch.code = f"INV/{last_number_invoice}/{jns_byr}/LA/{month}/{year}"
        invoice_sch.is_void = False
        
        invoice = await crud.invoice.create(obj_in=invoice_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)
        
        bidang_ids.append(invoice.bidang_id)

        #add payment detail
        detail = PaymentDetailCreateSch(payment_id=payment.id, invoice_id=invoice.id, amount=invoice.amount, is_void=False)
        await crud.payment_detail.create(obj_in=detail, created_by_id=current_worker.id, db_session=db_session, with_commit=False)

    #endregion

    #endregion
    sch.termin_id = termin.id
    sch.payment_id = payment.id
        
    new_obj = await crud.utj_khusus.create(obj_in=sch, created_by_id=current_worker.id, db_session=db_session)
    new_obj = await crud.utj_khusus.get_by_id(id=new_obj.id)

    background_task.add_task(HelperService().bidang_update_status, bidang_ids)
    
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

@router.get("/{id}", response_model=GetResponseBaseSch[UtjKhususByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.utj_khusus.get_by_id(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(UtjKhusus, id)

@router.put("/{id}", response_model=PutResponseBaseSch[UtjKhususSch])
async def update(id:UUID, sch:UtjKhususUpdateSch,
                 background_task:BackgroundTasks,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""
    db_session = db.session

    today = date.today()
    month = roman.toRoman(today.month)
    year = today.year
    bidang_ids = []

    obj_current = await crud.utj_khusus.get_by_id(id=id)

    if not obj_current:
        raise IdNotFoundException(UtjKhusus, id)
    
    obj_updated = await crud.utj_khusus.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)
    
    payment_current = await crud.payment.get_by_id(id=obj_current.payment_id)

    #region update payment
    sch_payment = PaymentUpdateSch(**sch.dict(exclude={"code"}),
                            code=payment_current.code,
                            payment_method=PaymentMethodEnum.Tunai
                        )

    payment = await crud.payment.update(obj_current=payment_current, obj_new=sch_payment, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)
    #endregion

    # region remove invoice and payment detail
    list_id_invoice = [inv.id for inv in sch.invoices if inv.id != None]
    if len(list_id_invoice) > 0:
        removed_invoice = await crud.invoice.get_multi_not_in_id_removed(list_ids=list_id_invoice, termin_id=obj_updated.id)
        for ls in removed_invoice:
            if len(ls.payment_details) > 0:
                bidang_ids.append(ls.bidang_id)
                await crud.payment_detail.remove_multiple_data(list_obj=ls.payment_details, db_session=db_session)
            
        if len(removed_invoice) > 0:
            await crud.invoice.remove_multiple_data(list_obj=removed_invoice, db_session=db_session)

    if len(list_id_invoice) == 0 and len(obj_current.termin.invoices) > 0:
        list_id_invoice = [dt.id for dt in obj_current.termin.invoices if dt.id is not None]
        removed_invoice = await crud.invoice.get_multi_in_id_removed(list_ids=list_id_invoice, termin_id=obj_updated.id)
        for ls in removed_invoice:
            if len(ls.payment_details) > 0:
                bidang_ids.append(ls.bidang_id)
                await crud.payment_detail.remove_multiple_data(list_obj=ls.payment_details, db_session=db_session)
            
        if len(removed_invoice) > 0:
            await crud.invoice.remove_multiple_data(list_obj=removed_invoice, db_session=db_session)
    #endregion

    #region add/update invoice and payment details
    for invoice in sch.invoices:
        if invoice.id:
            invoice_current = await crud.invoice.get_by_id(id=invoice.id)
            if invoice_current:
                invoice_updated_sch = InvoiceUpdateSch(**invoice.dict())
                invoice_updated_sch.is_void = invoice_current.is_void
                invoice_updated = await crud.invoice.update(obj_current=invoice_current, obj_new=invoice_updated_sch, with_commit=False, db_session=db_session, updated_by_id=current_worker.id)

                bidang_ids.append(invoice_current.bidang_id)

                payment_detail_current = next((payment_detail for payment_detail in invoice_current.payment_details if payment_detail.is_void != True), None)
                payment_dtl_updated = PaymentDetailUpdateSch(payment_id=payment.id, invoice_id=invoice_updated.id, amount=invoice_updated.amount)
                await crud.payment_detail.update(obj_current=payment_detail_current, obj_new=payment_dtl_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

            else:
                raise ContentNoChangeException(detail="data invoice tidak ditemukan")
        else:
            last_number_invoice = await generate_code_month(entity=CodeCounterEnum.Invoice, with_commit=False, db_session=db_session)
            invoice_sch = InvoiceCreateSch(**invoice.dict(), termin_id=obj_updated.id)
            invoice_sch.code = f"INV/{last_number_invoice}/{JenisBayarEnum.UTJ_KHUSUS}/LA/{month}/{year}"
            invoice_sch.is_void = False

            new_obj_invoice = await crud.invoice.create(obj_in=invoice_sch, db_session=db_session, with_commit=False)

            bidang_ids.append(new_obj_invoice.bidang_id)

            #add payment detail
            detail = PaymentDetailCreateSch(payment_id=payment.id, invoice_id=new_obj_invoice.id, amount=new_obj_invoice.amount, is_void=False)
            await crud.payment_detail.create(obj_in=detail, created_by_id=current_worker.id, db_session=db_session, with_commit=False)

    #endregion

    await db_session.commit()
    await db_session.refresh(obj_updated)

    obj_updated = await crud.utj_khusus.get_by_id(id=obj_updated.id)

    background_task.add_task(HelperService().bidang_update_status, bidang_ids)
    return create_response(data=obj_updated)

   