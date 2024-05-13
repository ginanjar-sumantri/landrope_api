from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models import HasilPetaLokasi, HasilPetaLokasiDetail, Planing, Skpt, Bidang, Project, KjbDt, BundleHd, BundleDt
from schemas.hasil_peta_lokasi_sch import HasilPetaLokasiCreateSch, HasilPetaLokasiUpdateSch, HasilPetaLokasiReadySpkSch, HasilPetaLokasiUpdateCloud
from typing import List
from uuid import UUID
from datetime import datetime

class CRUDHasilPetaLokasi(CRUDBase[HasilPetaLokasi, HasilPetaLokasiCreateSch, HasilPetaLokasiUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> HasilPetaLokasi | None:
        
        db_session = db_session or db.session
        
        query = select(HasilPetaLokasi).where(HasilPetaLokasi.id == id
                                                    ).options(selectinload(HasilPetaLokasi.details
                                                                            ).options(selectinload(HasilPetaLokasiDetail.bidang
                                                                                            ).options(selectinload(Bidang.pemilik))
                                                                            ).options(selectinload(HasilPetaLokasiDetail.bidang_overlap)
                                                                            )
                                                    ).options(selectinload(HasilPetaLokasi.bidang)
                                                    ).options(selectinload(HasilPetaLokasi.kjb_dt
                                                                            ).options(selectinload(KjbDt.bundlehd
                                                                                            ).options(selectinload(BundleHd.bundledts
                                                                                                            ).options(selectinload(BundleDt.dokumen))
                                                                                            )
                                                                            )
                                                    ).options(selectinload(HasilPetaLokasi.request_peta_lokasi)
                                                    ).options(selectinload(HasilPetaLokasi.planing
                                                                            ).options(selectinload(Planing.project
                                                                                        ).options(selectinload(Project.sub_projects))
                                                                            ).options(selectinload(Planing.desa))
                                                    ).options(selectinload(HasilPetaLokasi.skpt
                                                                            ).options(selectinload(Skpt.ptsk))
                                                    ).options(selectinload(HasilPetaLokasi.pemilik)
                                                    ).options(selectinload(HasilPetaLokasi.sub_project))
                                                    

        response = await db_session.execute(query)

        return response.scalar_one_or_none()

    async def get_by_bidang_id(
                    self, 
                    *, 
                    bidang_id: UUID | str,
                    db_session: AsyncSession | None = None
                    ) -> HasilPetaLokasi | None:
        
        db_session = db_session or db.session
        query = select(HasilPetaLokasi).where(HasilPetaLokasi.bidang_id == bidang_id)

        response = await db_session.execute(query)

        return response.scalars().one_or_none()
    
    async def get_by_kjb_dt_id(
                    self, 
                    *, 
                    kjb_dt_id: UUID | str,
                    db_session: AsyncSession | None = None
                    ) -> HasilPetaLokasi | None:
        
        db_session = db_session or db.session
        query = select(HasilPetaLokasi).where(HasilPetaLokasi.kjb_dt_id == kjb_dt_id)

        response = await db_session.execute(query)

        return response.scalars().one_or_none()

    async def get_by_id_for_cloud(
                    self, 
                    *, 
                    id: UUID | str,
                    db_session: AsyncSession | None = None
                    ) -> HasilPetaLokasiUpdateCloud | None:
        
        db_session = db_session or db.session
        query = text(f"""
                    select
                    id,
                    bidang_id,
                    status_hasil_peta_lokasi,
                    hasil_analisa_peta_lokasi,
                    pemilik_id,
                    luas_surat,
                    planing_id,
                    sub_project_id,
                    skpt_id,
                    luas_ukur,
                    luas_nett,
                    luas_clear,
                    luas_gu_pt,
                    luas_gu_perorangan,
                    updated_by_id,
                    no_peta,
                    created_at
                    from hasil_peta_lokasi
                    where id = '{str(id)}'
                    """)

        response = await db_session.execute(query)

        return response.fetchone()
    
    async def get_ready_spk(self, keyword: str | None = None) -> list[HasilPetaLokasiReadySpkSch]:
        
        db_session = db.session

        searching = f"""
                    Where id_bidang like '%{keyword}%'
                    or alashak like '%{keyword}%'
                    or jenis_bayar like '%{keyword}%'
                    """ if keyword else ""
        
        query = f"""
                with subquery as (select
                b.id,
                b.id_bidang,
                b.alashak,
                tr.id as kjb_termin_id,
                hd.satuan_bayar,
                hd.satuan_harga,
                tr.nilai,
                'DP' as jenis_bayar,
                b.planing_id,
                hd.code as kjb_hd_code,
                b.group,
                b.manager_id
                from hasil_peta_lokasi hpl
                inner join bidang b ON b.id = hpl.bidang_id
                inner join kjb_dt dt ON dt.id = hpl.kjb_dt_id
                inner join kjb_harga hg ON hg.kjb_hd_id = dt.kjb_hd_id and hg.jenis_alashak = dt.jenis_alashak
                inner join kjb_termin tr ON hg.id = tr.kjb_harga_id and tr.jenis_bayar = 'DP' and tr.nilai > 0
                inner join kjb_hd hd ON hd.id = dt.kjb_hd_id
                Where 
                    NOT EXISTS (select 1 from checklist_kelengkapan_dokumen_dt c_dt
                                inner join checklist_kelengkapan_dokumen_hd c_hd ON c_hd.id = c_dt.checklist_kelengkapan_dokumen_hd_id
                                inner join bundle_dt b_dt ON b_dt.id = c_dt.bundle_dt_id and b_dt.meta_data is NULL
                                Where c_hd.bidang_id = b.id
                                and c_dt.jenis_bayar IN ('DP', 'UTJ'))
                    AND NOT EXISTS (select 1 from spk s
                                where s.bidang_id = b.id AND s.jenis_bayar = 'DP' and s.is_void is FALSE)
                    AND NOT EXISTS (select 1 from spk ss
                                where ss.bidang_id = b.id and ss.jenis_bayar = 'LUNAS' and ss.is_void is FALSE)
                    AND hpl.status_hasil_peta_lokasi = 'Lanjut'
                UNION
                select 
                b.id,
                b.id_bidang,
                b.alashak,
                tr.id as kjb_termin_id,
                hd.satuan_bayar,
                hd.satuan_harga,
                tr.nilai,
                'PELUNASAN' as jenis_bayar,
                b.planing_id,
                hd.code as kjb_hd_code,
                b.group,
                b.manager_id
                from hasil_peta_lokasi hpl
                inner join kjb_dt dt ON dt.id = hpl.kjb_dt_id
                inner join kjb_harga hg ON hg.kjb_hd_id = dt.kjb_hd_id and hg.jenis_alashak = dt.jenis_alashak
                inner join kjb_termin tr ON hg.id = tr.kjb_harga_id and tr.jenis_bayar = 'PELUNASAN' and tr.nilai > 0
                inner join kjb_hd hd ON hd.id = dt.kjb_hd_id
                inner join bidang b ON b.id = hpl.bidang_id
                Where 
                    NOT EXISTS (select 1 from checklist_kelengkapan_dokumen_dt c_dt
                                inner join checklist_kelengkapan_dokumen_hd c_hd ON c_hd.id = c_dt.checklist_kelengkapan_dokumen_hd_id
                                inner join bundle_dt b_dt ON b_dt.id = c_dt.bundle_dt_id
                                Where c_hd.bidang_id = b.id
                                and c_dt.jenis_bayar IN ('PELUNASAN', 'DP', 'UTJ')
                                and b_dt.meta_data is null)
                    AND NOT EXISTS (select 1 from spk s
                                where s.bidang_id = b.id AND s.jenis_bayar = 'PELUNASAN' and s.is_void is FALSE)
                    AND NOT EXISTS (select 1 from spk ss
                                where ss.bidang_id = b.id and ss.jenis_bayar = 'LUNAS' and ss.is_void is FALSE)
                    AND hpl.status_hasil_peta_lokasi = 'Lanjut'
                UNION
                select 
                b.id,
                b.id_bidang,
                b.alashak,
                null as kjb_termin_id,
                null as satuan_bayar,
                null as satuan_harga,
                null as nilai,
                'PENGEMBALIAN_BEBAN_PENJUAL' as jenis_bayar,
                b.planing_id,
                hd.code as kjb_hd_code,
                b.group,
                b.manager_id
                from hasil_peta_lokasi hpl
                inner join bidang b ON b.id = hpl.bidang_id
                inner join kjb_dt dt ON dt.id = hpl.kjb_dt_id
                inner join kjb_hd hd ON hd.id = dt.kjb_hd_id
                Where 
                    EXISTS (select 1 
                            from bidang_komponen_biaya kb
                            left outer join invoice_detail inv_dt ON inv_dt.bidang_komponen_biaya_id = kb.id
                            left outer join invoice inv ON inv.id = inv_dt.invoice_id
                            left outer join termin tr ON tr.id = inv.termin_id
                            where kb.is_void != true and kb.is_retur = true
                            and tr.id is null and tr.jenis_bayar = 'PENGEMBALIAN_BEBAN_PENJUAL')
                    AND NOT EXISTS (select 1 from checklist_kelengkapan_dokumen_hd c_hd
                                    inner join checklist_kelengkapan_dokumen_dt c_dt ON c_hd.id = c_dt.checklist_kelengkapan_dokumen_hd_id 
                                    and c_dt.jenis_bayar = 'BIAYA_LAIN'
                                    inner join bundle_dt b_dt ON b_dt.id = c_dt.bundle_dt_id
                                    Where c_hd.bidang_id = hpl.bidang_id
                                    and b_dt.meta_data is null)
                    AND NOT EXISTS (select 1 from spk s
                                where s.bidang_id = b.id AND s.jenis_bayar = 'PENGEMBALIAN_BEBAN_PENJUAL' and s.is_void is FALSE)

                    AND hpl.status_hasil_peta_lokasi = 'Lanjut'
                UNION
                select 
                b.id,
                b.id_bidang,
                b.alashak,
                null as kjb_termin_id,
                null as satuan_bayar,
                null as satuan_harga,
                null as nilai,
                'PAJAK' as jenis_bayar,
                b.planing_id,
                hd.code as kjb_hd_code,
                b.group,
                b.manager_id
                from hasil_peta_lokasi hpl
                inner join bidang b ON b.id = hpl.bidang_id
                inner join kjb_dt dt ON dt.id = hpl.kjb_dt_id
                inner join kjb_hd hd ON hd.id = dt.kjb_hd_id
                Where NOT EXISTS (select 1 from spk s
                                where s.bidang_id = b.id AND s.jenis_bayar = 'PAJAK' and s.is_void is FALSE)
                        AND hpl.status_hasil_peta_lokasi = 'Lanjut'
                Order by id_bidang)
                select s.*, 
                pr.name as project_name,
                ds.name as desa_name,
                mng.name as manager_name
                from subquery s
                inner join planing pl on pl.id = s.planing_id
                inner join project pr on pr.id = pl.project_id
                inner join desa ds on ds.id = pl.desa_id
                inner join manager mng on mng.id = s.manager_id
                {searching}
                """
        
        result = await db_session.execute(query)
        rows = result.all()

        objs = [HasilPetaLokasiReadySpkSch(id=row[0],
                                        id_bidang=row[1],
                                        alashak=row[2],
                                        kjb_termin_id=row[3],
                                        satuan_bayar=row[4],
                                        satuan_harga=row[5],
                                        nilai=row[6],
                                        jenis_bayar=row[7],
                                        planing_id=row[8],
                                        kjb_hd_code=row[9],
                                        group=row[10],
                                        manager_id=row[11],
                                        project_name=row[12],
                                        desa_name=row[13],
                                        manager_name=row[14]) for row in rows]
        
        return objs

hasil_peta_lokasi = CRUDHasilPetaLokasi(HasilPetaLokasi)