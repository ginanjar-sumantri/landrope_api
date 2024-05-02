# import crud
# from uuid import UUID, uuid4
# from datetime import date, datetime
# from common.enum import PaymentMethodEnum, ActivityEnum, SatuanBayarEnum, activity_landrope_to_activity_rfp_dict


# class RfpService:

#     async def init_rfp(self, termin_id:UUID):

#         termin = await crud.termin.get_by_id(id=termin_id)
    
#         # INIT RFP HEADER
#         rfp_hd_id = uuid4()
#         obj_rfp_hd = {}
#         obj_rfp_hd["id"] = rfp_hd_id
#         obj_rfp_hd["client_id"] = ""
#         obj_rfp_hd["client_ref_no"] = termin.id
#         obj_rfp_hd["grace_period"] = termin.last_status_at.date()
#         obj_rfp_hd["date_doc"] = termin.last_status_at.date()
#         obj_rfp_hd["document_type_code"] = "OPR-INT"
#         obj_rfp_hd["ref_no"] = termin.nomor_memo

#         ### SETUP PAY TO
#         pay_to = [f'{termin_bayar.pay_to} ({termin_bayar.rekening.nomor_rekening} an {termin_bayar.rekening.nama_pemilik_rekening})' for termin_bayar in termin.termin_bayars if termin_bayar.pay_to != None and termin_bayar.rekening_id != None]
#         obj_rfp_hd["pay_to"] = ", ".join(pay_to)
#         obj_rfp_hd["descs"] = ""

#         obj_rfp_hd["rfp_lines"] = []
#         obj_rfp_hd["rfp_banks"] = []
#         obj_rfp_hd["rfp_allocations"] = []

#         # INIT RFP LINE, RFP BANK, RFP ALLOCATION
#         for termin_bayar in termin.termin_bayars:
#             obj_rfp_line = {}
#             obj_rfp_bank = {}
#             obj_rfp_allocation = {}
#             if termin_bayar.payment_method == PaymentMethodEnum.Tunai:
#                 continue

#             rfp_activity_code: str | None = None

#             if termin_bayar.activity in [ActivityEnum.UTJ, ActivityEnum.BIAYA_TANAH]:
#                 rfp_activity_code = activity_landrope_to_activity_rfp_dict.get(termin_bayar.activity, None)
                
#                 # RFP LINE
#                 rfp_line_id = uuid4()
#                 obj_rfp_line["id"] = rfp_line_id
#                 obj_rfp_line["activity_code"] = rfp_activity_code
#                 obj_rfp_line["amount"] = termin_bayar.amount
#                 obj_rfp_line["descs"] = termin.nomor_memo
#                 obj_rfp_line["rfp_line_dts"] = []
#                 obj_rfp_hd["rfp_lines"].append(obj_rfp_line)
                

#                 ## INIT RFP LINE DETAIL
#                 for inv_bayar in termin_bayar.invoice_bayars:
#                     obj_rfp_line_dt = {}

#                     invoice = await crud.invoice.get(id=inv_bayar.invoice_id)
#                     if invoice.is_void:
#                         continue

#                     bidang = await crud.bidang.get(id=invoice.bidang_id)
#                     spk = await crud.spk.get(id=invoice.spk_id)

#                     id_bidang_complete = f'{bidang.id_bidang}' if bidang.id_bidang_lama is None else f'{bidang.id_bidang} ({bidang.id_bidang_lama})'

#                     obj_rfp_line_dt["name"] = bidang.id_bidang
#                     obj_rfp_line_dt["amount"] = inv_bayar.amount

#                     if spk:
#                         amount = f"{str(spk.amount) + '%' if spk.satuan_bayar == SatuanBayarEnum.Percentage else ''}"
                        
#                         description = f"{id_bidang_complete} {spk.jenis_bayar} {amount}, GROUP {termin.tahap.group or ''}"
#                         obj_rfp_line_dt["desc"] = description
#                     else:
#                         description = f"{id_bidang_complete} UTJ, GROUP {termin.tahap.group or ''}"
#                         obj_rfp_line_dt["desc"] = description
                    
                    
#                     obj_rfp_line["rfp_line_dts"].append(obj_rfp_line_dt)

