from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from crud.base_crud import CRUDBase
from models.tahap_model import TahapDetail
from schemas.tahap_detail_sch import TahapDetailCreateSch, TahapDetailUpdateSch
from typing import List
from uuid import UUID

class CRUDTahapDetail(CRUDBase[TahapDetail, TahapDetailCreateSch, TahapDetailUpdateSch]):
    async def get_multi_removed_detail(
           self, 
           *, 
           list_ids: List[UUID | str],
           tahap_id:UUID | str,
           db_session : AsyncSession | None = None) -> List[TahapDetail] | None:
        
        db_session = db_session or db.session
        query = select(self.model).where(
            and_(
            ~self.model.id.in_(list_ids),
            self.model.tahap_id == tahap_id,
            self.model.is_void == False
        ))
        response =  await db_session.execute(query)
        return response.scalars().all()
   
    async def get_bidang_id_by_tahap_id(self, 
                                    *, 
                                    tahap_id:UUID | str,
                                    db_session : AsyncSession | None = None, 
                                    query : TahapDetail | Select[TahapDetail]| None = None
                                    ) -> List[UUID] | None:
        
        db_session = db_session or db.session
        if query is None:
            query = select(self.model.bidang_id).where(
                            and_(
                                    self.model.tahap_id == tahap_id,
                                    self.model.is_void != True
                                ))
        response =  await db_session.execute(query)
        return response.scalars().all()
    

    async def get_multi_by_tahap_id(self, 
                                    *, 
                                    tahap_id:UUID | str,
                                    db_session : AsyncSession | None = None, 
                                    query : TahapDetail | Select[TahapDetail]| None = None
                                    ) -> List[UUID] | None:
        
        db_session = db_session or db.session
        
        query = text(f"""
                    select
                    td.id,
                    t.id as tahap_id,
                    b.id as bidang_id,
                    b.id_bidang,
                    b.alashak,
                    b.group,
                    b.luas_surat,
                    b.luas_ukur,
                    b.luas_gu_perorangan,
                    b.luas_gu_pt,
                    b.luas_nett,
                    b.luas_clear,
                    b.luas_pbt_perorangan,
                    b.luas_pbt_pt,
                    b.luas_bayar,
                    b.harga_akta,
                    b.harga_transaksi,
                    b.harga_akta,
                    pr.name as project_name,
                    ds.name as desa_name,
                    pl.name as planing_name,
                    Case
                        When b.skpt_id is NULL Then pn.name
                        ELSE pt.name
                    End as ptsk_name,
                    (b.luas_bayar * b.harga_transaksi) as total_harga,
                    SUM(CASE
                            WHEN bb.satuan_bayar = 'Percentage' and bb.satuan_harga = 'Per_Meter2' Then
                                Case
                                    WHEN b.luas_bayar is Null Then ROUND((bb.amount * (b.luas_surat * b.harga_transaksi))/100, 2)
                                    ELSE ROUND((bb.amount * (b.luas_bayar * b.harga_transaksi))/100, 2)
                                End
                            WHEN bb.satuan_bayar = 'Amount' and bb.satuan_harga = 'Per_Meter2' Then
                                Case
                                    WHEN b.luas_bayar is Null Then ROUND((bb.amount * b.luas_surat), 2)
                                    ELSE ROUND((bb.amount * b.luas_bayar), 2)
                                End
                            WHEN bb.satuan_bayar = 'Amount' and bb.satuan_harga = 'Lumpsum' Then bb.amount
                        End) As total_beban,
                    SUM(i.amount) As total_invoice,
                    ((b.luas_bayar * b.harga_transaksi) - (SUM(CASE
                            WHEN bb.satuan_bayar = 'Percentage' and bb.satuan_harga = 'Per_Meter2' Then
                                Case
                                    WHEN b.luas_bayar is Null Then ROUND((bb.amount * (b.luas_surat * b.harga_transaksi))/100, 2)
                                    ELSE ROUND((bb.amount * (b.luas_bayar * b.harga_transaksi))/100, 2)
                                End
                            WHEN bb.satuan_bayar = 'Amount' and bb.satuan_harga = 'Per_Meter2' Then
                                Case
                                    WHEN b.luas_bayar is Null Then ROUND((bb.amount * b.luas_surat), 2)
                                    ELSE ROUND((bb.amount * b.luas_bayar), 2)
                                End
                            WHEN bb.satuan_bayar = 'Amount' and bb.satuan_harga = 'Lumpsum' Then bb.amount
                        End) + SUM(i.amount))) As sisa_pelunasan
                    from tahap_detail td
                    inner join bidang b on b.id = td.bidang_id
                    inner join tahap t on t.id = td.tahap_id
                    inner join invoice i on i.bidang_id = b.id
                    inner join invoice_detail idt on idt.invoice_id = i.id
                    inner join bidang_komponen_biaya kb on kb.id = idt.bidang_komponen_biaya_id
                    inner join beban_biaya bb on kb.beban_biaya_id = bb.id
                    left outer join planing pl on pl.id = b.planing_id
                    left outer join project pr on pr.id = pl.project_id
                    left outer join desa ds on ds.id = pl.desa_id
                    left outer join skpt sk on sk.id = b.skpt_id
                    left outer join ptsk pt on pt.id = sk.ptsk_id
                    left outer join ptsk pn on pn.id = b.penampung_id
                    where 
                    t.id = '{str(tahap_id)}'
                    and i.is_void != true
                    and kb.is_void != true
                    group by td.id, t.id, b.id, i.id, pr.id, ds.id, pl.id, pn.id, pt.id
            """)
            
        response =  await db_session.execute(query)
        return response.fetchall()
    

tahap_detail = CRUDTahapDetail(TahapDetail)