from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, case, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from crud.base_crud import CRUDBase
from models import Spk, Bidang
from schemas.spk_sch import SpkCreateSch, SpkUpdateSch, SpkForTerminSch
from common.enum import JenisBayarEnum
from uuid import UUID
from decimal import Decimal
from typing import List


class CRUDSpk(CRUDBase[Spk, SpkCreateSch, SpkUpdateSch]):
    async def get_by_id_for_termin(self, *, id: UUID | str, db_session: AsyncSession | None = None) -> SpkForTerminSch | None:
        db_session = db_session or db.session
        query = select(Spk.id.label("spk_id"),
                       Spk.code.label("spk_code"),
                       Bidang.id.label("bidang_id"),
                       Bidang.id_bidang,
                       Bidang.alashak,
                       Bidang.group,
                       Bidang.luas_bayar,
                       Bidang.harga_transaksi,
                       Bidang.harga_akta,
                       (Bidang.luas_bayar * Bidang.harga_transaksi).label("total_harga"),
                       Spk.satuan_bayar,
                       Spk.nilai.label("spk_amount")
                       ).select_from(Spk
                            ).join(Bidang, Bidang.id == Spk.bidang_id
                            ).where(self.model.id == id)

        response = await db_session.execute(query)

        return response.fetchone()
    
    async def get_multi_by_tahap_id(self, 
                                *,
                                tahap_id:UUID,
                                jenis_bayar:JenisBayarEnum,
                               db_session : AsyncSession | None = None
                        ) -> List[SpkForTerminSch]:
        db_session = db_session or db.session
        
        query = text(f"""
                    SELECT 
                    s.id as spk_id,
                    s.code as spk_code,
                    s.satuan_bayar as spk_satuan_bayar,
                    s.nilai as spk_nilai,
                    b.id as bidang_id,
                    b.id_bidang,
                    b.alashak,
                    b.group,
                    b.luas_bayar,
                    b.harga_transaksi,
                    b.harga_akta,
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
                    SUM(CASE WHEN i.is_void != false THEN i.amount ELSE 0 END) As total_invoice,
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
                    End) + SUM(CASE WHEN i.is_void != false THEN i.amount ELSE 0 END))) As sisa_pelunasan,
                    CASE
                        WHEN s.satuan_bayar = 'Percentage' Then ROUND((s.nilai * (b.luas_bayar * b.harga_transaksi))/100, 2)
                        ELSE s.nilai
                    END As amount
                FROM spk s
                LEFT OUTER JOIN bidang b ON s.bidang_id = b.id
                LEFT OUTER JOIN tahap_detail td ON td.bidang_id = b.id
                LEFT OUTER JOIN invoice i ON i.spk_id = s.id
                LEFT OUTER JOIN tahap t ON t.id = td.tahap_id
                INNER JOIN bidang_komponen_biaya kb ON kb.bidang_id = b.id
                INNER JOIN beban_biaya bb ON kb.beban_biaya_id = bb.id
                WHERE 
                s.jenis_bayar = '{jenis_bayar}' and 
                (i.spk_id is null or i.is_void = true) and
                kb.is_void != true and
                and t.id = '{str(tahap_id)}'
                GROUP BY b.id, s.id
                """)

        response =  await db_session.execute(query)
        return response.fetchall()

spk = CRUDSpk(Spk)