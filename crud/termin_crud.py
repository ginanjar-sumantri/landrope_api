from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from common.enum import JenisBayarEnum
from crud.base_crud import CRUDBase
from models import Termin, Invoice, Tahap, Bidang, Skpt, TerminBayar, PaymentDetail, Payment, Planing, InvoiceDetail, BidangKomponenBiaya, Spk
from schemas.termin_sch import (TerminCreateSch, TerminUpdateSch, TerminByIdForPrintOut, 
                                TerminInvoiceforPrintOut, TerminExcelSch,
                                TerminBebanBiayaForPrintOut, TerminUtjHistoryForPrintOut, TerminHistoriesSch)
from typing import List
from uuid import UUID

class CRUDTermin(CRUDBase[Termin, TerminCreateSch, TerminUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> Termin | None:
        
        db_session = db_session or db.session
        
        query = select(Termin).where(Termin.id == id)
        query = query.options(selectinload(Termin.tahap
                        ).options(selectinload(Tahap.planing
                                ).options(selectinload(Planing.project))
                        ).options(selectinload(Tahap.ptsk))
                ).options(selectinload(Termin.kjb_hd)
                ).options(selectinload(Termin.invoices
                        ).options(selectinload(Invoice.details
                                ).options(selectinload(InvoiceDetail.bidang_komponen_biaya
                                                ).options(selectinload(BidangKomponenBiaya.bidang)
                                                ).options(selectinload(BidangKomponenBiaya.beban_biaya))
                                )
                        ).options(selectinload(Invoice.bidang
                                ).options(selectinload(Bidang.skpt
                                                ).options(selectinload(Skpt.ptsk)
                                                )
                                ).options(selectinload(Bidang.planing)
                                ).options(selectinload(Bidang.invoices
                                                ).options(selectinload(Invoice.termin)
                                                ).options(selectinload(Invoice.payment_details))
                                )
                        ).options(selectinload(Invoice.payment_details
                                ).options(selectinload(PaymentDetail.payment
                                                ).options(selectinload(Payment.giro))
                                )
                        ).options(selectinload(Invoice.spk
                                                ).options(selectinload(Spk.bidang
                                                                ).options(selectinload(Bidang.komponen_biayas))
                                                )
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
                        t.id as tahap_id,
                        tr.created_at,
                        tr.tanggal_transaksi,
                        tr.tanggal_rencana_transaksi,
                        (tr.jenis_bayar || ' ' || Count(i.id) || 'BID' || ' (' || 'L Bayar' || ' ' || Sum(COALESCE(b.luas_bayar, 0)) || 'M2)' ) as jenis_bayar_ext,
                        t.nomor_tahap,
                        tr.nomor_memo,
                        SUM(i.amount) as amount,
                        pr.name as project_name,
                        ds.name as desa_name,
                        pt.name as ptsk_name,
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
                        left outer join desa ds on ds.id = pl.desa_id
                        left outer join ptsk pt on pt.id = t.ptsk_id
                        left outer join manager mng on mng.id = tr.manager_id
                        left outer join sales sls on sls.id = tr.sales_id
                        left outer join notaris nt on nt.id = tr.notaris_id
                        where tr.id = '{str(id)}'
                        group by tr.id, t.id, pr.id, ds.id, pt.id, mng.id, sls.id, nt.id
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
                                                jenis_bayar:JenisBayarEnum | None = None,
                                                db_session: AsyncSession | None = None
                                                ) -> List[TerminBebanBiayaForPrintOut] | None:
        db_session = db_session or db.session

        filter_by_jenis_bayar:str = ""
        if jenis_bayar == JenisBayarEnum.PENGEMBALIAN_BEBAN_PENJUAL:
             filter_by_jenis_bayar = "and bkb.is_retur = true"
        
        if jenis_bayar == JenisBayarEnum.BIAYA_LAIN:
             filter_by_jenis_bayar = "and bkb.is_add_pay = true"

        query = text(f"""
                        With subquery as (select
                        bb.name as beban_biaya_name,
                        case
                                when bkb.beban_pembeli is true and t.jenis_bayar != 'PENGEMBALIAN_BEBAN_PENJUAL' then '(Beban Pembeli)'
                                when bkb.beban_pembeli is false and t.jenis_bayar = 'PENGEMBALIAN_BEBAN_PENJUAL' then '(Pengembalian Beban Penjual)'
                        else '(Beban Penjual)'
                        end as tanggungan,
                        idt.amount As amount,
                        bkb.beban_pembeli,
                        bkb.is_void
                        from termin t
                        inner join invoice i on i.termin_id = t.id
                        inner join invoice_detail idt on idt.invoice_id = i.id
                        inner join bidang_komponen_biaya bkb on bkb.id = idt.bidang_komponen_biaya_id
                        inner join bidang b on b.id = bkb.bidang_id
                        inner join beban_biaya bb on bb.id = bkb.beban_biaya_id
                        where 
                        i.is_void != true
                        and bkb.is_void != true
                        {filter_by_jenis_bayar}
                        and t.id = '{str(id)}'
                        )
                        Select beban_biaya_name, tanggungan, coalesce(sum(amount), 0) as amount, beban_pembeli, is_void
                        from subquery
                        group by beban_biaya_name, tanggungan, beban_pembeli, is_void
                     """)


        response = await db_session.execute(query)

        return response.fetchall()
    
    async def get_termin_by_bidang_ids_for_excel(self, *, list_id:list[UUID]) -> list[TerminExcelSch]:
         
        db_session = db.session

        ids:str = ""
        for bidang_id in list_id:
             ids += f"'{bidang_id}',"
        
        ids = ids[0:-1]

        query = text(f"""
                        select
                        i.bidang_id as bidang_id,
                        b.id_bidang as id_bidang,
                        tr.jenis_bayar as jenis_bayar,
                        Coalesce(round(s.amount, 0)::text, '') as percentage,
                        i.amount::text as amount
                        from termin tr
                        inner join invoice i on i.termin_id = tr.id
                        inner join bidang b on i.bidang_id = b.id
                        left outer join spk s on s.id = i.spk_id
                        where i.bidang_id in ({ids});
                """)
        
        response = await db_session.execute(query)

        result = response.fetchall()

        result_return = [TerminExcelSch(**dict(tr)) for tr in result]

        return result_return
    
    async def get_multi_by_bidang_ids(self, bidang_ids:list[UUID], current_termin_id:UUID
                                      ) -> list[TerminHistoriesSch]:
        
        db_session = db.session

        ids:str = ""
        for bidang_id in bidang_ids:
                ids += f"'{bidang_id}',"
        
        ids = ids[0:-1]

        query = text(f"""
                with subquery as (select
                tr.id,
                case
                        when tr.jenis_bayar != 'UTJ' and tr.jenis_bayar != 'UTJ_KHUSUS' and tr.jenis_bayar != 'PENGEMBALIAN_BEBAN_PENJUAL' and tr.jenis_bayar != 'BIAYA_LAIN' then 
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
                Sum(pd.amount) as amount,
                tr.created_at
                from termin tr
                inner join invoice i on tr.id = i.termin_id
                inner join payment_detail pd on i.id = pd.invoice_id
                inner join payment py on py.id = pd.payment_id
                left outer join spk s on s.id = i.spk_id
                where tr.is_void != true
                and i.is_void != true
                and i.bidang_id in ({ids})
                and pd.is_void != true
                and py.is_void != true
                and tr.id != '{current_termin_id}'
                group by tr.id, tr.tanggal_transaksi, i.created_at, s.satuan_bayar, s.amount
                order by created_at asc)
                select id, str_jenis_bayar, tanggal_transaksi, jenis_bayar, sum(amount) as amount, created_at from subquery
                group by id, str_jenis_bayar, tanggal_transaksi, jenis_bayar, created_at
                order by created_at
                """)
        

        response = await db_session.execute(query)

        return response.fetchall()


termin = CRUDTermin(Termin)