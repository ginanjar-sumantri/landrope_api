from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import exc
from crud.base_crud import CRUDBase
from models import Payment, PaymentDetail, PaymentGiroDetail, PaymentKomponenBiayaDetail, Invoice, Termin, Giro, Bidang, Skpt, InvoiceDetail, BidangKomponenBiaya
from schemas.payment_sch import PaymentCreateSch, PaymentUpdateSch
from schemas.giro_sch import GiroCreateSch, GiroUpdateSch
from schemas.payment_giro_detail_sch import PaymentGiroDetailCreateSch
from common.enum import PaymentMethodEnum
from common.generator import generate_code
from models.code_counter_model import CodeCounterEnum
from uuid import UUID
from datetime import datetime
import crud

class CRUDPayment(CRUDBase[Payment, PaymentCreateSch, PaymentUpdateSch]):
    async def create(self, *, 
                     obj_in: PaymentCreateSch | Payment, 
                     created_by_id : UUID | str | None = None, 
                     db_session : AsyncSession | None = None,
                     with_commit: bool | None = True) -> Payment :
        db_session = db_session or db.session
        db_obj = self.model.from_orm(obj_in) #type ignore
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()
        if created_by_id:
            db_obj.created_by_id = created_by_id
            db_obj.updated_by_id = created_by_id

        last_number = await generate_code(entity=CodeCounterEnum.Payment, db_session=db_session, with_commit=False)
        db_obj.code = f"PAY-{last_number}"

        giro_temp = []
        for giro_dt in obj_in.giros:
            obj_giro: Giro = None
            if giro_dt.giro_id is None and giro_dt.payment_method != PaymentMethodEnum.Tunai:
                
                obj_giro = await crud.giro.get_by_nomor_giro_and_payment_method(nomor_giro=giro_dt.nomor_giro, 
                                                                                        payment_method=giro_dt.payment_method)
                if obj_giro:
                    obj_giro.tanggal_buka = giro_dt.tanggal_buka
                    obj_giro.tanggal_cair = giro_dt.tanggal_cair
                    obj_giro.updated_by_id = created_by_id
                    obj_giro.updated_at = datetime.utcnow()

                    db_session.add(obj_giro)
                    
                else:
                    entity = CodeCounterEnum.Giro if giro_dt.payment_method == PaymentMethodEnum.Giro else CodeCounterEnum.Cek
                    last = await generate_code(entity=entity, db_session=db_session, with_commit=False)
                    obj_giro = Giro(code=f"{giro_dt.payment_method.value}-{last}",
                                                 nomor_giro=giro_dt.nomor_giro,
                                                 amount=giro_dt.amount,
                                                 is_active=True,
                                                 from_master=False,
                                                 tanggal=giro_dt.payment_date,
                                                 bank_code=giro_dt.bank_code,
                                                 payment_method=giro_dt.payment_method,
                                                 tanggal_buka=giro_dt.tanggal_buka,
                                                 tanggal_cair=giro_dt.tanggal_cair
                                                )
                    db_session.add(obj_giro)

            obj_payment_giro_detail = PaymentGiroDetail(**giro_dt.dict(exclude={"giro_id", "giro_index"}), 
                                                    giro_id=obj_giro.id if obj_giro else None, 
                                                    created_by_id=created_by_id, 
                                                    updated_by_id=created_by_id, 
                                                    created_at=datetime.utcnow, 
                                                    updated_at=datetime.utcnow)
            
            db_obj.giro_details.append(obj_payment_giro_detail)

            giro_temp.append({"payment_giro_detail_id" : obj_payment_giro_detail.id, "giro_index" : giro_dt.giro_index})

        for payment_dt in obj_in.details:
            obj_payment_giro_detail_id = next((giro_detail["payment_giro_detail_id"] for giro_detail in giro_temp if giro_detail["giro_index"] == payment_dt.giro_index), None)
            obj_payment_dt = PaymentDetail(**payment_dt.dict(exclude={"giro_index"}), 
                                            payment_giro_detail_id=obj_payment_giro_detail_id,
                                            created_by_id=created_by_id,
                                            updated_by_id=created_by_id,
                                            created_at=datetime.utcnow,
                                            updated_at=datetime.utcnow)
            
            db_obj.details.append(obj_payment_dt)

        for payment_komponen_biaya_dt in obj_in.komponens:
            obj_payment_giro_detail_id = next((giro_detail["payment_giro_detail_id"] for giro_detail in giro_temp if giro_detail["giro_index"] == payment_komponen_biaya_dt.giro_index), None)
            obj_invoices_dt = await crud.invoice_detail.get_multi_by_invoice_ids(list_ids=[dt.invoice_id for dt in obj_in.details], beban_biaya_id=payment_komponen_biaya_dt.beban_biaya_id)

            for inv_dt in obj_invoices_dt:
                obj_payment_komponen_biaya_dt = PaymentKomponenBiayaDetail(invoice_detail_id=inv_dt.id,
                                                                            payment_giro_detail_id=obj_payment_giro_detail_id,
                                                                            beban_biaya_id=payment_komponen_biaya_dt.beban_biaya_id,
                                                                            amount=payment_komponen_biaya_dt.amount,
                                                                            created_by_id=created_by_id,
                                                                            updated_by_id=created_by_id,
                                                                            created_at=datetime.utcnow,
                                                                            updated_at=datetime.utcnow)
                
                db_obj.komponen_biaya_details.append(obj_payment_komponen_biaya_dt)
        
        try:
            db_session.add(db_obj)
            if with_commit:
                await db_session.commit()
        except exc.IntegrityError:
            await db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
        
        if with_commit:
            await db_session.refresh(db_obj)
        return db_obj

    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> Payment | None:
        
        db_session = db_session or db.session
        
        query = select(Payment).where(Payment.id == id
                                ).options(selectinload(Payment.giro
                                                    ).options(selectinload(Giro.payment))
                                ).options(selectinload(Payment.details
                                                    ).options(selectinload(PaymentDetail.invoice
                                                                        ).options(selectinload(Invoice.bidang
                                                                                            ).options(selectinload(Bidang.planing)
                                                                                            ).options(selectinload(Bidang.skpt
                                                                                                                ).options(selectinload(Skpt.ptsk))
                                                                                            ).options(selectinload(Bidang.penampung)
                                                                                            ).options(selectinload(Bidang.invoices
                                                                                                                ).options(selectinload(Invoice.payment_details)
                                                                                                                ).options(selectinload(Invoice.termin))
                                                                                            )
                                                                        ).options(selectinload(Invoice.termin
                                                                                            ).options(selectinload(Termin.tahap))
                                                                        ).options(selectinload(Invoice.payment_details)
                                                                        ).options(selectinload(Invoice.details
                                                                                            ).options(selectinload(InvoiceDetail.bidang_komponen_biaya
                                                                                                                ).options(selectinload(BidangKomponenBiaya.beban_biaya))
                                                                                            )
                                                                        )
                                                    )
                                )
                                    
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()

payment = CRUDPayment(Payment)