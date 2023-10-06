from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models import Invoice, InvoiceDetail, BidangKomponenBiaya, PaymentDetail, Payment, Termin, Bidang, Skpt
from schemas.invoice_sch import InvoiceCreateSch, InvoiceUpdateSch, InvoiceForPrintOutUtj
from typing import List
from uuid import UUID

class CRUDInvoice(CRUDBase[Invoice, InvoiceCreateSch, InvoiceUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> Invoice | None:
        
        db_session = db_session or db.session
        
        query = select(Invoice).where(Invoice.id == id
                                    ).options(selectinload(Invoice.termin
                                                        ).options(selectinload(Termin.tahap))
                                    ).options(selectinload(Invoice.spk)
                                    ).options(selectinload(Invoice.bidang
                                                        ).options(selectinload(Bidang.skpt
                                                                        ).options(selectinload(Skpt.ptsk))
                                                        ).options(selectinload(Bidang.penampung)
                                                        )
                                    ).options(selectinload(Invoice.details
                                                        ).options(selectinload(InvoiceDetail.bidang_komponen_biaya
                                                                            ).options(selectinload(BidangKomponenBiaya.beban_biaya))
                                                        )
                                    ).options(selectinload(Invoice.payment_details
                                                        ).options(selectinload(PaymentDetail.payment
                                                                            ).options(selectinload(Payment.giro))
                                                        )
                                    )
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_invoice_by_termin_id_for_printout_utj(self, 
                                            *, 
                                            termin_id: UUID | str, 
                                            db_session: AsyncSession | None = None
                                            ) -> List[InvoiceForPrintOutUtj] | None:
            db_session = db_session or db.session
            query = text(f"""
                        select 
                        b.id as bidang_id,
                        pm.name as pemilik_name,
                        b.mediator,
                        b.alashak,
                        b.luas_surat,
                        b.id_bidang,
                        ds.name as desa_name,
                        b.no_peta,
                        pr.name as project_name,
                        case
                            when b.skpt_id is not null then pt.name
                            else pn.name || '(PENAMPUNG)'
                        end as ptsk_name,
                        i.amount,
                        tr.jenis_bayar
                        from invoice i
                        inner join termin tr on tr.id = i.termin_id
                        inner join bidang b on b.id = i.bidang_id
                        left outer join planing pl on pl.id = b.planing_id
                        left outer join project pr on pr.id = pl.project_id
                        left outer join desa ds on ds.id = pl.desa_id
                        left outer join skpt sk on sk.id = b.skpt_id
                        left outer join ptsk pt on pt.id = sk.ptsk_id
                        left outer join ptsk pn on pn.id = b.penampung_id
                        left outer join pemilik pm on pm.id = b.pemilik_id
                        where tr.jenis_bayar = 'UTJ'
                        and i.is_void != true
                        and tr.id = '{str(termin_id)}'
                        """)

            response = await db_session.execute(query)

            return response.fetchall()

invoice = CRUDInvoice(Invoice)