#                 # RFP BANK
#                 rfp_bank_id = uuid4()
#                 obj_rfp_bank["id"] = rfp_bank_id
#                 obj_rfp_bank["amount"] = termin_bayar.amount
#                 obj_rfp_bank["date_doc"] = termin.last_status_at.date()
#                 obj_rfp_hd["rfp_banks"].append(obj_rfp_bank)

#                 # RFP ALLOCATION
#                 rfp_allocation_id = uuid4()
#                 obj_rfp_allocation["id"] = rfp_allocation_id
#                 obj_rfp_allocation["amount"] = termin_bayar.amount
#                 obj_rfp_allocation["rfp_head_id"] = rfp_hd_id
#                 obj_rfp_allocation["rfp_bank_id"] = rfp_bank_id
#                 obj_rfp_allocation["rfp_line_id"] = rfp_line_id
#                 obj_rfp_hd["rfp_allocations"].append(obj_rfp_allocation)

#             else:
#                 # RFP BANK
#                 rfp_bank_id = uuid4()
#                 obj_rfp_bank["id"] = rfp_bank_id
#                 obj_rfp_bank["amount"] = termin_bayar.amount
#                 obj_rfp_bank["date_doc"] = termin.last_status_at.date()
#                 obj_rfp_hd["rfp_banks"].append(obj_rfp_bank)

#                 #RFP LINE
#                 for termin_bayar_dt in termin_bayar.termin_bayar_dts:
#                     beban_biaya = await crud.bebanbiaya.get(id=termin_bayar_dt.beban_biaya_id)
#                     amount_beban = sum([inv_dt.amount for inv in termin.invoices if inv.is_void != True for inv_dt in inv.details if inv_dt.beban_biaya_id == termin_bayar_dt.beban_biaya_id])
#                     rfp_activity_code = beban_biaya.activity_code
                    
#                     rfp_line_id = uuid4()
#                     obj_rfp_line["id"] = rfp_line_id
#                     obj_rfp_line["activity_code"] = rfp_activity_code
#                     obj_rfp_line["amount"] = amount_beban
#                     obj_rfp_line["descs"] = termin.nomor_memo
#                     obj_rfp_line["rfp_line_dts"] = []
#                     obj_rfp_hd["rfp_lines"].append(obj_rfp_line)

#                     ## INIT RFP LINE DETAIL
#                     for invoice in termin.invoices:
#                         obj_rfp_line_dt = {}

#                         if invoice.is_void:
#                             continue

#                         invoice_dt = next((inv_dt for inv_dt in invoice.details if inv_dt.beban_biaya_id == termin_bayar_dt.beban_biaya_id), None)
#                         if invoice_dt is None:
#                             continue

#                         bidang = await crud.bidang.get(id=invoice.bidang_id)

#                         id_bidang_complete = f'{bidang.id_bidang}' if bidang.id_bidang_lama is None else f'{bidang.id_bidang} ({bidang.id_bidang_lama})'

#                         obj_rfp_line_dt["name"] = bidang.id_bidang
#                         obj_rfp_line_dt["amount"] = invoice_dt.amount
#                         description = f"{id_bidang_complete} {beban_biaya.name.upper()}, GROUP {termin.tahap.group or ''}"
#                         obj_rfp_line_dt["desc"] = description
                        
#                         obj_rfp_line["rfp_line_dts"].append(obj_rfp_line_dt)

#                     # RFP ALLOCATION
#                     rfp_allocation_id = uuid4()
#                     obj_rfp_allocation["id"] = rfp_allocation_id
#                     obj_rfp_allocation["amount"] = termin_bayar.amount
#                     obj_rfp_allocation["rfp_head_id"] = rfp_hd_id
#                     obj_rfp_allocation["rfp_bank_id"] = rfp_bank_id
#                     obj_rfp_allocation["rfp_line_id"] = rfp_line_id
#                     obj_rfp_hd["rfp_allocations"].append(obj_rfp_allocation)

#         return obj_rfp_hd

                


