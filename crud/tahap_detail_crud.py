from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from crud.base_crud import CRUDBase
from models import TahapDetail, Bidang, Planing, Skpt, BidangKomponenBiaya
from schemas.tahap_detail_sch import TahapDetailCreateSch, TahapDetailUpdateSch, TahapDetailExtSch, TahapDetailForPrintOut
from typing import List
from uuid import UUID

class CRUDTahapDetail(CRUDBase[TahapDetail, TahapDetailCreateSch, TahapDetailUpdateSch]):
    async def get_multi_not_in_id_removed(
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

        query = query.options(selectinload(TahapDetail.bidang
                                        ).options(selectinload(Bidang.invoices))
                    )
        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_multi_in_id_removed(
           self, 
           *, 
           list_ids: List[UUID | str],
           tahap_id:UUID | str,
           db_session : AsyncSession | None = None) -> List[TahapDetail] | None:
        
        db_session = db_session or db.session
        query = select(self.model).where(
            and_(
            self.model.id.in_(list_ids),
            self.model.tahap_id == tahap_id,
            self.model.is_void == False
        ))

        query = query.options(selectinload(TahapDetail.bidang
                                        ).options(selectinload(Bidang.invoices))
                    )
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
    
    async def get_by_bidang_id(self, 
                                    *, 
                                    bidang_id:UUID | str,
                                    db_session : AsyncSession | None = None, 
                                    query : TahapDetail | Select[TahapDetail]| None = None
                                    ) -> TahapDetail | None:
        
        db_session = db_session or db.session
        if query is None:
            query = select(self.model.bidang_id).where(
                            and_(
                                    self.model.bidang_id == bidang_id,
                                    self.model.is_void != True
                                ))
        response =  await db_session.execute(query)
        return response.fetchone()

    async def get_multi_by_tahap_id_for_printout(self, 
                                            *, 
                                            tahap_id: UUID | str, 
                                            db_session: AsyncSession | None = None
                                            ) -> List[TahapDetailForPrintOut] | None:
            db_session = db_session or db.session
            query = text(f"""
                        select
                        td.id,
                        b.id as bidang_id,
                        b.id_bidang,
                        th.group,
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
                        COALESCE((b.harga_transaksi * b.luas_bayar), 0) as total_harga
                        from tahap_detail td
                        inner join tahap th on th.id = td.tahap_id
                        inner join bidang b on b.id = td.bidang_id
                        inner join planing pl on pl.id = b.planing_id
                        inner join project pr on pr.id = pl.project_id
                        inner join desa ds on ds.id = pl.desa_id
                        left outer join skpt sk on sk.id = b.skpt_id
                        left outer join ptsk pt on pt.id = sk.ptsk_id
                        left outer join ptsk pn on pn.id = b.penampung_id
                        left outer join pemilik pm on pm.id = b.pemilik_id
                        where 
                        td.tahap_id = '{str(tahap_id)}'
                        """)

            response = await db_session.execute(query)

            return response.fetchall()
    
    async def get_multi_by_tahap(self, 
                                    *, 
                                    tahap_id:UUID | str,
                                    db_session : AsyncSession | None = None, 
                                    query : TahapDetail | Select[TahapDetail]| None = None
                                    ) -> List[TahapDetail] | None:
        
        db_session = db_session or db.session
        
        query = select(TahapDetail).where(TahapDetail.tahap_id == tahap_id
                                        ).options(selectinload(TahapDetail.tahap)
                                        ).options(selectinload(TahapDetail.bidang
                                                            ).options(selectinload(Bidang.planing
                                                                                ).options(selectinload(Planing.project)
                                                                                ).options(selectinload(Planing.desa))
                                                            ).options(selectinload(Bidang.skpt
                                                                                ).options(selectinload(Skpt.ptsk))
                                                            ).options(selectinload(Bidang.penampung)
                                                            ).options(selectinload(Bidang.komponen_biayas
                                                                                ).options(selectinload(BidangKomponenBiaya.beban_biaya))
                                                            ).options(selectinload(Bidang.invoices)
                                                            )
                                        )
            
        response =  await db_session.execute(query)
        return response.fetchall()
    

tahap_detail = CRUDTahapDetail(TahapDetail)