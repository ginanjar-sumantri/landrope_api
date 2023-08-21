from crud.base_crud import CRUDBase
from models.bundle_model import BundleHd, BundleDt
from models.kjb_model import KjbDt
from models.dokumen_model import Dokumen
from schemas.bundle_dt_sch import BundleDtCreateSch, BundleDtUpdateSch, BundleDtMetaDynSch
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, and_
from fastapi_async_sqlalchemy import db

from uuid import UUID

class CRUDBundleDt(CRUDBase[BundleDt, BundleDtCreateSch, BundleDtUpdateSch]):
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
                                                        ))
        
        print(query)
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()

bundledt = CRUDBundleDt(BundleDt)