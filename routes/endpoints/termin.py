from uuid import UUID
from fastapi import APIRouter, status, Depends, Request, HTTPException, Response, UploadFile, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, or_, and_, func, update, delete
from sqlalchemy import cast, String
from sqlalchemy.orm import selectinload
import crud
from models import (Termin, Worker, Invoice, InvoiceDetail, InvoiceBayar, Tahap, TahapDetail, KjbHd, Spk, Bidang, TerminBayar, 
                    PaymentDetail, Payment, PaymentGiroDetail, Planing, Workflow, WorkflowNextApprover, BidangKomponenBiaya, Planing, Project,
                    Desa, Ptsk)
from models.code_counter_model import CodeCounterEnum
from schemas.tahap_sch import TahapForTerminByIdSch, TahapSch, TahapSrcSch
from schemas.tahap_detail_sch import TahapDetailForPrintOut, TahapDetailForExcel
from schemas.termin_sch import (TerminSch, TerminCreateSch, TerminUpdateSch, 
                                TerminByIdSch, TerminByIdForPrintOut,
                                TerminBidangIDSch, TerminIdSch, TerminHistoriesSch,
                                TerminBebanBiayaForPrintOut, TerminVoidSch)
from schemas.termin_bayar_sch import TerminBayarCreateSch, TerminBayarUpdateSch, TerminBayarForPrintout
from schemas.invoice_sch import (InvoiceCreateSch, InvoiceUpdateSch, InvoiceForPrintOutUtj, InvoiceForPrintOutExt, InvoiceHistoryforPrintOut,
                                 InvoiceHistoryInTermin, InvoiceLuasBayarSch)
from schemas.invoice_detail_sch import InvoiceDetailCreateSch, InvoiceDetailUpdateSch
from schemas.invoice_bayar_sch import InvoiceBayarCreateSch, InvoiceBayarlUpdateSch
from schemas.spk_sch import SpkSrcSch, SpkInTerminSch, SpkHistorySch, SpkIdSch, SpkJenisBayarSch
from schemas.kjb_hd_sch import KjbHdForTerminByIdSch, KjbHdSearchSch
from schemas.bidang_sch import BidangForUtjSch, BidangExcelSch
from schemas.bidang_komponen_biaya_sch import BidangKomponenBiayaUpdateSch, BidangKomponenBiayaSch, BidangKomponenBiayaCreateSch
from schemas.bidang_overlap_sch import BidangOverlapForPrintout, BidangOverlapExcelSch
from schemas.hasil_peta_lokasi_detail_sch import HasilPetaLokasiDetailForUtj
from schemas.kjb_harga_sch import KjbHargaAktaSch
from schemas.payment_detail_sch import PaymentDetailForPrintout
from schemas.marketing_sch import ManagerSrcSch, SalesSrcSch
from schemas.rekening_sch import RekeningSch
from schemas.notaris_sch import NotarisSrcSch
from schemas.beban_biaya_sch import BebanBiayaEstimatedAmountSch
from schemas.workflow_sch import WorkflowCreateSch, WorkflowSystemCreateSch, WorkflowSystemAttachmentSch, WorkflowUpdateSch
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, ContentNoChangeException, DocumentFileNotFoundException)
from common.ordered import OrderEnumSch
from common.enum import (JenisBayarEnum, StatusSKEnum, HasilAnalisaPetaLokasiEnum, 
                        WorkflowEntityEnum, WorkflowLastStatusEnum, StatusPembebasanEnum, SatuanBayarEnum, SatuanHargaEnum,
                        jenis_bayar_to_termin_status_pembebasan_dict, jenis_bayar_to_code_counter_enum,
                        jenis_bayar_to_text)
