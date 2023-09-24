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
from schemas.termin_sch import (TerminCreateSch, TerminUpdateSch, TerminByIdForPrintOut, 
                                TerminBidangForPrintOut, TerminInvoiceforPrintOut, TerminInvoiceHistoryforPrintOut)
from typing import List
from uuid import UUID

class CRUDTermin(CRUDBase[Termin, TerminCreateSch, TerminUpdateSch]):

    async def get_by_id_for_printout(self, 
                  *, 
                  id: UUID | str, db_session: AsyncSession | None = None
                  ) -> TerminByIdForPrintOut | None:
        
        db_session = db_session or db.session

        query = select(self.model.id,
                       self.model.code,
                       self.model.tahap_id,
                       self.model.created_at).where(self.model.id == id)

        response = await db_session.execute(query)

        return response.fetchone()

    async def get_bidang_tahap_by_id_for_printout(self, 
                                                        *, 
                                                        id: UUID | str, 
                                                        db_session: AsyncSession | None = None
                                                        ) -> List[TerminBidangForPrintOut] | None:
        db_session = db_session or db.session
        query = text(f""""
                     
                    select
                    b.id as bidang_id,
                    b.id_bidang,
                    b.group,
                    case
                        when b.skpt_id is Null then pn.name
                        else pt.name
                    end as ptsk_name,
                    sk.status as status_il,
                    pr.name as project_name,
                    ds.name as desa_name,
                    pm.name as pemilik_name,
                    b.alashak,
                    b.luas_surat,
                    b.luas_ukur,
                    b.luas_gu_perorangan,
                    b.luas_nett,
                    b.luas_pbt_perorangan,
                    b.luas_bayar,
                    b.no_peta,
                    b.harga_transaksi,
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
            query = select(Bidang.id,
                           Bidang.id_bidang,
                           Termin.jenis_bayar,
                           Spk.nilai,
                           Spk.satuan_bayar,
                           Termin.created_at.label("tanggal_bayar"),
                           Invoice.amount
                           ).select_from(Invoice
                                ).join(Invoice, Termin.id == Invoice.termin_id
                                ).join(Spk, Spk.id == Invoice.spk_id
                                ).join(Bidang, Bidang.id == Invoice.bidang_id
                                ).where(and_(
                                    Invoice.is_void != True,
                                    Bidang.id.in_(b for b in list_id),
                                    Termin.id != termin_id
                                ))
            

            response = await db_session.execute(query)

            return response.fetchall()
    
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

termin = CRUDTermin(Termin)