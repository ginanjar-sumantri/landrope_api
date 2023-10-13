from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models import Invoice, InvoiceDetail, BidangKomponenBiaya, PaymentDetail, Payment, Termin, Bidang, Skpt, Planing
from schemas.invoice_sch import InvoiceCreateSch, InvoiceUpdateSch, InvoiceForPrintOutUtj, InvoiceForPrintOut
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
                                                        ).options(selectinload(Bidang.planing
                                                                            ).options(selectinload(Planing.project)
                                                                            ).options(selectinload(Planing.desa))
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
                                            jenis_bayar:str,
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
                        where tr.jenis_bayar = '{jenis_bayar}'
                        and i.is_void != true
                        and tr.id = '{str(termin_id)}'
                        """)

            response = await db_session.execute(query)

            return response.fetchall()
    
    async def get_invoice_by_termin_id_for_printout(self, 
                                            *, 
                                            termin_id: UUID | str, 
                                            db_session: AsyncSession | None = None
                                            ) -> List[InvoiceForPrintOut] | None:
            db_session = db_session or db.session
            query = text(f"""
                        select
                        b.id as bidang_id,
                        b.id_bidang,
                        b.group,
                        b.jenis_bidang,
                        case
                            when b.skpt_id is Null then ds.name || '-' || pr.name || '-' || pn.name || ' (PENAMPUNG)'
                            else ds.name || '-' || pr.name || '-' || pt.name || ' (' || Replace(sk.status,  '_', ' ') || ')'
                        end as lokasi,
                        case
                            when b.skpt_id is Null then pn.name
                            else pt.name
                        end as ptsk_name,
                        sk.status as status_il,
                        pr.name as project_name,
                        ds.name as desa_name,
                        COALESCE(pm.name, '') as pemilik_name,
                        b.alashak,
                        COALESCE(b.luas_surat,0) as luas_surat,
                        COALESCE(b.luas_ukur,0) as luas_ukur,
                        COALESCE(b.luas_gu_perorangan,0) as luas_gu_perorangan,
                        COALESCE(b.luas_nett,0) as luas_nett,
                        COALESCE(b.luas_pbt_perorangan,0) as luas_pbt_perorangan,
                        COALESCE(b.luas_bayar,0) as luas_bayar,
                        COALESCE(b.no_peta, '') as no_peta,
                        COALESCE(b.harga_transaksi,0) as harga_transaksi,
                        (b.harga_transaksi * b.luas_bayar) as total_harga
                        from invoice i
                        inner join termin tr on i.termin_id = tr.id
                        inner join bidang b on b.id = i.bidang_id
                        inner join planing pl on pl.id = b.planing_id
                        inner join project pr on pr.id = pl.project_id
                        inner join desa ds on ds.id = pl.desa_id
                        left outer join skpt sk on sk.id = b.skpt_id
                        left outer join ptsk pt on pt.id = sk.ptsk_id
                        left outer join ptsk pn on pn.id = b.penampung_id
                        left outer join pemilik pm on pm.id = b.pemilik_id
                        where tr.id = '{str(termin_id)}'
                        and i.is_void != true
                        """)

            response = await db_session.execute(query)

            return response.fetchall()
    
invoice = CRUDInvoice(Invoice)