from common.rounder import RoundTwo
from common.generator import generate_code_month
from services.gcloud_task_service import GCloudTaskService
from services.gcloud_storage_service import GCStorageService
from services.helper_service import HelperService, BundleHelper, BidangHelper, KomponenBiayaHelper
from services.workflow_service import WorkflowService
from services.adobe_service import PDFToExcelService
from decimal import Decimal
from services.pdf_service import PdfService
from jinja2 import Environment, FileSystemLoader
from datetime import date, datetime
from io import BytesIO, StringIO
from typing import Dict
import json
import numpy
import roman
import pandas as pd
import time

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[TerminSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: TerminCreateSch,
            background_task:BackgroundTasks,
            request: Request,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    db_session = db.session
    sch.is_void = False

    today = date.today()
    month = roman.toRoman(today.month)
    year = today.year
    jns_byr:str = ""

    if sch.jenis_bayar == JenisBayarEnum.UTJ or sch.jenis_bayar == JenisBayarEnum.UTJ_KHUSUS:
        jns_byr = JenisBayarEnum.UTJ.value
        last_number = await generate_code_month(entity=CodeCounterEnum.Utj, with_commit=False, db_session=db_session)
        sch.code = f"{last_number}/{jns_byr}/LA/{month}/{year}"
    else:
        code_counter = jenis_bayar_to_code_counter_enum.get(sch.jenis_bayar, sch.jenis_bayar)
        jns_byr = jenis_bayar_to_text.get(sch.jenis_bayar, sch.jenis_bayar)
        last_number = await generate_code_month(entity=code_counter, with_commit=False, db_session=db_session)
        sch.code = f"{last_number}/{jns_byr}/LA/{month}/{year}"

    new_obj = await crud.termin.create(obj_in=sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)

    termin_bayar_temp = []
    #add termin bayar
    for termin_bayar in sch.termin_bayars:
        termin_bayar_sch = TerminBayarCreateSch(**termin_bayar.dict(), termin_id=new_obj.id)
        obj_termin_bayar = await crud.termin_bayar.create(obj_in=termin_bayar_sch,  db_session=db_session, with_commit=False, created_by_id=current_worker.id)
        termin_bayar_temp.append({"termin_bayar_id" : obj_termin_bayar.id, "id_index" : termin_bayar.id_index})

    #add invoice
    for invoice in sch.invoices:
        last_number = await generate_code_month(entity=CodeCounterEnum.Invoice, with_commit=False, db_session=db_session)
        invoice_sch = InvoiceCreateSch(**invoice.dict(), termin_id=new_obj.id, code=f"INV/{last_number}/{jns_byr}/LA/{month}/{year}", is_void=False)
        new_obj_invoice = await crud.invoice.create(obj_in=invoice_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)

        #remove bidang komponen biaya
        await db_session.execute(delete(BidangKomponenBiaya).where(and_(BidangKomponenBiaya.id.in_(r.bidang_komponen_biaya_id for r in invoice.details if r.bidang_komponen_biaya_id is not None and r.is_deleted), 
                                                                        BidangKomponenBiaya.bidang_id == invoice.bidang_id)))

        master_beban_biayas = await crud.bebanbiaya.get_by_ids(list_ids=[bb.beban_biaya_id for bb in invoice.details if bb.beban_biaya_id is not None])

        #add invoice_detail
        for dt in invoice.details:
            if dt.is_deleted:
                continue

            if dt.bidang_komponen_biaya_id is None and dt.beban_biaya_id and dt.is_deleted != True:
                master_beban_biaya = next((bb for bb in master_beban_biayas if bb.id == dt.beban_biaya_id), None)
                bidang_komponen_biaya_new = BidangKomponenBiayaCreateSch(
                amount = dt.komponen_biaya_amount,
                formula = master_beban_biaya.formula,
                satuan_bayar = dt.satuan_bayar,
                satuan_harga = dt.satuan_harga,
                is_add_pay = master_beban_biaya.is_add_pay,
                beban_biaya_id = dt.beban_biaya_id,
                beban_pembeli = dt.beban_pembeli,
                estimated_amount = dt.amount,
                bidang_id = invoice.bidang_id,
                is_paid = False,
                is_exclude_spk = True,
                is_retur = False,
                is_void = False)

                obj_bidang_komponen_biaya = await crud.bidang_komponen_biaya.create(obj_in=bidang_komponen_biaya_new, db_session=db_session, with_commit=False, created_by_id=current_worker.id)
                dt.bidang_komponen_biaya_id = obj_bidang_komponen_biaya.id

            invoice_dtl_sch = InvoiceDetailCreateSch(**dt.dict(), invoice_id=new_obj_invoice.id)
            await crud.invoice_detail.create(obj_in=invoice_dtl_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)

        for dt_bayar in invoice.bayars:
            termin_bayar_id = next((termin_bayar["termin_bayar_id"] for termin_bayar in termin_bayar_temp if termin_bayar["id_index"] == dt_bayar.id_index), None)
            invoice_bayar_new = InvoiceBayarCreateSch(termin_bayar_id=termin_bayar_id, invoice_id=new_obj_invoice.id, amount=dt_bayar.amount)
            await crud.invoice_bayar.create(obj_in=invoice_bayar_new, db_session=db_session, with_commit=False, created_by_id=current_worker.id)

    if sch.jenis_bayar in [JenisBayarEnum.DP, JenisBayarEnum.LUNAS, JenisBayarEnum.PELUNASAN]:
        status_pembebasan = jenis_bayar_to_termin_status_pembebasan_dict.get(sch.jenis_bayar, None)
        await BidangHelper().update_status_pembebasan(list_bidang_id=[inv.bidang_id for inv in sch.invoices], status_pembebasan=status_pembebasan, db_session=db_session)
    
    #workflow
    if new_obj.jenis_bayar not in [JenisBayarEnum.UTJ_KHUSUS, JenisBayarEnum.UTJ]:
        flow = await crud.workflow_template.get_by_entity(entity=WorkflowEntityEnum.TERMIN)
        wf_sch = WorkflowCreateSch(reference_id=new_obj.id, entity=WorkflowEntityEnum.TERMIN, flow_id=flow.flow_id, version=1, last_status=WorkflowLastStatusEnum.ISSUED, step_name="ISSUED")
        
        await crud.workflow.create(obj_in=wf_sch, created_by_id=new_obj.created_by_id, db_session=db_session, with_commit=False)

        GCloudTaskService().create_task(payload={
                                                    "id":str(new_obj.id)
                                                }, 
                                        base_url=f'{request.base_url}landrope/termin/task-workflow')

    await db_session.commit()
    await db_session.refresh(new_obj)

    new_obj = await crud.termin.get_by_id(id=new_obj.id)

    return create_response(data=new_obj)

async def make_sure_all_komponen_biaya_not_outstanding(sch: TerminCreateSch):
    bidang_ids = [x.bidang_id for x in sch.invoices]
    invoice_details = [y for x in sch.invoices for y in x.details]

    komponen_biayas = await crud.bidang_komponen_biaya.get_multi_by_bidang_ids(list_bidang_id=bidang_ids)
    
    for komponen_biaya in komponen_biayas:
        outstanding:Decimal = 0
        invoice_detail = next((inv for inv in invoice_details if inv.bidang_komponen_biaya_id == komponen_biaya.id), None)
        if invoice_detail:
            outstanding = komponen_biaya.estimated_amount - (sum([inv_dtl.amount for inv_dtl in komponen_biaya.invoice_details if inv_dtl.invoice.is_void != True]) + invoice_detail.amount)
        else:
            outstanding = komponen_biaya.estimated_amount - sum([inv_dtl.amount for inv_dtl in komponen_biaya.invoice_details if inv_dtl.invoice.is_void != True])

        if outstanding > 0:
            raise HTTPException(status_code=422, detail="Failed create Termin. Detail : Ada bidang yang komponen biayanya masih memiliki outstanding!")

@router.get("", response_model=GetResponsePaginatedSch[TerminSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None,
            is_utj:bool = False,
            filter_query:str = None,
            filter_list: str | None = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    jenis_bayars = []
    if is_utj:
        jenis_bayars = [JenisBayarEnum.UTJ.value, 
                        JenisBayarEnum.UTJ_KHUSUS.value]
    else:
        jenis_bayars = [JenisBayarEnum.DP.value, 
                        JenisBayarEnum.LUNAS.value, 
                        JenisBayarEnum.PENGEMBALIAN_BEBAN_PENJUAL.value, 
                        JenisBayarEnum.BEGINNING_BALANCE.value, 
                        JenisBayarEnum.BIAYA_LAIN.value, 
                        JenisBayarEnum.SISA_PELUNASAN.value,
                        JenisBayarEnum.PELUNASAN.value]

    query = select(Termin).outerjoin(Invoice, Invoice.termin_id == Termin.id
                        ).outerjoin(Tahap, Tahap.id == Termin.tahap_id
                        ).outerjoin(KjbHd, KjbHd.id == Termin.kjb_hd_id
                        ).outerjoin(Spk, Spk.id == Invoice.spk_id
                        ).outerjoin(Bidang, Bidang.id == Invoice.bidang_id
                        ).outerjoin(Ptsk, Ptsk.id == Tahap.ptsk_id
                        ).outerjoin(Planing, Planing.id == Tahap.planing_id
                        ).outerjoin(Project, Project.id == Planing.project_id
                        ).outerjoin(Desa, Desa.id == Planing.desa_id
                        ).where(Termin.jenis_bayar.in_(jenis_bayars)).distinct()
    
    if filter_list == "list_approval":
        subquery_workflow = (select(Workflow.reference_id).join(Workflow.workflow_next_approvers
                                ).where(and_(WorkflowNextApprover.email == current_worker.email, 
                                            Workflow.entity == WorkflowEntityEnum.TERMIN,
                                            Workflow.last_status != WorkflowLastStatusEnum.COMPLETED))
                    ).distinct()
        
        query = query.filter(Termin.id.in_(subquery_workflow))
    
    if keyword and keyword != '':
        query = query.filter(
            or_(
                Termin.code.ilike(f'%{keyword}%'),
                Termin.jenis_bayar.ilike(f'%{keyword}%'),
                Termin.nomor_memo.ilike(f'%{keyword}%'),
                cast(Tahap.nomor_tahap, String).ilike(f'%{keyword}%'),
                KjbHd.code.ilike(f'%{keyword}%'),
                Bidang.id_bidang.ilike(f'%{keyword}%'),
                Bidang.alashak.ilike(f'%{keyword}%'),
                Ptsk.name.ilike(f'%{keyword}%'),
                Project.name.ilike(f'%{keyword}%'),
                Desa.name.ilike(f'%{keyword}%'),
                Tahap.group.ilike(f'%{keyword}%')
            )
        )

    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
                query = query.where(getattr(Termin, key) == value)
    
    query = query.distinct()

    objs = await crud.termin.get_multi_paginated_ordered(params=params, order_by="created_at", order=OrderEnumSch.descendent, query=query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[TerminByIdSch])
async def get_by_id(id:UUID,
                    current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Get an object by id"""
    
    obj = await crud.termin.get_by_id(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Termin, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[TerminSch])
async def update_(
            id:UUID,
            sch:TerminUpdateSch,
            request:Request,
            background_task:BackgroundTasks,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    db_session = db.session

    obj_current = await crud.termin.get_by_id(id=id)
    if not obj_current:
        raise IdNotFoundException(Termin, id)

    if sch.jenis_bayar not in [JenisBayarEnum.UTJ_KHUSUS, JenisBayarEnum.UTJ]:
        msg_error_wf = "Memo Approval Has Been Completed!" if WorkflowLastStatusEnum.COMPLETED else "Memo Approval Need Approval!"
        
        if obj_current.status_workflow not in [WorkflowLastStatusEnum.NEED_DATA_UPDATE, WorkflowLastStatusEnum.REJECTED]:
            raise HTTPException(status_code=422, detail=f"Failed update. Detail : {msg_error_wf}")
    
    if sch.jenis_bayar in [JenisBayarEnum.UTJ_KHUSUS, JenisBayarEnum.UTJ]:
        kjb_hd_current = await crud.kjb_hd.get(id=sch.kjb_hd_id)
        total_utj = sum([dt.amount for dt in sch.invoices])

        if total_utj > kjb_hd_current.utj_amount:
            raise HTTPException(status_code=422, detail="Total UTJ tidak boleh lebih besar dari UTJ amount di KJB")
    
    sch.is_void = obj_current.is_void

    today = date.today()
    month = roman.toRoman(today.month)
    year = today.year
    jns_byr:str = ""

    if sch.jenis_bayar == JenisBayarEnum.UTJ or sch.jenis_bayar == JenisBayarEnum.UTJ_KHUSUS:
        jns_byr = JenisBayarEnum.UTJ.value
    else:
        jns_byr = jenis_bayar_to_text.get(sch.jenis_bayar, sch.jenis_bayar)

    if sch.file:
        file_name=f"MEMO PEMBAYARAN-{sch.nomor_memo.replace('/', '_').replace('.', '')}-{obj_current.code.replace('/', '_')}"
        try:
            file_upload_path = await BundleHelper().upload_to_storage_from_base64(base64_str=sch.file, file_name=file_name)
        except ZeroDivisionError as e:
            raise HTTPException(status_code=422, detail="Failed upload dokumen Memo Pembayaran")
        
        sch.file_upload_path = file_upload_path
        
    
    obj_updated = await crud.termin.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

    termin_bayar_temp = []
    for termin_bayar in sch.termin_bayars:
        if termin_bayar.id:
            termin_bayar_current = await crud.termin_bayar.get(id=termin_bayar.id)
            termin_bayar_updated = TerminBayarUpdateSch(**termin_bayar.dict(), termin_id=obj_updated.id)
            obj_termin_bayar = await crud.termin_bayar.update(obj_current=termin_bayar_current, obj_new=termin_bayar_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)
        else:
            termin_bayar_sch = TerminBayarCreateSch(**termin_bayar.dict(), termin_id=obj_updated.id)
            obj_termin_bayar = await crud.termin_bayar.create(obj_in=termin_bayar_sch,  db_session=db_session, with_commit=False, created_by_id=current_worker.id)
        
        termin_bayar_temp.append({"termin_bayar_id" : obj_termin_bayar.id, "id_index" : termin_bayar.id_index})

    #delete invoice
    await db_session.execute(delete(Invoice).where(and_(Invoice.id.notin_(r.id for r in sch.invoices if r.id is not None), 
                                                        Invoice.termin_id == obj_updated.id)))

    for invoice in sch.invoices:

        #remove bidang komponen biaya
        await db_session.execute(delete(BidangKomponenBiaya).where(and_(BidangKomponenBiaya.id.in_(r.bidang_komponen_biaya_id for r in invoice.details if r.bidang_komponen_biaya_id is not None and r.is_deleted), 
                                                                        BidangKomponenBiaya.bidang_id == invoice.bidang_id)))

        if invoice.id:
            invoice_current = await crud.invoice.get_by_id(id=invoice.id)
            if invoice_current:
                invoice_updated_sch = InvoiceUpdateSch(**invoice.dict())
                invoice_updated_sch.is_void = invoice_current.is_void
                invoice_updated = await crud.invoice.update(obj_current=invoice_current, obj_new=invoice_updated_sch, with_commit=False, db_session=db_session, updated_by_id=current_worker.id)
            
                #delete invoice_detail not exists
                await db_session.execute(delete(InvoiceDetail).where(and_(InvoiceDetail.id.notin_(dt.id for dt in invoice.details if dt.id != None), 
                                                        InvoiceDetail.invoice_id == obj_updated.id)))
                
                #delete invoice_bayar not exists
                await db_session.execute(delete(InvoiceBayar).where(and_(InvoiceBayar.id.notin_(dt.id for dt in invoice.bayars if dt.id != None), 
                                                        InvoiceBayar.invoice_id == obj_updated.id)))

                for dt in invoice.details:
                    if dt.is_deleted:
                        continue
                    if dt.id is None:
                        if dt.bidang_komponen_biaya_id is None and dt.beban_biaya_id and dt.is_deleted != True:
                            bidang_komponen_biaya_current = await crud.bidang_komponen_biaya.get_by_bidang_id_and_beban_biaya_id(bidang_id=invoice.bidang_id, beban_biaya_id=dt.beban_biaya_id)
                            if bidang_komponen_biaya_current is None:
                                master_beban_biaya = await crud.bebanbiaya.get(id=dt.beban_biaya_id)
                                bidang_komponen_biaya_new = BidangKomponenBiayaCreateSch(
                                amount = dt.komponen_biaya_amount,
                                formula = master_beban_biaya.formula,
                                satuan_bayar = dt.satuan_bayar,
                                satuan_harga = dt.satuan_harga,
                                is_add_pay = master_beban_biaya.is_add_pay,
                                beban_biaya_id = dt.beban_biaya_id,
                                beban_pembeli = dt.beban_pembeli,
                                estimated_amount = dt.amount,
                                bidang_id = invoice.bidang_id,
                                is_paid = False,
                                is_exclude_spk = True,
                                is_retur = False,
                                is_void = False)

                                obj_bidang_komponen_biaya = await crud.bidang_komponen_biaya.create(obj_in=bidang_komponen_biaya_new, db_session=db_session, with_commit=False, created_by_id=current_worker.id)
                                dt.bidang_komponen_biaya_id = obj_bidang_komponen_biaya.id
                            else:
                                dt.bidang_komponen_biaya_id = bidang_komponen_biaya_current.id

                        invoice_dtl_sch = InvoiceDetailCreateSch(**dt.dict(), invoice_id=invoice.id)
                        await crud.invoice_detail.create(obj_in=invoice_dtl_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)
                    else:
                        invoice_dtl_current = await crud.invoice_detail.get(id=dt.id)
                        invoice_dtl_updated_sch = InvoiceDetailUpdateSch(**dt.dict(), invoice_id=invoice_updated.id)
                        await crud.invoice_detail.update(obj_current=invoice_dtl_current, obj_new=invoice_dtl_updated_sch, db_session=db_session, with_commit=False)

                for dt_bayar in invoice.bayars:
                    termin_bayar_id = next((termin_bayar["termin_bayar_id"] for termin_bayar in termin_bayar_temp if termin_bayar["id_index"] == dt_bayar.id_index), None)
                    if dt_bayar.id is None:
                        invoice_bayar_new = InvoiceBayarCreateSch(termin_bayar_id=termin_bayar_id, invoice_id=new_obj_invoice.id, amount=dt_bayar.amount)
                        await crud.invoice_bayar.create(obj_in=invoice_bayar_new, db_session=db_session, with_commit=False, created_by_id=current_worker.id)
                    else:
                        invoice_bayar_current = await crud.invoice_bayar.get(id=dt_bayar.id)
                        invoice_bayar_updated = InvoiceBayarlUpdateSch.from_orm(invoice_bayar_current)
                        invoice_bayar_updated.termin_bayar_id = termin_bayar_id
                        invoice_bayar_updated.amount = dt_bayar.amount
                        await crud.invoice_bayar.update(obj_current=invoice_bayar_current, obj_new=invoice_bayar_updated, db_session=db_session, with_commit=False, updated_by_id=current_worker.id)


            else:
                raise ContentNoChangeException(detail="data invoice tidak ditemukan")
        else:
            last_number = await generate_code_month(entity=CodeCounterEnum.Invoice, with_commit=False, db_session=db_session)
            invoice_sch = InvoiceCreateSch(**invoice.dict(), termin_id=obj_updated.id)
            invoice_sch.code = f"INV/{last_number}/{jns_byr}/LA/{month}/{year}"
            invoice_sch.is_void = False
            new_obj_invoice = await crud.invoice.create(obj_in=invoice_sch, db_session=db_session, with_commit=False)

            #add invoice_detail
            for dt in invoice.details:
                if dt.is_deleted:
                    continue
                if dt.bidang_komponen_biaya_id is None and dt.beban_biaya_id and dt.is_deleted != True:
                    bidang_komponen_biaya_current = await crud.bidang_komponen_biaya.get_by_bidang_id_and_beban_biaya_id(bidang_id=invoice.bidang_id, beban_biaya_id=dt.beban_biaya_id)
                    if bidang_komponen_biaya_current is None:
                        master_beban_biaya = await crud.bebanbiaya.get(id=dt.beban_biaya_id)
                        bidang_komponen_biaya_new = BidangKomponenBiayaCreateSch(
                        amount = dt.komponen_biaya_amount,
                        formula = master_beban_biaya.formula,
                        satuan_bayar = dt.satuan_bayar,
                        satuan_harga = dt.satuan_harga,
                        is_add_pay = master_beban_biaya.is_add_pay,
                        beban_biaya_id = dt.beban_biaya_id,
                        beban_pembeli = dt.beban_pembeli,
                        estimated_amount = dt.amount,
                        bidang_id = invoice.bidang_id,
                        is_paid = False,
                        is_exclude_spk = True,
                        is_retur = False,
                        is_void = False)

                        obj_bidang_komponen_biaya = await crud.bidang_komponen_biaya.create(obj_in=bidang_komponen_biaya_new, db_session=db_session, with_commit=False, created_by_id=current_worker.id)
                        dt.bidang_komponen_biaya_id = obj_bidang_komponen_biaya.id
                    else:
                        dt.bidang_komponen_biaya_id = bidang_komponen_biaya_current.id

                invoice_dtl_sch = InvoiceDetailCreateSch(**dt.dict(), invoice_id=new_obj_invoice.id)
                await crud.invoice_detail.create(obj_in=invoice_dtl_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)


    #delete termin bayar
    await db_session.execute(delete(TerminBayar).where(and_(TerminBayar.id.notin_(r.id for r in sch.termin_bayars if r.id is not None), 
                                                        TerminBayar.termin_id == obj_updated.id)))

    #workflow
    if obj_updated.jenis_bayar not in [JenisBayarEnum.UTJ_KHUSUS, JenisBayarEnum.UTJ]:
        wf_current = await crud.workflow.get_by_reference_id(reference_id=obj_updated.id)
        if wf_current:
            if wf_current.last_status not in [WorkflowLastStatusEnum.REJECTED, WorkflowLastStatusEnum.NEED_DATA_UPDATE]:
                raise HTTPException(status_code=422, detail="Failed update termin. Detail : Workflow is running")

            wf_updated = WorkflowUpdateSch(**wf_current.dict(exclude={"last_status", "step_name"}), last_status=WorkflowLastStatusEnum.ISSUED, step_name="ISSUED" if WorkflowLastStatusEnum.REJECTED else "On Progress Update Data")
            if wf_updated.version is None:
                wf_updated.version = 1
                
            await crud.workflow.update(obj_current=wf_current, obj_new=wf_updated, updated_by_id=obj_updated.updated_by_id, db_session=db_session, with_commit=False)
        else:
            flow = await crud.workflow_template.get_by_entity(entity=WorkflowEntityEnum.TERMIN)
            wf_sch = WorkflowCreateSch(reference_id=obj_updated.id, entity=WorkflowEntityEnum.TERMIN, flow_id=flow.flow_id, version=1, last_status=WorkflowLastStatusEnum.ISSUED, step_name="ISSUED")
            
            await crud.workflow.create(obj_in=wf_sch, created_by_id=obj_updated.updated_by_id, db_session=db_session, with_commit=False)
        
        GCloudTaskService().create_task(payload={
                                                    "id":str(obj_updated.id)
                                                }, 
                                        base_url=f'{request.base_url}landrope/termin/task-workflow')

    await db_session.commit()
    await db_session.refresh(obj_updated)

    if obj_updated.jenis_bayar not in [JenisBayarEnum.UTJ_KHUSUS, JenisBayarEnum.UTJ]:
        background_task.add_task(generate_printout, obj_updated.id)
        background_task.add_task(merge_memo_signed, obj_updated.id)
    else:
        background_task.add_task(generate_printout_utj, obj_updated.id)
       

    obj_updated = await crud.termin.get_by_id(id=obj_updated.id)

    return create_response(data=obj_updated)

@router.get("/search/kjb_hd", response_model=GetResponseBaseSch[list[KjbHdSearchSch]])
async def get_list_kjb_hd(
                keyword:str = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(KjbHd)
    query = query.outerjoin(Termin, Termin.kjb_hd_id == KjbHd.id)
    query = query.filter(Termin.kjb_hd_id == None)
    query = query.filter(or_(KjbHd.is_draft != True, KjbHd.is_draft is None))
    
    if keyword:
        query = query.filter(KjbHd.code.ilike(f'%{keyword}%'))


    objs = await crud.kjb_hd.get_multi_no_page(query=query)
    return create_response(data=objs)

@router.get("/search/kjb_hd/{id}", response_model=GetResponseBaseSch[KjbHdForTerminByIdSch])
async def get_list_bidang_by_kjb_hd_id(
                id:UUID,
                termin_id:UUID | None = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    obj = await crud.kjb_hd.get_by_id_for_termin(id=id)
    bidang_details = await crud.bidang.get_multi_by_kjb_hd_id(kjb_hd_id=id)

    obj_return = KjbHdForTerminByIdSch(**dict(obj))

    bidangs = []
    for b in bidang_details:
        bidang = BidangForUtjSch(**dict(b))
        bidangs.append(bidang)

    obj_return.bidangs = bidangs

    return create_response(data=obj_return)

@router.get("/search/tahap", response_model=GetResponseBaseSch[list[TahapSrcSch]])
async def get_list_tahap(
                keyword: str | None = None,
                jenis_bayar: JenisBayarEnum | None = None, 
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(Tahap)
    query = query.join(TahapDetail, Tahap.id == TahapDetail.tahap_id)
    query = query.join(Spk, TahapDetail.bidang_id == Spk.bidang_id)
    query = query.join(Planing, Planing.id == Tahap.planing_id)
    query = query.join(Project, Project.id == Planing.project_id)
    query = query.outerjoin(Invoice, and_(Spk.id == Invoice.spk_id, Invoice.is_void != True))
    query = query.where(and_(Spk.jenis_bayar != JenisBayarEnum.PAJAK,
                            Spk.is_void != True,
                            Invoice.id == None,
                            Spk.status_workflow == WorkflowLastStatusEnum.COMPLETED))
    
    if jenis_bayar:
        query = query.filter(Spk.jenis_bayar == jenis_bayar)
    
    if keyword:
        query = query.filter(or_(cast(Tahap.nomor_tahap, String).ilike(f'%{keyword}%'),
                                Project.name.ilike(f'%{keyword}%')))

    query = query.distinct()
    query = query.options(selectinload(Tahap.planing
                        ).options(selectinload(Planing.project))
                )

    objs = await crud.tahap.get_multi_no_page(query=query)
    return create_response(data=objs)

@router.get("/search/tahap/{id}", response_model=GetResponseBaseSch[list[SpkJenisBayarSch]])
async def get_list_tahap_by_id(
                id: UUID | None = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(Spk).join(TahapDetail, TahapDetail.bidang_id == Spk.bidang_id
                        ).outerjoin(Invoice, and_(Spk.id == Invoice.spk_id, Invoice.is_void != True)
                        ).where(and_(TahapDetail.tahap_id == id,
                                    Spk.jenis_bayar != JenisBayarEnum.PAJAK,
                                    Spk.is_void != True,
                                    Invoice.id == None,
                                    Spk.status_workflow == WorkflowLastStatusEnum.COMPLETED))

    objs = await crud.spk.get_multi_no_page(query=query)

    spk_jenis_bayars = []
    jenis_bayars = []
    for spk in objs:
        if spk.jenis_bayar not in jenis_bayars:
            spk_ = SpkJenisBayarSch(jenis_bayar=spk.jenis_bayar)
            spk_jenis_bayars.append(spk_)
            jenis_bayars.append(spk.jenis_bayar)

    return create_response(data=spk_jenis_bayars)

@router.get("/search/komponen_biaya", response_model=GetResponseBaseSch[list[BidangKomponenBiayaSch]])
async def get_list_komponen_biaya_by_bidang_id_and_invoice_id(
                bidang_id:UUID,
                invoice_id:UUID,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""
    pengembalian = False
    invoice = await crud.invoice.get_by_id(id=invoice_id)
    if invoice.jenis_bayar == JenisBayarEnum.PENGEMBALIAN_BEBAN_PENJUAL:
        pengembalian = True
    
    biaya_lain = False
    if invoice.jenis_bayar == JenisBayarEnum.BIAYA_LAIN:
        biaya_lain = True
    
    objs = await crud.bidang_komponen_biaya.get_multi_beban_by_invoice_id(invoice_id=invoice_id, pengembalian=pengembalian, biaya_lain=biaya_lain)
    if bidang_id:
        objs_2 = await crud.bidang_komponen_biaya.get_multi_beban_by_bidang_id(bidang_id=bidang_id)
        for obj2 in objs_2:
            obj1 = next((obj for obj in objs if obj.beban_biaya_id == obj2.beban_biaya_id), None)
            if obj1:
                continue
            else:
                objs.append(obj2)

    return create_response(data=objs)

@router.get("/search/komponen_biaya/bidang/{spk_id}", response_model=GetResponseBaseSch[list[BidangKomponenBiayaSch]])
async def get_list_komponen_biaya_by_spk_id(
                spk_id:UUID,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    spk = await crud.spk.get(id=spk_id)

    objs = []
    if spk.jenis_bayar == JenisBayarEnum.PENGEMBALIAN_BEBAN_PENJUAL:
        objs = await crud.bidang_komponen_biaya.get_multi_pengembalian_beban_by_bidang_id(bidang_id=spk.bidang_id)
    elif spk.jenis_bayar == JenisBayarEnum.BIAYA_LAIN:
        objs = await crud.bidang_komponen_biaya.get_multi_beban_biaya_lain_by_bidang_id(bidang_id=spk.bidang_id)
    else:
        objs = await crud.bidang_komponen_biaya.get_multi_beban_by_bidang_id(bidang_id=spk.bidang_id)

    return create_response(data=objs)

@router.post("/search/notaris", response_model=GetResponseBaseSch[list[NotarisSrcSch]])
async def get_list_manager(
                sch:TerminBidangIDSch,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    list_id = [id.bidang_id for id in sch.bidangs]

    objs = await crud.notaris.get_multi_by_bidang_ids(list_ids=list_id)

    return create_response(data=objs)

@router.post("/search/manager", response_model=GetResponseBaseSch[list[ManagerSrcSch]])
async def get_list_manager(
                sch:TerminBidangIDSch,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    list_id = [id.bidang_id for id in sch.bidangs]

    objs = await crud.manager.get_multi_by_bidang_ids(list_ids=list_id)

    return create_response(data=objs)

@router.post("/search/sales", response_model=GetResponseBaseSch[list[SalesSrcSch]])
async def get_list_sales(
                sch:TerminBidangIDSch,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    list_id = [id.bidang_id for id in sch.bidangs]

    objs = await crud.sales.get_multi_by_bidang_ids_and_manager_id(list_ids=list_id, manager_id=sch.manager_id)

    return create_response(data=objs)

@router.post("/search/rekening", response_model=GetResponseBaseSch[list[RekeningSch]])
async def get_list_rekening(
                sch:TerminBidangIDSch,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    list_id = [id.bidang_id for id in sch.bidangs]

    objs = await crud.rekening.get_multi_by_bidang_ids(list_ids=list_id)

    return create_response(data=objs)

@router.get("/search/spk", response_model=GetResponseBaseSch[list[SpkSrcSch]])
async def get_list_spk_by_tahap_id(
                tahap_id:UUID | None = None,
                termin_id:UUID | None = None,
                jenis_bayar:JenisBayarEnum | None = None,
                keyword:str = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""
    objs = []

    if tahap_id == None and termin_id == None:
        objs = await crud.spk.get_multi_by_keyword_tahap_id_and_termin_id(keyword=keyword)
        objs = [spk for spk in objs if len([invoice for invoice in spk.invoices if invoice.is_void != True]) == 0 and spk.is_void != True]

    if tahap_id and termin_id == None:
        objs_with_tahap = await crud.spk.get_multi_by_keyword_tahap_id_and_termin_id(keyword=keyword, 
                                                                                     tahap_id=tahap_id, 
                                                                                     jenis_bayar=jenis_bayar)
        objs = objs + objs_with_tahap
        # objs = list(set(objs + objs_with_tahap))
    
    if tahap_id and termin_id:
        objs_with_tahap_termin = await crud.spk.get_multi_by_keyword_tahap_id_and_termin_id(keyword=keyword, 
                                                                                            tahap_id=tahap_id, 
                                                                                            termin_id=termin_id,
                                                                                            jenis_bayar=jenis_bayar)
        objs = objs + objs_with_tahap_termin

    
    objs = [obj for obj in objs if obj.status_workflow == WorkflowLastStatusEnum.COMPLETED]

    return create_response(data=objs)

@router.get("/search/spk/{id}", response_model=GetResponseBaseSch[SpkInTerminSch])
async def get_by_id(id:UUID,
                    current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Get an object by id"""

    obj = await crud.spk.get_by_id_in_termin(id=id)

    if obj.status_workflow != WorkflowLastStatusEnum.COMPLETED:
        raise HTTPException(status_code=422, detail="SPK must completed approval")

    spk = SpkInTerminSch(spk_id=obj.id, 
                        spk_code=obj.code, 
                        spk_amount=obj.amount, 
                        spk_satuan_bayar=obj.satuan_bayar,
                        bidang_id=obj.bidang_id, 
                        id_bidang=obj.id_bidang, 
                        alashak=obj.alashak, 
                        group=obj.bidang.group,
                        luas_bayar=obj.bidang.luas_bayar, 
                        harga_transaksi=obj.bidang.harga_transaksi, 
                        harga_akta=obj.bidang.harga_akta, 
                        amount=round(obj.spk_amount,0), 
                        utj_amount=obj.utj_amount, 
                        project_id=obj.bidang.planing.project_id, 
                        project_name=obj.bidang.project_name, 
                        sub_project_id=obj.bidang.sub_project_id,
                        sub_project_name=obj.bidang.sub_project_name, 
                        nomor_tahap=obj.bidang.nomor_tahap, 
                        tahap_id=obj.bidang.tahap_id,
                        jenis_bayar=obj.jenis_bayar, 
                        jenis_alashak=obj.bidang.jenis_alashak,
                        manager_id=obj.bidang.manager_id, 
                        manager_name=obj.bidang.manager_name,
                        sales_id=obj.bidang.sales_id, 
                        sales_name=obj.bidang.sales_name, 
                        notaris_id=obj.bidang.notaris_id, 
                        notaris_name=obj.bidang.notaris_name, 
                        mediator=obj.bidang.mediator, 
                        desa_name=obj.bidang.desa_name, 
                        ptsk_name=obj.bidang.ptsk_name, 
                        harga_standard=obj.harga_standard,
                        harga_standard_girik=obj.harga_standard_girik,
                        harga_standard_sertifikat=obj.harga_standard_sertifikat
                        )

    if obj.jenis_bayar == JenisBayarEnum.SISA_PELUNASAN:
        bidang = await crud.bidang.get_by_id(id=obj.bidang_id)
        spk.amount = bidang.sisa_pelunasan

    if obj:
        return create_response(data=spk)
    else:
        raise IdNotFoundException(Bidang, id)

@router.post("/search/spk/by-ids", response_model=GetResponseBaseSch[list[SpkInTerminSch]])
async def get_by_ids(sch:SpkIdSch,
                    current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Get an object by id"""

    objs = await crud.spk.get_by_ids_in_termin(list_id=sch.spk_ids)

    if any(obj for obj in objs if obj.status_workflow != WorkflowLastStatusEnum.COMPLETED):
        raise HTTPException(status_code=422, detail=f"All SPK must be completed approval")

    spks = []
    for obj in objs:
        spk = SpkInTerminSch(spk_id=obj.id, 
                        spk_code=obj.code, 
                        spk_amount=obj.amount, 
                        spk_satuan_bayar=obj.satuan_bayar,
                        bidang_id=obj.bidang_id, 
                        id_bidang=obj.id_bidang, 
                        alashak=obj.alashak, 
                        group=obj.bidang.group,
                        luas_bayar=obj.bidang.luas_bayar, 
                        harga_transaksi=obj.bidang.harga_transaksi, 
                        harga_akta=obj.bidang.harga_akta, 
                        amount=round(obj.spk_amount,0), 
                        utj_amount=obj.utj_amount, 
                        project_id=obj.bidang.planing.project_id, 
                        project_name=obj.bidang.project_name, 
                        sub_project_id=obj.bidang.sub_project_id,
                        sub_project_name=obj.bidang.sub_project_name, 
                        nomor_tahap=obj.bidang.nomor_tahap, 
                        tahap_id=obj.bidang.tahap_id,
                        jenis_bayar=obj.jenis_bayar, 
                        jenis_alashak=obj.bidang.jenis_alashak,
                        manager_id=obj.bidang.manager_id, 
                        manager_name=obj.bidang.manager_name,
                        sales_id=obj.bidang.sales_id, 
                        sales_name=obj.bidang.sales_name, 
                        notaris_id=obj.bidang.notaris_id, 
                        notaris_name=obj.bidang.notaris_name, 
                        mediator=obj.bidang.mediator, 
                        desa_name=obj.bidang.desa_name, 
                        ptsk_name=obj.bidang.ptsk_name, 
                        harga_standard=obj.harga_standard,
                        harga_standard_girik=obj.harga_standard_girik,
                        harga_standard_sertifikat=obj.harga_standard_sertifikat
                        )

        if obj.jenis_bayar == JenisBayarEnum.SISA_PELUNASAN:
            bidang = await crud.bidang.get_by_id(id=obj.bidang_id)
            spk.amount = bidang.sisa_pelunasan

        spks.append(spk)

    return create_response(data=spks)
    
@router.get("/history/memo/{bidang_id}", response_model=GetResponseBaseSch[list[InvoiceHistoryInTermin]])
async def get_list_history_memo_by_bidang_id(bidang_id:UUID,
                                            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Get list history memo bayar dp by bidang_id"""

    objs = await crud.invoice.get_multi_history_invoice_by_bidang_id(bidang_id=bidang_id)

    return create_response(data=objs)

@router.get("/print-out/{id}")
async def printout(id:UUID | str, current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Print out UTJ"""
    obj_current = await crud.termin.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Termin, id)
    
    # file_path = obj_current.file_path

    # if file_path is None:
    file_path = await generate_printout(id=id)
    
    try:
        file_bytes = await GCStorageService().download_dokumen(file_path=file_path)
    except Exception as e:
        raise DocumentFileNotFoundException(dokumenname=obj_current.code)
    
    ext = obj_current.file_path.split('.')[-1]

    response = Response(content=file_bytes, media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename={obj_current.code.replace('/', '_')}.{ext}"
    return response

@router.get("/print-out/excel/{id}")
async def printout(id:UUID | str,
                   current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Print out DP Pelunasan"""
    try:
        obj = await crud.termin.get_by_id_for_printout(id=id)
        if obj is None:
            raise IdNotFoundException(Termin, id)
        
        termin_header = TerminByIdForPrintOut(**dict(obj))
        obj_tanggal_transaksi = datetime.strptime(str(termin_header.tanggal_transaksi), "%Y-%m-%d")
        tanggal_transaksi = obj_tanggal_transaksi.strftime("%d-%m-%Y")

        obj_created_at = datetime.strptime(str(termin_header.created_at.date()), "%Y-%m-%d")
        bulan_created_en = obj_created_at.strftime('%B')
        bulan_created_id = bulan_dict.get(bulan_created_en, bulan_created_en)
        created_at = obj_created_at.strftime(f'%d {bulan_created_id} %Y')

        date_obj = datetime.strptime(str(termin_header.tanggal_rencana_transaksi), "%Y-%m-%d")
        nama_bulan_inggris = date_obj.strftime('%B')  # Mendapatkan nama bulan dalam bahasa Inggris
        nama_bulan_indonesia = bulan_dict.get(nama_bulan_inggris, nama_bulan_inggris)  # Mengonversi ke bahasa Indonesia
        tanggal_hasil = date_obj.strftime(f'%d {nama_bulan_indonesia} %Y')
        day_of_week = date_obj.strftime("%A")
        hari_transaksi:str|None = HelperService().ToDayName(day_of_week)

        remarks = termin_header.remark.splitlines()
        #perhitungan utj (jika invoice dlm termin dikurangi utj) & data invoice di termin yg akan di printout
        amount_utj_used = []
        termin_invoices:list[InvoiceForPrintOutExt] = []
        obj_invoices = await crud.invoice.get_invoice_by_termin_id_for_printout(termin_id=id)
        for inv in obj_invoices:
            iv = InvoiceForPrintOutExt(**dict(inv))
            invoice_curr = await crud.invoice.get_utj_amount_by_id(id=iv.id)
            amount_utj_used.append(invoice_curr.utj_amount)
            termin_invoices.append(iv)
        
        amount_utj = sum(amount_utj_used) or 0

        #untuk list bidang dalam 1 tahap
        obj_bidangs = await crud.tahap_detail.get_multi_by_tahap_id_for_printout(tahap_id=termin_header.tahap_id)

        bidangs:list[TahapDetailForPrintOut] = []
        nomor_urut_bidang = []
        overlap_exists = False
        no = 1
        for bd in obj_bidangs:
            bidang = TahapDetailForPrintOut(**dict(bd),
                                        no=no,
                                        total_hargaExt="{:,.0f}".format(bd.total_harga),
                                        harga_transaksiExt = "{:,.0f}".format(bd.harga_transaksi),
                                        luas_suratExt = "{:,.0f}".format(bd.luas_surat),
                                        luas_nettExt = "{:,.0f}".format(bd.luas_nett),
                                        luas_ukurExt = "{:,.0f}".format(bd.luas_ukur),
                                        luas_gu_peroranganExt = "{:,.0f}".format(bd.luas_gu_perorangan),
                                        luas_pbt_peroranganExt = "{:,.0f}".format(bd.luas_pbt_perorangan),
                                        luas_bayarExt = "{:,.0f}".format(bd.luas_bayar),
                                        is_bold=False)
            

            bidang_in_termin = next((bd_in_termin for bd_in_termin in termin_invoices if bd_in_termin.bidang_id == bidang.bidang_id), None)
            if bidang_in_termin:
                bidang.is_bold = True
                nomor_urut_bidang.append(bidang.no)

            overlaps = await crud.bidangoverlap.get_multi_by_bidang_id_for_printout(bidang_id=bd.bidang_id)
            list_overlap = []
            for ov in overlaps:
                overlap = BidangOverlapForPrintout(**dict(ov))
                bidang_utama = await crud.bidang.get_by_id(id=bd.bidang_id)
                if (bidang_utama.status_sk == StatusSKEnum.Sudah_Il and bidang_utama.hasil_analisa_peta_lokasi == HasilAnalisaPetaLokasiEnum.Overlap) or (bidang_utama.status_sk == StatusSKEnum.Belum_IL and bidang_utama.hasil_analisa_peta_lokasi == HasilAnalisaPetaLokasiEnum.Clear):
                    nib_perorangan:str = ""
                    nib_perorangan_meta_data = await crud.bundledt.get_meta_data_by_dokumen_name_and_bidang_id(dokumen_name='NIB PERORANGAN', bidang_id=bidang_utama.id)
                    if nib_perorangan_meta_data:
                        if nib_perorangan_meta_data.meta_data is not None and nib_perorangan_meta_data.meta_data != "":
                            metadata_dict = json.loads(nib_perorangan_meta_data.meta_data.replace("'", "\""))
                            nib_perorangan = metadata_dict[f'{nib_perorangan_meta_data.key_field}']
                    overlap.nib = nib_perorangan

                list_overlap.append(overlap)

            bidang.overlaps = list_overlap

            if len(bidang.overlaps) > 0:
                overlap_exists = True

            bidangs.append(bidang)
            no = no + 1
        
        nomor_urut:str = ""
        for no in nomor_urut_bidang:
            nomor_urut += f"{no}, "
        
        nomor_urut = f"No. {nomor_urut[0:-2]}"

        list_bidang_id = [bd.bidang_id for bd in obj_bidangs]

        total_luas_surat = "{:,.0f}".format(sum([b.luas_surat for b in obj_bidangs]))
        total_luas_ukur = "{:,.0f}".format(sum([b.luas_ukur for b in obj_bidangs]))
        total_luas_gu_perorangan = "{:,.0f}".format(sum([b.luas_gu_perorangan for b in obj_bidangs]))
        total_luas_nett = "{:,.0f}".format(sum([b.luas_nett for b in obj_bidangs]))
        total_luas_pbt_perorangan = "{:,.0f}".format(sum([b.luas_pbt_perorangan for b in obj_bidangs]))
        total_luas_bayar = "{:,.0f}".format(sum([b.luas_bayar for b in obj_bidangs]))
        total_harga = "{:,.0f}".format(sum([b.total_harga for b in obj_bidangs]))

        termin_histories = []
        current_termin_histories = await crud.termin.get_multi_by_bidang_ids(bidang_ids=list_bidang_id, current_termin_id=id)
        for termin in current_termin_histories:
            termin_history = TerminHistoriesSch(**dict(termin))
            obj_history_tanggal_transaksi = datetime.strptime(str(termin_history.tanggal_transaksi), "%Y-%m-%d")
            termin_history.str_tanggal_transaksi = obj_history_tanggal_transaksi.strftime("%d-%m-%Y")

            termin_history.str_amount = "{:,.0f}".format(termin.amount)
            if termin_history.jenis_bayar not in [JenisBayarEnum.UTJ, JenisBayarEnum.UTJ_KHUSUS]:
                invoice_in_termin_histories = await crud.invoice.get_multi_invoice_id_luas_bayar_by_termin_id(termin_id=termin_history.id)
                count_bidang = len(invoice_in_termin_histories)
                sum_luas_bayar = "{:,.0f}".format(sum([invoice_.luas_bayar or 0 for invoice_ in invoice_in_termin_histories if invoice_.luas_bayar is not None]))
                termin_history.str_jenis_bayar = f"{termin_history.str_jenis_bayar} {count_bidang}BID luas {sum_luas_bayar}m2"

            komponen_biayas = []
            obj_komponen_biayas = await crud.termin.get_beban_biaya_by_id_for_printout(id=termin.id, jenis_bayar=termin.jenis_bayar)
            for bb in obj_komponen_biayas:
                beban_biaya = TerminBebanBiayaForPrintOut(**dict(bb))
                beban_biaya.beban_biaya_name = f"{beban_biaya.beban_biaya_name} {beban_biaya.tanggungan}"
                beban_biaya.amountExt = "{:,.0f}".format(beban_biaya.amount)
                komponen_biayas.append(beban_biaya)

            termin_history.beban_biayas = komponen_biayas
            invoices = await crud.invoice.get_multi_by_termin_id(termin_id=termin.id)

            nomor_uruts = []
            for invoice in invoices:
                nomor = next((bidang.no for bidang in bidangs if bidang.bidang_id == invoice.bidang_id), None)
                if nomor:
                    nomor_uruts.append(nomor)
            
            index_no:str = ""
            
            nomor_uruts = sorted(nomor_uruts, key=lambda obj:obj)
            for no in nomor_uruts:
                index_no += f"{no}, "
            
            index_no = index_no[0:-2]

            termin_history.index_bidang = f"No. {index_no}"
            termin_histories.append(termin_history)

        komponen_biayas = []
        obj_komponen_biayas = await crud.termin.get_beban_biaya_by_id_for_printout(id=id, jenis_bayar=termin_header.jenis_bayar)
        for bb in obj_komponen_biayas:
            beban_biaya = TerminBebanBiayaForPrintOut(**dict(bb))
            beban_biaya.beban_biaya_name = f"{beban_biaya.beban_biaya_name} {beban_biaya.tanggungan}"
            beban_biaya.amountExt = "{:,.0f}".format(beban_biaya.amount)
            komponen_biayas.append(beban_biaya)
        
        amount_beban_biayas = [beban_penjual.amount for beban_penjual in obj_komponen_biayas if beban_penjual.beban_pembeli == False and beban_penjual.is_void != True]
        amount_beban_biaya = sum(amount_beban_biayas)

        harga_aktas = []
        obj_kjb_hargas = await crud.kjb_harga.get_harga_akta_by_termin_id_for_printout(termin_id=id)
        for hg in obj_kjb_hargas:
            harga_akta = KjbHargaAktaSch(**dict(hg))
            harga_akta.harga_aktaExt = "{:,.0f}".format(hg.harga_akta)
            harga_aktas.append(harga_akta)

        
        no = 1
        obj_termin_bayar = await crud.termin_bayar.get_multi_by_termin_id_for_printout(termin_id=id)
        filename = "memo_tanah_overlap_ext_excel.html" if overlap_exists else "memo_tanah_ext_excel.html"
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template(filename)

        render_template = template.render(code=termin_header.nomor_memo or "",
                                        created_at=created_at,
                                        nomor_tahap=termin_header.nomor_tahap,
                                        project_name=termin_header.project_name,
                                        desa_name=termin_header.desa_name,
                                        ptsk_name=termin_header.ptsk_name,
                                        notaris_name=termin_header.notaris_name,
                                        manager_name=termin_header.manager_name.upper(),
                                        sales_name=termin_header.sales_name.upper(),
                                        mediator=termin_header.mediator.upper(),
                                        data=bidangs,
                                        total_luas_surat=total_luas_surat,
                                        total_luas_ukur=total_luas_ukur,
                                        total_luas_gu_perorangan=total_luas_gu_perorangan,
                                        total_luas_nett=total_luas_nett,
                                        total_luas_pbt_perorangan=total_luas_pbt_perorangan,
                                        total_luas_bayar=total_luas_bayar,
                                        total_harga=total_harga,
                                        data_invoice_history=termin_histories,
                                        data_beban_biaya=komponen_biayas,
                                        data_harga_akta=harga_aktas,
                                        data_payment=obj_termin_bayar,
                                        nomor_urut_bidang=nomor_urut,
                                        tanggal_transaksi=tanggal_transaksi,
                                        tanggal_rencana_transaksi=tanggal_hasil,
                                        hari_transaksi=hari_transaksi,
                                        jenis_bayar=termin_header.jenis_bayar_ext.replace('_', ' '),
                                        amount="{:,.0f}".format(((termin_header.amount - amount_beban_biaya) - amount_utj)),
                                        remarks=remarks
                                        )
        
        try:
            doc = await PdfService().get_pdf(render_template)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed generate document")
        
        excel = await PDFToExcelService().export_pdf_to_excel(data=doc)
    
        return StreamingResponse(excel, 
                                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                headers={"Content-Disposition": "attachment;filename=memo_pembayaran.xlsx"})   
    
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.get("/excel/{id}")
async def termin_excel(id:UUID):

    termin = await crud.termin.get_by_id(id=id)

    date_obj = datetime.strptime(str(termin.tanggal_rencana_transaksi), "%Y-%m-%d")
    nama_bulan_inggris = date_obj.strftime('%B')  # Mendapatkan nama bulan dalam bahasa Inggris
    nama_bulan_indonesia = bulan_dict.get(nama_bulan_inggris, nama_bulan_inggris)  # Mengonversi ke bahasa Indonesia
    tanggal_hasil = date_obj.strftime(f'%d {nama_bulan_indonesia} %Y')

    obj_bidangs = await crud.tahap_detail.get_multi_by_tahap_id_for_printout(tahap_id=termin.tahap_id)

    bidangs:list[TahapDetailForExcel] = []
    nomor_urut_bidang = []
    overlap_exists = False
    no = 1
    for bd in obj_bidangs:
        bidang = TahapDetailForExcel(**dict(bd),
                                    no=no,
                                    total_hargaExt="{:,.0f}".format(bd.total_harga or 0),
                                    harga_transaksiExt = "{:,.0f}".format(bd.harga_transaksi or 0),
                                    luas_suratExt = "{:,.0f}".format(bd.luas_surat or 0),
                                    luas_nettExt = "{:,.0f}".format(bd.luas_nett or 0),
                                    luas_ukurExt = "{:,.0f}".format(bd.luas_ukur or 0),
                                    luas_gu_peroranganExt = "{:,.0f}".format(bd.luas_gu_perorangan or 0),
                                    luas_pbt_peroranganExt = "{:,.0f}".format(bd.luas_pbt_perorangan or 0),
                                    luas_bayarExt = "{:,.0f}".format(bd.luas_bayar or 0),
                                    is_bold=False)
        

        overlaps = await crud.bidangoverlap.get_multi_by_bidang_id_for_printout(bidang_id=bd.bidang_id)
        list_overlap = []
        for ov in overlaps:
            overlap = BidangOverlapForPrintout(**dict(ov))
            bidang_utama = await crud.bidang.get_by_id(id=bd.bidang_id)
            if (bidang_utama.status_sk == StatusSKEnum.Sudah_Il and bidang_utama.hasil_analisa_peta_lokasi == HasilAnalisaPetaLokasiEnum.Overlap) or (bidang_utama.status_sk == StatusSKEnum.Belum_IL and bidang_utama.hasil_analisa_peta_lokasi == HasilAnalisaPetaLokasiEnum.Clear):
                overlap.nib = await BundleHelper().get_key_value(dokumen_name="NIB PERORANGAN", bidang_id=bidang_utama.id)

            list_overlap.append(overlap)

        bidang.overlaps = list_overlap

        if len(bidang.overlaps) > 0:
            overlap_exists = True

        pembayarans = await crud.bidang.get_all_pembayaran_by_bidang_id(bidang_id=bidang.bidang_id)
        bidang.pembayarans = pembayarans

        bidangs.append(bidang)
        no = no + 1
    
    html_content = await generate_html_content(list_tahap_detail=bidangs, overlap_exists=overlap_exists, tanggal=tanggal_hasil)

    try:
        doc = await PdfService().get_pdf(html_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed generate pdf document")
    
    
    excel = await PDFToExcelService().export_pdf_to_excel(data=doc)
    
    
    return StreamingResponse(excel, 
                            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            headers={"Content-Disposition": "attachment;filename=memo_pembayaran.xlsx"})   

@router.get("/print-out/utj/{id}")
async def printout(id:UUID | str, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Print out UTJ"""
    obj_current = await crud.termin.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Termin, id)
    
    
    file_path = await generate_printout_utj(id=id)
    
    try:
        file_bytes = await GCStorageService().download_dokumen(file_path=file_path)
    except Exception as e:
        raise DocumentFileNotFoundException(dokumenname=obj_current.code)
    
    ext = obj_current.file_path.split('.')[-1]

    response = Response(content=file_bytes, media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename={obj_current.code.replace('/', '_')}.{ext}"
    return response

async def generate_html_content(list_tahap_detail:list[TahapDetailForExcel], overlap_exists:bool|None = False, tanggal:str|None = '') -> str | None:
    html_content = "<html><body>"
    html_content = """<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="pdfkit-page-size" content="Legal" />
    <meta name="pdfkit-orientation" content="Landscape" />
    <title>Memo Tanah Overlap</title>
    <style>
      @page {
        size: A3 landscape;
      }

      body {
        margin: 0;
        font-family: Arial, sans-serif;
      }
      </style>
      </head>"""
    html_content += """<table border='1'>"""
    html_content += f"""
    <tr>
    <td>No</td><td>:</td><td></td>
    </tr>
    <tr>
    <td>Tanggal</td><td>:</td><td>{tanggal}</td>
    </tr>
    """
    
    if overlap_exists:
        html_content += """
        <tr>
        <th colspan='10' style='background-color: white; border-left: none; border-top: none'></th>
        <th align='center' colspan='10'>OVERLAP DAMAI</td>
        <th
            style='
              background-color: white;
              border-right: none;
              border-top: none;
            '
            colspan='2'
          ></th>
        </tr>
        """

    html_content +="""
        <tr>  
        <th>NO</th>
        <th>ID BID</th>
        <th>ALIAS</th>
        <th>PEMILIK</th>
        <th>SURAT ASAL</th>
        <th>L SURAT</th>
        <th>L UKUR</th>
        <th>L NETT</th>
        <th>L BAYAR</th>
        <th>NO PETA</th>"""
    
    if overlap_exists:
          html_content += """ 
          <th>KET</th>
          <th>NAMA</th>
          <th>ALASHAK</th>
          <th>THP</th>
          <th>LUAS</th>
          <th>L.O</th>
          <th>KAT</th>
          <th>NO NIB</th>
          <th>ID BID</th>
          <th>STATUS</th>"""

    html_content += """
          <th>HARGA</th>
          <th>JUMLAH</th>"""
    
    # Menambahkan kolom pembayaran
    all_payment_types = []
    for bidang in list_tahap_detail:
        for pembayaran in bidang.pembayarans:
            exists = next((types for types in all_payment_types if types['name'] == pembayaran.name and types['id_pembayaran'] == pembayaran.id_pembayaran), None)
            if exists:
                continue
            all_payment_types.append({'name':pembayaran.name, 'id_pembayaran':pembayaran.id_pembayaran})
    for payment_type in all_payment_types:
        html_content += f"<th>{payment_type['name'].replace('_', ' ')}</th>"
    html_content += "</tr>"

    for bidang in list_tahap_detail:
        html_content += f"""<tr>
        <td rowspan='{len(bidang.overlaps)}'>{bidang.no}</td>
        <td rowspan='{len(bidang.overlaps)}'>{bidang.id_bidang}</td>
        <td rowspan='{len(bidang.overlaps)}'>{bidang.group}</td>
        <td rowspan='{len(bidang.overlaps)}'>{bidang.pemilik_name}</td>
        <td rowspan='{len(bidang.overlaps)}'>{bidang.alashak}</td>
        <td rowspan='{len(bidang.overlaps)}'>{bidang.luas_suratExt}</td>
        <td rowspan='{len(bidang.overlaps)}'>{bidang.luas_ukurExt}</td>
        <td rowspan='{len(bidang.overlaps)}'>{bidang.luas_nettExt}</td>
        <td rowspan='{len(bidang.overlaps)}'>{bidang.luas_bayarExt}</td>
        <td rowspan='{len(bidang.overlaps)}'>{bidang.no_peta}</td>
        """
        if len(bidang.overlaps) > 0:
        # Menambahkan data overlap
            for i, overlap in enumerate(bidang.overlaps):
                if i == 0:
                    html_content += f"""
                                    <td>{overlap.ket}</td>
                                    <td>{overlap.nama}</td>
                                    <td>{overlap.alashak}</td>
                                    <td></td>
                                    <td>{overlap.luasExt}</td>
                                    <td>{overlap.luas_overlapExt}</td>
                                    <td>{overlap.kat}</td>
                                    <td>{overlap.nib or ''}</td>
                                    <td>{overlap.id_bidang}</td>
                                    <td>{overlap.status_overlap}</td>
                                    <td rowspan='{len(bidang.overlaps)}'>{bidang.harga_transaksiExt}</td>
                                    <td rowspan='{len(bidang.overlaps)}'>{bidang.total_hargaExt}</td>
                                    """
                    # Menambahkan data Pembayaran
                    if bidang.pembayarans:
                        for payment_type in all_payment_types:
                            matching_payment = next((p for p in bidang.pembayarans if p.name == payment_type['name'] and p.id_pembayaran == payment_type['id_pembayaran']), None)
                            if matching_payment:
                                amount_bayar = "{:,.0f}".format(matching_payment.amount)
                                html_content += f"<td rowspan='{len(bidang.overlaps)}'>{amount_bayar}</td>"
                            else:
                                html_content += f"<td rowspan='{len(bidang.overlaps)}'>-</td>"
                    else:
                        for payment_type in all_payment_types:
                            html_content += f"<td rowspan='{len(bidang.overlaps)}'>-</td>"
                    html_content += "</tr>"
                else:
                    html_content += f"""<tr>
                                    <td>{overlap.ket}</td>
                                    <td>{overlap.nama}</td>
                                    <td>{overlap.alashak}</td>
                                    <td></td>
                                    <td>{overlap.luasExt}</td>
                                    <td>{overlap.luas_overlapExt}</td>
                                    <td>{overlap.kat}</td>
                                    <td>{overlap.nib or ''}</td>
                                    <td>{overlap.id_bidang}</td>
                                    <td>{overlap.status_overlap}</td></tr>"""
        else:
            if overlap_exists:
                html_content += f"""<td align="center">-</td>
                                    <td align='center'>-</td>
                                    <td align='center'>-</td>
                                    <td align='center'>-</td>
                                    <td align='center'>-</td>
                                    <td align='right'>-</td>
                                    <td align='right'>-</td>
                                    <td align='right'>-</td>
                                    <td align='right'>-</td>
                                    <td align='center'>-</td>"""
            
            html_content += f"""<td align='right'>{ bidang.harga_transaksiExt or '' }</td>
                                <td align='right'>{ bidang.total_hargaExt or '' }</td>"""
            
            # Menambahkan data Pembayaran
            if bidang.pembayarans:
                for payment_type in all_payment_types:
                    matching_payment = next((p for p in bidang.pembayarans if p.name == payment_type['name'] and p.id_pembayaran == payment_type['id_pembayaran']), None)
                    if matching_payment:
                        amount_bayar = "{:,.0f}".format(matching_payment.amount)
                        html_content += f"<td rowspan='{len(bidang.overlaps)}'>{amount_bayar}</td>"
                    else:
                        html_content += f"<td rowspan='{len(bidang.overlaps)}'>-</td>"
            else:
                for payment_type in all_payment_types:
                    html_content += f"<td rowspan='{len(bidang.overlaps)}'>-</td>"
            html_content += "</tr>"
    
    total_luas_surat = "{:,.0f}".format(sum([b.luas_surat for b in list_tahap_detail]))
    total_luas_ukur = "{:,.0f}".format(sum([b.luas_ukur for b in list_tahap_detail]))
    total_luas_nett = "{:,.0f}".format(sum([b.luas_nett for b in list_tahap_detail]))
    total_luas_bayar = "{:,.0f}".format(sum([b.luas_bayar for b in list_tahap_detail]))
    total_harga = "{:,.0f}".format(sum([b.total_harga for b in list_tahap_detail]))

    html_content += f"""<tr>
                    <td></td>
                    <td colspan='4'>Sub Total</td>
                    <td>{total_luas_surat}</td>
                    <td>{total_luas_ukur}</td>
                    <td>{total_luas_nett}</td>
                    <td>{total_luas_bayar}</td>
                """
    if overlap_exists:
        total_luas_surat_ov = "{:,.0f}".format(sum([ov.luas for b in list_tahap_detail for ov in b.overlaps]))
        total_luas_ov = "{:,.0f}".format(sum([ov.luas_overlap for b in list_tahap_detail for ov in b.overlaps]))
        html_content += f"""
                <td colspan='5'></td>
                <td>{total_luas_surat_ov}</td>
                <td>{total_luas_ov}</td>
                <td colspan='5'></td>
                """
    else:
        html_content += f"""
                <td colspan='2'></td>
                """
    html_content += f"""<td>{total_harga}</td>"""

    # Menambahkan total data Pembayaran
    
    for payment_type in all_payment_types:
        total_pembayaran = "{:,.0f}".format(sum([p.amount for b in list_tahap_detail for p in b.pembayarans if p.name == payment_type['name'] and p.id_pembayaran == payment_type['id_pembayaran']]))
        
        html_content += f"""<td>{total_pembayaran}</td>"""

    html_content += "</tr>"

    html_content += "</table></body></html>"

    return html_content

async def generate_printout_utj(id:UUID | str):
     
    """Print out UTJ"""
    
    obj = await crud.termin.get_by_id_for_printout(id=id)
    if obj is None:
        raise IdNotFoundException(Termin, id)
    
    termin_header = TerminByIdForPrintOut(**dict(obj))

    data =  []
    no:int = 1
    invoices = await crud.invoice.get_invoice_by_termin_id_for_printout_utj(termin_id=id, jenis_bayar=termin_header.jenis_bayar)
    for inv in invoices:
        invoice = InvoiceForPrintOutUtj(**dict(inv))
        invoice.amountExt = "{:,.0f}".format(invoice.amount)
        invoice.luas_suratExt = "{:,.0f}".format(invoice.luas_surat)
        keterangan:str = ""
        keterangans = await crud.hasil_peta_lokasi_detail.get_keterangan_by_bidang_id_for_printout_utj(bidang_id=inv.bidang_id)
        for k in keterangans:
            kt = HasilPetaLokasiDetailForUtj(**dict(k))
            if kt.keterangan is not None and kt.keterangan != '':
                keterangan += f'{kt.keterangan}, '
        keterangan = keterangan[0:-2]
        invoice.keterangan = keterangan
        invoice.no = no
        no = no + 1

        data.append(invoice)

    array_total_luas_surat = numpy.array([b.luas_surat for b in invoices])
    total_luas_surat = numpy.sum(array_total_luas_surat)
    total_luas_surat = "{:,.0f}".format(total_luas_surat)

    array_total_amount = numpy.array([b.amount for b in invoices])
    total_amount = numpy.sum(array_total_amount)
    total_amount = "{:,.0f}".format(total_amount)

    filename:str = "utj.html" if termin_header.jenis_bayar == "UTJ" else "utj_khusus.html"
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template(filename)

    render_template = template.render(code=termin_header.code,
                                    manager_name=termin_header.k_manager_name,
                                    sales_name=termin_header.k_sales_name,
                                    data=data,
                                    total_luas_surat=total_luas_surat,
                                    total_amount=total_amount)
    
    try:
        doc = await PdfService().get_pdf(render_template)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed generate document")
    
    obj_current = await crud.termin.get(id=id)

    binary_io_data = BytesIO(doc)
    file = UploadFile(file=binary_io_data, filename=f"{obj_current.code.replace('/', '_')}.pdf")

    try:
        file_path = await GCStorageService().upload_file_dokumen(file=file, file_name=f"{obj_current.code.replace('/', '_')}")
        obj_updated = TerminUpdateSch(**obj_current.dict())
        obj_updated.file_path = file_path
        await crud.termin.update(obj_current=obj_current, obj_new=obj_updated)

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed generate document")
    
    return file_path

async def generate_printout(id:UUID | str):

    obj = await crud.termin.get_by_id_for_printout(id=id)
    if obj is None:
        raise IdNotFoundException(Termin, id)
    
    termin_header = TerminByIdForPrintOut(**dict(obj))
    obj_tanggal_transaksi = datetime.strptime(str(termin_header.tanggal_transaksi), "%Y-%m-%d")
    tanggal_transaksi = obj_tanggal_transaksi.strftime("%d-%m-%Y")

    obj_created_at = datetime.strptime(str(termin_header.created_at.date()), "%Y-%m-%d")
    bulan_created_en = obj_created_at.strftime('%B')
    bulan_created_id = bulan_dict.get(bulan_created_en, bulan_created_en)
    created_at = obj_created_at.strftime(f'%d {bulan_created_id} %Y')

    date_obj = datetime.strptime(str(termin_header.tanggal_rencana_transaksi), "%Y-%m-%d")
    nama_bulan_inggris = date_obj.strftime('%B')  # Mendapatkan nama bulan dalam bahasa Inggris
    nama_bulan_indonesia = bulan_dict.get(nama_bulan_inggris, nama_bulan_inggris)  # Mengonversi ke bahasa Indonesia
    tanggal_hasil = date_obj.strftime(f'%d {nama_bulan_indonesia} %Y')
    day_of_week = date_obj.strftime("%A")
    hari_transaksi:str|None = HelperService().ToDayName(day_of_week)

    remarks = termin_header.remark.splitlines()
    #perhitungan utj (jika invoice dlm termin dikurangi utj) & data invoice di termin yg akan di printout
    amount_utj_used = []
    termin_invoices:list[InvoiceForPrintOutExt] = []
    obj_invoices = await crud.invoice.get_invoice_by_termin_id_for_printout(termin_id=id)
    for inv in obj_invoices:
        iv = InvoiceForPrintOutExt(**dict(inv))
        invoice_curr = await crud.invoice.get_utj_amount_by_id(id=iv.id)
        amount_utj_used.append(invoice_curr.utj_amount)
        termin_invoices.append(iv)
    
    amount_utj = sum(amount_utj_used) or 0

    #untuk list bidang dalam 1 tahap
    obj_bidangs = await crud.tahap_detail.get_multi_by_tahap_id_for_printout(tahap_id=termin_header.tahap_id)

    bidangs:list[TahapDetailForPrintOut] = []
    nomor_urut_bidang = []
    overlap_exists = False
    no = 1
    for bd in obj_bidangs:
        bidang = TahapDetailForPrintOut(**dict(bd),
                                    no=no,
                                    total_hargaExt="{:,.0f}".format(bd.total_harga),
                                    harga_transaksiExt = "{:,.0f}".format(bd.harga_transaksi),
                                    luas_suratExt = "{:,.0f}".format(bd.luas_surat),
                                    luas_nettExt = "{:,.0f}".format(bd.luas_nett),
                                    luas_ukurExt = "{:,.0f}".format(bd.luas_ukur),
                                    luas_gu_peroranganExt = "{:,.0f}".format(bd.luas_gu_perorangan),
                                    luas_pbt_peroranganExt = "{:,.0f}".format(bd.luas_pbt_perorangan),
                                    luas_bayarExt = "{:,.0f}".format(bd.luas_bayar),
                                    is_bold=False)
        

        bidang_in_termin = next((bd_in_termin for bd_in_termin in termin_invoices if bd_in_termin.bidang_id == bidang.bidang_id), None)
        if bidang_in_termin:
            bidang.is_bold = True
            nomor_urut_bidang.append(bidang.no)

        overlaps = await crud.bidangoverlap.get_multi_by_bidang_id_for_printout(bidang_id=bd.bidang_id)
        list_overlap = []
        for ov in overlaps:
            overlap = BidangOverlapForPrintout(**dict(ov))
            bidang_utama = await crud.bidang.get_by_id(id=bd.bidang_id)
            if (bidang_utama.status_sk == StatusSKEnum.Sudah_Il and bidang_utama.hasil_analisa_peta_lokasi == HasilAnalisaPetaLokasiEnum.Overlap) or (bidang_utama.status_sk == StatusSKEnum.Belum_IL and bidang_utama.hasil_analisa_peta_lokasi == HasilAnalisaPetaLokasiEnum.Clear):
                nib_perorangan:str = ""
                nib_perorangan_meta_data = await crud.bundledt.get_meta_data_by_dokumen_name_and_bidang_id(dokumen_name='NIB PERORANGAN', bidang_id=bidang_utama.id)
                if nib_perorangan_meta_data:
                    if nib_perorangan_meta_data.meta_data is not None and nib_perorangan_meta_data.meta_data != "":
                        metadata_dict = json.loads(nib_perorangan_meta_data.meta_data.replace("'", "\""))
                        nib_perorangan = metadata_dict[f'{nib_perorangan_meta_data.key_field}']
                overlap.nib = nib_perorangan

            list_overlap.append(overlap)

        bidang.overlaps = list_overlap

        if len(bidang.overlaps) > 0:
            overlap_exists = True

        bidangs.append(bidang)
        no = no + 1
    
    nomor_urut:str = ""
    for no in nomor_urut_bidang:
        nomor_urut += f"{no}, "
    
    nomor_urut = f"No. {nomor_urut[0:-2]}"

    list_bidang_id = [bd.bidang_id for bd in obj_bidangs]

    total_luas_surat = "{:,.0f}".format(sum([b.luas_surat for b in obj_bidangs]))
    total_luas_ukur = "{:,.0f}".format(sum([b.luas_ukur for b in obj_bidangs]))
    total_luas_gu_perorangan = "{:,.0f}".format(sum([b.luas_gu_perorangan for b in obj_bidangs]))
    total_luas_nett = "{:,.0f}".format(sum([b.luas_nett for b in obj_bidangs]))
    total_luas_pbt_perorangan = "{:,.0f}".format(sum([b.luas_pbt_perorangan for b in obj_bidangs]))
    total_luas_bayar = "{:,.0f}".format(sum([b.luas_bayar for b in obj_bidangs]))
    total_harga = "{:,.0f}".format(sum([b.total_harga for b in obj_bidangs]))

    termin_histories = []
    current_termin_histories = await crud.termin.get_multi_by_bidang_ids(bidang_ids=list_bidang_id, current_termin_id=id)
    for termin in current_termin_histories:
        termin_history = TerminHistoriesSch(**dict(termin))
        if termin_history.tanggal_transaksi:
            obj_history_tanggal_transaksi = datetime.strptime(str(termin_history.tanggal_transaksi), "%Y-%m-%d")
            termin_history.str_tanggal_transaksi = obj_history_tanggal_transaksi.strftime("%d-%m-%Y")
        else:
            termin_history.str_tanggal_transaksi = ""

        termin_history.str_amount = "{:,.0f}".format(termin.amount)
        if termin_history.jenis_bayar not in [JenisBayarEnum.UTJ, JenisBayarEnum.UTJ_KHUSUS]:
            invoice_in_termin_histories = await crud.invoice.get_multi_invoice_id_luas_bayar_by_termin_id(termin_id=termin_history.id)
            count_bidang = len(invoice_in_termin_histories)
            sum_luas_bayar = "{:,.0f}".format(sum([invoice_.luas_bayar or 0 for invoice_ in invoice_in_termin_histories if invoice_.luas_bayar is not None]))
            termin_history.str_jenis_bayar = f"{termin_history.str_jenis_bayar} {count_bidang}BID luas {sum_luas_bayar}m2"

        komponen_biayas = []
        obj_komponen_biayas = await crud.termin.get_beban_biaya_by_id_for_printout(id=termin.id, jenis_bayar=termin.jenis_bayar)
        for bb in obj_komponen_biayas:
            beban_biaya = TerminBebanBiayaForPrintOut(**dict(bb))
            beban_biaya.beban_biaya_name = f"{beban_biaya.beban_biaya_name} {beban_biaya.tanggungan}"
            beban_biaya.amountExt = "{:,.0f}".format(beban_biaya.amount)
            komponen_biayas.append(beban_biaya)

        termin_history.beban_biayas = komponen_biayas
        invoices = await crud.invoice.get_multi_by_termin_id(termin_id=termin.id)

        nomor_uruts = []
        for invoice in invoices:
            nomor = next((bidang.no for bidang in bidangs if bidang.bidang_id == invoice.bidang_id), None)
            if nomor:
                nomor_uruts.append(nomor)
        
        index_no:str = ""
        
        nomor_uruts = sorted(nomor_uruts, key=lambda obj:obj)
        for no in nomor_uruts:
            index_no += f"{no}, "
        
        index_no = index_no[0:-2]

        termin_history.index_bidang = f"No. {index_no}"
        termin_histories.append(termin_history)

    komponen_biayas = []
    obj_komponen_biayas = await crud.termin.get_beban_biaya_by_id_for_printout(id=id, jenis_bayar=termin_header.jenis_bayar)
    for bb in obj_komponen_biayas:
        beban_biaya = TerminBebanBiayaForPrintOut(**dict(bb))
        beban_biaya.beban_biaya_name = f"{beban_biaya.beban_biaya_name} {beban_biaya.tanggungan}"
        beban_biaya.amountExt = "{:,.0f}".format(beban_biaya.amount)
        komponen_biayas.append(beban_biaya)
    
    amount_beban_biayas = [beban_penjual.amount for beban_penjual in obj_komponen_biayas if beban_penjual.beban_pembeli == False and beban_penjual.is_void != True]
    amount_beban_biaya = sum(amount_beban_biayas)

    harga_aktas = []
    obj_kjb_hargas = await crud.kjb_harga.get_harga_akta_by_termin_id_for_printout(termin_id=id)
    for hg in obj_kjb_hargas:
        harga_akta = KjbHargaAktaSch(**dict(hg))
        harga_akta.harga_aktaExt = "{:,.0f}".format(hg.harga_akta)
        harga_aktas.append(harga_akta)

    
    no = 1
    obj_termin_bayar = await crud.termin_bayar.get_multi_by_termin_id_for_printout(termin_id=id)
    
    filename = "memo_tanah_overlap_ext.html" if overlap_exists else "memo_tanah_ext.html"
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template(filename)

    render_template = template.render(code=termin_header.nomor_memo or "",
                                    created_at=created_at,
                                    nomor_tahap=termin_header.nomor_tahap,
                                    section_name=termin_header.section_name,
                                    project_name=termin_header.project_name,
                                    desa_name=termin_header.desa_name,
                                    ptsk_name=termin_header.ptsk_name,
                                    notaris_name=termin_header.notaris_name,
                                    manager_name=termin_header.manager_name.upper(),
                                    sales_name=termin_header.sales_name.upper(),
                                    mediator=termin_header.mediator.upper(),
                                    data=bidangs,
                                    total_luas_surat=total_luas_surat,
                                    total_luas_ukur=total_luas_ukur,
                                    total_luas_gu_perorangan=total_luas_gu_perorangan,
                                    total_luas_nett=total_luas_nett,
                                    total_luas_pbt_perorangan=total_luas_pbt_perorangan,
                                    total_luas_bayar=total_luas_bayar,
                                    total_harga=total_harga,
                                    data_invoice_history=termin_histories,
                                    data_beban_biaya=komponen_biayas,
                                    data_harga_akta=harga_aktas,
                                    data_payment=obj_termin_bayar,
                                    nomor_urut_bidang=nomor_urut,
                                    tanggal_transaksi=tanggal_transaksi,
                                    tanggal_rencana_transaksi=tanggal_hasil,
                                    hari_transaksi=hari_transaksi,
                                    jenis_bayar=termin_header.jenis_bayar_ext.replace('_', ' '),
                                    amount="{:,.0f}".format(((termin_header.amount - amount_beban_biaya) - amount_utj)),
                                    remarks=remarks
                                    )
    
    try:
        doc = await PdfService().get_pdf(render_template)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed generate document")
    
    obj_current = await crud.termin.get(id=id)

    binary_io_data = BytesIO(doc)
    file = UploadFile(file=binary_io_data, filename=f"{obj_current.code.replace('/', '_')}.pdf")

    try:
        file_path = await GCStorageService().upload_file_dokumen(file=file, file_name=f"{obj_current.code.replace('/', '_')}-{str(obj_current.id)}", is_public=True)
        obj_updated = TerminUpdateSch(**obj_current.dict())
        obj_updated.file_path = file_path
        await crud.termin.update(obj_current=obj_current, obj_new=obj_updated)

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed generate document")
    
    return file_path

async def merge_memo_signed(id:UUID | str):

    db_session = db.session
    termin = await crud.termin.get(id=id)
    details = await crud.invoice.get_multi_by_termin_id(termin_id=id)

    for detail in details:
        bidang = await crud.bidang.get(id=detail.bidang_id)
        bundle = await crud.bundlehd.get_by_id(id=bidang.bundle_hd_id)
        if bundle:
            await BundleHelper().merge_memo_signed(bundle=bundle, code=f"{termin.code}-{str(termin.updated_at.date())}", tanggal=termin.updated_at.date(), file_path=termin.file_upload_path, worker_id=termin.updated_by_id, db_session=db_session)
    
    await db_session.commit()

@router.post("/export/excel")
async def get_report(
                termin_ids:TerminIdSch|None = None, 
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    filename:str = ''
    query = select(Termin)
    if termin_ids.termin_ids:
        query = query.filter(Termin.id.in_(termin_ids.termin_ids))
    
    query = query.filter(~Termin.jenis_bayar.in_([JenisBayarEnum.UTJ.value, JenisBayarEnum.UTJ_KHUSUS.value]))

    query = query.distinct()
    query = query.options(selectinload(Termin.invoices
                                ).options(selectinload(Invoice.bidang
                                                    ).options(selectinload(Bidang.pemilik)
                                                    ).options(selectinload(Bidang.planing
                                                                ).options(selectinload(Planing.project)
                                                                ).options(selectinload(Planing.desa))
                                                    ).options(selectinload(Bidang.invoices
                                                                ).options(selectinload(Invoice.payment_details)
                                                                ).options(selectinload(Invoice.termin))
                                                    )
                                ).options(selectinload(Invoice.payment_details
                                                    ).options(selectinload(PaymentDetail.payment
                                                                ).options(selectinload(Payment.giro))
                                                    ).options(selectinload(PaymentDetail.payment_giro
                                                                ).options(selectinload(PaymentGiroDetail.giro))
                                                    )
                                ).options(selectinload(Invoice.termin
                                                    ).options(selectinload(Termin.tahap)
                                                    )
                                ).options(selectinload(Invoice.details
                                                    ).options(selectinload(InvoiceDetail.bidang_komponen_biaya
                                                                        ).options(selectinload(BidangKomponenBiaya.beban_biaya)
                                                                        ).options(selectinload(BidangKomponenBiaya.bidang))
                                                    )
                                )
                )

    objs = await crud.termin.get_multi_no_page(query=query)

    data = [{
                "Id Bidang" : invoice.id_bidang, 
                "Id Bidang Lama" : invoice.id_bidang_lama,
                "Project" : invoice.bidang.project_name, 
                "Desa" : invoice.bidang.desa_name,
                "Nomor Tahap" : invoice.termin.nomor_tahap,
                "Nomor Memo" : invoice.termin.nomor_memo,
                "Group" : invoice.bidang.group,
                "Pemilik" : invoice.bidang.pemilik_name,
                "Alashak" : invoice.alashak,
                "Luas Surat" : f'{"{:,.0f}".format(RoundTwo(invoice.bidang.luas_surat or 0))}',
                "Luas Bayar" : f'{"{:,.0f}".format(RoundTwo(invoice.bidang.luas_bayar or 0))}', 
                "Jumlah" :  f'Rp. {"{:,.0f}".format(RoundTwo(invoice.amount_nett))}',
                "Jenis Bayar" : invoice.jenis_bayar,
                "Status Workflow" : invoice.step_name_workflow if invoice.status_workflow != WorkflowLastStatusEnum.COMPLETED else invoice.status_workflow or "-",
                "Tanggal Last Workflow" : invoice.last_status_at,
                "Harga Transaksi" : f'Rp. {"{:,.0f}".format(RoundTwo(Decimal(invoice.bidang.harga_transaksi or 0)))}', 
                "Nomor Giro" : ','.join([f'{payment_detail.nomor_giro if payment_detail else {""}} : Rp. {"{:,.0f}".format(payment_detail.amount)}' for payment_detail in invoice.payment_details]),
                "Tanggal Pembayaran" : invoice.termin.tanggal_rencana_transaksi,
                "Payment Status" : invoice.payment_status if invoice.payment_status else invoice.payment_status_ext,
                "Tanggal Last Payment Status" : invoice.last_payment_status_at
            }
            for termin in objs for invoice in termin.invoices]

    
    df = pd.DataFrame(data=data)

    output = BytesIO()
    df.to_excel(output, index=False, sheet_name=f'Memo Pembayaran')

    output.seek(0)

    return StreamingResponse(BytesIO(output.getvalue()), 
                            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            headers={"Content-Disposition": "attachment;filename=memo_data.xlsx"})

@router.put("/void/{id}", response_model=GetResponseBaseSch[TerminByIdSch])
async def void(id:UUID, 
            sch:TerminVoidSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """void a obj by its ids"""
    db_session = db.session

    obj_current = await crud.termin.get_by_id(id=id)

    if not obj_current:
        raise IdNotFoundException(Termin, id)
    
    invoice_ids = [inv.id for inv in obj_current.invoices if inv.is_void != True]
    payment_actived = await crud.payment_detail.get_multi_payment_actived_by_invoice_id(list_ids=invoice_ids)

    if len(payment_actived) > 0:
        raise HTTPException(status_code=422, detail="Failed void. Detail : Invoice di dalam Termin memiliki payment yang sedang aktif ")
    
    obj_updated = TerminUpdateSch.from_orm(obj_current)
    obj_updated.is_void = True
    obj_updated.void_reason = sch.void_reason
    obj_updated.void_by_id = current_worker.id
    obj_updated.void_at = date.today()

    obj_updated = await crud.termin.update(obj_current=obj_current, obj_new=obj_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

    update_query = update(Invoice).where(and_(Invoice.id.in_(invoice_ids), Invoice.termin_id == obj_current.id)
                                        ).values(is_void=True, void_reason=sch.void_reason, void_by_id=current_worker.id, void_at=date.today())
    
    await db_session.execute(update_query)
    await db_session.commit()

    obj_updated = await crud.termin.get_by_id(id=obj_updated.id)
    return create_response(data=obj_updated) 

@router.post("/task-workflow")
async def create_workflow(payload:Dict):
    
    id = payload.get("id", None)
    obj = await crud.termin.get(id=id)

    if not obj:
        raise IdNotFoundException(Spk, id)
    
    wf_current = await crud.workflow.get_by_reference_id(reference_id=id)
    if not wf_current:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    trying:int = 0
    while obj.file_path is None:
        await generate_printout(id=id)
        if trying > 7:
            raise HTTPException(status_code=404, detail="File not found")
        obj = await crud.termin.get(id=id)
        time.sleep(2)
        trying += 1
    
    public_url = await GCStorageService().public_url(file_path=obj.file_path)

    wf_system_attachment = WorkflowSystemAttachmentSch(name=f"{obj.code}", url=public_url)
    wf_system_sch = WorkflowSystemCreateSch(client_ref_no=str(id), 
                                            flow_id=wf_current.flow_id, 
                                            descs=f"""Dokumen Memo Pembayaran {obj.code} ini membutuhkan Approval dari Anda:<br><br>
                                                    Tanggal: {obj.created_at.date()}<br>
                                                    Dokumen: {obj.code}<br><br>
                                                    Berikut lampiran dokumen terkait : """,
                                            attachments=[vars(wf_system_attachment)],
                                            version=wf_current.version)
    
    body = vars(wf_system_sch)
    response, msg = await WorkflowService().create_workflow(body=body)

    if response is None:
        raise HTTPException(status_code=422, detail=f"Failed to connect workflow system. Detail : {msg}")
    
    wf_updated = WorkflowUpdateSch(**wf_current.dict(exclude={"last_status"}), last_status=response.last_status)
    await crud.workflow.update(obj_current=wf_current, obj_new=wf_updated, updated_by_id=obj.updated_by_id)

    return {"message" : "successfully"}

bulan_dict = {
    "January": "Januari",
    "February": "Februari",
    "March": "Maret",
    "April": "April",
    "May": "Mei",
    "June": "Juni",
    "July": "Juli",
    "August": "Agustus",
    "September": "September",
    "October": "Oktober",
    "November": "November",
    "December": "Desember"
}

@router.get("/download-file/{id}")
async def download_file(id:UUID):
    """Download File Dokumen"""

    obj_current = await crud.termin.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Termin, id)
    if obj_current.file_upload_path is None:
        raise DocumentFileNotFoundException(dokumenname=obj_current.code)
    try:
        file_bytes = await GCStorageService().download_dokumen(file_path=obj_current.file_upload_path)
    except Exception as e:
        raise DocumentFileNotFoundException(dokumenname=obj_current.code)
    
    ext = obj_current.file_path.split('.')[-1]

    # return FileResponse(file, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={obj_current.id}.{ext}"})
    response = Response(content=file_bytes, media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename=Hasil Peta Lokasi-{id}-{obj_current.code}.{ext}"
    return response

@router.get("/estimated/amount", response_model=GetResponseBaseSch[BebanBiayaEstimatedAmountSch])
async def get_estimated_amount(bidang_id:UUID, beban_biaya_id:UUID):

    master_beban_biaya = await crud.bebanbiaya.get(id=beban_biaya_id)
    if master_beban_biaya is None:
        raise HTTPException(status_code=422, detail="master beban biaya tidak ditemukan")
    
    result = BebanBiayaEstimatedAmountSch.from_orm(master_beban_biaya)

    bidang_komponen_biaya_current = await crud.bidang_komponen_biaya.get_by_bidang_id_and_beban_biaya_id(bidang_id=bidang_id, beban_biaya_id=beban_biaya_id)

    if master_beban_biaya.satuan_bayar == SatuanBayarEnum.Amount and master_beban_biaya.satuan_harga == SatuanHargaEnum.Lumpsum:
        if bidang_komponen_biaya_current:
            result.estimated_amount = master_beban_biaya.amount - bidang_komponen_biaya_current.invoice_detail_amount
            result.bidang_id = bidang_id
            result.amount = master_beban_biaya.amount
        else:
            result.estimated_amount = master_beban_biaya.amount 
            result.bidang_id = bidang_id
            result.amount = master_beban_biaya.amount
    else:
        if bidang_komponen_biaya_current:
            result.estimated_amount = bidang_komponen_biaya_current.komponen_biaya_outstanding
            result.bidang_id = bidang_id
        else:
            estimated_amount = await KomponenBiayaHelper().get_estimated_amount_v2(bidang_id=bidang_id, formula=master_beban_biaya.formula, beban_biaya_id=master_beban_biaya.id)
            result.estimated_amount = estimated_amount
            result.bidang_id = bidang_id

    return create_response(data=result)

@router.get("/estimated/amount/edited", response_model=GetResponseBaseSch[BebanBiayaEstimatedAmountSch])
async def get_estimated_amount_edited(bidang_id:UUID, beban_biaya_id:UUID, 
                                    amount:Decimal | None = None, 
                                    satuan_bayar:SatuanBayarEnum | None = None, 
                                    satuan_harga:SatuanHargaEnum | None = None):

    master_beban_biaya = await crud.bebanbiaya.get(id=beban_biaya_id)
    if master_beban_biaya is None:
        raise HTTPException(status_code=422, detail="master beban biaya tidak ditemukan")
    
    result = BebanBiayaEstimatedAmountSch.from_orm(master_beban_biaya)

    bidang_komponen_biaya_current = await crud.bidang_komponen_biaya.get_by_bidang_id_and_beban_biaya_id(bidang_id=bidang_id, beban_biaya_id=beban_biaya_id)

    if satuan_bayar == SatuanBayarEnum.Amount and satuan_harga == SatuanHargaEnum.Lumpsum:
        if bidang_komponen_biaya_current:
            result.estimated_amount = amount - bidang_komponen_biaya_current.invoice_detail_amount
            result.bidang_id = bidang_id
            result.amount = amount
        else:
            result.estimated_amount = amount 
            result.bidang_id = bidang_id
            result.amount = amount
    else:
        if bidang_komponen_biaya_current:
            if amount:
                estimated_amount = await KomponenBiayaHelper().get_estimated_amount_v2(bidang_id=bidang_id, formula=master_beban_biaya.formula, beban_biaya_id=master_beban_biaya.id, amount=amount)
                estimated_amount = estimated_amount - bidang_komponen_biaya_current.invoice_detail_amount
                result.estimated_amount = estimated_amount
                result.bidang_id = bidang_id
                result.amount = amount
            else:
                result.estimated_amount = bidang_komponen_biaya_current.komponen_biaya_outstanding
                result.bidang_id = bidang_id
        else:
            estimated_amount = await KomponenBiayaHelper().get_estimated_amount_v2(bidang_id=bidang_id, formula=master_beban_biaya.formula, beban_biaya_id=master_beban_biaya.id, amount=amount)
            result.estimated_amount = estimated_amount
            result.bidang_id = bidang_id

    return create_response(data=result)
