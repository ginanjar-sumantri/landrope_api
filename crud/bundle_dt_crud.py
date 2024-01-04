from sqlalchemy.orm import selectinload
from crud.base_crud import CRUDBase
from models import BundleHd, BundleDt, KjbDt, Dokumen
from schemas.bundle_dt_sch import BundleDtCreateSch, BundleDtUpdateSch, BundleDtMetaDynSch, BundleDtMetaData,BundleDtForCloud
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, and_, text
from fastapi_async_sqlalchemy import db

from uuid import UUID

class CRUDBundleDt(CRUDBase[BundleDt, BundleDtCreateSch, BundleDtUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> BundleDt | None:
        
        db_session = db_session or db.session
        
        query = select(BundleDt).where(BundleDt.id == id).options(selectinload(BundleDt.bundlehd
                                                                    ).options(selectinload(BundleHd.bidang)
                                                                    ).options(selectinload(BundleHd.kjb_dt))
                                                        ).options(selectinload(BundleDt.dokumen).options(selectinload(Dokumen.kategori_dokumen)))

        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_by_bundle_hd_id(self, 
                *,
                bundle_hd_id: UUID | str,
                db_session: AsyncSession | None = None
                ) -> list[BundleDt] | None:
        
        db_session = db_session or db.session
        query = select(self.model).where(self.model.bundle_hd_id == bundle_hd_id)

        response = await db_session.execute(query)

        return response.scalars().all()
    
    async def get_by_bundle_hd_id_and_dokumen_id(self, 
                *,
                bundle_hd_id: UUID | str,
                dokumen_id: UUID | str,
                db_session: AsyncSession | None = None
                ) -> BundleDt | None:
        
        db_session = db_session or db.session
        query = select(self.model).where(                                           
            and_(self.model.bundle_hd_id == bundle_hd_id,
                self.model.dokumen_id == dokumen_id))
        
        response = await db_session.execute(query)

        return response.scalars().one_or_none()
    
    async def get_by_bundle_hd_id_and_dokumen_id_for_cloud(self, 
                *,
                bundle_hd_id: UUID | str,
                dokumen_id: UUID | str,
                db_session: AsyncSession | None = None
                ) -> BundleDtForCloud | None:
        
        db_session = db_session or db.session
        query = select(self.model.id).where(                                           
            and_(self.model.bundle_hd_id == bundle_hd_id,
                self.model.dokumen_id == dokumen_id))
        
        response = await db_session.execute(query)

        return response.fetchone()
    
    async def get_meta_data_and_dyn_form(self, 
                                         *, 
                                         id: UUID | str,
                                         dokumen_id: UUID | str, 
                                         db_session: AsyncSession | None = None
                                         ) -> BundleDt | None:
        db_session = db_session or db.session
        query = select(BundleDt).select_from(BundleDt
                                            ).outerjoin(BundleHd, BundleDt.bundle_hd_id == BundleHd.id
                                            ).outerjoin(KjbDt, BundleHd.id == KjbDt.bundle_hd_id
                                            ).outerjoin(Dokumen, BundleDt.dokumen_id == Dokumen.id
                                            ).where(and_(
                                                            KjbDt.id == id,
                                                            Dokumen.id == dokumen_id
                                                        )).options(selectinload(BundleDt.dokumen))
        
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_meta_data_by_dokumen_name_and_bidang_id(self,
                                         *, 
                                         dokumen_name: str,
                                         bidang_id: UUID | str, 
                                         db_session: AsyncSession | None = None
                                         ) -> BundleDtMetaData | None:
        
        db_session = db_session or db.session

        query = text(f"""
                    select
                    b.id as bidang_id,
                    b.id_bidang,
                    bdt.meta_data,
                    d.key_field
                    from bundle_dt bdt
                    inner join bundle_hd bhd on bhd.id = bdt.bundle_hd_id
                    inner join bidang b on bhd.id = b.bundle_hd_id
                    inner join dokumen d on d.id = bdt.dokumen_id
                    where d.name = '{dokumen_name}'
                    and b.id = '{str(bidang_id)}'
                    """)
        
        response = await db_session.execute(query)

        return response.fetchone()
    
    async def get_multi_by_meta_data_and_dokumen_id(self, keyword:str|None = None, 
                                                dokumen_id:UUID|None=None,
                                                limit:int|None = 100) -> list[BundleDt]:

        db_session = db.session

        query = select(BundleDt)
        query = query.join(BundleDt.dokumen)
        query = query.where(and_(BundleDt.meta_data.ilike(f"%{keyword}%"), Dokumen.id == dokumen_id))
        query = query.order_by(BundleDt.updated_at.desc())
        query = query.limit(limit)
        query = query.options(selectinload(BundleDt.dokumen))

        response = await db_session.execute(query)

        return response.scalars().all()
    

bundledt = CRUDBundleDt(BundleDt)