from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy import exc
from sqlalchemy.orm import selectinload
from common.generator import generate_code_bundle
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models import BundleHd, BundleDt, Planing, KjbDt, Bidang
from schemas.bundle_hd_sch import BundleHdCreateSch, BundleHdUpdateSch
from schemas.bundle_dt_sch import BundleDtCreateSch
from datetime import datetime
from uuid import UUID
import crud

class CRUDBundleHd(CRUDBase[BundleHd, BundleHdCreateSch, BundleHdUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> BundleHd | None:
        
        db_session = db_session or db.session
        
        query = select(BundleHd).where(BundleHd.id == id).options(selectinload(BundleHd.planing).options(selectinload(Planing.project)).options(selectinload(Planing.desa))
                                                        ).options(selectinload(BundleHd.kjb_dt
                                                                        ).options(selectinload(KjbDt.kjb_hd)
                                                                        )
                                                        ).options(selectinload(BundleHd.bidang
                                                                        ).options(selectinload(Bidang.planing
                                                                                            ).options(selectinload(Planing.project)
                                                                                            ).options(selectinload(Planing.desa)
                                                                                            )
                                                                        )
                                                        ).options(selectinload(BundleHd.bundledts
                                                                    ).options(selectinload(BundleDt.dokumen))
                                                        )

        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def create_and_generate(self, *, 
                                obj_in: BundleHdCreateSch | BundleHd, 
                                created_by_id : UUID | str | None = None, 
                                db_session : AsyncSession | None = None,
                                with_commit : bool | None = True) -> BundleHd :
        
        db_session = db_session or db.session
        db_obj = self.model.from_orm(obj_in) #type ignore
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()
        if created_by_id:
            db_obj.created_by_id = created_by_id
        
        try:
            db_obj.code = await generate_code_bundle(planing_id=db_obj.planing_id, db_session=db_session, with_commit=with_commit)

            dokumens = await crud.dokumen.get_all()
            for i in dokumens:
                if i.is_active == False:
                    continue
                
                code = db_obj.code + i.code
                bundle_dt = BundleDt(code=code, dokumen_id=i.id, created_by_id=created_by_id, updated_by_id=created_by_id)
                db_obj.bundledts.append(bundle_dt)

            db_session.add(db_obj)

            if with_commit:
                await db_session.commit()
                await db_session.refresh(db_obj)

        except exc.IntegrityError:
            await db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
        
        
        
        return db_obj
    
    async def get_by_keyword(self, *, keyword: str, db_session: AsyncSession | None = None) -> BundleHd | None:
        db_session = db_session or db.session
        query = select(self.model).where(and_(
                                self.model.keyword.ilike(f'%{keyword}%'),
                                BundleHd.kjb_dt == None, 
                                BundleHd.bidang == None
                                )).options(selectinload(self.model.kjb_dt)
                                ).options(selectinload(self.model.bidang)
                                )
        
        response = await db_session.execute(query)

        return response.scalars().first()

    async def get_by_dokumen_not_exists(self, dokumen_id:UUID):

        db_session = db.session

        query = f"""
                select hd.id from bundle_hd hd
                left join bundle_dt dt on hd.id = dt.bundle_hd_id and 
                    dt.dokumen_id = '{dokumen_id}'
                where dt.id is null
                """
        
        response = await db_session.execute(query)
        return response.fetchall()

bundlehd = CRUDBundleHd(BundleHd)