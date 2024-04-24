from uuid import UUID
from fastapi import APIRouter, status, Depends, BackgroundTasks, HTTPException
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, or_, func, case, cast, Float, and_
from sqlalchemy import String
from sqlalchemy.orm import selectinload
from models import (Invoice, Worker, Bidang, Termin, PaymentDetail, Payment, InvoiceDetail, BidangKomponenBiaya,
                    Planing, Ptsk, Skpt, Project, Desa, Tahap, PaymentGiroDetail)
from models.code_counter_model import CodeCounterEnum
from schemas.invoice_sch import (InvoiceSch, InvoiceCreateSch, InvoiceUpdateSch, InvoiceByIdSch, InvoiceVoidSch, InvoiceByIdVoidSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, 
                                  DeleteResponseBaseSch, GetResponsePaginatedSch, 
                                  PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.generator import generate_code_month
from common.enum import JenisBayarEnum, WorkflowLastStatusEnum
from services.helper_service import HelperService
from datetime import date
import crud
import json
import roman


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[InvoiceSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: InvoiceCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    db_session = db.session
        
    new_obj = await crud.invoice.create(obj_in=sch, created_by_id=current_worker.id, db_session=db_session)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[InvoiceSch])
async def get_list(
                params: Params=Depends(), 
                order_by:str = None, 
                keyword:str = None,
                outstanding:bool|None = False,
                filter_query:str=None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(Invoice).outerjoin(Bidang, Bidang.id == Invoice.bidang_id
                        ).outerjoin(Termin, Termin.id == Invoice.termin_id
                        ).outerjoin(Planing, Planing.id == Bidang.planing_id
                        ).outerjoin(Project, Project.id == Planing.project_id
                        ).outerjoin(Desa, Desa.id == Planing.desa_id
                        ).outerjoin(Skpt, Skpt.id == Bidang.skpt_id
                        ).outerjoin(Ptsk, Ptsk.id == Skpt.ptsk_id
                        ).outerjoin(Tahap, Tahap.id == Termin.tahap_id)
        
    if keyword:
        query = query.filter(
            or_(
                Bidang.id_bidang.ilike(f'%{keyword}%'),
                Bidang.alashak.ilike(f'%{keyword}%'),
                Termin.code.ilike(f'%{keyword}%'),
                Termin.nomor_memo.ilike(f'%{keyword}%'),
                Invoice.code.ilike(f'%{keyword}%'),
                Project.name.ilike(f'%{keyword}%'),
                Desa.name.ilike(f'%{keyword}%'),
                Ptsk.name.ilike(f'%{keyword}%'),
                cast(Tahap.nomor_tahap, String).ilike(f'%{keyword}%'),
                Termin.jenis_bayar.ilike(f'%{keyword}%'),
                Planing.name.ilike(f'%{keyword}%')
            )
        )
    
    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
                query = query.where(getattr(Invoice, key) == value)

    if outstanding:
        invoice_outstandings = await crud.invoice.get_multi_outstanding_invoice()
        ids = [inv.id for inv in invoice_outstandings]

        query = query.filter(Invoice.id.in_(ids))

    query = query.distinct()
    query = query.options(selectinload(Invoice.bidang
                                    ).options(selectinload(Bidang.skpt
                                                    ).options(selectinload(Skpt.ptsk))
                                    ).options(selectinload(Bidang.penampung)
                                    )
                ).options(selectinload(Invoice.details
                                    ).options(selectinload(InvoiceDetail.bidang_komponen_biaya
                                                        ).options(selectinload(BidangKomponenBiaya.beban_biaya)
                                                        ).options(selectinload(BidangKomponenBiaya.bidang))
                                    )
                ).options(selectinload(Invoice.payment_details
                                    ).options(selectinload(PaymentDetail.payment
                                                        ).options(selectinload(Payment.giro))
                                    )
                )

    objs = await crud.invoice.get_multi_paginated_ordered(params=params, query=query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[InvoiceByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.invoice.get_by_id(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Invoice, id)

@router.put("/{id}", response_model=PutResponseBaseSch[InvoiceSch])
async def update(id:UUID, sch:InvoiceUpdateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.invoice.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Invoice, id)
    
    obj_updated = await crud.invoice.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[InvoiceSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Delete a object"""

    obj_current = await crud.invoice.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Invoice, id)
    
    obj_deleted = await crud.invoice.remove(id=id)

    return obj_deleted

@router.put("/void/{id}", response_model=GetResponseBaseSch[InvoiceByIdVoidSch])
async def void(id:UUID, sch:InvoiceVoidSch,
               background_task:BackgroundTasks,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """void a obj by its ids"""
    db_session = db.session

    obj_current = await crud.invoice.get_by_id(id=id)

    if not obj_current:
        raise IdNotFoundException(Invoice, id)
    
    if obj_current.termin.jenis_bayar not in [JenisBayarEnum.UTJ_KHUSUS, JenisBayarEnum.UTJ]:
        if obj_current.termin.status_workflow == WorkflowLastStatusEnum.NEED_DATA_UPDATE:
            raise HTTPException(status_code=422, detail=f"Failed void. Detail : Need Data Update")

    
    bidang_current = await crud.bidang.get_by_id_for_spk(id=obj_current.bidang_id)
    if obj_current.jenis_bayar not in [JenisBayarEnum.LUNAS, JenisBayarEnum.PELUNASAN, JenisBayarEnum.PENGEMBALIAN_BEBAN_PENJUAL, JenisBayarEnum.SISA_PELUNASAN, JenisBayarEnum.BIAYA_LAIN] and bidang_current.has_invoice_lunas:
        raise HTTPException(status_code=422, detail="Failed void. Detail : Bidang on invoice already have invoice lunas!")
    
    obj_updated = obj_current
    obj_updated.is_void = True
    obj_updated.void_reason = sch.void_reason
    obj_updated.void_by_id = current_worker.id
    obj_updated.void_at = date.today()

    obj_updated = await crud.invoice.update(obj_current=obj_current, obj_new=obj_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

    if obj_current.jenis_bayar != JenisBayarEnum.PENGEMBALIAN_BEBAN_PENJUAL:
        for dt in obj_current.details:
            bidang_komponen_biaya_current = await crud.bidang_komponen_biaya.get(id=dt.bidang_komponen_biaya_id)
            bidang_komponen_biaya_updated = bidang_komponen_biaya_current
            

            await crud.bidang_komponen_biaya.update(obj_current=bidang_komponen_biaya_current, obj_new=bidang_komponen_biaya_updated, db_session=db_session, with_commit=False)

    bidang_ids = []
    for dt in obj_current.payment_details:
        payment_dtl_updated = dt
        payment_dtl_updated.is_void = True
        payment_dtl_updated.void_reason = sch.void_reason
        payment_dtl_updated.void_by_id = current_worker.id
        payment_dtl_updated.void_at = date.today()
        
        await crud.payment_detail.update(obj_current=dt, obj_new=payment_dtl_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

    await db_session.commit()

    bidang_ids.append(obj_updated.bidang_id)

    background_task.add_task(HelperService().bidang_update_status, bidang_ids)

    obj_updated = await crud.invoice.get_by_id(id=obj_updated.id)
    return create_response(data=obj_updated) 

@router.get("/updated/payment_status",)
async def payment_status_updated():

    """Get an object by id"""

    db_session = db.session

    query = select(Invoice
                ).join(Termin, Termin.id == Invoice.termin_id
                ).where(and_(Invoice.payment_status == None, Invoice.is_void != True, Termin.jenis_bayar.notin_(["UTJ", "UTJ_KHUSUS"])))
    query = query.options(selectinload(Invoice.payment_details
                                ).options(selectinload(PaymentDetail.payment
                                                ).options(selectinload(Payment.giro))
                                ).options(selectinload(PaymentDetail.payment_giro
                                                ).options(selectinload(PaymentGiroDetail.giro))
                                )
            )
    objs = await crud.invoice.get_multi_no_page(query=query)

    for obj in objs:
        payment_detail = next((pay for pay in obj.payment_details if pay.is_void != True), None)
        if payment_detail:
            if payment_detail.giro_id:
                giro = await crud.giro.get(id=payment_detail.giro_id)
                if giro:
                    invoice_updated = InvoiceUpdateSch.from_orm(obj)
                    if giro.tanggal_buka:
                        invoice_updated.payment_status = "BUKA_GIRO"
                    if giro.tanggal_cair:
                        invoice_updated.payment_status = "CAIR_GIRO"
                    if giro.tanggal_buka is None and giro.tanggal_cair is None:
                        invoice_updated.payment_status = None
                    
                    await crud.invoice.update(obj_current=obj, obj_new=invoice_updated, db_session=db_session, with_commit=False)
            elif payment_detail.payment.giro_id:
                giro = await crud.giro.get(id=payment_detail.payment.giro_id)
                if giro:
                    invoice_updated = InvoiceUpdateSch.from_orm(obj)
                    if giro.tanggal_buka:
                        invoice_updated.payment_status = "BUKA_GIRO"
                    if giro.tanggal_cair:
                        invoice_updated.payment_status = "CAIR_GIRO"
                    if giro.tanggal_buka is None and giro.tanggal_cair is None:
                        invoice_updated.payment_status = None
                    
                    await crud.invoice.update(obj_current=obj, obj_new=invoice_updated, db_session=db_session, with_commit=False)
            else:
                pass

    
    await db_session.commit()

    return {"message" : "Successfully"}