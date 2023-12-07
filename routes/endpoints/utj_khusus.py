from uuid import UUID
from fastapi import APIRouter, status, Depends, BackgroundTasks, HTTPException
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select
from models import UtjKhusus, UtjKhususDetail, Worker, KjbDt, Invoice, PaymentDetail, KjbHd, Termin
from schemas.utj_khusus_sch import (UtjKhususSch, UtjKhususCreateSch, UtjKhususUpdateSch, UtjKhususByIdSch)
from schemas.utj_khusus_detail_sch import (UtjKhususDetailCreateSch, UtjKhususDetailUpdateSch)
from schemas.termin_sch import TerminCreateSch
from schemas.payment_sch import PaymentCreateSch, PaymentUpdateSch
from schemas.payment_detail_sch import PaymentDetailCreateSch, PaymentDetailUpdateSch
from schemas.invoice_sch import InvoiceCreateSch, InvoiceUpdateSch
from schemas.kjb_hd_sch import KjbHdSearchSch, KjbHdForUtjKhususByIdSch
from schemas.kjb_dt_sch import KjbDtForUtjKhususSch
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

    #region add termin 
    jns_byr = JenisBayarEnum.UTJ_KHUSUS.value
    last_number_termin = await generate_code_month(entity=CodeCounterEnum.Utj, with_commit=False, db_session=db_session)
    termin_code = f"{last_number_termin}/{jns_byr}/LA/{month}/{year}"

    sch_termin = TerminCreateSch(code=termin_code, kjb_hd_id=sch.kjb_hd_id,
                                jenis_bayar=JenisBayarEnum.UTJ_KHUSUS, 
                                is_void=False)
    
    termin = await crud.termin.create(obj_in=sch_termin, db_session=db_session, with_commit=False, created_by_id=current_worker.id)
    #endregion

    sch.termin_id = termin.id
    sch.payment_id = payment.id
    sch.code = termin_code
    new_obj = await crud.utj_khusus.create(obj_in=sch, created_by_id=current_worker.id, db_session=db_session, with_commit=False)

    # region add invoice and payment detail
    for dt in sch.details:
        kjb_dt_current = await crud.kjb_dt.get_by_id(id=dt.kjb_dt_id)
        if not kjb_dt_current:
            raise IdNotFoundException(KjbDt, dt.kjb_dt_id)
        
        if dt.invoice_id is None and kjb_dt_current.hasil_peta_lokasi:
            last_number_invoice = await generate_code_month(entity=CodeCounterEnum.Invoice, with_commit=False, db_session=db_session)

            invoice_sch = InvoiceCreateSch(
                        bidang_id=kjb_dt_current.hasil_peta_lokasi.bidang_id,
                        code=f"INV/{last_number_invoice}/{jns_byr}/LA/{month}/{year}",
                        amount=dt.amount,
                        termin_id=termin.id,
                        is_void=False
                    )
            
            invoice = await crud.invoice.create(obj_in=invoice_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)
            
            dt.invoice_id = invoice.id
            bidang_ids.append(invoice.bidang_id)

            #add payment detail
            payment_detail_sch = PaymentDetailCreateSch(payment_id=payment.id, invoice_id=invoice.id, amount=invoice.amount, is_void=False)
            await crud.payment_detail.create(obj_in=payment_detail_sch, created_by_id=current_worker.id, db_session=db_session, with_commit=False)

        detail_sch = UtjKhususDetailCreateSch(**dt.dict(), utj_khusus_id=new_obj.id)
        await crud.utj_khusus_detail.create(obj_in=detail_sch, created_by_id=current_worker.id, db_session=db_session, with_commit=False)
    
    #endregion
    
    await db_session.commit()
    await db_session.refresh(new_obj)

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

    # region remove detail, invoice and payment detail
    removed_invoice:list[Invoice] = []
    list_id_detail = [dt.id for dt in sch.details if dt.id != None]
    if len(list_id_detail) > 0:
        removed_utj_detail = await crud.utj_khusus_detail.get_multi_not_in_id_removed(list_ids=list_id_detail, utj_khusus_id=id)
        for utj_khusus_detail in removed_utj_detail:
            if utj_khusus_detail.invoice:
                removed_invoice.append(utj_khusus_detail.invoice)
                if len(utj_khusus_detail.invoice.payment_details) > 0:
                    bidang_ids.append(utj_khusus_detail.invoice.bidang_id)
                    await crud.payment_detail.remove_multiple_data(list_obj=utj_khusus_detail.invoice.payment_details, db_session=db_session)        
            
        if len(removed_invoice) > 0:
            await crud.invoice.remove_multiple_data(list_obj=removed_invoice, db_session=db_session)

        if len(removed_utj_detail) > 0:
            await crud.utj_khusus_detail.remove_multiple_data(list_obj=removed_utj_detail, db_session=db_session)

    if len(list_id_detail) == 0 and len(obj_current.details) > 0:
        list_id_invoice = [dt.invoice_id for dt in obj_current.details if dt.invoice_id is not None]
        removed_invoice = await crud.invoice.get_multi_in_id_removed(list_ids=list_id_invoice, termin_id=obj_updated.termin_id)
        for invoice in removed_invoice:
            if len(invoice.payment_details) > 0:
                bidang_ids.append(invoice.bidang_id)
                await crud.payment_detail.remove_multiple_data(list_obj=invoice.payment_details, db_session=db_session)
            
        if len(removed_invoice) > 0:
            await crud.invoice.remove_multiple_data(list_obj=removed_invoice, db_session=db_session)
        
        if len(obj_current.details) > 0:
            await crud.utj_khusus_detail.remove_multiple_data(list_obj=obj_current.details, db_session=db_session)
    #endregion

    #region add/update detail invoice and payment details
    for dt in sch.details:
        if dt.id:
            utj_khusus_detail_current = await crud.utj_khusus_detail.get_by_id(id=dt.id)
            if not utj_khusus_detail_current:
                raise IdNotFoundException(UtjKhususDetail, dt.id)

            invoice_current = await crud.invoice.get_by_id(id=utj_khusus_detail_current.invoice_id)
            if invoice_current:
                invoice_updated_sch = InvoiceUpdateSch(amount=dt.amount)
                invoice_updated = await crud.invoice.update(obj_current=invoice_current, obj_new=invoice_updated_sch, with_commit=False, db_session=db_session, updated_by_id=current_worker.id)

                bidang_ids.append(invoice_current.bidang_id)

                payment_detail_current = next((payment_detail for payment_detail in invoice_current.payment_details if payment_detail.is_void != True), None)
                payment_dtl_updated = PaymentDetailUpdateSch(payment_id=payment.id, invoice_id=invoice_updated.id, amount=invoice_updated.amount)
                await crud.payment_detail.update(obj_current=payment_detail_current, obj_new=payment_dtl_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

            
            utj_khusus_detail_update = UtjKhususDetailUpdateSch(**utj_khusus_detail_current.dict(exclude={"amount"}),
                                                                amount=dt.amount)
            
            await crud.utj_khusus_detail.update(obj_current=utj_khusus_detail_current, obj_new=utj_khusus_detail_update, updated_by_id=current_worker.id,
                                                db_session=db_session, with_commit=False)
        else:
            kjb_dt_current = await crud.kjb_dt.get_by_id(id=dt.kjb_dt_id)
            if not kjb_dt_current:
                raise IdNotFoundException(KjbDt, dt.kjb_dt_id)
            
            if dt.invoice_id is None and kjb_dt_current.hasil_peta_lokasi:
                last_number_invoice = await generate_code_month(entity=CodeCounterEnum.Invoice, with_commit=False, db_session=db_session)
                invoice_sch = InvoiceCreateSch(
                            bidang_id=kjb_dt_current.hasil_peta_lokasi.bidang_id,
                            code=f"INV/{last_number_invoice}/{JenisBayarEnum.UTJ_KHUSUS}/LA/{month}/{year}",
                            amount=dt.amount,
                            termin_id=obj_updated.termin_id,
                            is_void=False
                        )
                
                invoice = await crud.invoice.create(obj_in=invoice_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)
                
                dt.invoice_id = invoice.id
                bidang_ids.append(invoice.bidang_id)

                #add payment detail
                payment_detail_sch = PaymentDetailCreateSch(payment_id=payment.id, invoice_id=invoice.id, amount=invoice.amount, is_void=False)
                await crud.payment_detail.create(obj_in=payment_detail_sch, created_by_id=current_worker.id, db_session=db_session, with_commit=False)

            utj_khusus_detail_sch = UtjKhususDetailCreateSch(**dt.dict(), utj_khusus_id=obj_updated.id)
            await crud.utj_khusus_detail.create(obj_in=utj_khusus_detail_sch, created_by_id=current_worker.id, db_session=db_session, with_commit=False)

    #endregion

    await db_session.commit()
    await db_session.refresh(obj_updated)

    obj_updated = await crud.utj_khusus.get_by_id(id=obj_updated.id)

    background_task.add_task(HelperService().bidang_update_status, bidang_ids)

    return create_response(data=obj_updated)

@router.get("/search/kjb_hd", response_model=GetResponseBaseSch[list[KjbHdSearchSch]])
async def get_list_kjb_hd(
                keyword:str = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(KjbHd)
    query = query.outerjoin(Termin, Termin.kjb_hd_id == KjbHd.id)
    query = query.filter(Termin.kjb_hd_id == None)
    
    if keyword:
        query = query.filter(KjbHd.code.ilike(f'%{keyword}%'))


    objs = await crud.kjb_hd.get_multi_no_page(query=query)
    return create_response(data=objs)

@router.get("/search/kjb_hd/{id}", response_model=GetResponseBaseSch[KjbHdForUtjKhususByIdSch])
async def get_list_bidang_by_kjb_hd_id(
                id:UUID,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    obj = await crud.kjb_hd.get_by_id_for_termin(id=id)
    kjb_dts = await crud.kjb_dt.get_multi_by_kjb_hd_id(kjb_hd_id=id)

    obj_return = KjbHdForUtjKhususByIdSch(**dict(obj))

    kjbdts = []
    for b in kjb_dts:
        kjb_dt = KjbDtForUtjKhususSch(id=b.id,
                                    id_bidang=b.hasil_peta_lokasi.id_bidang if b.hasil_peta_lokasi != None else None,
                                    alashak=b.alashak,
                                    luas_bayar=b.hasil_peta_lokasi.bidang.luas_bayar if b.hasil_peta_lokasi != None else None,
                                    luas_surat=b.luas_surat,
                                    luas_surat_by_ttn=b.luas_surat_by_ttn)
        kjbdts.append(kjb_dt)

    obj_return.kjb_dts = kjbdts

    return create_response(data=obj_return)

# @router.get("/print-out/utj/{id}")
# async def printout(id:UUID | str,
#                         current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
#     """Print out UTJ"""
#     try :
#         obj = await crud.utj_khusus.get_by_id(id=id)
#         if obj is None:
#             raise IdNotFoundException(Termin, id)

#         data =  []
#         no:int = 1
#         invoices = await crud.invoice.get_invoice_by_termin_id_for_printout_utj(termin_id=id, jenis_bayar=termin_header.jenis_bayar)
#         for inv in invoices:
#             invoice = InvoiceForPrintOutUtj(**dict(inv))
#             invoice.amountExt = "{:,.0f}".format(invoice.amount)
#             invoice.luas_suratExt = "{:,.0f}".format(invoice.luas_surat)
#             keterangan:str = ""
#             keterangans = await crud.hasil_peta_lokasi_detail.get_keterangan_by_bidang_id_for_printout_utj(bidang_id=inv.bidang_id)
#             for k in keterangans:
#                 kt = HasilPetaLokasiDetailForUtj(**dict(k))
#                 if kt.keterangan is not None and kt.keterangan != '':
#                     keterangan += f'{kt.keterangan}, '
#             keterangan = keterangan[0:-2]
#             invoice.keterangan = keterangan
#             invoice.no = no
#             no = no + 1

#             data.append(invoice)

#         array_total_luas_surat = numpy.array([b.luas_surat for b in invoices])
#         total_luas_surat = numpy.sum(array_total_luas_surat)
#         total_luas_surat = "{:,.0f}".format(total_luas_surat)

#         array_total_amount = numpy.array([b.amount for b in invoices])
#         total_amount = numpy.sum(array_total_amount)
#         total_amount = "{:,.0f}".format(total_amount)

#         filename:str = "utj.html" if termin_header.jenis_bayar == "UTJ" else "utj_khusus.html"
#         env = Environment(loader=FileSystemLoader("templates"))
#         template = env.get_template(filename)

#         render_template = template.render(code=termin_header.code,
#                                         data=data,
#                                         total_luas_surat=total_luas_surat,
#                                         total_amount=total_amount)
        
#         try:
#             doc = await PdfService().get_pdf(render_template)
#         except Exception as e:
#             raise HTTPException(status_code=500, detail="Failed generate document")
        
#         response = Response(doc, media_type='application/pdf')
#         response.headers["Content-Disposition"] = f"attachment; filename={termin_header.code}.pdf"
#         return response
#     except Exception as e:
#         raise HTTPException(status_code=422, detail=str(e))