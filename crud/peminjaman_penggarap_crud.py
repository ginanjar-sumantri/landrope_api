from fastapi import HTTPException
from fastapi.security import HTTPBearer
from fastapi.encoders import jsonable_encoder
from sqlmodel import and_, select
from sqlmodel.ext.asyncio.session import AsyncSession
from crud.base_crud import CRUDBase
from models import Role, PeminjamanPenggarap
from models import PeminjamanPenggarap
from schemas.peminjaman_penggarap_sch import PeminjamanPenggarapUpdateSch, PeminjamanPenggarapCreateSch, PeminjamanPenggarapSch
from fastapi_async_sqlalchemy import db
from datetime import datetime
from sqlalchemy import exc
import crud


from uuid import UUID, uuid4
from datetime import datetime, date

token_auth_scheme = HTTPBearer()


class CRUDPeminjamanPenggarap(CRUDBase[PeminjamanPenggarap, PeminjamanPenggarapCreateSch, PeminjamanPenggarapUpdateSch]):
    async def create(self, *, 
                     obj_in: PeminjamanPenggarapCreateSch | PeminjamanPenggarap, 
                     created_by_id : UUID | str | None = None, 
                     db_session : AsyncSession | None = None,
                     with_commit: bool | None = True) -> PeminjamanPenggarap :
        db_session = db_session or db.session
        db_obj = self.model.from_orm(obj_in) #type ignore
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()
        if created_by_id:
            db_obj.created_by_id = created_by_id
            db_obj.updated_by_id = created_by_id
        
        try:
            db_session.add(db_obj)
            if with_commit:
                await db_session.commit()
        except exc.IntegrityError:
            await db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
        
        if with_commit:
            await db_session.refresh(db_obj)

        return db_obj
    
peminjaman_penggarap = CRUDPeminjamanPenggarap(PeminjamanPenggarap)
