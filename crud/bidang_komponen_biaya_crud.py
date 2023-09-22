from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_, text
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.bidang_komponen_biaya_model import BidangKomponenBiaya
from schemas.bidang_komponen_biaya_sch import BidangKomponenBiayaCreateSch, BidangKomponenBiayaUpdateSch, BidangKomponenBiayaBebanPenjualSch
from typing import List
from uuid import UUID

class CRUDBidangKomponenBiaya(CRUDBase[BidangKomponenBiaya, BidangKomponenBiayaCreateSch, BidangKomponenBiayaUpdateSch]):
    async def get_by_bidang_id_and_beban_biaya_id(
            self, 
            *, 
            bidang_id: UUID | str, 
            beban_biaya_id: UUID | str, 
            db_session: AsyncSession | None = None) -> BidangKomponenBiaya | None:
        db_session = db_session or db.session
        query = select(self.model).where(and_(
                            self.model.bidang_id == bidang_id,
                            self.model.beban_biaya_id == beban_biaya_id
            ))
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_multi_by_bidang_id(
            self, 
            *, 
            bidang_id: UUID | str,
            db_session: AsyncSession | None = None
            ) -> List[BidangKomponenBiaya] | None:
        
        db_session = db_session or db.session
        query = select(self.model).where(self.model.bidang_id == bidang_id)
        response = await db_session.execute(query)

        return response.scalars().all()
    
    async def get_multi_beban_penjual_by_bidang_id(
            self, 
            *, 
            bidang_id: UUID | str,
            db_session: AsyncSession | None = None
            ) -> List[BidangKomponenBiayaBebanPenjualSch] | None:
        
        db_session = db_session or db.session
        query = text(f"""
                        select
                        b.id As bidang_id,
                        b.id_bidang,
                        b.alashak,
                        b.luas_surat,
                        b.luas_bayar,
                        b.harga_transaksi,
						kb.id As komponen_id,
                        bb.name,
                        bb.satuan_harga,
                        bb.satuan_bayar,
                        bb.amount as beban_biaya_amount,
                        CASE
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
                        END As total_beban
                        from bidang_komponen_biaya kb
                        inner join bidang b on kb.bidang_id = b.id
                        inner join beban_biaya bb on kb.beban_biaya_id = bb.id
                        where kb.beban_pembeli != true and kb.is_void != true
                        and b.id = '{str(bidang_id)}'
                """)

        response = await db_session.execute(query)

        return response.fetchall()

bidang_komponen_biaya = CRUDBidangKomponenBiaya(BidangKomponenBiaya)