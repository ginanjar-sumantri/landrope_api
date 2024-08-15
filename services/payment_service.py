from fastapi_async_sqlalchemy import db
from schemas.bidang_sch import BidangUpdateSch
from schemas.invoice_sch import InvoiceUpdateSch
from common.enum import StatusBidangEnum, PaymentStatusEnum, PaymentMethodEnum
from shapely import wkb, wkt
from uuid import UUID
import crud

class PaymentService:

    async def bidang_update_status(self, bidang_ids:list[UUID]):
        for id in bidang_ids:
            payment_details = await crud.payment_detail.get_payment_detail_by_bidang_id(bidang_id=id)
            if len(payment_details) > 0:
                bidang_current = await crud.bidang.get_by_id(id=id)
                if bidang_current.geom :
                    bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))
                if bidang_current.geom_ori :
                    bidang_current.geom_ori = wkt.dumps(wkb.loads(bidang_current.geom_ori.data, hex=True))
                bidang_updated = BidangUpdateSch(status=StatusBidangEnum.Bebas)
                await crud.bidang.update(obj_current=bidang_current, obj_new=bidang_updated)
            else:
                bidang_current = await crud.bidang.get_by_id(id=id)
                if bidang_current.geom :
                    bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))
                bidang_updated = BidangUpdateSch(status=StatusBidangEnum.Deal)
                await crud.bidang.update(obj_current=bidang_current, obj_new=bidang_updated)

    async def invoice_update_payment_status(self, payment_id:UUID):
        
        db_session = db.session
        payment_current = await crud.payment.get_by_id(id=payment_id)
        payment_details_current = await crud.payment_detail.get_by_payment_id(payment_id=payment_id)

        for payment_detail in payment_details_current:
            if payment_detail.is_void:
                # payment_detais = await crud.payment_detail.get_multi_payment_actived_by_invoice_id()
                continue
            else:
                invoice_current = await crud.invoice.get(id=payment_detail.invoice_id)
                invoice_updated = InvoiceUpdateSch.from_orm(invoice_current)
                if payment_current.giro_id:
                    if payment_current.tanggal_buka is None and payment_current.tanggal_cair is None:
                        invoice_updated.payment_status = None
                    if payment_current.tanggal_buka:
                        invoice_updated.payment_status = PaymentStatusEnum.BUKA_GIRO
                    if payment_current.tanggal_cair:
                        invoice_updated.payment_status = PaymentStatusEnum.CAIR_GIRO
                else:
                    payment_giro_detail = await crud.payment_giro_detail.get(id=payment_detail.payment_giro_detail_id)
                    if payment_giro_detail.payment_method == PaymentMethodEnum.Giro:
                        giro = await crud.giro.get(id=payment_giro_detail.giro_id)
                        if giro:
                            if giro.tanggal_buka:
                                invoice_updated.payment_status = PaymentStatusEnum.BUKA_GIRO
                            if giro.tanggal_cair:
                                invoice_updated.payment_status = PaymentStatusEnum.CAIR_GIRO
                            if giro.tanggal_buka is None and giro.tanggal_cair is None:
                                invoice_updated.payment_status = None
            
            await crud.invoice.update(obj_current=invoice_current, obj_new=invoice_updated, db_session=db_session, with_commit=False)
        
        await db_session.commit()