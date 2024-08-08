
from fastapi import HTTPException, status

from fastapi_async_sqlalchemy import db
from sqlmodel.ext.asyncio.session import AsyncSession
import crud.payment_komponen_biaya_detail_crud
from models import Invoice, Worker
from schemas.invoice_sch import InvoiceUpdateSch
from schemas.payment_detail_sch import PaymentDetailUpdateSch
from schemas.termin_sch import TerminUpdateBaseSch
from common.enum import JenisBayarEnum

from datetime import date

import crud

class InvoiceService:

    async def void(self, obj_current: Invoice, current_worker: Worker, reason: str):

        db_session = db.session
        db_session.autoflush = False

        if obj_current.termin.jenis_bayar in [JenisBayarEnum.UTJ, JenisBayarEnum.UTJ_KHUSUS]:
            await self.void_invoice_utj(obj_current=obj_current, db_session=db_session)
        else:
            await self.void_invoice_reguler(obj_current=obj_current, reason=reason, current_worker=current_worker, db_session=db_session)


    # VOID INVOICE UTJ. DELETE DATA INVOICE DAN PAYMENT DETAIL
    async def void_invoice_utj(self, obj_current: Invoice, db_session: AsyncSession):

        # PERIKSA APAKAH UTJ BIDANG TERSEBUT TELAH MEMILIKI REALISASI DI MEMO PEMBAYARAN (DP, LUNAS/PELUNASAN)
        invoice_have_termin_bayar_utj = await crud.invoice.get_invoice_have_termin_bayar_utj_by_bidang_id(bidang_id=obj_current.bidang_id)
        if invoice_have_termin_bayar_utj:
            termin = await crud.termin.get(id=invoice_have_termin_bayar_utj.termin_id)
            bidang = await crud.bidang.get(id=obj_current.bidang_id)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"UTJ bidang {bidang.id_bidang} memiliki realisasi pada memo {termin.code}")

        for payment_detail in obj_current.payment_details:
            await crud.payment_detail.remove(id=payment_detail.id, db_session=db_session, with_commit=False)

        await crud.invoice.remove(id=obj_current.id, db_session=db_session, with_commit=False)

        try:
            await db_session.commit()
        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e.args))

    # VOID INVOICE DILUAR UTJ. UPDATE FLAG IS VOID, VOID REASON PADA INVOICE DAN TERMIN. DELETE INVOICE DETAIL.
    async def void_invoice_reguler(self, obj_current: Invoice, reason: str, current_worker: Worker, db_session: AsyncSession):

        obj_updated = InvoiceUpdateSch.from_orm(obj_current)
        obj_updated.is_void = True
        obj_updated.void_reason = reason
        obj_updated.void_by_id = current_worker.id
        obj_updated.void_at = date.today()

        await crud.invoice.update(obj_current=obj_current, obj_new=obj_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

        # VOID PAYMENT DETAIL
        for dt in obj_current.payment_details:
            payment_dtl_updated = PaymentDetailUpdateSch.from_orm(dt)
            payment_dtl_updated.is_void = True
            payment_dtl_updated.void_reason = reason
            payment_dtl_updated.void_by_id = current_worker.id
            payment_dtl_updated.void_at = date.today()
            
            await crud.payment_detail.update(obj_current=dt, obj_new=payment_dtl_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

        

        # DELETE INVOICE DETAIL KETIKA INVOICE BUKAN DARI UTJ/UTJ KHUSUS
        for inv_dtl in obj_current.details:

             # DELETE PAYMENT KOMPONEN BIAYA DETAIL BY INVOICE DETAIL ID
            payment_komponen_biayas = await crud.payment_komponen_biaya_detail.get_by_invoice_detail_id(invoice_detail_id=inv_dtl.id)

            for pkb in payment_komponen_biayas:
                await crud.payment_komponen_biaya_detail.remove(id=pkb.id, db_session=db_session, with_commit=False)

            await crud.invoice_detail.remove(id=inv_dtl.id, db_session=db_session, with_commit=False)

        # VOID TERMIN APA BILA SEMUA INVOICE YANG ADA DI TERMIN TERSEBUT SUDAH DIVOID
        invoices_active = await crud.invoice.get_multi_invoice_active_by_termin_id(termin_id=obj_current.termin_id, invoice_id=obj_current.id, db_session=db_session)
        if len(invoices_active) == 0:
            termin = await crud.termin.get(id=obj_current.termin_id)
            termin_updated = TerminUpdateBaseSch.from_orm(termin)
            termin_updated.is_void = True
            termin_updated.void_reason = reason
            termin_updated.void_by_id = current_worker.id
            termin_updated.void_at = date.today()
            await crud.termin.update(obj_current=termin, obj_new=termin_updated, db_session=db_session, with_commit=False)

        try:
            await db_session.commit()
        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e.args))

        