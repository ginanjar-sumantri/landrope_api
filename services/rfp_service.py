import crud
import requests
from uuid import UUID, uuid4
from datetime import date, datetime
from schemas.rfp_sch import RfpCreateResponseSch
from common.enum import PaymentMethodEnum, ActivityEnum, SatuanBayarEnum, activity_landrope_to_activity_rfp_dict
from configs.config import settings

class RfpService:

    RFP_BASE_URL = settings.RFP_BASE_URL
    RFP_CLIENT_ID = settings.RFP_CLIENT_ID
    OAUTH2_TOKEN = settings.OAUTH2_TOKEN
    CONNECTION_FAILED = "Cannot create connection to authentication server."

    async def init_rfp(self, termin_id:UUID):

        termin = await crud.termin.get_by_id(id=termin_id)
    
        # INIT RFP HEADER
        rfp_hd_id = uuid4()
        obj_rfp_hd = {}
        obj_rfp_hd["id"] = str(rfp_hd_id)
        obj_rfp_hd["client_id"] = self.RFP_CLIENT_ID
        obj_rfp_hd["client_ref_no"] = str(termin.id)
        obj_rfp_hd["created_by_outh_id"] = "42b8cb0e-7e78-4728-a89b-493dfc5e4fd1"
        obj_rfp_hd["grace_period"] = str(termin.last_status_at.date())
        obj_rfp_hd["date_doc"] = str(termin.last_status_at.date())
        obj_rfp_hd["document_type_code"] = "OPR-INT"
        obj_rfp_hd["ref_no"] = termin.nomor_memo

        ### SETUP PAY TO
        pay_to = [f'{termin_bayar.pay_to} ({termin_bayar.rekening.nomor_rekening} an {termin_bayar.rekening.nama_pemilik_rekening})' for termin_bayar in termin.termin_bayars if termin_bayar.pay_to != None and termin_bayar.rekening_id != None]
        obj_rfp_hd["pay_to"] = ", ".join(pay_to)
        
        rfp_hd_descs = []

        obj_rfp_hd["rfp_lines"] = []
        obj_rfp_hd["rfp_banks"] = []
        obj_rfp_hd["rfp_allocations"] = []

        # SETUP FIRST DESC for RFP HEADER
        invoice_in_termin_histories = await crud.invoice.get_multi_invoice_id_luas_bayar_by_termin_id(termin_id=termin.id)
        count_bidang = len(invoice_in_termin_histories)
        sum_luas_bayar = "{:,.0f}".format(sum([invoice_.luas_bayar or 0 for invoice_ in invoice_in_termin_histories if invoice_.luas_bayar is not None]))
        termin_desc = f"{termin.jenis_bayar} {count_bidang}BID luas {sum_luas_bayar}m2"
        rfp_hd_descs.append(termin_desc)

        # INIT RFP LINE, RFP BANK, RFP ALLOCATION
        for termin_bayar in termin.termin_bayars:
            obj_rfp_line = {}
            obj_rfp_bank = {}
            obj_rfp_allocation = {}
            if termin_bayar.payment_method == PaymentMethodEnum.Tunai:
                continue

            rfp_activity_code: str | None = None

            if termin_bayar.activity in [ActivityEnum.UTJ, ActivityEnum.BIAYA_TANAH]:
                rfp_activity_code = activity_landrope_to_activity_rfp_dict.get(termin_bayar.activity, None)
                
                # RFP LINE
                rfp_line_id = uuid4()
                obj_rfp_line["id"] = str(rfp_line_id)
                obj_rfp_line["activity_code"] = rfp_activity_code
                obj_rfp_line["amount"] = str(termin_bayar.amount)
                obj_rfp_line["descs"] = termin.nomor_memo
                obj_rfp_line["rfp_line_dts"] = []
                obj_rfp_hd["rfp_lines"].append(obj_rfp_line)
                

                ## INIT RFP LINE DETAIL
                for inv_bayar in termin_bayar.invoice_bayars:
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
                    obj_rfp_line_dt["amount"] = str(inv_bayar.amount)

                    description: str = ""

                    if spk:
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
                obj_rfp_bank["date_doc"] = str(termin.last_status_at.date())
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
                obj_rfp_bank["date_doc"] = str(termin.last_status_at.date())
                obj_rfp_hd["rfp_banks"].append(obj_rfp_bank)

                #RFP LINE
                for termin_bayar_dt in termin_bayar.termin_bayar_dts:
                    beban_biaya = await crud.bebanbiaya.get(id=termin_bayar_dt.beban_biaya_id)
                    amount_beban = sum([inv_dt.amount for inv in termin.invoices if inv.is_void != True for inv_dt in inv.details if inv_dt.beban_biaya_id == termin_bayar_dt.beban_biaya_id])
                    rfp_activity_code = beban_biaya.activity_code
                    
                    rfp_line_id = uuid4()
                    obj_rfp_line["id"] = str(rfp_line_id)
                    obj_rfp_line["activity_code"] = rfp_activity_code
                    obj_rfp_line["amount"] = str(amount_beban)
                    obj_rfp_line["descs"] = termin.nomor_memo
                    obj_rfp_line["rfp_line_dts"] = []
                    obj_rfp_hd["rfp_lines"].append(obj_rfp_line)

                    ## INIT RFP LINE DETAIL
                    for invoice in termin.invoices:
                        obj_rfp_line_dt = {}
                        rfp_line_dt_id = uuid4()

                        if invoice.is_void:
                            continue

                        invoice_dt = next((inv_dt for inv_dt in invoice.details if inv_dt.beban_biaya_id == termin_bayar_dt.beban_biaya_id), None)
                        if invoice_dt is None:
                            continue

                        bidang = await crud.bidang.get(id=invoice.bidang_id)

                        id_bidang_complete = f'{bidang.id_bidang}' if bidang.id_bidang_lama is None else f'{bidang.id_bidang} ({bidang.id_bidang_lama})'

                        obj_rfp_line_dt["id"] = str(rfp_line_dt_id)
                        obj_rfp_line_dt["name"] = bidang.id_bidang
                        obj_rfp_line_dt["amount"] = str(invoice_dt.amount)
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
        
        obj_rfp_hd["descs"] = ",".join(rfp_hd_descs)

        return obj_rfp_hd
    
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
                return RfpCreateResponseSch(**data), "OK"
            else:
                print(f'{response.status_code}:{response.reason}')
                return None, response.reason
        except Exception as e:
            return None, self.CONNECTION_FAILED


                


