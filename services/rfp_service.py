import crud
import requests
from uuid import UUID, uuid4
from datetime import date, datetime, timedelta
from fastapi import HTTPException, status
from fastapi_async_sqlalchemy import db
from common.exceptions import IdNotFoundException
from schemas.termin_sch import TerminUpdateBaseSch
from schemas.rfp_sch import RfpHeadNotificationSch
from schemas.invoice_sch import InvoiceUpdateSch
from schemas.invoice_detail_sch import InvoiceDetailUpdateSch
from schemas.payment_sch import PaymentCreateSch
from schemas.payment_detail_sch import PaymentDetailExtSch, PaymentDetailUpdateSch, PaymentDetailCreateSch
from schemas.payment_giro_detail_sch import PaymentGiroDetailExtSch, PaymentGiroDetailCreateSch
from schemas.payment_komponen_biaya_detail_sch import PaymentKomponenBiayaDetailExtSch, PaymentKomponenBiayaDetailCreateSch
from schemas.termin_bayar_sch import TerminBayarUpdateSch
from schemas.giro_sch import GiroCreateSch, GiroUpdateSch
from schemas.bidang_komponen_biaya_sch import BidangKomponenBiayaUpdateSch
from services.payment_service import PaymentService
from common.enum import PaymentMethodEnum, ActivityEnum, SatuanBayarEnum, activity_landrope_to_activity_rfp_dict
from common.generator import generate_code
from models.code_counter_model import CodeCounterEnum
from configs.config import settings

