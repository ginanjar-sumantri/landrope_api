from fastapi import HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from fastapi.security import HTTPBearer
from fastapi.encoders import jsonable_encoder
from sqlmodel import and_, select
from sqlmodel.ext.asyncio.session import AsyncSession
from crud.base_crud import CRUDBase
from models import Role, PeminjamanHeader
from models.code_counter_model import CodeCounterEnum
from sqlalchemy.orm import selectinload
from schemas.peminjaman_header_sch import PeminjamanHeaderCreateSch, PeminjamanHeaderUpdateSch, PeminjamanHeaderEditSch
from schemas.peminjaman_bidang_sch import PeminjamanBidangCreateSch
from schemas.peminjaman_penggarap_sch import PeminjamanPenggarapCreateSch
from typing import List
from sqlalchemy import text
from fastapi_async_sqlalchemy import db
from sqlalchemy import extract, desc
from datetime import datetime
from sqlalchemy import exc
import crud

from services.gcloud_storage_service import GCStorageService

from common.generator import generate_code_reset_by_year

from uuid import UUID, uuid4
import roman
from datetime import datetime, date

token_auth_scheme = HTTPBearer()


class CRUDPeminjamanHeader(CRUDBase[PeminjamanHeader, PeminjamanHeaderCreateSch, PeminjamanHeaderUpdateSch]):
    async def create(self, *, 
                     obj_in: PeminjamanHeaderCreateSch | PeminjamanHeader, 
                     created_by_id : UUID | str | None = None, 
                     db_session : AsyncSession | None = None,
                     with_commit: bool | None = True) -> PeminjamanHeader :
        db_session = db_session or db.session
        db_obj = self.model.from_orm(obj_in) #type ignore
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()
        if created_by_id:
            db_obj.created_by_id = created_by_id
            db_obj.updated_by_id = created_by_id

        try:

            if obj_in.kategori.lower() == "sawah":
                kat = "S"
            elif obj_in.kategori.lower() == "empang":
                    kat = "E"
            else:
                kat = ""
        
            nomor_perjanjian_template = f"[code]/{kat}/IZIN/LA/{roman.toRoman(date.today().month)}/{date.today().year}"

            db_obj.nomor_perjanjian = await generate_code_reset_by_year(entity=CodeCounterEnum.Peminjaman,
                                                                    code_template=nomor_perjanjian_template,
                                                                    db_session=db_session, with_commit=False)

            db_session.add(db_obj)

            for dt in obj_in.peminjaman_bidangs:
                sch = PeminjamanBidangCreateSch(bidang_id=dt, peminjaman_header_id=db_obj.id)
                await crud.peminjaman_bidang.create(obj_in=sch, created_by_id=created_by_id, db_session=db_session, with_commit=False)

            if with_commit:
                await db_session.commit()

        except exc.IntegrityError:
            await db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
        
        if with_commit:
            await db_session.refresh(db_obj)

        return db_obj
    
    async def edit(self, 
                     *, 
                     obj_current : PeminjamanHeader, 
                     obj_new : PeminjamanHeaderEditSch,
                     updated_by_id: UUID | str | None = None,
                     db_session : AsyncSession | None = None,
                     with_commit: bool | None = True) -> PeminjamanHeader :
        db_session =  db_session or db.session
        obj_data = jsonable_encoder(obj_current)

        if isinstance(obj_new, dict):
            update_data =  obj_new
        else:
            update_data = obj_new.dict(exclude_unset=True)
        
        for field in obj_data:
            if field in update_data:
                setattr(obj_current, field, update_data[field])
            if field == "updated_at":
                setattr(obj_current, field, datetime.utcnow())
        
        if updated_by_id:
            obj_current.updated_by_id = updated_by_id
        
        try:
            db_session.add(obj_current)

            current_peminjaman_bidangs = await crud.peminjaman_bidang.get_by_peminjaman_header_id(peminjaman_header_id=obj_current.id)
            current_ids = [x.id for x in current_peminjaman_bidangs]

            for dt in obj_new.peminjaman_bidangs:
                sch = PeminjamanBidangCreateSch(bidang_id=dt, peminjaman_header=obj_current.id)
                await crud.peminjaman_bidang.create(obj_in=sch, created_by_id=updated_by_id, db_session=db_session, with_commit=False)

            for remove_id in current_ids:
                await crud.peminjaman_bidang.remove(id=remove_id, with_commit=False)

            if with_commit:
                await db_session.commit()
                await db_session.refresh(obj_current)

        except exc.IntegrityError:
            await db_session.rollback()
            raise HTTPException(status_code=400, detail="Failed Edit")

        return obj_current
    
    async def update(self, 
                     *, 
                     obj_current : PeminjamanHeader, 
                     obj_new : PeminjamanHeaderUpdateSch,
                     file: UploadFile | None = None,
                     updated_by_id: UUID | str | None = None,
                     db_session : AsyncSession | None = None,
                     with_commit: bool | None = True) -> PeminjamanHeader :
        db_session =  db_session or db.session
        obj_data = jsonable_encoder(obj_current)

        if isinstance(obj_new, dict):
            update_data =  obj_new
        else:
            update_data = obj_new.dict(exclude_unset=True) #This tell pydantic to not include the values that were not sent
        
        for field in obj_data:
            if field in update_data:
                setattr(obj_current, field, update_data[field])
            if field == "updated_at":
                setattr(obj_current, field, datetime.utcnow())
        
        if updated_by_id:
            obj_current.updated_by_id = updated_by_id

        obj_current.is_lock = True
        
        try:
            db_session.add(obj_current)

            for dt in obj_new.peminjaman_penggaraps:
                    sch = PeminjamanPenggarapCreateSch(**dt.dict(exclude={"peminjaman_header_id"}), peminjaman_header_id=obj_current.id)
                    await crud.peminjaman_bidang.create(
                        obj_in=sch, 
                        created_by_id=updated_by_id, 
                        db_session=db_session, 
                        with_commit=False
                    )

            if with_commit:
                await db_session.commit()
                await db_session.refresh(obj_current)

        except exc.IntegrityError:
            await db_session.rollback()
            raise HTTPException(status_code=400, detail="Failed Updated")

        return obj_current

    async def get(self, 
                  *, 
                  id: UUID | str | None = None,
                  with_select_in_load: bool | None = False,
                  db_session: AsyncSession | None = None
                  ) -> PeminjamanHeader | None:
        
        db_session = db_session or db.session

        query = select(PeminjamanHeader).where(PeminjamanHeader.id == id)

        if with_select_in_load:
            query = query.options(selectinload(PeminjamanHeader.project), selectinload(PeminjamanHeader.desa), 
                                selectinload(PeminjamanHeader.ptsk), selectinload(PeminjamanHeader.peminjaman_bidangs))

        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
peminjaman_header = CRUDPeminjamanHeader(PeminjamanHeader)
