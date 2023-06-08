from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select
from sqlalchemy import exc

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.dokumen_model import BundleHd, BundleDt
from schemas.bundle_hd_sch import BundleHdCreateSch, BundleHdUpdateSch
from schemas.bundle_dt_sch import BundleDtCreateSch
from datetime import datetime
from uuid import UUID
import crud

class CRUDBundleHd(CRUDBase[BundleHd, BundleHdCreateSch, BundleHdUpdateSch]):
    async def create_and_generate(self, *, obj_in: BundleHdCreateSch | BundleHd, created_by_id : UUID | str | None = None, 
                     db_session : AsyncSession | None = None) -> BundleHd :
        db_session = db_session or db.session
        db_obj = self.model.from_orm(obj_in) #type ignore
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()
        if created_by_id:
            db_obj.created_by_id = created_by_id
        
        try:
            dokumens = await crud.dokumen.get_all()
            for i in dokumens:
                code = db_obj.code + i.code
                bundle_dt = BundleDt(code=code, dokumen_id=i.id)
                db_obj.bundledts.append(bundle_dt)

            db_session.add(db_obj)
            await db_session.commit()

        except exc.IntegrityError:
            await db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
        
        await db_session.refresh(db_obj)
        
        return db_obj

bundlehd = CRUDBundleHd(BundleHd)