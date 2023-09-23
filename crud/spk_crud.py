from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, case, text, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from crud.base_crud import CRUDBase
from models import Spk, Bidang
from schemas.spk_sch import SpkCreateSch, SpkUpdateSch, SpkForTerminSch, SpkPrintOut, SpkDetailPrintOut
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

    async def get_by_id_for_printout(self, 
                                     *, 
                                     id: UUID | str, 
                                     db_session: AsyncSession | None = None
                                     ) -> SpkPrintOut | None:
        
        db_session = db_session or db.session

        query = text(f"""
                select
                kh.code As kjb_hd_code,
                b.jenis_bidang,
                b.id_bidang,
                b.alashak,
                b.no_peta,
                b.group,
                b.luas_surat,
                b.luas_ukur,
                p.name As pemilik_name,
                ds.name As desa_name,
                nt.name As notaris_name,
                pr.name As project_name,
                pt.name As ptsk_name,
                sk.status As status_il,
                hpl.hasil_analisa_peta_lokasi As analisa,
                s.jenis_bayar,
                s.nilai,
                s.satuan_bayar,
                mng.name As manager_name,
                sls.name As sales_name,
				w.name as worker_name
                from spk s
                left join bidang b on s.bidang_id = b.id
                left join hasil_peta_lokasi hpl on b.id = hpl.bidang_id
                left join kjb_dt kd on hpl.kjb_dt_id = kd.id
                left join kjb_hd kh on kd.kjb_hd_id = kh.id
                left join pemilik p on b.pemilik_id = p.id
                left join planing pl on b.planing_id = pl.id
                left join project pr on pl.project_id = pr.id
                left join desa ds on pl.desa_id = ds.id
                left join notaris nt on b.notaris_id = nt.id
                left join skpt sk on b.skpt_id = sk.id
                left join ptsk pt on sk.ptsk_id = pt.id
                left join manager mng on b.manager_id = mng.id
                left join sales sls on b.sales_id = sls.id
				left join worker w on w.id = s.created_by_id
                where s.id = '{str(id)}'
        """)

        response = await db_session.execute(query)

        return response.fetchone()

    async def get_beban_biaya_by_id_for_printout(self, 
                                                 *, 
                                                 id: UUID | str, 
                                                 db_session: AsyncSession | None = None
                                                 ) -> SpkDetailPrintOut | None:
        db_session = db_session or db.session
        query = text(f"""
                    select 
                    case
                        when bkb.beban_pembeli = true Then 'DITANGGUNG PT'
                        else 'DITANGGUNG PENJUAL'
                    end as tanggapan,
                    bb.name
                    from spk s
                    inner join bidang b on b.id = s.bidang_id
                    inner join bidang_komponen_biaya bkb on bkb.bidang_id = b.id
                    inner join beban_biaya bb on bb.id = bkb.beban_biaya_id
                    where s.id = '{str(id)}'
                    and bb.is_tax = true
                    and bkb.is_void != true
                    """)

        response = await db_session.execute(query)

        return response.fetchall()

    async def get_kelengkapan_by_id_for_printout(self,
                                                *, 
                                                id: UUID | str, 
                                                db_session: AsyncSession | None = None
                                                ) -> SpkDetailPrintOut | None:
            
            db_session = db_session or db.session

            query = text(f"""
                    select 
                    d.name,
                    kd.tanggapan
                    from spk s
                    inner join spk_kelengkapan_dokumen kd on kd.spk_id = s.id
                    inner join bundle_dt bdt on bdt.id = kd.bundle_dt_id
                    inner join dokumen d on d.id = bdt.dokumen_id
                    where s.id = '{str(id)}'
                    """)

            response = await db_session.execute(query)

            return response.fetchall()
    
    async def get_rekening_by_id_for_printout(self,
                                                *, 
                                                id: UUID | str, 
                                                db_session: AsyncSession | None = None
                                                ) -> List[str] | None:
            
            db_session = db_session or db.session

            query = text(f"""
                    select 
                    (r.bank_rekening || ' (' || r.nomor_rekening || ') ' || ' a/n ' || r.nama_pemilik_rekening) as rekening
                    from spk s
                    inner join bidang b on b.id = s.bidang_id
                    left outer join pemilik p on p.id = b.pemilik_id
                    left outer join rekening r on r.pemilik_id = p.id
                    where s.id = '{str(id)}'
                    """)

            response = await db_session.execute(query)

            return response.fetchall()
spk = CRUDSpk(Spk)