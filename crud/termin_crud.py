from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.termin_model import Termin
from models.invoice_model import Invoice
from models.tahap_model import Tahap
from models.kjb_model import KjbHd
from models.spk_model import Spk
from models.bidang_model import Bidang
from models import Planing, Project, Worker
from schemas.termin_sch import (TerminCreateSch, TerminUpdateSch, TerminByIdForPrintOut, 
                                TerminBidangForPrintOut, TerminInvoiceforPrintOut, TerminInvoiceHistoryforPrintOut,
                                TerminBebanBiayaForPrintOut, TerminUtjHistoryForPrintOut)
from typing import List
from uuid import UUID

class CRUDTermin(CRUDBase[Termin, TerminCreateSch, TerminUpdateSch]):

    async def get(self, *, id: UUID | str, db_session: AsyncSession | None = None) -> Termin | None:
        db_session = db_session or db.session
        query = select(Termin).outerjoin(Tahap, Tahap.id == Termin.tahap_id
                        ).outerjoin(KjbHd, KjbHd.id == Termin.kjb_hd_id
                        ).outerjoin(Worker, Worker.id == Termin.updated_by_id
                        ).outerjoin(Invoice, Invoice.termin_id == Termin.id
                        ).where(Termin.id == id)
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
                    (tr.jenis_bayar || ' ' || Count(i.id) || 'BID' || ' (' || 'L Bayar' || ' ' || Sum(b.luas_bayar) || 'M2)' ) as jenis_bayar,
                    t.nomor_tahap,
                    SUM(i.amount) as amount,
                    pr.name as project_name
                    from termin tr
                    inner join invoice i on i.termin_id = tr.id
                    inner join bidang b on b.id = i.bidang_id
                    left outer join tahap t on t.id = tr.tahap_id
                    left outer join planing pl on pl.id = t.planing_id
                    left outer join project pr on pr.id = pl.project_id
                    where tr.id = '{str(id)}'
                    group by tr.id, t.id, pr.id
                    """)

        response = await db_session.execute(query)

        return response.fetchone()

    async def get_bidang_tahap_by_id_for_printout(self, 
                                                        *, 
                                                        id: UUID | str, 
                                                        db_session: AsyncSession | None = None
                                                        ) -> List[TerminBidangForPrintOut] | None:
        db_session = db_session or db.session
        query = text(f"""
                    select
                    b.id as bidang_id,
                    b.id_bidang,
                    b.group,
                    case
                        when b.skpt_id is Null then ds.name || '-' || pr.name || '-' || pn.name || ' (PENAMPUNG)'
                        else ds.name || '-' || pr.name || '-' || pt.name || ' (' || sk.status || ')'
                    end as lokasi,
					case
                        when b.skpt_id is Null then pn.name
                        else pt.name
                    end as ptsk_name,
                    sk.status as status_il,
                    pr.name as project_name,
                    ds.name as desa_name,
                    pm.name as pemilik_name,
                    b.alashak,
                    COALESCE(b.luas_surat, 0) as luas_surat,
                    COALESCE(b.luas_ukur,0) as luas_ukur,
                    COALESCE(b.luas_gu_perorangan,0) as luas_gu_perorangan,
                    COALESCE(b.luas_nett,0) as luas_nett,
                    COALESCE(b.luas_pbt_perorangan,0) as luas_pbt_perorangan,
                    COALESCE(b.luas_bayar,0) as luas_bayar,
                    b.no_peta,
                    COALESCE(b.harga_transaksi,0) as harga_transaksi,
                    (b.harga_transaksi * b.luas_bayar) as total_harga
                    from termin tr
                    inner join tahap th on th.id = tr.tahap_id
                    inner join tahap_detail thd on thd.tahap_id = th.id
                    inner join bidang b on b.id = thd.bidang_id
                    inner join planing pl on pl.id = b.planing_id
                    inner join project pr on pr.id = pl.project_id
                    inner join desa ds on ds.id = pl.desa_id
                    left outer join skpt sk on sk.id = b.skpt_id
                    left outer join ptsk pt on pt.id = sk.ptsk_id
                    left outer join ptsk pn on pn.id = b.penampung_id
                    left outer join pemilik pm on pm.id = b.pemilik_id
                    where tr.id = '{str(id)}' and thd.is_void != true
                    """)
        

        response = await db_session.execute(query)

        return response.fetchall()

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
    
    async def get_history_invoice_by_bidang_ids_for_printout(self, 
                                            *, 
                                            list_id: List[UUID] | List[str],
                                            termin_id:UUID | str,
                                            db_session: AsyncSession | None = None
                                            ) -> List[TerminInvoiceHistoryforPrintOut] | None:
            db_session = db_session or db.session
            # query = select(Bidang.id,
            #                Bidang.id_bidang,
            #                Termin.jenis_bayar,
            #                Spk.nilai,
            #                Spk.satuan_bayar,
            #                Termin.created_at.label("tanggal_bayar"),
            #                Invoice.amount
            #                ).select_from(Invoice
            #                     ).join(Termin, Termin.id == Invoice.termin_id
            #                     ).join(Spk, Spk.id == Invoice.spk_id
            #                     ).join(Bidang, Bidang.id == Invoice.bidang_id
            #                     ).where(and_(
            #                         Invoice.is_void != True,
            #                         Bidang.id.in_(b for b in list_id),
            #                         Termin.id != termin_id
            #                     ))
            ids:str = ""
            for bidang_id in list_id:
                ids += f"'{bidang_id}',"
            
            ids = ids[0:-1]

            query = text(f"""select 
                            b.id_bidang,
                            case
                                when tr.jenis_bayar != 'UTJ' then 
                                    case 
                                        when s.satuan_bayar = 'Percentage' then tr.jenis_bayar || ' ' || s.nilai || '%'
                                        else tr.jenis_bayar || ' (' || s.nilai || ')'
                                    end
                                else tr.jenis_bayar
                            end as str_jenis_bayar,
                            tr.tanggal_transaksi,
                            tr.jenis_bayar,
                            Sum(i.amount) as amount
                            from Invoice i
                            inner join Termin tr on tr.id = i.termin_id
                            inner join bidang b on b.id = i.bidang_id
                            left outer join spk s on s.id = i.spk_id
                            where tr.is_void != true
                            and i.is_void != true
                            and i.bidang_id in ({ids})
                            group by b.id, tr.jenis_bayar, tr.tanggal_transaksi, s.satuan_bayar, s.nilai
                         """)
            

            response = await db_session.execute(query)

            return response.fetchall()
    
    async def get_history_utj_by_bidang_ids_for_printout(self, 
                                            *, 
                                            ids:str,
                                            db_session: AsyncSession | None = None
                                            ) -> TerminUtjHistoryForPrintOut | None:
            db_session = db_session or db.session
            query = text(f"""
                        select 
                        b.id_bidang,
                        tr.jenis_bayar,
                        Sum(i.amount) as amount
                        from Invoice i
                        inner join Termin tr on tr.id = i.termin_id
                        inner join bidang b on b.id = i.bidang_id
                        where tr.is_void != true
                        and i.is_void != true
                        and tr.jenis_bayar = 'UTJ'
                        and i.bidang_id in ({ids})
                        group by b.id, tr.jenis_bayar
                        """)

            response = await db_session.execute(query)

            return response.fetchone()
    
    async def get_history_termin_by_tahap_id_for_printout(self, 
                                            *, 
                                            tahap_id: UUID | str,
                                            termin_id:UUID | str,
                                            db_session: AsyncSession | None = None
                                            ) -> List[TerminInvoiceHistoryforPrintOut] | None:
            db_session = db_session or db.session
            query = select(Termin.jenis_bayar,
                           Termin.amount
                           ).select_from(Termin
                                ).join(Tahap, Tahap.id == Termin.tahap_id
                                ).where(and_(
                                    Tahap.id == tahap_id,
                                    Termin.id != termin_id,
                                    Termin.is_void != True
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