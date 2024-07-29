from uuid import UUID
from fastapi import APIRouter, status, Depends, BackgroundTasks, HTTPException, status
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, or_, func, case, cast, Float, and_
from sqlalchemy import String
from sqlalchemy.orm import selectinload
from models import (Invoice, Worker, Bidang, Termin, PaymentDetail, Payment, InvoiceDetail, BidangKomponenBiaya,
                    Planing, Ptsk, Skpt, Project, Desa, Tahap, PaymentGiroDetail)
from schemas.invoice_sch import (InvoiceSch, InvoiceCreateSch, InvoiceUpdateSch, InvoiceByIdSch, InvoiceVoidSch, InvoiceByIdVoidSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, 
                                  DeleteResponseBaseSch, GetResponsePaginatedSch, 
                                  PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.generator import generate_code_month
from common.enum import JenisBayarEnum, WorkflowLastStatusEnum, WorkflowEntityEnum
from services.helper_service import HelperService
from services.invoice_service import InvoiceService
import crud
import json


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

    items = []
    reference_ids = [invoice.termin_id for invoice in objs.data.items]
    workflows = await crud.workflow.get_by_reference_ids(reference_ids=reference_ids, entity=WorkflowEntityEnum.TERMIN)

    for obj in objs.data.items:
        workflow = next((wf for wf in workflows if wf.reference_id == obj.termin_id), None)
        if workflow:
            obj.status_workflow = workflow.last_status
            obj.step_name_workflow = workflow.step_name

        items.append(obj)

    objs.data.items = items

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

@router.put("/void/{id}")
async def void(id:UUID, sch:InvoiceVoidSch,
               background_task:BackgroundTasks,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """void a obj by its ids"""

    obj_current = await crud.invoice.get_by_id(id=id)

    if not obj_current:
        raise IdNotFoundException(Invoice, id)
    
    if obj_current.termin.jenis_bayar not in [JenisBayarEnum.UTJ_KHUSUS, JenisBayarEnum.UTJ]:
        workflow = await crud.workflow.get_by_reference_id(reference_id=obj_current.termin.id)
        if workflow:
            if workflow.last_status == WorkflowLastStatusEnum.NEED_DATA_UPDATE:
                raise HTTPException(status_code=422, detail=f"Failed void. Detail : Need Data Update")
            
    if obj_current.termin.rfp_ref_no is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice has have RFP")
    
    bidang_current = await crud.bidang.get_by_id_for_spk(id=obj_current.bidang_id)
    if obj_current.jenis_bayar not in [JenisBayarEnum.LUNAS, JenisBayarEnum.PELUNASAN, JenisBayarEnum.PENGEMBALIAN_BEBAN_PENJUAL, JenisBayarEnum.SISA_PELUNASAN, JenisBayarEnum.BIAYA_LAIN] and bidang_current.has_invoice_lunas:
        raise HTTPException(status_code=422, detail="Failed void. Detail : Bidang on invoice already have invoice lunas!")
    
    await InvoiceService().void(obj_current=obj_current, current_worker=current_worker, reason=sch.void_reason)
    
    bidang_ids = []
    bidang_ids.append(obj_current.bidang_id)
    
    # BACKGROUND TASKS UNTUK UPDATE STATUS BEBAS/BELUM BEBAS BIDANG
    background_task.add_task(HelperService().bidang_update_status, bidang_ids)


    return create_response({"detail": "SUCCESS"})


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