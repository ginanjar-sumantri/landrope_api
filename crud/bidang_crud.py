from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, and_, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy import text
from sqlalchemy.orm import selectinload
from typing import List
from crud.base_crud import CRUDBase
from models import (Bidang, Skpt, Ptsk, Planing, Project, Desa, JenisSurat, JenisLahan, Kategori, KategoriSub, KategoriProyek, Invoice,
                    Manager, Sales, Notaris, BundleHd, HasilPetaLokasi, KjbDt, KjbHd, TahapDetail)
from schemas.bidang_sch import (BidangCreateSch, BidangUpdateSch, BidangPercentageLunasForSpk,
                                BidangForUtjSch, BidangTotalBebanPenjualByIdSch, BidangTotalInvoiceByIdSch)
from common.exceptions import (IdNotFoundException, NameNotFoundException, ImportFailedException, FileNotFoundException)
from common.enum import StatusBidangEnum
from services.gcloud_storage_service import GCStorageService
from services.geom_service import GeomService
from io import BytesIO
from uuid import UUID
from geoalchemy2 import functions
from shapely.geometry import shape
from geoalchemy2.shape import from_shape
from shapely  import wkt, wkb


class CRUDBidang(CRUDBase[Bidang, BidangCreateSch, BidangUpdateSch]):
    async def get_by_id(
                  self,
                  *,
                  id:UUID,
                  db_session: AsyncSession | None = None
    ) -> Bidang | None:
           
           db_session = db_session or db.session

           query = select(Bidang).where(Bidang.id == id).options(selectinload(Bidang.pemilik)
                                                        ).options(selectinload(Bidang.planing).options(selectinload(Planing.project)).options(selectinload(Planing.desa))
                                                        ).options(selectinload(Bidang.jenis_surat)
                                                        ).options(selectinload(Bidang.kategori)
                                                        ).options(selectinload(Bidang.kategori_sub)
                                                        ).options(selectinload(Bidang.kategori_proyek)
                                                        ).options(selectinload(Bidang.skpt).options(selectinload(Skpt.ptsk))
                                                        ).options(selectinload(Bidang.manager)
                                                        ).options(selectinload(Bidang.sales)
                                                        ).options(selectinload(Bidang.notaris)
                                                        ).options(selectinload(Bidang.bundlehd)
                                                        ).options(selectinload(Bidang.hasil_peta_lokasi)
                                                        ).options(selectinload(Bidang.sub_project)
                                                        ).options(selectinload(Bidang.invoices)
                                                        ).options(selectinload(Bidang.overlaps)
                                                        ).options(selectinload(Bidang.komponen_biayas)
                                                        ).options(selectinload(Bidang.tahap_details
                                                                            ).options(selectinload(TahapDetail.tahap))
                                                        )
           
           response = await db_session.execute(query)
           return response.scalar_one_or_none()
    
    async def get_by_id_for_tahap(
                  self,
                  *,
                  id:UUID,
                  db_session: AsyncSession | None = None
    ) -> Bidang | None:
           
           db_session = db_session or db.session

           query = select(Bidang).where(Bidang.id == id).options(selectinload(Bidang.planing
                                                                            ).options(selectinload(Planing.project)
                                                                            ).options(selectinload(Planing.desa)
                                                                            )
                                                        ).options(selectinload(Bidang.skpt
                                                                            ).options(selectinload(Skpt.ptsk))
                                                        ).options(selectinload(Bidang.overlaps)
                                                        ).options(selectinload(Bidang.sub_project)
                                                        ).options(selectinload(Bidang.hasil_peta_lokasi
                                                                            ).options(selectinload(HasilPetaLokasi.kjb_dt)
                                                                            )
                                                        )
           
           response = await db_session.execute(query)
           return response.scalar_one_or_none()
   
    async def get_by_id_bidang(
        self, *, idbidang: str, db_session: AsyncSession | None = None
    ) -> Bidang:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Bidang).where(Bidang.id_bidang == idbidang))
        return obj.scalar_one_or_none()
    
    async def get_by_id_bidang_lama(
        self, *, idbidang_lama: str, db_session: AsyncSession | None = None
    ) -> Bidang:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Bidang).where(Bidang.id_bidang_lama == idbidang_lama))
        return obj.scalar_one_or_none()
    
    async def get_by_id_bidang_id_bidang_lama(
        self, *, idbidang: str, idbidang_lama: str, db_session: AsyncSession | None = None
    ) -> Bidang:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Bidang).where(and_(Bidang.id_bidang == idbidang, Bidang.id_bidang_lama == idbidang_lama)))
        return obj.scalar_one_or_none()
    
    async def get_intersect_bidang(
            self, 
            *, 
            id:UUID | str,
            db_session : AsyncSession | None = None, 
            geom) -> list[Bidang] | None:
        
        # g = shape(geom)
        # wkb = from_shape(g)

        db_session = db_session or db.session
        query = select(Bidang
                       ).where(and_(Bidang.id != id, 
                                    functions.ST_IsValid(Bidang.geom) == True,
                                    Bidang.status != StatusBidangEnum.Batal)
                               ).filter(functions.ST_Intersects(Bidang.geom, geom))
        
        response =  await db_session.execute(query)
        
        return response.scalars().all()
        
    async def get_all_bidang_tree_report_map(
            self, 
            *,
            project_id:UUID,
            desa_id:UUID,
            ptsk_id:UUID,
            db_session : AsyncSession | None = None, 
            query : Bidang | Select[Bidang]| None = None
            ):
       
    
        db_session = db_session or db.session
        query = select(Bidang.id,
                       Bidang.id_bidang,
                       Bidang.id_bidang_lama,
                       Bidang.alashak,
                       Ptsk.id.label("ptsk_id"),
                       Ptsk.name.label("ptsk_name"),
                       Desa.id.label("desa_id"),
                       Desa.name.label("desa_name"),
                       Project.id.label("project_id"),
                       Project.name.label("project_name")
                       ).select_from(Bidang
                                    ).join(Skpt, Bidang.skpt_id == Skpt.id
                                    ).join(Ptsk, Skpt.ptsk_id == Ptsk.id
                                    ).join(Planing, Bidang.planing_id == Planing.id
                                    ).join(Desa, Planing.desa_id == Desa.id
                                    ).join(Project, Planing.project_id == Project.id
                                    ).where(and_(
                                        Project.id == project_id,
                                        Desa.id == desa_id,
                                        
                                    )).order_by(text("id_bidang asc"))
        
        if ptsk_id == UUID("00000000-0000-0000-0000-000000000000"):
            query = query.where(Bidang.skpt_id == None)
        else:
            query = query.where(Ptsk.id == ptsk_id)
        
        response =  await db_session.execute(query)
        return response.fetchall()
    
    async def get_multi_by_kjb_hd_id(self, 
                                *,
                                kjb_hd_id:UUID,
                               db_session : AsyncSession | None = None
                        ) -> List[BidangForUtjSch]:
        db_session = db_session or db.session
        
        query = select(Bidang.id.label("bidang_id"),
                       Bidang.id_bidang,
                       Bidang.luas_surat,
                       Project.name.label("project_name"),
                       Desa.name.label("desa_name")
                       ).join(HasilPetaLokasi, HasilPetaLokasi.bidang_id == Bidang.id
                            ).join(KjbDt, KjbDt.id == HasilPetaLokasi.kjb_dt_id
                            ).join(KjbHd, KjbHd.id == KjbDt.kjb_hd_id
                            ).outerjoin(Planing, Planing.id == Bidang.planing_id
                            ).outerjoin(Project, Project.id == Planing.project_id
                            ).outerjoin(Desa, Desa.id == Planing.desa_id
                            ).where(KjbHd.id == kjb_hd_id)

        response =  await db_session.execute(query)
        return response.fetchall()

    async def get_total_beban_penjual_by_bidang_id(
            self, 
            *, 
            bidang_id: UUID | str,
            db_session: AsyncSession | None = None
            ) -> BidangTotalBebanPenjualByIdSch | None:
        
        db_session = db_session or db.session
        query = text(f"""
                        select
                        b.id as bidang_id,
                        b.id_bidang,
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
                            End) As total_beban_penjual
                        from bidang b
                        inner join bidang_komponen_biaya kb on b.id = kb.bidang_id
                        inner join beban_biaya bb on bb.id = kb.beban_biaya_id
                        where kb.is_void != true
                        and kb.beban_pembeli = false
                        and b.id = '{str(bidang_id)}'
                        group by b.id
                """)

        response = await db_session.execute(query)

        return response.fetchone()
    
    async def get_total_invoice_by_bidang_id(
            self, 
            *, 
            bidang_id: UUID | str,
            db_session: AsyncSession | None = None
            ) -> BidangTotalInvoiceByIdSch | None:
        
        db_session = db_session or db.session
        query = text(f"""
                        select
                        b.id,
                        b.id_bidang,
                        sum(i.amount) as total_invoice
                        from bidang b
                        inner join invoice i on b.id = i.bidang_id
                        and i.is_void != true
                        and b.id = '{str(bidang_id)}'
                        group by b.id
                """)

        response = await db_session.execute(query)

        return response.fetchone()

    async def get_percentage_lunas(self,
                                   *, 
                                    bidang_id: UUID | str, 
                                    db_session: AsyncSession | None = None
                                    ) ->  BidangPercentageLunasForSpk | None:
            
            db_session = db_session or db.session

            query = text(f"""
                    select
                    bidang_id,
                    (100 - SUM(amount)) as percentage_lunas
                    from spk
                    where bidang_id = '{str(bidang_id)}'
                    group by bidang_id
                    """)

            response = await db_session.execute(query)

            return response.fetchone()
bidang = CRUDBidang(Bidang)