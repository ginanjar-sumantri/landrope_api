from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_, text, func
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from common.enum import JenisBayarEnum, ActivityEnum
from crud.base_crud import CRUDBase
from models import (Invoice, InvoiceDetail, InvoiceBayar, BidangKomponenBiaya, PaymentDetail, Payment, 
                    Termin, TerminBayar, Bidang, Skpt, Planing, Spk)
from schemas.invoice_sch import InvoiceCreateSch, InvoiceUpdateSch, InvoiceForPrintOutUtj, InvoiceForPrintOut, InvoiceHistoryforPrintOut, InvoiceLuasBayarSch
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
                                                        ).options(selectinload(Bidang.invoices
                                                                            ).options(selectinload(Invoice.payment_details)
                                                                            ).options(selectinload(Invoice.termin))
                                                        )
                                    ).options(selectinload(Invoice.details
                                                        ).options(selectinload(InvoiceDetail.bidang_komponen_biaya
                                                                            ).options(selectinload(BidangKomponenBiaya.beban_biaya)
                                                                            ).options(selectinload(BidangKomponenBiaya.bidang))
                                                        )
                                    ).options(selectinload(Invoice.payment_details
                                                        ).options(selectinload(PaymentDetail.payment
                                                                            ).options(selectinload(Payment.giro))
                                                        )
                                    )
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_utj_amount_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> Invoice | None:
        
        db_session = db_session or db.session
        
        query = select(Invoice).where(Invoice.id == id
                                    ).options(selectinload(Invoice.bidang
                                                    ).options(selectinload(Bidang.invoices
                                                                    ).options(selectinload(Invoice.termin)
                                                                    ).options(selectinload(Invoice.payment_details))
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
                        and i.amount > 0
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
                        i.id,
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
    
    async def get_multi_not_in_id_removed(self, *, list_ids: List[UUID | str], termin_id:UUID, db_session : AsyncSession | None = None
                                ) -> List[Invoice] | None:
        
        db_session = db_session or db.session
        query = select(self.model).where(and_(~self.model.id.in_(list_ids), 
                                              self.model.termin_id == termin_id)
                                              ).options(selectinload(Invoice.payment_details))
        
        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_multi_in_id_removed(self, *, 
                                    list_ids: List[UUID | str], 
                                    termin_id: UUID,
                                    db_session : AsyncSession | None = None) -> List[Invoice] | None:
        db_session = db_session or db.session
        query = select(self.model).where(and_(self.model.id.in_(list_ids), self.model.termin_id == termin_id)).options(selectinload(Invoice.payment_details))
        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_history_invoice_by_bidang_ids_for_printout(self, 
                                            *, 
                                            list_id: List[UUID] | List[str],
                                            termin_id:UUID | str,
                                            db_session: AsyncSession | None = None
                                            ) -> List[InvoiceHistoryforPrintOut] | None:
            db_session = db_session or db.session
            ids:str = ""
            for bidang_id in list_id:
                ids += f"'{bidang_id}',"
            
            ids = ids[0:-1]

            query = text(f"""
                            select 
                            b.id,
                            b.id_bidang,
                            case
                                when tr.jenis_bayar != 'UTJ' and tr.jenis_bayar != 'UTJ_KHUSUS' and tr.jenis_bayar != 'PENGEMBALIAN_BEBAN_PENJUAL' then 
                                    case 
                                        when s.satuan_bayar = 'Percentage' then tr.jenis_bayar || ' ' || Coalesce(s.amount,0) || '%'
                                        else tr.jenis_bayar || ' (' || s.amount || ')'
                                    end
                                else Replace(tr.jenis_bayar, '_', ' ')
                            end as str_jenis_bayar,
                            case
                                when tr.jenis_bayar = 'UTJ' then MAX(DATE(py.payment_date))
                                else MAX(DATE(py.payment_date))
                            end tanggal_transaksi,
                            tr.jenis_bayar,
                            Sum(pd.amount) as amount
                            from Invoice i
                            inner join Termin tr on tr.id = i.termin_id
                            inner join bidang b on b.id = i.bidang_id
                            inner join payment_detail pd on i.id = pd.invoice_id
                            inner join payment py on py.id = pd.payment_id
                            left outer join spk s on s.id = i.spk_id
                            where tr.is_void != true
                            and i.is_void != true
                            and i.bidang_id in ({ids})
                            and pd.is_void != true
                            and py.is_void != true
                            and tr.id != '{termin_id}'
                            group by b.id, tr.jenis_bayar, tr.tanggal_transaksi, i.created_at, s.satuan_bayar, s.amount
                         """)
            

            response = await db_session.execute(query)

            return response.fetchall()

    async def get_multi_history_invoice_by_bidang_id(self, 
                  *, 
                  bidang_id: UUID | str | None = None,
                  jenis_bayar: JenisBayarEnum | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> list[Invoice] | None:
        
        db_session = db_session or db.session
        
        query = select(Invoice)
        if jenis_bayar:
             query = query.join(Invoice.termin)
             query = query.filter(Termin.jenis_bayar == jenis_bayar)

        query = query.filter(Invoice.bidang_id == bidang_id)
        query = query.filter(Invoice.is_void != True)
        
        query = query.distinct()

        query = query.options(selectinload(Invoice.spk))
        query = query.options(selectinload(Invoice.termin))
        query = query.options(selectinload(Invoice.bidang
                                ).options(selectinload(Bidang.invoices
                                            ).options(selectinload(Invoice.termin)
                                            ).options(selectinload(Invoice.payment_details))
                                )
                    )
        query = query.options(selectinload(Invoice.details
                                ).options(selectinload(InvoiceDetail.bidang_komponen_biaya
                                            ).options(selectinload(BidangKomponenBiaya.bidang))
                                )
                    )
        query = query.options(selectinload(Invoice.payment_details))
        
        response = await db_session.execute(query)

        return response.scalars().all()

    #for update in termin function
    async def get_ids_by_termin_id(self, *, termin_id:UUID | str | None = None) -> list[UUID]:
        db_session = db.session

        query = select(Invoice).where(Invoice.termin_id == termin_id)
        
        response = await db_session.execute(query)
        result = response.scalars().all()

        datas = [data.id for data in result]
        return datas
         

    async def get_multi_by_termin_id(self, 
                  *, 
                  termin_id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> list[Invoice] | None:
        
        db_session = db_session or db.session
        
        query = select(Invoice)

        query = query.filter(Invoice.termin_id == termin_id)
        query = query.filter(Invoice.is_void != True)

        query = query.options(selectinload(Invoice.spk))
        query = query.options(selectinload(Invoice.termin))
        query = query.options(selectinload(Invoice.bidang
                                ).options(selectinload(Bidang.invoices
                                            ).options(selectinload(Invoice.termin)
                                            ).options(selectinload(Invoice.payment_details))
                                )
                    )
        
        query = query.options(selectinload(Invoice.details
                                ).options(selectinload(InvoiceDetail.bidang_komponen_biaya
                                            ).options(selectinload(BidangKomponenBiaya.bidang))
                                )
                    ).options(selectinload(Invoice.bayars)
                    )
        query = query.options(selectinload(Invoice.payment_details))
        
        response = await db_session.execute(query)

        return response.scalars().all()
    
    async def get_multi_invoice_active_by_termin_id(self, 
                  *, 
                  termin_id: UUID | str | None = None,
                  invoice_id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> list[Invoice] | None:
        
        db_session = db_session or db.session
        
        query = select(Invoice).where(and_(Invoice.is_void == False, Invoice.id != invoice_id, Invoice.termin_id == termin_id))
        
        response = await db_session.execute(query)

        return response.scalars().all()

    async def get_multi_outstanding_invoice(self, 
                  *, 
                  keyword: str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> list[Invoice] | None:
        
        db_session = db_session or db.session

        filter:str = ""
        
        if keyword:
             filter = f"""
                    AND (lower(b.id_bidang) LIKE lower('%{keyword}%') OR 
                    lower(b.alashak) LIKE lower('%{keyword}%') OR 
                    lower(i.code) LIKE lower('%{keyword}%') OR 
                    lower(t.code) LIKE lower('%{keyword}%') OR 
                    lower(t.nomor_memo) LIKE lower('%{keyword}%'))
                    """

        query = text(f"""
                    WITH
                    payment_detail_query AS (SELECT 
                        pdt.invoice_id,
                        SUM(pdt.amount) AS amount
                    FROM payment_detail pdt
                        INNER JOIN invoice i ON i.id = pdt.invoice_id
                    WHERE COALESCE(pdt.is_void, FALSE) IS FALSE
                        AND COALESCE(i.is_void, FALSE) IS FALSE
                        AND COALESCE(pdt.realisasi, FALSE) IS FALSE
                    GROUP BY pdt.invoice_id)
                    SELECT
                        i.*
                    FROM invoice i
                        LEFT JOIN payment_detail_query p ON i.id = p.invoice_id
                        INNER JOIN termin tr ON tr.id = i.termin_id
                        INNER JOIN bidang b ON b.id = i.bidang_id
                    WHERE 
                        COALESCE(i.amount_netto, 0) - COALESCE(p.amount, 0) > 0
                        AND COALESCE(i.is_void, FALSE) IS FALSE
                    {filter}
        """)

        query = query.options(selectinload(Invoice.bidang)
                            ).options(selectinload(Invoice.termin
                                                ).options(selectinload(Termin.tahap))
                            ).options(selectinload(Invoice.payment_details)
                            ).options(selectinload(Invoice.details
                                                ).options(selectinload(InvoiceDetail.bidang_komponen_biaya
                                                                    ).options(selectinload(BidangKomponenBiaya.beban_biaya))
                                                )
                            ).options(selectinload(Invoice.bidang
                                                ).options(selectinload(Bidang.invoices
                                                                    ).options(selectinload(Invoice.termin)
                                                                    ).options(selectinload(Invoice.payment_details))
                                                )
                            )
        
        response = await db_session.execute(query)

        return response.fetchall()
    
    async def get_multi_outstanding_utj_invoice(self, 
                  *, 
                  keyword: str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> list[Invoice] | None:
        
        db_session = db_session or db.session

        filter:str = ""
        
        if keyword:
             filter = f"""
                    AND (lower(b.id_bidang) LIKE lower('%{keyword}%') OR 
                    lower(b.alashak) LIKE lower('%{keyword}%') OR 
                    lower(i.code) LIKE lower('%{keyword}%') OR 
                    lower(t.code) LIKE lower('%{keyword}%') OR 
                    lower(t.nomor_memo) LIKE lower('%{keyword}%'))
                    """

        query = text(f"""
                    with payment as (select sum(amount) as amount, invoice_id from payment_detail
                    where is_void != True
                    and COALESCE(realisasi, False) is False
                    group by invoice_id)
                    select i.* from invoice i
                    left join payment p on p.invoice_id = i.id
                    inner join bidang b on b.id = i.bidang_id
                    inner join termin t on t.id = i.termin_id
                    where i.is_void is false
                    and t.jenis_bayar in ('UTJ', 'UTJ_KHUSUS')
                    and (i.amount - Coalesce(p.amount, 0)) > 0
                    and COALESCE(i.realisasi, False) is False
                    {filter}
        """)

        query = query.options(selectinload(Invoice.bidang)
                            ).options(selectinload(Invoice.termin
                                                ).options(selectinload(Termin.tahap))
                            ).options(selectinload(Invoice.payment_details)
                            ).options(selectinload(Invoice.details
                                                ).options(selectinload(InvoiceDetail.bidang_komponen_biaya
                                                                    ).options(selectinload(BidangKomponenBiaya.beban_biaya))
                                                )
                            ).options(selectinload(Invoice.bidang
                                                ).options(selectinload(Bidang.invoices
                                                                    ).options(selectinload(Invoice.termin)
                                                                    ).options(selectinload(Invoice.payment_details))
                                                )
                            )
        
        response = await db_session.execute(query)

        return response.fetchall()
    
    async def get_multi_invoice_id_luas_bayar_by_termin_id(self, 
                  *, 
                  termin_id: UUID,
                  db_session: AsyncSession | None = None
                  ) -> list[InvoiceLuasBayarSch] | None:
        
        db_session = db_session or db.session

        query = text(f"""
                        select i.id, b.luas_bayar 
                        from invoice i
                        inner join bidang b on i.bidang_id = b.id
                        where i.termin_id = '{str(termin_id)}'
                        and i.is_void != True
                        and b.luas_bayar is not null
        """)
        
        response = await db_session.execute(query)

        result = response.fetchall()

        return [InvoiceLuasBayarSch(**dict(ret)) for ret in result]
    
    #to get invoice utj for payment memo bayar include utj
    async def get_multi_by_bidang_ids(self, 
                  *, 
                  bidang_ids: List[UUID]| list[str] | None = None,
                  db_session: AsyncSession | None = None
                  ) -> list[Invoice] | None:
        
        db_session = db_session or db.session
        
        query = select(Invoice).join(Termin, Termin.id == Invoice.termin_id)

        query = query.filter(Invoice.is_void != True)
        query = query.filter(Invoice.bidang_id.in_(bidang_ids))
        query = query.filter(Termin.jenis_bayar.in_([JenisBayarEnum.UTJ, JenisBayarEnum.UTJ_KHUSUS]))
        
        query = query.options(selectinload(Invoice.spk))
        query = query.options(selectinload(Invoice.termin))
        query = query.options(selectinload(Invoice.bidang
                                ).options(selectinload(Bidang.invoices
                                            ).options(selectinload(Invoice.termin)
                                            ).options(selectinload(Invoice.payment_details))
                                )
                    )
        query = query.options(selectinload(Invoice.details
                                ).options(selectinload(InvoiceDetail.bidang_komponen_biaya
                                            ).options(selectinload(BidangKomponenBiaya.bidang))
                                )
                    )
        query = query.options(selectinload(Invoice.payment_details))
        
        response = await db_session.execute(query)

        return response.scalars().all()
    
    async def get_multi_by_bidang_id(self, 
                  *, 
                  bidang_id: UUID | None = None,
                  db_session: AsyncSession | None = None
                  ) -> list[Invoice] | None:
        
        db_session = db_session or db.session
        
        query = select(Invoice).where(Invoice.bidang_id == bidang_id)
        
        response = await db_session.execute(query)

        return response.scalars().all()
    
    async def get_multi_by_bidang_id_and_termin_is_draft(self, *, bidang_id:UUID | str | None = None) -> list[Invoice]:
        db_session = db.session

        query = select(Invoice).join(Termin, and_(Termin.is_draft == True, Termin.id == Invoice.termin_id)
                            ).where(Invoice.bidang_id == bidang_id)
        
        response = await db_session.execute(query)
        return response.scalars().all()
    
    async def get_invoice_have_termin_bayar_utj_by_bidang_id(self, 
                  *, 
                  bidang_id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> Invoice| None:
        
        db_session = db_session or db.session
        
        query = select(Invoice).join(InvoiceBayar, Invoice.id == InvoiceBayar.invoice_id
                            ).join(TerminBayar, TerminBayar.id == InvoiceBayar.termin_bayar_id
                            ).where(and_(
                                 Invoice.is_void == False,
                                 InvoiceBayar.amount > 0,
                                 TerminBayar.activity == ActivityEnum.UTJ,
                                 Invoice.bidang_id == bidang_id
                            )
                            ).limit(1)

        
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()

invoice = CRUDInvoice(Invoice)