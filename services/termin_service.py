from sqlmodel import and_, delete
from models.code_counter_model import CodeCounterEnum
from models import Termin, TerminBayar, TerminBayarDt, BidangKomponenBiaya
from schemas.termin_sch import TerminCreateSch, TerminUpdateSch
from schemas.termin_bayar_sch import TerminBayarCreateSch, TerminBayarUpdateSch
from schemas.termin_bayar_dt_sch import TerminBayarDtCreateSch, TerminBayarDtUpdateSch
from schemas.invoice_sch import InvoiceCreateSch, InvoiceUpdateSch
from schemas.invoice_detail_sch import InvoiceDetailCreateSch, InvoiceDetailUpdateSch
from schemas.invoice_bayar_sch import InvoiceBayarCreateSch, InvoiceBayarlUpdateSch
from schemas.bidang_komponen_biaya_sch import BidangKomponenBiayaCreateSch
from common.enum import JenisBayarEnum, jenis_bayar_to_code_counter_enum, jenis_bayar_to_text
from common.generator import generate_code_month

import crud

from datetime import date
from uuid import UUID
import roman

class TerminService:

    # INITIAL TERMIN
    async def init_termin(self, sch: TerminCreateSch, db_session, worker_id:UUID):
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

        new_obj = await crud.termin.create(obj_in=sch, db_session=db_session, with_commit=False, created_by_id=worker_id)

        return new_obj

    # CREATE TERMIN, INVOICE, INVOICE DETAIL, INVOICE BAYAR, TERMIN BAYAR
    async def create_termin(self, sch: TerminCreateSch, db_session, worker_id:UUID):

        new_obj = await self.init_termin(sch=sch, db_session=db_session, worker_id=worker_id)

        termin_bayar_temp, current_ids_termin_byr = await self.manipulation_termin_bayar(termin=new_obj, sch=sch, db_session=db_session, worker_id=worker_id)

    
    # MANIPULATION TERMIN BAYAR AND TERMIN BAYAR DETAIL (CREATE OR UPDATE)
    async def manipulation_termin_bayar(self, termin:Termin, sch:TerminCreateSch | TerminUpdateSch, db_session, worker_id:UUID):

        termin_bayar_temp = []
        current_ids_termin_byr = await crud.termin_bayar.get_ids_by_termin_id(termin_id=termin.id) # FOR DELETE 

        for termin_bayar in sch.termin_bayars:
            termin_bayar_current = await crud.termin_bayar.get(id=termin_bayar.id)
            if termin_bayar_current:
                termin_bayar_updated = TerminBayarUpdateSch(**termin_bayar.dict(), termin_id=termin.id)
                obj_termin_bayar = await crud.termin_bayar.update(obj_current=termin_bayar_current, obj_new=termin_bayar_updated, updated_by_id=worker_id, db_session=db_session, with_commit=False)
                current_ids_termin_byr.remove(obj_termin_bayar.id)

                if termin_bayar.termin_bayar_dts:
                    #delete termin_bayar_detail not exists
                    await db_session.execute(delete(TerminBayarDt).where(and_(TerminBayarDt.id.notin_(dt.id for dt in termin_bayar.termin_bayar_dts if dt.id != None), 
                                                            TerminBayarDt.termin_bayar_id == obj_termin_bayar.id)))
                    
                    for termin_bayar_dt in termin_bayar.termin_bayar_dts:
                        if termin_bayar_dt.id is None:
                            termin_bayar_dt_sch = TerminBayarDtCreateSch(**termin_bayar_dt.dict(), termin_bayar_id=obj_termin_bayar.id)
                            await crud.termin_bayar_dt.create(obj_in=termin_bayar_dt_sch, db_session=db_session, with_commit=False, created_by_id=worker_id)
                        else:
                            termin_bayar_dt_current = await crud.termin_bayar_dt.get(id=termin_bayar_dt.id)
                            termin_bayar_dt_updated_sch = TerminBayarDtUpdateSch(**termin_bayar_dt.dict(), termin_bayar_id=obj_termin_bayar.id)
                            await crud.termin_bayar_dt.update(obj_current=termin_bayar_dt_current, obj_new=termin_bayar_dt_updated_sch, db_session=db_session, with_commit=False)
            else:
                termin_bayar_sch = TerminBayarCreateSch(**termin_bayar.dict(), termin_id=termin.id)
                obj_termin_bayar = await crud.termin_bayar.create(obj_in=termin_bayar_sch,  db_session=db_session, with_commit=False, created_by_id=worker_id)
                if termin_bayar.termin_bayar_dts:
                    for termin_bayar_dt in termin_bayar.termin_bayar_dts:
                        termin_bayar_dt_sch = TerminBayarDtCreateSch(**termin_bayar_dt.dict(), termin_bayar_id=obj_termin_bayar.id)
                        await crud.termin_bayar_dt.create(obj_in=termin_bayar_dt_sch, db_session=db_session, with_commit=False, created_by_id=worker_id)
        
            termin_bayar_temp.append({"termin_bayar_id" : obj_termin_bayar.id, "id_index" : termin_bayar.id_index})

        
        return termin_bayar_temp, current_ids_termin_byr

    # MANIPULATION INVOICE, INVOICE DETAIL AND INVOICE BAYAR (CREATE OR UPDATE)
    async def manipulation_invoice(self, termin:Termin, sch:TerminCreateSch | TerminUpdateSch, termin_bayar_temp,  db_session, worker_id:UUID):
        
        today = date.today()
        month = roman.toRoman(today.month)
        year = today.year

        current_ids_invoice = await crud.invoice.get_ids_by_termin_id(termin_id=termin.id)
        current_ids_invoice_dt = await crud.invoice_detail.get_ids_by_invoice_ids(list_ids=current_ids_invoice)
        current_ids_invoice_byr = await crud.invoice_bayar.get_ids_by_invoice_ids(list_ids=current_ids_invoice)

        for invoice in sch.invoices:
            #remove bidang komponen biaya
            await db_session.execute(delete(BidangKomponenBiaya).where(and_(BidangKomponenBiaya.id.in_(r.bidang_komponen_biaya_id for r in invoice.details if r.bidang_komponen_biaya_id is not None and r.is_deleted), 
                                                                            BidangKomponenBiaya.bidang_id == invoice.bidang_id)))

            invoice_current = await crud.invoice.get_by_id(id=invoice.id)
            if invoice_current:
                invoice_updated_sch = InvoiceUpdateSch(**invoice.dict())
                invoice_updated_sch.is_void = invoice_current.is_void
                invoice_updated = await crud.invoice.update(obj_current=invoice_current, obj_new=invoice_updated_sch, with_commit=False, db_session=db_session, updated_by_id=worker_id)
                current_ids_invoice.remove(invoice_current.id)

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

                                obj_bidang_komponen_biaya = await crud.bidang_komponen_biaya.create(obj_in=bidang_komponen_biaya_new, db_session=db_session, with_commit=False, created_by_id=worker_id)
                                dt.bidang_komponen_biaya_id = obj_bidang_komponen_biaya.id
                            else:
                                dt.bidang_komponen_biaya_id = bidang_komponen_biaya_current.id

                        invoice_dtl_sch = InvoiceDetailCreateSch(**dt.dict(), invoice_id=invoice.id)
                        await crud.invoice_detail.create(obj_in=invoice_dtl_sch, db_session=db_session, with_commit=False, created_by_id=worker_id)
                    else:
                        invoice_dtl_current = await crud.invoice_detail.get(id=dt.id)
                        invoice_dtl_updated_sch = InvoiceDetailUpdateSch(**dt.dict(), invoice_id=invoice_updated.id)
                        await crud.invoice_detail.update(obj_current=invoice_dtl_current, obj_new=invoice_dtl_updated_sch, db_session=db_session, with_commit=False)
                        current_ids_invoice_dt.remove(invoice_dtl_current.id)

                for dt_bayar in invoice.bayars:
                    termin_bayar_id = next((termin_bayar["termin_bayar_id"] for termin_bayar in termin_bayar_temp if termin_bayar["id_index"] == dt_bayar.id_index), None)
                    if dt_bayar.id is None:
                        invoice_bayar_new = InvoiceBayarCreateSch(termin_bayar_id=termin_bayar_id, invoice_id=invoice.id, amount=dt_bayar.amount)
                        await crud.invoice_bayar.create(obj_in=invoice_bayar_new, db_session=db_session, with_commit=False, created_by_id=worker_id)
                    else:
                        invoice_bayar_current = await crud.invoice_bayar.get(id=dt_bayar.id)
                        invoice_bayar_updated = InvoiceBayarlUpdateSch.from_orm(invoice_bayar_current)
                        invoice_bayar_updated.termin_bayar_id = termin_bayar_id
                        invoice_bayar_updated.amount = dt_bayar.amount
                        await crud.invoice_bayar.update(obj_current=invoice_bayar_current, obj_new=invoice_bayar_updated, db_session=db_session, with_commit=False, updated_by_id=worker_id)
                        current_ids_invoice_byr.remove(invoice_bayar_current.id)
                
            else:
                last_number = await generate_code_month(entity=CodeCounterEnum.Invoice, with_commit=False, db_session=db_session)
                invoice_sch = InvoiceCreateSch(**invoice.dict(), termin_id=termin.id)
                invoice_sch.code = f"INV/{last_number}/{termin.jenis_bayar.value}/LA/{month}/{year}"
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

                            obj_bidang_komponen_biaya = await crud.bidang_komponen_biaya.create(obj_in=bidang_komponen_biaya_new, db_session=db_session, with_commit=False, created_by_id=worker_id)
                            dt.bidang_komponen_biaya_id = obj_bidang_komponen_biaya.id
                        else:
                            dt.bidang_komponen_biaya_id = bidang_komponen_biaya_current.id

                    invoice_dtl_sch = InvoiceDetailCreateSch(**dt.dict(), invoice_id=new_obj_invoice.id)
                    await crud.invoice_detail.create(obj_in=invoice_dtl_sch, db_session=db_session, with_commit=False, created_by_id=worker_id)

                for dt_bayar in invoice.bayars:
                    termin_bayar_id = next((termin_bayar["termin_bayar_id"] for termin_bayar in termin_bayar_temp if termin_bayar["id_index"] == dt_bayar.id_index), None)
                    invoice_bayar_new = InvoiceBayarCreateSch(termin_bayar_id=termin_bayar_id, invoice_id=new_obj_invoice.id, amount=dt_bayar.amount)
                    await crud.invoice_bayar.create(obj_in=invoice_bayar_new, db_session=db_session, with_commit=False, created_by_id=worker_id)