from fastapi import HTTPException, Request, UploadFile
from fastapi_async_sqlalchemy import db
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import and_, delete, update
from models.code_counter_model import CodeCounterEnum
from models import Termin, Worker, Invoice

from schemas.kjb_harga_sch import KjbHargaAktaSch
from schemas.termin_sch import TerminCreateSch, TerminUpdateSch, TerminByIdForPrintOut, TerminHistoriesSch, TerminBebanBiayaForPrintOut, TerminVoidSch
from schemas.termin_bayar_sch import TerminBayarCreateSch, TerminBayarUpdateSch
from schemas.termin_bayar_dt_sch import TerminBayarDtCreateSch, TerminBayarDtUpdateSch
from schemas.invoice_sch import InvoiceCreateSch, InvoiceUpdateSch, InvoiceForPrintOutUtj, InvoiceForPrintOutExt
from schemas.invoice_detail_sch import InvoiceDetailCreateSch, InvoiceDetailUpdateSch
from schemas.invoice_bayar_sch import InvoiceBayarCreateSch, InvoiceBayarlUpdateSch
from schemas.tahap_detail_sch import TahapDetailForExcel, TahapDetailForPrintOut
from schemas.spk_sch import SpkInTerminSch
from schemas.bidang_overlap_sch import BidangOverlapForPrintout
from schemas.bidang_komponen_biaya_sch import BidangKomponenBiayaCreateSch, BidangKomponenBiayaUpdateSch
from schemas.hasil_peta_lokasi_detail_sch import HasilPetaLokasiDetailForUtj
from schemas.workflow_sch import WorkflowUpdateSch, WorkflowCreateSch, WorkflowSystemCreateSch, WorkflowSystemAttachmentSch

from services.helper_service import BundleHelper, HelperService
from services.gcloud_task_service import GCloudTaskService
from services.gcloud_storage_service import GCStorageService
from services.helper_service import BidangHelper
from services.pdf_service import PdfService
from services.adobe_service import PDFToExcelService
from services.encrypt_service import encrypt_id
from services.workflow_service import WorkflowService

from common.exceptions import IdNotFoundException
from common.enum import (JenisBayarEnum, jenis_bayar_to_code_counter_enum, jenis_bayar_to_text, WorkflowEntityEnum, 
                        WorkflowLastStatusEnum, ActivityEnum, jenis_bayar_to_termin_status_pembebasan_dict, StatusSKEnum, HasilAnalisaPetaLokasiEnum)
from common.generator import generate_code_month

import crud
import roman
import json
import logging
import time

from datetime import date, datetime
from uuid import UUID, uuid4
from decimal import Decimal
from io import BytesIO

from jinja2 import Environment, FileSystemLoader

