from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models import Termin, Invoice, Tahap, Bidang, Skpt, TerminBayar, PaymentDetail, Payment, Planing, InvoiceDetail
from schemas.termin_sch import (TerminCreateSch, TerminUpdateSch, TerminByIdForPrintOut, 
                                TerminInvoiceforPrintOut,
                                TerminBebanBiayaForPrintOut, TerminUtjHistoryForPrintOut)
from typing import List
from uuid import UUID

class CRUDTermin(CRUDBase[Termin, TerminCreateSch, TerminUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> Termin | None:
        
        db_session = db_session or db.session
        
        query = select(Termin).where(Termin.id == id).options(selectinload(Termin.tahap
                                                                ).options(selectinload(Tahap.planing
                                                                        ).options(selectinload(Planing.project))
                                                                ).options(selectinload(Tahap.ptsk))
                                                    ).options(selectinload(Termin.kjb_hd)
                                                    ).options(selectinload(Termin.invoices
                                                                ).options(selectinload(Invoice.details
                                                                        ).options(selectinload(InvoiceDetail.bidang_komponen_biaya))
                                                                ).options(selectinload(Invoice.bidang
                                                                        ).options(selectinload(Bidang.skpt
                                                                                        ).options(selectinload(Skpt.ptsk)
                                                                                        )
                                                                        ).options(selectinload(Bidang.planing)
                                                                        ).options(selectinload(Bidang.invoices
                                                                                        ).options(selectinload(Invoice.termin))
                                                                        )
                                                                ).options(selectinload(Invoice.payment_details
                                                                        ).options(selectinload(PaymentDetail.payment
                                                                                        ).options(selectinload(Payment.giro))
                                                                        )
                                                                ).options(selectinload(Invoice.spk)
                                                                )
                                                    ).options(selectinload(Termin.notaris)
                                                    ).options(selectinload(Termin.termin_bayars
                                                                ).options(selectinload(TerminBayar.rekening)
                                                                        )
                                                    ).options(selectinload(Termin.manager)
                                                    ).options(selectinload(Termin.sales)
                                                    )
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    

    async def get_by_id_for_printout(self, 
                  *, 
                  id: UUID | str, db_session: AsyncSession | None = None
                  ) -> TerminByIdForPrintOut | None:
        
        db_session = db_session or db.session

        query = text(f"""
                    select
                    tr.id,
                    tr.code,
                    t.id,
                    tr.created_at,
                    tr.tanggal_transaksi,
                    tr.tanggal_rencana_transaksi,
                    (tr.jenis_bayar || ' ' || Count(i.id) || 'BID' || ' (' || 'L Bayar' || ' ' || Sum(b.luas_bayar) || 'M2)' ) as jenis_bayar,
                    t.nomor_tahap,
                    SUM(i.amount) as amount,
                    pr.name as project_name,
                    Coalesce(tr.mediator, '') as mediator,
                    Coalesce(mng.name, '') as manager_name,
                    Coalesce(sls.name, '') as sales_name,
                    Coalesce(nt.name, '') as notaris_name,
                    tr.jenis_bayar,
                    tr.remark
                    from termin tr
                    inner join invoice i on i.termin_id = tr.id
                    inner join bidang b on b.id = i.bidang_id
                    left outer join tahap t on t.id = tr.tahap_id
                    left outer join planing pl on pl.id = t.planing_id
                    left outer join project pr on pr.id = pl.project_id
                    left outer join manager mng on mng.id = tr.manager_id
                    left outer join sales sls on sls.id = tr.sales_id
                    left outer join notaris nt on nt.id = tr.notaris_id
                    where tr.id = '{str(id)}'
                    group by tr.id, t.id, pr.id, mng.id, sls.id, nt.id
                    """)

        response = await db_session.execute(query)

        return response.fetchone()


    async def get_invoice_by_id_for_printout(self, 
                                            *, 
                                            id: UUID | str, 
                                            db_session: AsyncSession | None = None
                                            ) -> List[TerminInvoiceforPrintOut] | None:
            db_session = db_session or db.session
            query = select(Invoice.id.label("invoice_id"),
                        Invoice.bidang_id,
                        Invoice.amount).select_from(Termin
                                ).join(Invoice, Termin.id == Invoice.termin_id
                                ).where(and_(
                                    Termin.id == id,
                                    Invoice.is_void != True
                                ))
            

            response = await db_session.execute(query)

            return response.fetchall()
    
    async def get_beban_biaya_by_id_for_printout(self, 
                                                *, 
                                                id: UUID | str, 
                                                db_session: AsyncSession | None = None
                                                ) -> List[TerminBebanBiayaForPrintOut] | None:
        db_session = db_session or db.session
        query = text(f"""
                    select
                    b.id_bidang,
                    bb.name as beban_biaya_name,
                    case
                        when bkb.beban_pembeli is true then '(BEBAN PEMBELI)'
                        else '(BEBAN PENJUAL)'
                    end as tanggungan,
                    SUM(idt.amount) as amount
                    from termin t
                    inner join invoice i on i.termin_id = t.id
                    inner join invoice_detail idt on idt.invoice_id = i.id
                    inner join bidang_komponen_biaya bkb on bkb.id = idt.bidang_komponen_biaya_id
                    inner join bidang b on b.id = bkb.bidang_id
                    inner join beban_biaya bb on bb.id = bkb.beban_biaya_id
                    where i.is_void != true
                    and bkb.is_void != true
                    and t.id = '{str(id)}'
                    group by bb.id, bkb.id, b.id
                     """)
        

        response = await db_session.execute(query)

        return response.fetchall()

termin = CRUDTermin(Termin)