class RfpService:

    RFP_BASE_URL = settings.RFP_BASE_URL
    RFP_CLIENT_ID = settings.RFP_CLIENT_ID
    OAUTH2_TOKEN = settings.OAUTH2_TOKEN
    CONNECTION_FAILED = "Cannot create connection to authentication server."

    # INISIASI MODEL DATA RFP MENYESUAIKAN DATA DARI MEMO BAYAR (TERMIN)
    # DIPANGGIL PADA FUNCTION "create_rfp"
    async def init_rfp(self, termin_id:UUID):

        termin = await crud.termin.get(id=termin_id)
        if termin is None:
            raise IdNotFoundException(model=crud.termin.model, id=termin_id)
        
        workflow = await crud.workflow.get_by_reference_id(reference_id=termin.id)
        if workflow is None:
            raise IdNotFoundException(model=crud.workflow.model, id=termin_id)
        
        tahap = await crud.tahap.get(id=termin.tahap_id)
        if tahap is None:
            raise IdNotFoundException(model=crud.tahap.model, id=termin.tahap_id)
        
        ptsk = await crud.ptsk.get(id=tahap.ptsk_id)
        if ptsk is None:
            raise IdNotFoundException(model=crud.ptsk.model, id=tahap.ptsk_id)
    
        # INIT RFP HEADER
        rfp_hd_id = uuid4()
        obj_rfp_hd = {}
        obj_rfp_hd["id"] = str(rfp_hd_id)
        obj_rfp_hd["client_id"] = self.RFP_CLIENT_ID
        obj_rfp_hd["client_ref_no"] = str(termin.id)
        obj_rfp_hd["created_by_outh_id"] = "42b8cb0e-7e78-4728-a89b-493dfc5e4fd1"
        obj_rfp_hd["grace_period"] = str(self.add_days(n=7,d=workflow.last_status_at).date())
        obj_rfp_hd["date_doc"] = str(workflow.last_status_at.date())
        obj_rfp_hd["document_type_code"] = "OPR-INT"
        obj_rfp_hd["company_code"] = ptsk.code
        obj_rfp_hd["company_name"] = ptsk.name
        obj_rfp_hd["ref_no"] = termin.nomor_memo

        ### SETUP PAY TO
        pay_to = []
        termin_bayars = await crud.termin_bayar.get_multi_by_termin_id(termin_id=termin.id)
        for termin_bayar in termin_bayars:
            p = f"{termin_bayar.pay_to or ''} ({float(termin_bayar.amount)})"

            pay_to.append(p)

        obj_rfp_hd["pay_to"] = ", ".join(pay_to)
        
        rfp_hd_descs = []

        obj_rfp_hd["rfp_lines"] = []
        obj_rfp_hd["rfp_banks"] = []
        obj_rfp_hd["rfp_allocations"] = []

        # SETUP FIRST DESC for RFP HEADER
        invoice_in_termin_histories = await crud.invoice.get_multi_invoice_id_luas_bayar_by_termin_id(termin_id=termin.id)
        count_bidang = len(invoice_in_termin_histories)
        sum_luas_surat = "{:,.0f}".format(sum([invoice_.luas_surat or 0 for invoice_ in invoice_in_termin_histories if invoice_.luas_surat is not None]))
        
        spk_of_amount = await crud.spk.get(id=next((inv_h.spk_id for inv_h in invoice_in_termin_histories), None))
        amount = f"{str(spk_of_amount.amount) + '%' if spk_of_amount.satuan_bayar == SatuanBayarEnum.Percentage else ''}"
            
        uraian = f"{termin.jenis_bayar} {amount} {count_bidang} Bidang, luas {sum_luas_surat}m2, GROUP {termin.group}"
        rfp_hd_descs.append(uraian)

        obj_rfp_hd["uraian"] = uraian

        # INIT RFP LINE, RFP BANK, RFP ALLOCATION
        for termin_bayar in termin_bayars:
            obj_rfp_line = {}
            obj_rfp_bank = {}
            obj_rfp_allocation = {}
            # if termin_bayar.payment_method == PaymentMethodEnum.Tunai:
            #     continue

            rfp_activity_code: str | None = None

            if termin_bayar.activity in [ActivityEnum.UTJ, ActivityEnum.BIAYA_TANAH]:
                rfp_activity_code = activity_landrope_to_activity_rfp_dict.get(termin_bayar.activity, None)
                
                # RFP LINE
                rfp_line_id = uuid4()
                obj_rfp_line["id"] = str(rfp_line_id)
                obj_rfp_line["activity_code"] = rfp_activity_code
                obj_rfp_line["amount"] = str(termin_bayar.amount)
                obj_rfp_line["descs"] = termin.nomor_memo
                obj_rfp_line["reff_no"] = str(termin_bayar.id)
                obj_rfp_line["pay_to"] = f"{termin_bayar.pay_to or ''} ({float(termin_bayar.amount)})"
                obj_rfp_line["rfp_line_dts"] = []
                obj_rfp_hd["rfp_lines"].append(obj_rfp_line)
                

                ## INIT RFP LINE DETAIL
                invoice_bayars = await crud.invoice_bayar.get_multi_by_termin_bayar_id(termin_bayar_id=termin_bayar.id)
                for inv_bayar in invoice_bayars:
                    obj_rfp_line_dt = {}
                    rfp_line_dt_id = uuid4()

                    invoice = await crud.invoice.get(id=inv_bayar.invoice_id)
                    if invoice.is_void:
                        continue

                    bidang = await crud.bidang.get(id=invoice.bidang_id)
                    spk = await crud.spk.get(id=invoice.spk_id)

                    id_bidang_complete = f'{bidang.id_bidang}' if bidang.id_bidang_lama is None else f'{bidang.id_bidang} ({bidang.id_bidang_lama})'

                    obj_rfp_line_dt["id"] = str(rfp_line_dt_id)
                    obj_rfp_line_dt["name"] = bidang.id_bidang
                    obj_rfp_line_dt["amount"] = str(float(inv_bayar.amount))
                    obj_rfp_line_dt["estimated_amount"] = str(float(inv_bayar.amount))

                    description: str = ""

                    if spk and termin_bayar.activity == ActivityEnum.BIAYA_TANAH:
                        amount = f"{str(spk.amount) + '%' if spk.satuan_bayar == SatuanBayarEnum.Percentage else ''}"
                        description = f"{id_bidang_complete} {spk.jenis_bayar} {amount}, GROUP {termin.tahap.group or ''}"
                        obj_rfp_line_dt["desc"] = description
                    else:
                        description = f"{id_bidang_complete} UTJ, GROUP {termin.tahap.group or ''}"
                        obj_rfp_line_dt["desc"] = description

                    if description not in rfp_hd_descs:
                        rfp_hd_descs.append(description)
                    
                    
                    obj_rfp_line["rfp_line_dts"].append(obj_rfp_line_dt)

                # RFP BANK
                rfp_bank_id = uuid4()
                obj_rfp_bank["id"] = str(rfp_bank_id)
                obj_rfp_bank["amount"] = str(termin_bayar.amount)
                obj_rfp_bank["date_doc"] = str(workflow.last_status_at.date())
                obj_rfp_bank["descs"] = str(termin_bayar.activity).replace("_", " ")
                obj_rfp_hd["rfp_banks"].append(obj_rfp_bank)

                # RFP ALLOCATION
                rfp_allocation_id = uuid4()
                obj_rfp_allocation["id"] = str(rfp_allocation_id)
                obj_rfp_allocation["amount"] = str(termin_bayar.amount)
                obj_rfp_allocation["rfp_head_id"] = str(rfp_hd_id)
                obj_rfp_allocation["rfp_bank_id"] = str(rfp_bank_id)
                obj_rfp_allocation["rfp_line_id"] = str(rfp_line_id)
                obj_rfp_hd["rfp_allocations"].append(obj_rfp_allocation)
            else:
                # RFP BANK
                rfp_bank_id = uuid4()
                obj_rfp_bank["id"] = str(rfp_bank_id)
                obj_rfp_bank["amount"] = str(termin_bayar.amount)
                obj_rfp_bank["date_doc"] = str(workflow.last_status_at.date())
                # obj_rfp_bank["descs"] = termin.nomor_memo [PINDAH KE BAWAH]
                obj_rfp_hd["rfp_banks"].append(obj_rfp_bank)

                #RFP LINE
                termin_bayar_dts = await crud.termin_bayar_dt.get_multi_by_termin_bayar_id(termin_bayar_id=termin_bayar.id)
                beban_biaya_names = []
                for termin_bayar_dt in termin_bayar_dts:
                    
                    beban_biaya = await crud.bebanbiaya.get(id=termin_bayar_dt.beban_biaya_id)
                    if beban_biaya is None:
                        raise IdNotFoundException(model=crud.bebanbiaya.model, id=termin_bayar_dt.beban_biaya_id)
                    
                    beban_biaya_names.append(beban_biaya.name)

                    invoice_details = await crud.invoice_detail.get_multi_by_termin_id_and_beban_biaya_id(termin_id=termin.id, beban_biaya_id=termin_bayar_dt.beban_biaya_id)
                    amount_beban = sum([inv_dt.amount for inv_dt in invoice_details])

                    if beban_biaya.activity_code is None:
                        raise HTTPException(status_code=422, detail=f"{beban_biaya.name} belum memiliki activity code")

                    rfp_activity_code = beban_biaya.activity_code
                    
                    rfp_line_id = uuid4()
                    obj_rfp_line["id"] = str(rfp_line_id)
                    obj_rfp_line["activity_code"] = rfp_activity_code
                    obj_rfp_line["amount"] = str(amount_beban)
                    obj_rfp_line["descs"] = termin.nomor_memo
                    obj_rfp_line["reff_no"] = str(termin_bayar.id)
                    obj_rfp_line["pay_to"] = f"{termin_bayar.pay_to or ''} ({float(termin_bayar.amount)})"
                    obj_rfp_line["rfp_line_dts"] = []
                    obj_rfp_hd["rfp_lines"].append(obj_rfp_line)

                    ## INIT RFP LINE DETAIL
                    invoices = await crud.invoice.get_multi_by_termin_id(termin_id=termin.id)
                    for invoice in invoices:
                        obj_rfp_line_dt = {}
                        rfp_line_dt_id = uuid4()

                        if invoice.is_void:
                            continue

                        invoice_dt = next((inv_dt for inv_dt in invoice.details if inv_dt.beban_biaya_id == termin_bayar_dt.beban_biaya_id), None)
                        if invoice_dt is None:
                            continue

                        bidang_komponen_biaya = await crud.bidang_komponen_biaya.get(id=invoice_dt.bidang_komponen_biaya_id)

                        bidang = await crud.bidang.get(id=invoice.bidang_id)

                        id_bidang_complete = f'{bidang.id_bidang}' if bidang.id_bidang_lama is None else f'{bidang.id_bidang} ({bidang.id_bidang_lama})'

                        obj_rfp_line_dt["id"] = str(rfp_line_dt_id)
                        obj_rfp_line_dt["name"] = bidang.id_bidang
                        obj_rfp_line_dt["amount"] = str(float(invoice_dt.amount))
                        obj_rfp_line_dt["estimated_amount"] = str(float(bidang_komponen_biaya.estimated_amount)) 
                        description = f"{id_bidang_complete} {beban_biaya.name.upper()}, GROUP {termin.tahap.group or ''}"
                        obj_rfp_line_dt["desc"] = description
                        
                        obj_rfp_line["rfp_line_dts"].append(obj_rfp_line_dt)

                    # RFP ALLOCATION
                    rfp_allocation_id = uuid4()
                    obj_rfp_allocation["id"] = str(rfp_allocation_id)
                    obj_rfp_allocation["amount"] = str(termin_bayar.amount)
                    obj_rfp_allocation["rfp_head_id"] = str(rfp_hd_id)
                    obj_rfp_allocation["rfp_bank_id"] = str(rfp_bank_id)
                    obj_rfp_allocation["rfp_line_id"] = str(rfp_line_id)
                    obj_rfp_hd["rfp_allocations"].append(obj_rfp_allocation)

                obj_rfp_bank["descs"] = ", ".join(beban_biaya_names)
                
        
        obj_rfp_hd["descs"] = ",".join(rfp_hd_descs)

        return obj_rfp_hd
    
    # FUNCTION CREATE RFP SETELAH MEMO PEMBAYARAN (TERMIN) APPROVALNYA COMPLETED
    async def create_rfp(self, termin_id:UUID):

        url = self.RFP_BASE_URL + '/rfpgl/client/api/rfp'

        request_data = await self.init_rfp(termin_id=termin_id)

        headers = {
            'Authorization': 'Bearer ' + self.OAUTH2_TOKEN,
            'Content-Type': 'Application/Json'
        }

        try:
            response = requests.post(url, json=request_data, headers=headers)
            if response.status_code == 200:
                data = response.json()['data']
                return RfpHeadNotificationSch(**data), "OK"
            else:
                print(f'{response.status_code}:{response.reason}')
                return None, response.reason
        except Exception as e:
            return None, self.CONNECTION_FAILED

    async def notification_center(self, background_task, payload):

        rfp_header_payload = payload.get('data', None)

        if rfp_header_payload is None:
            raise HTTPException(status_code=404, detail="payload not have data RFP")
        
        rfp_head = RfpHeadNotificationSch(**rfp_header_payload)

        if rfp_head.is_void:
            await self.rfp_void(rfp_head=rfp_head)
            return True

        if rfp_head.current_step not in ["Completed", "Finance Approval"]:
            await self.rfp_updated_status(rfp_head=rfp_head)
            return True
        
        if rfp_head.current_step == "Finance Approval":
            await self.rfp_generate_payment_giro_buka(background_task=background_task, rfp_head=rfp_head)
            return True

        if rfp_head.current_step == "Completed":
            await self.rfp_payment_giro_cair(background_task=background_task, rfp_head=rfp_head)
            return True
            

    # JIKA RFP VOID
    async def rfp_void(self, rfp_head:RfpHeadNotificationSch):
        
        db_session = db.session

        termin = await crud.termin.get(id=rfp_head.client_ref_no)

        if termin is None:
            raise HTTPException(status_code=404, detail=f"termin not found. Id : {rfp_head.client_ref_no}")
        
        worker = await crud.worker.get(id=termin.updated_by_id)

        invoices = await crud.invoice.get_multi_by_termin_id(termin_id=termin.id)
        for invoice in invoices:
            obj_updated = InvoiceUpdateSch.from_orm(invoice)
            obj_updated.is_void = True
            obj_updated.void_reason = rfp_head.void_reason
            obj_updated.void_by_id = worker.id
            obj_updated.void_at = date.today()

            await crud.invoice.update(obj_current=invoice, obj_new=obj_updated, db_session=db_session, with_commit=False)

            # VOID PAYMENT DETAIL
            for dt in invoice.payment_details:
                payment_dtl_updated = PaymentDetailUpdateSch.from_orm(dt)
                payment_dtl_updated.is_void = True
                payment_dtl_updated.void_reason = rfp_head.void_reason
                payment_dtl_updated.void_by_id = worker.id
                payment_dtl_updated.void_at = date.today()
                
                await crud.payment_detail.update(obj_current=dt, obj_new=payment_dtl_updated, db_session=db_session, with_commit=False)

            # DELETE INVOICE DETAIL KETIKA INVOICE BUKAN DARI UTJ/UTJ KHUSUS
            for inv_dtl in invoice.details:

                # DELETE PAYMENT KOMPONEN BIAYA DETAIL
                payment_komponen_biayas = await crud.payment_komponen_biaya_detail.get_by_invoice_detail_id(invoice_detail_id=inv_dtl.id)

                for pkb in payment_komponen_biayas:
                    await crud.payment_komponen_biaya_detail.remove(id=pkb.id, db_session=db_session, with_commit=False)

                await crud.invoice_detail.remove(id=inv_dtl.id, db_session=db_session, with_commit=False)

        # VOID TERMIN APA BILA SEMUA INVOICE YANG ADA DI TERMIN TERSEBUT SUDAH DIVOID
        invoices_active = await crud.invoice.get_multi_invoice_active_by_termin_id(termin_id=invoice.termin_id, invoice_id=invoice.id, db_session=db_session)
        if len(invoices_active) == 0:
            termin = await crud.termin.get(id=invoice.termin_id)
            termin_updated = TerminUpdateBaseSch.from_orm(termin)
            termin_updated.is_void = True
            termin_updated.void_reason = rfp_head.void_reason
            termin_updated.void_by_id = worker.id
            termin_updated.void_at = date.today()
            await crud.termin.update(obj_current=termin, obj_new=termin_updated, db_session=db_session, with_commit=False)

        try:
            await db_session.commit()
        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e.args))

    # UPDATE RFP LAST STATUS PADA MEMO BAYAR (TERMIN)
    async def rfp_updated_status(self, rfp_head:RfpHeadNotificationSch):
        
        termin = await crud.termin.get(id=rfp_head.client_ref_no)

        if termin is None:
            raise HTTPException(status_code=404, detail=f"termin not found. Id : {rfp_head.client_ref_no}")
        
        # UPDATE TERMIN
        termin_update = TerminUpdateBaseSch.from_orm(termin)
        termin_update.rfp_ref_no = rfp_head.id
        termin_update.rfp_last_status = rfp_head.current_step

        try:
            await crud.termin.update(obj_current=termin, obj_new=termin_update)
        except Exception as e:
            raise HTTPException(status_code=409, detail=str(e.args))

    # UPDATE LAST STATUS RFP PADA MEMO BAYAR (TERMIN)
    # GENERATE PAYMENT, PAYMENT DETAIL, PAYMENT GIRO, GIRO, PAYMENT KOMPONEN
    # UPDATE STATUS PEMBAYARAN INVOICE (GIRO BUKA)
    async def rfp_generate_payment_giro_buka(self, background_task, rfp_head:RfpHeadNotificationSch):
        
        db_session = db.session
        termin = await crud.termin.get(id=rfp_head.client_ref_no)

        if termin is None:
            raise HTTPException(status_code=404, detail=f"termin not found. Id : {rfp_head.client_ref_no}")

        rfp_lines = rfp_head.rfp_lines
        rfp_banks = rfp_head.rfp_banks
        rfp_allocations = rfp_head.rfp_allocations

        if rfp_lines is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="rfp line not define")
        
        if rfp_banks is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="rfp bank not define")
        
        if rfp_allocations is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="rfp allocation not define")
        
        # CREATE PAYMENT
        last_number = await generate_code(entity=CodeCounterEnum.Payment, db_session=db_session, with_commit=False)
        obj_payment_created = PaymentCreateSch(code=f"PAY-{last_number}", payment_method=PaymentMethodEnum.Giro, remark=f"{rfp_head.descs} (GENERATE FROM RFP DOC NO {rfp_head.doc_no})")
        obj_payment = await crud.payment.create(obj_in=obj_payment_created, db_session=db_session, with_commit=False)
        
        # CREATE GIRO
        giro_temps = []
        for rfp_bank in rfp_banks:
            obj_giro = await crud.giro.get_by_nomor_giro_and_payment_method(nomor_giro=rfp_bank.giro_no, payment_method=PaymentMethodEnum.Giro)

            if obj_giro:
                obj_giro_updated = GiroUpdateSch.from_orm(obj_giro)
                obj_giro_updated.tanggal_buka = rfp_bank.date_doc
                obj_giro_updated.tanggal_cair = rfp_bank.posting_date

                obj_giro = await crud.giro.update(obj_current=obj_giro, obj_new=obj_giro_updated, db_session=db_session, with_commit=False)
            else:
                last = await generate_code(entity=CodeCounterEnum.Giro, db_session=db_session, with_commit=False)
                obj_giro_created= GiroCreateSch(code=f"{PaymentMethodEnum.Giro.value}-{last}", nomor_giro=rfp_bank.giro_no,
                                                amount=rfp_bank.amount, is_active=True, from_master=False,
                                                bank_code=rfp_bank.bank_code, payment_method=PaymentMethodEnum.Giro,
                                                tanggal_buka=rfp_bank.date_doc, tanggal_cair=rfp_bank.posting_date)
                
                obj_giro = await crud.giro.create(obj_in=obj_giro_created, db_session=db_session, with_commit=False)
            
            giro_temps.append({"id": obj_giro, "rfp_bank_id": rfp_bank.id})


        # CREATE PAYMENT GIRO DETAIL
        # CREATE PAYMENT DETAIL
        # CREATE PAYMENT KOMPONEN DETAIL
        # UPDATE AMOUNT TERMIN BAYAR (CASE APABILA ESTIMASI AMOUNT DI UBAH DI SISI RFP)
        invoices = await crud.invoice.get_multi_by_termin_id(termin_id=termin.id)
        bidang_ids = [inv.bidang_id for inv in invoices if inv.is_void != True]
        utj_invoices = await crud.invoice.get_multi_by_bidang_ids(bidang_ids=bidang_ids)
        invoice_bayars = await crud.invoice_bayar.get_multi_by_termin_id(termin_id=termin.id)
        termin_bayars = await crud.termin_bayar.get_multi_by_termin_id(termin_id=termin.id)
        termin_bayar_details = await crud.termin_bayar_dt.get_by_termin_id(termin_id=termin.id)

        for rfp_line in rfp_lines:

            obj_termin_bayar = next((bayar for bayar in termin_bayars if str(bayar.id) == rfp_line.reff_no), None)
            if obj_termin_bayar is None:
                raise HTTPException(status_code=404, detail=f"rfp line for termin bayar not found")
            
            rfp_allocation = next((alloc for alloc in rfp_allocations if alloc.rfp_line_id == rfp_line.id), None)
            if rfp_allocation is None:
                raise HTTPException(status_code=404, detail=f"rfp allocation for termin bayar not found")
            
            rfp_bank = next((bank for bank in rfp_banks if bank.id == rfp_allocation.rfp_bank_id), None)
            if rfp_bank is None:
                raise HTTPException(status_code=404, detail=f"rfp bank for termin bayar not found")
            
            # CREATE PAYMENT GIRO DETAIL 
            giro_src = next((giro_temp for giro_temp in giro_temps if giro_temp["rfp_bank_id"] == rfp_bank.id), None)
            obj_payment_giro_dt_created = PaymentGiroDetailCreateSch(payment_id=obj_payment.id, payment_method=PaymentMethodEnum.Giro,
                                                                        giro_id=giro_src["id"], amount=rfp_line.amount, pay_to=obj_termin_bayar.pay_to)
            
            obj_payment_giro_dt = await crud.payment_giro_detail.create(obj_in=obj_payment_giro_dt_created, db_session=db_session, with_commit=False)

            # payment_giro_dt_temps.append({"payment_giro_dt_id" : obj_payment_giro_dt.id, "id_index" : obj_termin_bayar.id})
            
            for rfp_line_dt in rfp_line.rfp_line_dts:
                # CREATE PAYMENT DETAIL
                obj_bidang = await crud.bidang.get_by_id_bidang(idbidang=rfp_line_dt.name)
                if obj_bidang is None:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Id Bidang {rfp_line_dt.name} not found")
                
                # BIAYA TANAH
                if obj_termin_bayar.activity == ActivityEnum.BIAYA_TANAH:
                    invoice_bayar = next((inv_bayar for inv_bayar in invoice_bayars if inv_bayar.termin_bayar_id == obj_termin_bayar.id), None)
                    
                    obj_payment_detail_created = PaymentDetailCreateSch(payment_id=obj_payment.id, invoice_id=invoice_bayar.invoice_id, 
                                                                        amount=rfp_line_dt.amount, is_void=False, remark="Generate From RFP", 
                                                                        payment_giro_detail_id=obj_payment_giro_dt.id, realisasi=False)
                    await crud.payment_detail.create(obj_in=obj_payment_detail_created, db_session=db_session, with_commit=False)

                # UTJ REALISASI
                elif obj_termin_bayar.activity == ActivityEnum.UTJ:
                    utj_invoice = next((utj for utj in utj_invoices if utj.bidang_id == obj_bidang.id), None)
                    
                    obj_payment_detail_created = PaymentDetailCreateSch(payment_id=obj_payment.id, invoice_id=utj_invoice.id, 
                                                                        amount=rfp_line_dt.amount, is_void=False, remark="Generate From RFP", 
                                                                        payment_giro_detail_id=obj_payment_giro_dt.id, realisasi=True)
                    await crud.payment_detail.create(obj_in=obj_payment_detail_created, db_session=db_session, with_commit=False)

                # KOMPONEN BIAYA
                else:
                    termin_bayar_dt = next((t_bayar_dt for t_bayar_dt in termin_bayar_details if t_bayar_dt.termin_bayar_id == obj_termin_bayar.id), None)
                    invoice_details = await crud.invoice_detail.get_multi_by_termin_id_and_beban_biaya_id(termin_id=obj_termin_bayar.termin_id, beban_biaya_id=termin_bayar_dt.beban_biaya_id)

                    for invoice_detail in invoice_details:
                        obj_payment_komponen_biaya_dt_created = PaymentKomponenBiayaDetailCreateSch(payment_id=obj_payment.id, 
                                                                                                    invoice_detail_id=invoice_detail.id, 
                                                                                                    payment_giro_detail_id=obj_payment_giro_dt.id, 
                                                                                                    amount=rfp_line_dt.estimated_amount)
                        
                        await crud.payment_komponen_biaya_detail.create(obj_in=obj_payment_komponen_biaya_dt_created, db_session=db_session, with_commit=False)

                        # UPDATE INVOICE DETAIL
                        obj_invoice_dt_updated = InvoiceDetailUpdateSch.from_orm(invoice_detail)
                        obj_invoice_dt_updated.amount = rfp_line_dt.estimated_amount

                        await crud.invoice_detail.update(obj_current=invoice_detail, obj_new=obj_invoice_dt_updated, db_session=db_session, with_commit=False)

                        # UPDATE BIDANG KOMPONEN BIAYA
                        obj_bidang_komponen_biaya = await crud.bidang_komponen_biaya.get(id=invoice_detail.bidang_komponen_biaya_id)
                        obj_bidang_komponen_biaya_updated = BidangKomponenBiayaUpdateSch.from_orm(obj_bidang_komponen_biaya)
                        obj_bidang_komponen_biaya_updated.estimated_amount = rfp_line_dt.estimated_amount
                        obj_bidang_komponen_biaya_updated.paid_amount = rfp_line_dt.amount
                        obj_bidang_komponen_biaya_updated.is_paid = True

                        await crud.bidang_komponen_biaya.update(obj_current=obj_bidang_komponen_biaya, obj_new=obj_bidang_komponen_biaya_updated, db_session=db_session, with_commit=False)

                # UPDATE TERMIN BAYAR
                obj_termin_bayar_updated = TerminBayarUpdateSch.from_orm(obj_termin_bayar)
                obj_termin_bayar_updated.amount = rfp_line.amount

                await crud.termin_bayar.update(obj_current=obj_termin_bayar, obj_new=obj_termin_bayar_updated, db_session=db_session, with_commit=False)

            # UPDATE TERMIN
            termin_update = TerminUpdateBaseSch.from_orm(termin)
            termin_update.rfp_ref_no = rfp_head.id
            termin_update.rfp_last_status = rfp_head.current_step

            await crud.termin.update(obj_current=termin, obj_new=termin_update, db_session=db_session, with_commit=False)

            try:

                await db_session.commit()

            except Exception as e:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.args)
            
            background_task.add_task(await PaymentService().bidang_update_status(bidang_ids=bidang_ids))
            background_task.add_task(await PaymentService().invoice_update_payment_status(payment_id=obj_payment.id))

    # UPDATE RFP LAST STATUS RFP PADA MEMO BAYAR (TERMIN)
    # UPDATE TANGGAL CAIR GIRO
    # UPDATE STATUS PEMBAYARAN INVOICE (GIRO CAIR)
    async def rfp_payment_giro_cair(self, background_task, rfp_head:RfpHeadNotificationSch):
        
        db_session = db.session
        termin = await crud.termin.get(id=rfp_head.client_ref_no)

        if termin is None:
            raise HTTPException(status_code=404, detail=f"termin not found. Id : {rfp_head.client_ref_no}")

        rfp_lines = rfp_head.rfp_lines
        rfp_banks = rfp_head.rfp_banks
        rfp_allocations = rfp_head.rfp_allocations

        if rfp_lines is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="rfp line not define")
        
        if rfp_banks is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="rfp bank not define")
        
        if rfp_allocations is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="rfp allocation not define")
        
        invoices = await crud.invoice.get_multi_by_termin_id(termin_id=termin.id)
        bidang_ids = list(set([inv.bidang_id for inv in invoices if inv.is_void != True]))
        payment_details = await crud.payment_detail.get_multi_payment_actived_by_invoice_id(list_ids=[inv.id for inv in invoices])
        payment_ids = list(set([dt.payment_id for dt in payment_details]))
        giros = await crud.giro.get_distinct_giro_by_invoice_ids(invoice_ids=[inv.id for inv in invoices])

        for bank in rfp_banks:
            obj_giro = next((giro for giro in giros if bank.giro_no == giro.nomor_giro and bank.bank_code == giro.bank_code and bank.date_doc == giro.tanggal_buka), None)
            if obj_giro is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"RFP Bank {bank.giro_no} tidak ditemukan!")
            
            obj_giro_updated = GiroUpdateSch.from_orm(obj_giro)
            obj_giro_updated.tanggal_cair = bank.posting_date

            await crud.giro.update(obj_current=obj_giro,obj_new=obj_giro_updated, db_session=db_session, with_commit=False)
        
        # UPDATE TERMIN
        termin_update = TerminUpdateBaseSch.from_orm(termin)
        termin_update.rfp_ref_no = rfp_head.id
        termin_update.rfp_last_status = rfp_head.current_step

        await crud.termin.update(obj_current=termin, obj_new=termin_update, db_session=db_session, with_commit=False)

        try:
            await db_session.commit()
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.args)
        
        background_task.add_task(await PaymentService().bidang_update_status(bidang_ids=list(set(bidang_ids))))
        
        for payment_id in payment_ids:
            background_task.add_task(await PaymentService().invoice_update_payment_status(payment_id=payment_id))

        


    def add_days(self, n, d:date | None = datetime.today()):
        return d + timedelta(n)
    
    # # UPDATE RFP LAST STATUS PADA MEMO BAYAR (TERMIN) SEKALIGUS GENERATE PAYMENT
    # async def rfp_generate_payment_giro_cair(self, background_task, rfp_head:RfpHeadNotificationSch):

    #     termin = await crud.termin.get(id=rfp_head.client_ref_no)

    #     if termin is None:
    #         raise HTTPException(status_code=404, detail=f"termin not found. Id : {rfp_head.client_ref_no}")

    #     rfp_lines = rfp_head.rfp_lines
    #     rfp_banks = rfp_head.rfp_banks
    #     rfp_allocations = rfp_head.rfp_allocations

    #     if rfp_lines is None:
    #         raise HTTPException(status_code=404, detail="rfp line not define")
        
    #     if rfp_banks is None:
    #         raise HTTPException(status_code=404, detail="rfp bank not define")
        
    #     if rfp_allocations is None:
    #         raise HTTPException(status_code=404, detail="rfp allocation not define")
        

    #     # INIT PAYMENT
    #     payment = PaymentCreateSch(payment_method=PaymentMethodEnum.Giro, remark=f"{rfp_head.descs} (GENERATE FROM RFP DOC NO {rfp_head.doc_no})")
        
    #     termin_bayars = await crud.termin_bayar.get_multi_by_termin_id(termin_id=termin.id)

    #     # INIT PAYMENT GIRO DETAIL
    #     payment_giro_details = []
    #     for termin_bayar in termin_bayars:
    #         rfp_line = next((line for line in rfp_lines if line.reff_no == str(termin_bayar.id)), None)
    #         if rfp_line is None:
    #             raise HTTPException(status_code=404, detail=f"rfp line for termin bayar {termin_bayar.id} not found")
            
    #         rfp_allocation = next((alloc for alloc in rfp_allocations if alloc.rfp_line_id == rfp_line.id), None)
    #         if rfp_allocation is None:
    #             raise HTTPException(status_code=404, detail=f"rfp allocation for termin bayar {termin_bayar.id} not found")
            
    #         rfp_bank = next((bank for bank in rfp_banks if bank.id == rfp_allocation.rfp_bank_id), None)
    #         if rfp_bank is None:
    #             raise HTTPException(status_code=404, detail=f"rfp bank for termin bayar {termin_bayar.id} not found")

    #         payment_giro_detail = PaymentGiroDetailExtSch(nomor_giro=rfp_bank.giro_no, 
    #                                                         tanggal_buka=rfp_bank.date_doc,
    #                                                         tanggal_cair=rfp_bank.posting_date,
    #                                                         bank_code=rfp_bank.bank_code,
    #                                                         payment_date=rfp_bank.posting_date,
    #                                                         amount=termin_bayar.amount,
    #                                                         payment_method=PaymentMethodEnum.Giro,
    #                                                         pay_to=termin_bayar.pay_to,
    #                                                         id_index=termin_bayar.id
    #                                                     )
            
    #         payment_giro_details.append(payment_giro_detail)

    #     # INIT PAYMENT DETAIL
    #     payment_details = []

    #     invoices = await crud.invoice.get_multi_by_termin_id(termin_id=termin.id)
    
    #     bidang_ids = [inv.bidang_id for inv in invoices if inv.is_void != True]
    #     utj_invoices = await crud.invoice.get_multi_by_bidang_ids(bidang_ids=bidang_ids)
    #     invoice_bayars = await crud.invoice_bayar.get_multi_by_termin_id(termin_id=termin.id)

    #     for invoice_bayar in invoice_bayars:
    #         if (invoice_bayar.amount or 0) == 0:
    #             continue
    #         if invoice_bayar.termin_bayar.activity == ActivityEnum.BEBAN_BIAYA:
    #             continue
    #         elif invoice_bayar.termin_bayar.activity == ActivityEnum.UTJ:
    #             utj_invoice = next((utj for utj in utj_invoices if utj.bidang_id == invoice_bayar.invoice.bidang_id), None)
    #             if utj_invoice is None:
    #                 continue

    #             payment_detail = PaymentDetailExtSch(invoice_id=utj_invoice.id, amount=invoice_bayar.amount, id_index=invoice_bayar.termin_bayar_id, realisasi=True)
    #         else:
    #             regular_invoice = next((inv for inv in invoices if inv.id == invoice_bayar.invoice_id), None)
    #             if regular_invoice is None:
    #                 continue

    #             payment_detail = PaymentDetailExtSch(invoice_id=regular_invoice.id, amount=invoice_bayar.amount, id_index=invoice_bayar.termin_bayar_id, realisasi=False)

    #         payment_details.append(payment_detail)

    #     # INIT PAYMENT KOMPONEN BIAYA DETAIL
    #     payment_komponen_biaya_details = []
    #     termin_bayar_details = await crud.termin_bayar_dt.get_by_termin_id(termin_id=termin.id)
    #     komponens = await crud.bebanbiaya.get_multi_grouping_beban_biaya_by_termin_id(termin_id=termin.id)

    #     for termin_bayar_dt in termin_bayar_details:
    #         komponen = next((kb for kb in komponens if kb.beban_biaya_id == termin_bayar_dt.beban_biaya_id), None)

    #         rfp_line = next((line for line in rfp_lines if line.reff_no == termin_bayar_dt.termin_bayar_id), None)

    #         payment_komponen_biaya_detail = PaymentKomponenBiayaDetailExtSch(beban_biaya_id=termin_bayar_dt.beban_biaya_id, id_index=termin_bayar_dt.termin_bayar_id,
    #                                                                         amount=(komponen.amount or 0), termin_id=termin.id)
            
    #         payment_komponen_biaya_details.append(payment_komponen_biaya_detail)

    #     payment.details = payment_details
    #     payment.giros = payment_giro_details
    #     payment.komponens = payment_komponen_biaya_details

    #     # UPDATE TERMIN
    #     termin_update = TerminUpdateBaseSch.from_orm(termin)
    #     termin_update.rfp_ref_no = rfp_head.id
    #     termin_update.rfp_last_status = rfp_head.current_step

    #     try:
    #         db_session = db.session

    #         new_obj = await crud.payment.create(obj_in=payment, db_session=db_session, with_commit=False)
    #         await crud.termin.update(obj_current=termin, obj_new=termin_update, db_session=db_session, with_commit=False)

    #         await db_session.commit()

    #         background_task.add_task(await PaymentService().bidang_update_status(bidang_ids=bidang_ids))
    #         background_task.add_task(await PaymentService().invoice_update_payment_status(payment_id=new_obj.id))

    #     except Exception as e:
    #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.args) if e.args != "" or e.args is not None else str(e.detail))

                