class TerminService:

    # FILTER TERMIN
    async def filter_termin(self, sch: TerminCreateSch | TerminUpdateSch):
        # CHECKING DARI SISI TERMIN BAYAR APAKAH TOTAL PER TERMIN BAYAR SUDAH BALANCE ALLOCATENYA KE SEMUA INVOICE PADA MEMO
            for termin_bayar in sch.termin_bayars:
                if termin_bayar.activity == ActivityEnum.BEBAN_BIAYA:
                    if termin_bayar.termin_bayar_dts:
                        invoice_dts = []
                        for termin_bayar_dt in termin_bayar.termin_bayar_dts:
                            invoice_dts = [inv_dt.amount or 0 for inv in sch.invoices for inv_dt in inv.details if inv_dt.beban_biaya_id == termin_bayar_dt.beban_biaya_id]

                        if sum(invoice_dts) != termin_bayar.amount:
                            raise HTTPException(status_code=422, detail=f"""Giro/Cek/Tunai {termin_bayar.name} untuk Beban Biaya belum balance ke allocate Beban Biaya pada seluruh bidang di memo bayar. 
                                                Harap cek kembali nominal Giro/Cek/Tunai dengan total beban biaya yang di pilih pada Info Pembayaran""")
                else:
                    invoice_bayars = [inv_bayar.amount or 0 for inv in sch.invoices for inv_bayar in inv.bayars if inv_bayar.id_index == termin_bayar.id_index]

                    if len(invoice_bayars) == 0:
                        raise HTTPException(status_code=422, detail=f"Giro/Cek '{termin_bayar.name}' belum terallocate ke bidang-bidang pada memo")
                    
                    if termin_bayar.amount != sum(invoice_bayars):
                        raise HTTPException(status_code=422, detail=f"Nominal Allocation belum balance dengan Nominal Giro/Cek/Tunai '{termin_bayar.name}'")
            
            # CHECKING DARI SISI INVOICE APAKAH TOTAL BAYAR PER INVOICENYA SUDAH BALACE DENGAN ALLOCATE DARI TERMIN BAYAR
            # CHECKING ALLOCATE UTJ PERBIDANG APAKAH SUDAH SAMA DENGAN YG TELAH DIPAYMENT
            for invoice in sch.invoices:
                invoice_bayar_ = []
                bidang = await crud.bidang.get_by_id(id=invoice.bidang_id)

                for inv_bayar in invoice.bayars:
                    # CHECKING UTJ
                    tr_byr_utj = next((tr for tr in sch.termin_bayars if tr.id_index == inv_bayar.id_index and tr.activity in [ActivityEnum.UTJ]), None)
                    if tr_byr_utj:
                        if (tr_byr_utj.amount or 0) != 0:
                            if inv_bayar.amount != bidang.utj_amount:
                                raise HTTPException(status_code=422, detail=f"Nominal Allocation UTJ untuk bidang '{bidang.id_bidang}' tidak sama dengan nominal UTJ yang sudah dipayment")
                            if bidang.utj_realisasi_amount != 0:
                                raise HTTPException(status_code=422, detail=f"Bidang {bidang.id_bidang} sudah memiliki UTJ realisasi, di memo sebelumnya")
                            
                    # CHECKING REGULAR INVOICE
                    tr_byr = next((tr for tr in sch.termin_bayars if tr.id_index == inv_bayar.id_index and tr.activity in [ActivityEnum.BIAYA_TANAH]), None)
                    if tr_byr:
                        invoice_bayar_.append(inv_bayar)
                
                invoice_bayar_amount = sum([inv_bayar.amount or 0 for inv_bayar in invoice_bayar_])

                if invoice.amount_netto != invoice_bayar_amount:
                    raise HTTPException(status_code=422, detail="Allocation belum balance dengan Total Bayar Invoice, Cek Kembali masing-masing Total Bayar Invoice dengan Allocationnya!")

    # INITIALIZE TERMIN
    async def init_termin(self, sch: TerminCreateSch, db_session:AsyncSession, worker_id:UUID, month, year):

        code_counter = jenis_bayar_to_code_counter_enum.get(sch.jenis_bayar, sch.jenis_bayar)
        jns_byr = jenis_bayar_to_text.get(sch.jenis_bayar, sch.jenis_bayar)
        last_number = await generate_code_month(entity=code_counter, with_commit=False, db_session=db_session)
        sch.code = f"{last_number}/{jns_byr}/LA/{month}/{year}" 

        new_obj = await crud.termin.create(obj_in=sch, db_session=db_session, with_commit=False, created_by_id=worker_id)

        return new_obj

    # CREATE TERMIN, INVOICE, INVOICE DETAIL, INVOICE BAYAR, TERMIN BAYAR
    async def create_termin(self, sch: TerminCreateSch, db_session:AsyncSession, current_worker:Worker, request:Request):

        today = date.today()
        month = roman.toRoman(today.month)
        year = today.year

        # INITIALIZE TERMIN
        new_obj = await self.init_termin(sch=sch, db_session=db_session, worker_id=current_worker.id, month=month, year=year)

        # ADD TERMIN BAYAR
        termin_bayar_temp = []
        for termin_bayar in sch.termin_bayars:
            termin_bayar_sch = TerminBayarCreateSch(**termin_bayar.dict(), termin_id=new_obj.id)
            obj_termin_bayar = await crud.termin_bayar.create(obj_in=termin_bayar_sch,  db_session=db_session, with_commit=False, created_by_id=current_worker.id)

            # TEMPORARY DICTIONARY UNTUK MEMASANGKAN TERMIN BAYAR DENGAN INVOICE BAYAR
            termin_bayar_temp.append({"termin_bayar_id" : obj_termin_bayar.id, "id_index" : termin_bayar.id_index})

            # ADD TERMIN BAYAR DETAIL
            if termin_bayar.termin_bayar_dts:
                for termin_bayar_dt in termin_bayar.termin_bayar_dts:
                    termin_bayar_dt_sch = TerminBayarDtCreateSch(**termin_bayar_dt.dict(), termin_bayar_id=obj_termin_bayar.id)
                    await crud.termin_bayar_dt.create(obj_in=termin_bayar_dt_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)

        # ADD INVOICE
        for invoice in sch.invoices:
            last_number = await generate_code_month(entity=CodeCounterEnum.Invoice, with_commit=False, db_session=db_session)
            invoice_sch = InvoiceCreateSch(**invoice.dict(), 
                                            termin_id=new_obj.id, 
                                            code=f"INV/{last_number}/{jenis_bayar_to_text.get(sch.jenis_bayar, sch.jenis_bayar)}/LA/{month}/{year}", 
                                            is_void=False
                                        )
            # KALAU UTJ AMBIL AMOUNT NETTONYA DARI AMOUNT
            invoice_sch.amount_netto = invoice.amount if sch.jenis_bayar in (JenisBayarEnum.UTJ, JenisBayarEnum.UTJ_KHUSUS) else invoice.amount_netto
            
            new_obj_invoice = await crud.invoice.create(obj_in=invoice_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)

            # POPULATE DATA MASTER BEBAN BIAYA PERSIAPAN UNTUK MANIPULASI DATA INVOICE DETAIL
            master_beban_biayas = await crud.bebanbiaya.get_by_ids(list_ids=[bb.beban_biaya_id for bb in invoice.details if bb.beban_biaya_id is not None and bb.is_deleted != True])

            # ADD INVOICE DETAIL
            for dt in invoice.details:

                # LEWATI KOMPONEN BIAYA YANG INGIN DIHAPUS (EKSEKUSI DARI INVOICE DETAIL)
                if dt.is_deleted:
                    continue
                
                # CEK APAKAH AMOUNT BEBAN BIAYA TIDAK SAMA DENGAN 0
                if dt.amount == 0 and (sch.is_draft or False) == False:
                    bidang = await crud.bidang.get(id=invoice.bidang_id)
                    master_beban_biaya = next((bb for bb in master_beban_biayas if bb.id == dt.beban_biaya_id), None)
                    raise HTTPException(status_code=422, detail=f"Amount beban biaya {master_beban_biaya.name} pada bidang {bidang.id_bidang} masih 0, cek kembali beban biaya")
                    
                bidang_komponen_biaya_current = await crud.bidang_komponen_biaya.get(id=dt.bidang_komponen_biaya_id)

                # ADD KOMPONEN BIAYA BARU JIKA USER MENAMBAHKAN KOMPONEN BIAYA YANG TIDAK ADA DI MASTER BIDANG KOMPONEN BIAYA
                if bidang_komponen_biaya_current is None:

                    # VALIDASI BEBAN BIAYA YANG TERADD KEMBALI BERDASARKAN BEBAN BIAYA ID DAN BIDANG ID (TIDAK BOLEH ADA DOUBLE BEBAN BIAYA YANG SAMA)
                    bkb_has_exists = await crud.bidang_komponen_biaya.get_by_bidang_id_and_beban_biaya_id(bidang_id=invoice.bidang_id, beban_biaya_id=dt.beban_biaya_id)
                    if bkb_has_exists:
                        bidang_err = await crud.bidang.get(id=invoice.bidang_id)
                        raise HTTPException(status_code=422, detail=f"""Anda memasukkan beban biaya baru '{bkb_has_exists.beban_biaya_name}' 
                                            pada bidang {bidang_err.id_bidang}. Mohon cek kembali apakah beban tersebut sudah pernah ada pada Memo sebelumnya.""")

                    master_beban_biaya = next((bb for bb in master_beban_biayas if bb.id == dt.beban_biaya_id), None)
                    if master_beban_biaya is None:
                        raise HTTPException(status_code=404, detail="Beban Biaya not found in Master!")
                    
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
                    
                    # SIMPAN ID KOMPONEN BIAYA UNTUK INVOICE DETAIL
                    dt.bidang_komponen_biaya_id = obj_bidang_komponen_biaya.id

                # UPDATE KOMPONEN BIAYA DI MASTER JIKA KOMPONEN BIAYA EXISTS SESUAI DENGAN INPUTAN USER
                else:
                    bidang_komponen_biaya_new = BidangKomponenBiayaUpdateSch.from_orm(bidang_komponen_biaya_current)
                    bidang_komponen_biaya_new.amount = dt.komponen_biaya_amount
                    bidang_komponen_biaya_new.satuan_bayar = dt.satuan_bayar
                    bidang_komponen_biaya_new.satuan_harga = dt.satuan_harga
                    bidang_komponen_biaya_new.beban_biaya_id = dt.beban_biaya_id
                    bidang_komponen_biaya_new.beban_pembeli = dt.beban_pembeli
                    bidang_komponen_biaya_new.estimated_amount = dt.amount

                    bidang_komponen_biaya_current = await crud.bidang_komponen_biaya.update(obj_current=bidang_komponen_biaya_current, obj_new=bidang_komponen_biaya_new, db_session=db_session, with_commit=False, updated_by_id=current_worker.id)
                    
                    # SIMPAN ID KOMPONEN BIAYA UNTUK INVOICE DETAIL
                    dt.bidang_komponen_biaya_id = bidang_komponen_biaya_current.id

                invoice_dtl_sch = InvoiceDetailCreateSch(**dt.dict(), invoice_id=new_obj_invoice.id)
                await crud.invoice_detail.create(obj_in=invoice_dtl_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)

            # ADD INVOICE BAYAR
            for dt_bayar in invoice.bayars:
                termin_bayar_id = next((termin_bayar["termin_bayar_id"] for termin_bayar in termin_bayar_temp if termin_bayar["id_index"] == dt_bayar.id_index), None)
                invoice_bayar_new = InvoiceBayarCreateSch(termin_bayar_id=termin_bayar_id, invoice_id=new_obj_invoice.id, amount=dt_bayar.amount)
                await crud.invoice_bayar.create(obj_in=invoice_bayar_new, db_session=db_session, with_commit=False, created_by_id=current_worker.id)


        # UPDATE STATUS PEMBEBASAN PADA BIDANG SEKALIGUS MENJALANKAN WORKFLOW JIKA MEMO BUKAN DRAFT    
        if (sch.is_draft or False) == False:
            if sch.jenis_bayar in [JenisBayarEnum.DP, JenisBayarEnum.LUNAS, JenisBayarEnum.PELUNASAN]:
                status_pembebasan = jenis_bayar_to_termin_status_pembebasan_dict.get(sch.jenis_bayar, None)
                await BidangHelper().update_status_pembebasan(list_bidang_id=[inv.bidang_id for inv in sch.invoices], status_pembebasan=status_pembebasan, db_session=db_session)
        
            # CREATE WORKFLOW
            if new_obj.jenis_bayar not in [JenisBayarEnum.UTJ_KHUSUS, JenisBayarEnum.UTJ]:
                flow = await crud.workflow_template.get_by_entity(entity=WorkflowEntityEnum.TERMIN)
                wf_sch = WorkflowCreateSch(reference_id=new_obj.id, entity=WorkflowEntityEnum.TERMIN, flow_id=flow.flow_id, version=1, last_status=WorkflowLastStatusEnum.ISSUED, step_name="ISSUED")
                await crud.workflow.create(obj_in=wf_sch, created_by_id=new_obj.created_by_id, db_session=db_session, with_commit=False)

        # REMOVE BIDANG KOMPONEN BIAYA YANG TERPILIH FLAG IS_DELETE PADA INVOICE DETAIL
        current_ids_bidang_komponen_biaya = [r.bidang_komponen_biaya_id for invoice in sch.invoices for r in invoice.details if r.bidang_komponen_biaya_id is not None and r.is_deleted]
        for bkb in current_ids_bidang_komponen_biaya:
            await crud.bidang_komponen_biaya.remove(id=bkb, db_session=db_session, with_commit=False)       
        
        try:
            await db_session.commit()
            await db_session.refresh(new_obj)

            # CREATE TASK WORKFLOW SERVICE
            if (sch.is_draft or False) == False and new_obj.jenis_bayar not in [JenisBayarEnum.UTJ_KHUSUS, JenisBayarEnum.UTJ]:
                GCloudTaskService().create_task(payload={"id":str(new_obj.id)}, base_url=f'{request.base_url}landrope/termin/task-workflow')

        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e.args))
        
        return new_obj
    
    #EDIT TERMIN, INVOICE, INVOICE DETAIL, INVOICE BAYAR, TERMIN BAYAR
    async def edit_termin(self, obj_current:Termin, sch: TerminUpdateSch, db_session:AsyncSession, current_worker:Worker, request:Request):
            
        # POPULATE SEMUA ID UNTUK KEPERLUAN DELETE DI AKHIR FUNGSI
        current_ids_invoice = await crud.invoice.get_ids_by_termin_id(termin_id=obj_current.id)
        current_ids_invoice_dt = await crud.invoice_detail.get_ids_by_invoice_ids(list_ids=current_ids_invoice)
        current_ids_invoice_byr = await crud.invoice_bayar.get_ids_by_invoice_ids(list_ids=current_ids_invoice)
        current_ids_termin_byr = await crud.termin_bayar.get_ids_by_termin_id(termin_id=obj_current.id)
        current_ids_termin_byr_dt = await crud.termin_bayar_dt.get_ids_by_termin_bayar_ids(list_ids=current_ids_termin_byr)

        # REMOVE BIDANG KOMPONEN BIAYA YANG TERPILIH FLAG IS_DELETE PADA INVOICE DETAIL
        current_ids_bidang_komponen_biaya = [r.bidang_komponen_biaya_id for invoice in sch.invoices for r in invoice.details if r.bidang_komponen_biaya_id is not None and r.is_deleted]
        
        sch.is_void = obj_current.is_void

        today = date.today()
        month = roman.toRoman(today.month)
        year = today.year
        jns_byr:str = ""

        jns_byr = jenis_bayar_to_text.get(sch.jenis_bayar, sch.jenis_bayar)

        if sch.file:
            gn_id = uuid4().hex
            file_name=f"MEMO PEMBAYARAN-{sch.nomor_memo.replace('/', '_').replace('.', '')}-{obj_current.code.replace('/', '_')}-{gn_id}"
            try:
                file_upload_path = await BundleHelper().upload_to_storage_from_base64(base64_str=sch.file, file_name=file_name)
            except ZeroDivisionError as e:
                raise HTTPException(status_code=422, detail="Failed upload dokumen Memo Pembayaran")
            
            sch.file_upload_path = file_upload_path
            
        
        obj_updated = await crud.termin.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

        # ADD & EDIT TERMIN BAYAR 
        termin_bayar_temp = []
        for termin_bayar in sch.termin_bayars:
            termin_bayar_current = await crud.termin_bayar.get(id=termin_bayar.id)
            # EDIT
            if termin_bayar_current:
                termin_bayar_updated = TerminBayarUpdateSch(**termin_bayar.dict(), termin_id=obj_updated.id)
                obj_termin_bayar = await crud.termin_bayar.update(obj_current=termin_bayar_current, obj_new=termin_bayar_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)
                current_ids_termin_byr.remove(obj_termin_bayar.id)

                # ADD & EDIT TERMIN BAYAR DETAIL
                if termin_bayar.termin_bayar_dts:
                    for termin_bayar_dt in termin_bayar.termin_bayar_dts:
                        termin_bayar_dt_current = await crud.termin_bayar_dt.get(id=termin_bayar_dt.id)
                        if termin_bayar_dt_current:
                            termin_bayar_dt_updated_sch = TerminBayarDtUpdateSch(**termin_bayar_dt.dict(), termin_bayar_id=obj_termin_bayar.id)
                            await crud.termin_bayar_dt.update(obj_current=termin_bayar_dt_current, obj_new=termin_bayar_dt_updated_sch, db_session=db_session, with_commit=False)
                            current_ids_termin_byr_dt.remove(termin_bayar_dt_current.id)
                        else:
                            termin_bayar_dt_sch = TerminBayarDtCreateSch(**termin_bayar_dt.dict(), termin_bayar_id=obj_termin_bayar.id)
                            await crud.termin_bayar_dt.create(obj_in=termin_bayar_dt_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)
            # ADD
            else:
                termin_bayar_sch = TerminBayarCreateSch(**termin_bayar.dict(), termin_id=obj_updated.id)
                obj_termin_bayar = await crud.termin_bayar.create(obj_in=termin_bayar_sch,  db_session=db_session, with_commit=False, created_by_id=current_worker.id)
                
                # ADD TERMIN BAYAR DETAIL
                if termin_bayar.termin_bayar_dts:
                    for termin_bayar_dt in termin_bayar.termin_bayar_dts:
                        termin_bayar_dt_sch = TerminBayarDtCreateSch(**termin_bayar_dt.dict(), termin_bayar_id=obj_termin_bayar.id)
                        await crud.termin_bayar_dt.create(obj_in=termin_bayar_dt_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)
        
            termin_bayar_temp.append({"termin_bayar_id" : obj_termin_bayar.id, "id_index" : termin_bayar.id_index})

        # ADD & EDIT INVOICE
        for invoice in sch.invoices:
            
            # POPULATE DATA MASTER BEBAN BIAYA PERSIAPAN UNTUK MANIPULASI DATA INVOICE DETAIL
            master_beban_biayas = await crud.bebanbiaya.get_by_ids(list_ids=[bb.beban_biaya_id for bb in invoice.details if bb.beban_biaya_id is not None and bb.is_deleted != True])
            
            invoice_current = await crud.invoice.get_by_id(id=invoice.id)

            # EDIT
            if invoice_current:
                invoice_updated_sch = InvoiceUpdateSch(**invoice.dict())
                invoice_updated_sch.is_void = invoice_current.is_void
                # KALAU UTJ AMBIL AMOUNT NETTONYA DARI AMOUNT
                invoice_updated_sch.amount_netto = invoice.amount if sch.jenis_bayar in (JenisBayarEnum.UTJ, JenisBayarEnum.UTJ_KHUSUS) else invoice.amount_netto
                invoice_updated = await crud.invoice.update(obj_current=invoice_current, obj_new=invoice_updated_sch, with_commit=False, db_session=db_session, updated_by_id=current_worker.id)
                current_ids_invoice.remove(invoice_current.id)

                # ADD & EDIT INVOICE DETAIL
                for dt in invoice.details:

                    # LEWATI KOMPONEN BIAYA YANG INGIN DIHAPUS (EKSEKUSI DARI INVOICE DETAIL)
                    if dt.is_deleted:
                        continue
                    
                    # CEK APAKAH AMOUNT BEBAN BIAYA TIDAK SAMA DENGAN 0
                    if dt.amount == 0 and (sch.is_draft or False) == False:
                        bidang = await crud.bidang.get(id=invoice.bidang_id)
                        master_beban_biaya = next((bb for bb in master_beban_biayas if bb.id == dt.beban_biaya_id), None)
                        raise HTTPException(status_code=422, detail=f"Amount beban biaya {master_beban_biaya.name} pada bidang {bidang.id_bidang} masih 0, cek kembali beban biaya")
                    
                    invoice_dtl_current = await crud.invoice_detail.get(id=dt.id)
                    bidang_komponen_biaya_current = await crud.bidang_komponen_biaya.get(id=dt.bidang_komponen_biaya_id)

                    if invoice_dtl_current is None:
                        ## START KOMPONEN BIAYA
                        # ADD KOMPONEN BIAYA BARU JIKA USER MENAMBAHKAN KOMPONEN BIAYA YANG TIDAK ADA DI MASTER BIDANG KOMPONEN BIAYA
                        if bidang_komponen_biaya_current is None:

                            # VALIDASI BEBAN BIAYA YANG TERADD KEMBALI BERDASARKAN BEBAN BIAYA ID DAN BIDANG ID (TIDAK BOLEH ADA DOUBLE BEBAN BIAYA YANG SAMA)
                            bkb_has_exists = await crud.bidang_komponen_biaya.get_by_bidang_id_and_beban_biaya_id(bidang_id=invoice.bidang_id, beban_biaya_id=dt.beban_biaya_id)
                            if bkb_has_exists:
                                bidang_err = await crud.bidang.get(id=invoice.bidang_id)
                                raise HTTPException(status_code=422, detail=f"""Anda memasukkan beban biaya baru '{bkb_has_exists.beban_biaya_name}' 
                                                    pada bidang {bidang_err.id_bidang}. Mohon cek kembali apakah beban tersebut sudah pernah ada pada Memo sebelumnya.""")
                            
                            master_beban_biaya = next((bb for bb in master_beban_biayas if bb.id == dt.beban_biaya_id), None)
                            if master_beban_biaya is None:
                                raise HTTPException(status_code=404, detail="Beban Biaya not found in master!")

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
                            
                            # SIMPAN ID KOMPONEN BIAYA UNTUK INVOICE DETAIL
                            dt.bidang_komponen_biaya_id = obj_bidang_komponen_biaya.id

                        # EDIT KOMPONEN BIAYA
                        else:
                            bidang_komponen_biaya_new = BidangKomponenBiayaUpdateSch.from_orm(bidang_komponen_biaya_current)
                            bidang_komponen_biaya_new.amount = dt.komponen_biaya_amount
                            bidang_komponen_biaya_new.satuan_bayar = dt.satuan_bayar
                            bidang_komponen_biaya_new.satuan_harga = dt.satuan_harga
                            bidang_komponen_biaya_new.beban_biaya_id = dt.beban_biaya_id
                            bidang_komponen_biaya_new.beban_pembeli = dt.beban_pembeli
                            bidang_komponen_biaya_new.estimated_amount = dt.amount

                            bidang_komponen_biaya_current = await crud.bidang_komponen_biaya.update(obj_current=bidang_komponen_biaya_current, obj_new=bidang_komponen_biaya_new, db_session=db_session, with_commit=False, updated_by_id=current_worker.id)
                            dt.bidang_komponen_biaya_id = bidang_komponen_biaya_current.id
                        ## END KOMPONEN BIAYA

                        # ADD INVOICE DETAIL
                        invoice_dtl_sch = InvoiceDetailCreateSch(**dt.dict(), invoice_id=invoice.id)
                        await crud.invoice_detail.create(obj_in=invoice_dtl_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)
                    else:
                        ## START KOMPONEN BIAYA
                        # EDIT KOMPONEN BIAYA
                        bidang_komponen_biaya_new = BidangKomponenBiayaUpdateSch.from_orm(bidang_komponen_biaya_current)
                        bidang_komponen_biaya_new.amount = dt.komponen_biaya_amount
                        bidang_komponen_biaya_new.satuan_bayar = dt.satuan_bayar
                        bidang_komponen_biaya_new.satuan_harga = dt.satuan_harga
                        bidang_komponen_biaya_new.beban_biaya_id = dt.beban_biaya_id
                        bidang_komponen_biaya_new.beban_pembeli = dt.beban_pembeli
                        bidang_komponen_biaya_new.estimated_amount = dt.amount

                        bidang_komponen_biaya_current = await crud.bidang_komponen_biaya.update(obj_current=bidang_komponen_biaya_current, obj_new=bidang_komponen_biaya_new, db_session=db_session, with_commit=False, updated_by_id=current_worker.id)
                        dt.bidang_komponen_biaya_id = bidang_komponen_biaya_current.id
                        ## END KOMPONEN BIAYA

                        # EDIT INVOICE DETAIL
                        invoice_dtl_updated_sch = InvoiceDetailUpdateSch(**dt.dict(), invoice_id=invoice_updated.id)
                        await crud.invoice_detail.update(obj_current=invoice_dtl_current, obj_new=invoice_dtl_updated_sch, db_session=db_session, with_commit=False)
                        current_ids_invoice_dt.remove(invoice_dtl_current.id)

                # ADD & EDIT INVOICE BAYAR
                for dt_bayar in invoice.bayars:
                    termin_bayar_id = next((termin_bayar["termin_bayar_id"] for termin_bayar in termin_bayar_temp if termin_bayar["id_index"] == dt_bayar.id_index), None)
                    invoice_bayar_current = await crud.invoice_bayar.get(id=dt_bayar.id)

                    if invoice_bayar_current is None:
                        invoice_bayar_new = InvoiceBayarCreateSch(termin_bayar_id=termin_bayar_id, invoice_id=invoice.id, amount=dt_bayar.amount)
                        await crud.invoice_bayar.create(obj_in=invoice_bayar_new, db_session=db_session, with_commit=False, created_by_id=current_worker.id)
                    else:
                        invoice_bayar_updated = InvoiceBayarlUpdateSch.from_orm(invoice_bayar_current)
                        invoice_bayar_updated.termin_bayar_id = termin_bayar_id
                        invoice_bayar_updated.amount = dt_bayar.amount
                        await crud.invoice_bayar.update(obj_current=invoice_bayar_current, obj_new=invoice_bayar_updated, db_session=db_session, with_commit=False, updated_by_id=current_worker.id)
                        current_ids_invoice_byr.remove(invoice_bayar_current.id)
            # ADD
            else:
                last_number = await generate_code_month(entity=CodeCounterEnum.Invoice, with_commit=False, db_session=db_session)
                invoice_sch = InvoiceCreateSch(**invoice.dict(), 
                                                termin_id=obj_updated.id, 
                                                code=f"INV/{last_number}/{jns_byr}/LA/{month}/{year}", 
                                                is_void=False
                                            )
                
                # KALAU UTJ AMBIL AMOUNT NETTONYA DARI AMOUNT
                invoice_sch.amount_netto = invoice.amount if sch.jenis_bayar in (JenisBayarEnum.UTJ, JenisBayarEnum.UTJ_KHUSUS) else invoice.amount_netto
                
                new_obj_invoice = await crud.invoice.create(obj_in=invoice_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)

                # ADD INVOICE DETAIL
                for dt in invoice.details:

                    # LEWATI KOMPONEN BIAYA YANG INGIN DIHAPUS (EKSEKUSI DARI INVOICE DETAIL)
                    if dt.is_deleted:
                        continue
                    
                    # CEK APAKAH AMOUNT BEBAN BIAYA TIDAK SAMA DENGAN 0
                    if dt.amount == 0 and (sch.is_draft or False) == False :
                        bidang = await crud.bidang.get(id=invoice.bidang_id)
                        master_beban_biaya = next((bb for bb in master_beban_biayas if bb.id == dt.beban_biaya_id), None)
                        raise HTTPException(status_code=422, detail=f"Amount beban biaya {master_beban_biaya.name} pada bidang {bidang.id_bidang} masih 0, cek kembali beban biaya")
                    
                    bidang_komponen_biaya_current = await crud.bidang_komponen_biaya.get(id=dt.bidang_komponen_biaya_id) 

                    if bidang_komponen_biaya_current is None:
                        
                        # VALIDASI BEBAN BIAYA YANG TERADD KEMBALI BERDASARKAN BEBAN BIAYA ID DAN BIDANG ID (TIDAK BOLEH ADA DOUBLE BEBAN BIAYA YANG SAMA)
                        bkb_has_exists = await crud.bidang_komponen_biaya.get_by_bidang_id_and_beban_biaya_id(bidang_id=invoice.bidang_id, beban_biaya_id=dt.beban_biaya_id)
                        if bkb_has_exists:
                            bidang_err = await crud.bidang.get(id=invoice.bidang_id)
                            raise HTTPException(status_code=422, detail=f"""Anda memasukkan beban biaya baru '{bkb_has_exists.beban_biaya_name}' 
                                                pada bidang {bidang_err.id_bidang}. Mohon cek kembali apakah beban tersebut sudah pernah ada pada Memo sebelumnya.""")

                        master_beban_biaya = next((bb for bb in master_beban_biayas if bb.id == dt.beban_biaya_id), None)
                        if master_beban_biaya is None:
                            raise HTTPException(status_code=404, detail="Beban Biaya not found in Master!")
                        
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
                        
                        # SIMPAN ID KOMPONEN BIAYA UNTUK INVOICE DETAIL
                        dt.bidang_komponen_biaya_id = obj_bidang_komponen_biaya.id

                    # UPDATE KOMPONEN BIAYA DI MASTER JIKA KOMPONEN BIAYA EXISTS SESUAI DENGAN INPUTAN USER
                    else:
                        bidang_komponen_biaya_new = BidangKomponenBiayaUpdateSch.from_orm(bidang_komponen_biaya_current)
                        bidang_komponen_biaya_new.amount = dt.komponen_biaya_amount
                        bidang_komponen_biaya_new.satuan_bayar = dt.satuan_bayar
                        bidang_komponen_biaya_new.satuan_harga = dt.satuan_harga
                        bidang_komponen_biaya_new.beban_biaya_id = dt.beban_biaya_id
                        bidang_komponen_biaya_new.beban_pembeli = dt.beban_pembeli
                        bidang_komponen_biaya_new.estimated_amount = dt.amount

                        bidang_komponen_biaya_current = await crud.bidang_komponen_biaya.update(obj_current=bidang_komponen_biaya_current, obj_new=bidang_komponen_biaya_new, db_session=db_session, with_commit=False, updated_by_id=current_worker.id)
                        
                        # SIMPAN ID KOMPONEN BIAYA UNTUK INVOICE DETAIL
                        dt.bidang_komponen_biaya_id = bidang_komponen_biaya_current.id

                    invoice_dtl_sch = InvoiceDetailCreateSch(**dt.dict(), invoice_id=new_obj_invoice.id)
                    await crud.invoice_detail.create(obj_in=invoice_dtl_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)

                # ADD INVOICE BAYAR
                for dt_bayar in invoice.bayars:
                    termin_bayar_id = next((termin_bayar["termin_bayar_id"] for termin_bayar in termin_bayar_temp if termin_bayar["id_index"] == dt_bayar.id_index), None)
                    invoice_bayar_new = InvoiceBayarCreateSch(termin_bayar_id=termin_bayar_id, invoice_id=new_obj_invoice.id, amount=dt_bayar.amount)
                    await crud.invoice_bayar.create(obj_in=invoice_bayar_new, db_session=db_session, with_commit=False, created_by_id=current_worker.id)

        ## DELETED DATA BY ID
        for idt in current_ids_invoice_dt:
            await crud.invoice_detail.remove(id=idt, db_session=db_session, with_commit=False)
        
        for iby in current_ids_invoice_byr:
            await crud.invoice_bayar.remove(id=iby, db_session=db_session, with_commit=False)

        for inv in current_ids_invoice:
            await crud.invoice.remove(id=inv, db_session=db_session, with_commit=False)

        for trb_dt in current_ids_termin_byr_dt:
            await crud.termin_bayar_dt.remove(id=trb_dt, db_session=db_session, with_commit=False)

        for trb in current_ids_termin_byr:
            await crud.termin_bayar.remove(id=trb, db_session=db_session, with_commit=False)

        for bkb in current_ids_bidang_komponen_biaya:
            await crud.bidang_komponen_biaya.remove(id=bkb, db_session=db_session, with_commit=False)
        ## END DELETED DATA BY ID

        # UPDATE STATUS PEMBEBASAN PADA BIDANG SEKALIGUS MENJALANKAN WORKFLOW JIKA MEMO BUKAN DRAFT   
        if (sch.is_draft or False) == False:
            if sch.jenis_bayar in [JenisBayarEnum.DP, JenisBayarEnum.LUNAS, JenisBayarEnum.PELUNASAN]:
                status_pembebasan = jenis_bayar_to_termin_status_pembebasan_dict.get(sch.jenis_bayar, None)
                await BidangHelper().update_status_pembebasan(list_bidang_id=[inv.bidang_id for inv in sch.invoices], status_pembebasan=status_pembebasan, db_session=db_session)
        
            # WORKFLOW
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
        
        try:
            await db_session.commit()
            await db_session.refresh(obj_updated)
            
            # CREATE TASK WORKFLOW SERVICE
            if (sch.is_draft or False) == False and obj_updated.jenis_bayar not in [JenisBayarEnum.UTJ_KHUSUS, JenisBayarEnum.UTJ]:
                GCloudTaskService().create_task(payload={"id":str(obj_updated.id)}, base_url=f'{request.base_url}landrope/termin/task-workflow')

        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e.args))
        
        return obj_updated

    # UPDATE NOMOR MEMO DAN UPLOAD FILE MEMO ASSIGN
    async def update_nomor_memo_dan_file(self, sch:TerminUpdateSch, obj_current:Termin, worker_id:UUID, request:Request) -> Termin:

        db_session = db.session
        if sch.file:
            gn_id = uuid4().hex
            file_name=f"MEMO PEMBAYARAN-{sch.nomor_memo.replace('/', '_').replace('.', '')}-{obj_current.code.replace('/', '_')}-{gn_id}"
            try:
                file_upload_path = await BundleHelper().upload_to_storage_from_base64(base64_str=sch.file, file_name=file_name)
            except ZeroDivisionError as e:
                raise HTTPException(status_code=422, detail="Failed upload dokumen Memo Pembayaran")
            
            sch.file_upload_path = file_upload_path

        obj_updated = TerminUpdateSch(**obj_current.dict())
        obj_updated.nomor_memo = sch.nomor_memo
        obj_updated.file_upload_path = sch.file_upload_path
            
        obj_updated = await crud.termin.update(obj_current=obj_current, obj_new=obj_updated, updated_by_id=worker_id, db_session=db_session, with_commit=False)

        await self.send_workflow(reference_id=obj_updated.id, worker_id=worker_id, request=request, db_session=db_session)

        await db_session.commit()
        await db_session.refresh(obj_updated)

        # CREATE TASK WORKFLOW SERVICE
        GCloudTaskService().create_task(payload={"id":str(obj_updated.id)}, base_url=f'{request.base_url}landrope/termin/task-workflow')

        return obj_updated

    # SEND WORKFLOW
    async def send_workflow(self, reference_id:UUID, worker_id:UUID, request:Request, db_session):
        wf_current = await crud.workflow.get_by_reference_id(reference_id=reference_id)
        if wf_current:
            if wf_current.last_status not in [WorkflowLastStatusEnum.REJECTED, WorkflowLastStatusEnum.NEED_DATA_UPDATE]:
                raise HTTPException(status_code=422, detail="Failed update termin. Detail : Workflow is running")

            wf_updated = WorkflowUpdateSch(**wf_current.dict(exclude={"last_status", "step_name"}), last_status=WorkflowLastStatusEnum.ISSUED, step_name="ISSUED" if WorkflowLastStatusEnum.REJECTED else "On Progress Update Data")
            if wf_updated.version is None:
                wf_updated.version = 1
                
            await crud.workflow.update(obj_current=wf_current, obj_new=wf_updated, updated_by_id=worker_id, db_session=db_session, with_commit=False)
        else:
            flow = await crud.workflow_template.get_by_entity(entity=WorkflowEntityEnum.TERMIN)
            wf_sch = WorkflowCreateSch(reference_id=reference_id, entity=WorkflowEntityEnum.TERMIN, flow_id=flow.flow_id, version=1, last_status=WorkflowLastStatusEnum.ISSUED, step_name="ISSUED")
            
            await crud.workflow.create(obj_in=wf_sch, created_by_id=worker_id, db_session=db_session, with_commit=False)

    # GET BY ID SPK YANG INGIN DIBUAT MEMONYA
    async def get_spk_by_id(self, spk_id:UUID) -> SpkInTerminSch:

        obj = await crud.spk.get_by_id_in_termin(id=spk_id)

        if obj is None:
            raise HTTPException(status_code=404, detail="SPK not Found!")

        workflow = await crud.workflow.get_by_reference_id(reference_id=obj.id)
        if workflow is None:
            raise HTTPException(status_code=404, detail="Workflow not found")

        if workflow.last_status != WorkflowLastStatusEnum.COMPLETED:
            raise HTTPException(status_code=422, detail=f"SPK {obj.code} must completed approval")

        spk = SpkInTerminSch(spk_id=obj.id, 
                            spk_code=obj.code, 
                            spk_amount=obj.amount, 
                            spk_satuan_bayar=obj.satuan_bayar,
                            bidang_id=obj.bidang_id, 
                            id_bidang=obj.id_bidang, 
                            alashak=obj.alashak, 
                            group=obj.bidang.group,
                            luas_bayar=obj.bidang.luas_bayar, 
                            # harga_transaksi=obj.bidang.harga_transaksi if (obj.bidang.is_ptsl or False) == False else obj.bidang.harga_ptsl, 
                            harga_transaksi=obj.bidang.harga_transaksi, 
                            harga_akta=obj.bidang.harga_akta, 
                            amount=round(obj.spk_amount, 0), 
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
        elif obj.jenis_bayar == JenisBayarEnum.PELUNASAN:
            # beban_penjual_on_exists_invoice = await crud.invoice_detail.get_multi_beban_penjual_has_use_and_not_paid_by_bidang_id(bidang_id=obj.bidang_id)
            # beban_penjual_amount: Decimal = sum([beban.amount for beban in beban_penjual_on_exists_invoice]) or 0
            bidang = await crud.bidang.get_by_id(id=obj.bidang_id)
            if bidang.utj_has_use:
                spk.amount = bidang.sisa_pelunasan
            else:
                spk.amount = bidang.sisa_pelunasan + bidang.utj_amount

        return spk
    
    # VOID TERMIN
    async def void(self, sch:TerminVoidSch, obj_current:Termin, db_session:AsyncSession, current_worker:Worker):
        
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

        return obj_updated

    # TASK WORKFLOW
    async def task_workflow(self, obj: Termin, request):
        wf_current = await crud.workflow.get_by_reference_id(reference_id=obj.id)
        if not wf_current:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        trying:int = 0
        while obj.file_path is None:
            await TerminService().generate_printout_memo_bayar(id=obj.id)
            if trying > 7:
                raise HTTPException(status_code=404, detail="File not found")
            obj = await crud.termin.get(id=obj.id)
            time.sleep(2)
            trying += 1
        
        public_url = await encrypt_id(id=str(obj.id), request=request)
        wf_system_attachment = WorkflowSystemAttachmentSch(name=obj.code, url=f"{public_url}?en={WorkflowEntityEnum.TERMIN.value}")
        wf_system_sch = WorkflowSystemCreateSch(client_ref_no=str(obj.id), 
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
            logging.error(msg=f"Termin {obj.code} Failed to connect workflow system. Detail : {msg}")
            raise HTTPException(status_code=422, detail=f"Failed to connect workflow system. Detail : {msg}")
        
        wf_updated = WorkflowUpdateSch(**wf_current.dict(exclude={"last_status"}), last_status=response.last_status)
        
        await crud.workflow.update(obj_current=wf_current, obj_new=wf_updated, updated_by_id=obj.updated_by_id)

    # FILTER KOMPONEN BIAYA
    async def make_sure_all_komponen_biaya_not_outstanding(self, sch: TerminCreateSch):
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

    # GENERATE PRINTOUT UTJ
    async def generate_printout_utj(self, id:UUID | str):
     
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

        array_total_luas_surat = [b.luas_surat for b in invoices]
        total_luas_surat = sum(array_total_luas_surat)
        total_luas_surat = "{:,.0f}".format(total_luas_surat)

        array_total_amount = [b.amount for b in invoices]
        total_amount = sum(array_total_amount)
        total_amount = "{:,.0f}".format(total_amount)

        filename:str = "utj.html" if termin_header.jenis_bayar == "UTJ" else "utj_khusus.html"
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template(filename)

        render_template = template.render(code=termin_header.code,
                                        kjb_code=termin_header.kjb_code,
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
    
    async def generate_printout(self, id:UUID | str):
        obj = await crud.termin.get_by_id_for_printout(id=id)
        if obj is None:
            raise IdNotFoundException(Termin, id)
        
        termin_header = TerminByIdForPrintOut(**dict(obj))

        # MENGUBAH TANGGAL TRANSAKSI DAN CREATED DATE MENJADI FORMAT INDONESIA SESUAI DENGAN FORMAT USER
        tanggal_transaksi = (termin_header.tanggal_transaksi or date.today()).strftime("%d-%m-%Y")
        bulan_created_en = termin_header.created_at.strftime('%B')
        bulan_created_id = self.bulan_dict.get(bulan_created_en, bulan_created_en)
        created_at = termin_header.created_at.strftime(f'%d {bulan_created_id} %Y')

        nama_bulan_inggris = (termin_header.tanggal_rencana_transaksi or date.today()).strftime('%B')  # Mendapatkan nama bulan dalam bahasa Inggris
        nama_bulan_indonesia = self.bulan_dict.get(nama_bulan_inggris, nama_bulan_inggris)  # Mengonversi ke bahasa Indonesia
        tanggal_hasil = termin_header.tanggal_rencana_transaksi.strftime(f'%d {nama_bulan_indonesia} %Y')
        day_of_week = termin_header.tanggal_rencana_transaksi.strftime("%A")
        hari_transaksi:str|None = HelperService().ToDayName(day_of_week)

        remarks = (termin_header.remark or '').splitlines()
        # PERHITUNGAN UTJ (jika invoice dlm termin dikurangi utj) & data invoice di termin yg akan di printout
        # amount_utj_used = []
        termin_invoices:list[InvoiceForPrintOutExt] = []
        obj_invoices = await crud.invoice.get_invoice_by_termin_id_for_printout(termin_id=id)
        for inv in obj_invoices:
            iv = InvoiceForPrintOutExt(**dict(inv))
            # invoice_curr = await crud.invoice.get_utj_amount_by_id(id=iv.id)
            # amount_utj_used.append(invoice_curr.utj_amount)
            termin_invoices.append(iv)
        
        # amount_utj = sum(amount_utj_used) or 0

        # LIST BIDANG DALAM SATU TAHAP
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
                            metadata_dict = json.loads(nib_perorangan_meta_data.meta_data)
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

        # HISTORY TERMIN, BEBAN BIAYA
        termin_histories = []
        current_termin_histories = await crud.termin.get_multi_by_bidang_ids(bidang_ids=list_bidang_id, current_termin_id=id, jenis_bayar_current=obj.jenis_bayar)
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

            history_komponen_biayas = []
            obj_history_komponen_biayas = await crud.termin.get_beban_biaya_by_id_for_printout(id=termin.id, jenis_bayar=termin.jenis_bayar, is_history=True)
            for bb in obj_history_komponen_biayas:
                beban_biaya = TerminBebanBiayaForPrintOut(**dict(bb))
                beban_biaya.beban_biaya_name = f"{beban_biaya.beban_biaya_name} {beban_biaya.tanggungan}"
                beban_biaya.amountExt = "{:,.0f}".format(beban_biaya.amount)
                history_komponen_biayas.append(beban_biaya)

            termin_history.beban_biayas = history_komponen_biayas
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

        # KOMPONEN BIAYA TERMIN CURRENT
        komponen_biayas = []
        obj_komponen_biayas = await crud.termin.get_beban_biaya_by_id_for_printout(id=termin_header.id, jenis_bayar=termin_header.jenis_bayar)
        for bb in obj_komponen_biayas:
            beban_biaya = TerminBebanBiayaForPrintOut(**dict(bb))
            beban_biaya.beban_biaya_name = f"{beban_biaya.beban_biaya_name} {beban_biaya.tanggungan}"
            beban_biaya.amountExt = "{:,.0f}".format(beban_biaya.amount)
            komponen_biayas.append(beban_biaya)

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
                                        amount="{:,.0f}".format(((termin_header.amount_netto))),
                                        remarks=remarks
                                        )
        
        try:
            doc = await PdfService().get_pdf(render_template)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed generate document")
        
        return doc

    # GENERATE PRINTOUT MEMO BAYAR
    async def generate_printout_memo_bayar(self, id:UUID | str):

        doc = await self.generate_printout(id=id)
        
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

    # GENERATE PRINTOUT MEMO BAYAR TO EXCEL
    async def generate_printout_to_excel(self, id:UUID | str):

        doc = await self.generate_printout(id=id)
        excel = await PDFToExcelService().export_pdf_to_excel(data=doc)

        return excel

    # GENERATE TERMIN TO HTML CONTENT UNTUK GENERATE JADI EXCEL
    async def generate_html_content(self, list_tahap_detail:list[TahapDetailForExcel], overlap_exists:bool|None = False, tanggal:str|None = '') -> str | None:
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
    
    # MERGE MEMO YANG TELAH DITANDATANGANI KE BUNDLE
    async def merge_memo_signed(self, id:UUID | str):
        db_session = db.session
        termin = await crud.termin.get(id=id)
        details = await crud.invoice.get_multi_by_termin_id(termin_id=id)

        for detail in details:
            bidang = await crud.bidang.get(id=detail.bidang_id)
            bundle = await crud.bundlehd.get_by_id(id=bidang.bundle_hd_id)
            if bundle:
                await BundleHelper().merge_memo_signed(bundle=bundle, code=f"{termin.code}-{str(termin.updated_at.date())}", tanggal=termin.updated_at.date(), file_path=termin.file_upload_path, worker_id=termin.updated_by_id, db_session=db_session)
        
        await db_session.commit()

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
