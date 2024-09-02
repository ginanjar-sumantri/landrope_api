from fastapi import HTTPException, UploadFile
from fastapi_async_sqlalchemy import db
from fastapi.encoders import jsonable_encoder
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy import exc
from sqlalchemy.orm import selectinload
from crud.base_crud import CRUDBase
from models import PelepasanHeader, PelepasanBidang, Bidang
from models.code_counter_model import CodeCounterEnum
from schemas.pelepasan_header_sch import PelepasanHeaderCreateSch, PelepasanHeaderEditSch, PelepasanHeaderUpdateSch
from schemas.pelepasan_bidang_sch import PelepasanBidangCreateSch

from services.gcloud_storage_service import GCStorageService

from common.generator import generate_code_reset_by_year


from uuid import UUID, uuid4
from datetime import datetime, date
import crud
import roman

class CRUDPelepasanHeader(CRUDBase[PelepasanHeader, PelepasanHeaderCreateSch, PelepasanHeaderUpdateSch]):    
    async def create(self, *, 
                     obj_in: PelepasanHeaderCreateSch | PelepasanHeader, 
                     created_by_id : UUID | str | None = None, 
                     db_session : AsyncSession | None = None,
                     with_commit: bool | None = True) -> PelepasanHeader :
        db_session = db_session or db.session
        db_obj = self.model.from_orm(obj_in) #type ignore
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()
        if created_by_id:
            db_obj.created_by_id = created_by_id
            db_obj.updated_by_id = created_by_id

        try:
            nomor_pelepasan_template = f"[code]/PELEPASAN/LA/{roman.toRoman(date.today().month)}/{date.today().year}"

            db_obj.nomor_pelepasan = await generate_code_reset_by_year(entity=CodeCounterEnum.Pelepasan,
                                                                    code_template=nomor_pelepasan_template,
                                                                    db_session=db_session, with_commit=False)

            db_session.add(db_obj)

            for dt in obj_in.pelepasan_bidangs:
                sch = PelepasanBidangCreateSch(bidang_id=dt, pelepasan_header_id=db_obj.id)
                await crud.pelepasan_bidang.create(obj_in=sch, created_by_id=created_by_id, db_session=db_session, with_commit=False)

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
                     obj_current : PelepasanHeader, 
                     obj_new : PelepasanHeaderEditSch,
                     updated_by_id: UUID | str | None = None,
                     db_session : AsyncSession | None = None,
                     with_commit: bool | None = True) -> PelepasanHeader :
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
        
        try:
            db_session.add(obj_current)

            current_pelepasan_bidangs = await crud.pelepasan_bidang.get_by_pelepasan_header_id(pelepasan_header_id=obj_current.id)
            current_ids = [x.id for x in current_pelepasan_bidangs]

            for dt in obj_new.pelepasan_bidangs:
                sch = PelepasanBidangCreateSch(bidang_id=dt, pelepasan_header_id=obj_current.id)
                await crud.pelepasan_bidang.create(obj_in=sch, created_by_id=updated_by_id, db_session=db_session, with_commit=False)

            for remove_id in current_ids:
                await crud.pelepasan_bidang.remove(id=remove_id, with_commit=False)

            if with_commit:
                await db_session.commit()
                await db_session.refresh(obj_current)

        except exc.IntegrityError:
            await db_session.rollback()
            raise HTTPException(status_code=400, detail="Failed Edit")

        return obj_current
    
    async def update(self, 
                     *, 
                     obj_current : PelepasanHeader, 
                     obj_new : PelepasanHeaderUpdateSch,
                     file: UploadFile | None = None,
                     updated_by_id: UUID | str | None = None,
                     db_session : AsyncSession | None = None,
                     with_commit: bool | None = True) -> PelepasanHeader :
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

        if file:
            obj_current.file_path = await GCStorageService().upload_file_dokumen(file=file, file_name=f"{obj_current.nomor_pelepasan.replace('/', '_')} - {uuid4().hex}")
        
        obj_current.is_lock = True
        
        try:
            db_session.add(obj_current)

            if with_commit:
                await db_session.commit()
                await db_session.refresh(obj_current)

        except exc.IntegrityError:
            await db_session.rollback()
            raise HTTPException(status_code=400, detail="Failed Edit")

        return obj_current

    async def get(self, 
                  *, 
                  id: UUID | str | None = None,
                  with_select_in_load: bool | None = False,
                  db_session: AsyncSession | None = None
                  ) -> PelepasanHeader | None:
        
        db_session = db_session or db.session

        query = select(PelepasanHeader).where(PelepasanHeader.id == id)

        if with_select_in_load:
            query = query.options(selectinload(PelepasanHeader.project), selectinload(PelepasanHeader.desa), 
                                selectinload(PelepasanHeader.ptsk), selectinload(PelepasanHeader.jenis_surat),
                                selectinload(PelepasanHeader.pelepasan_bidangs).options(selectinload(PelepasanBidang.bidang).options(selectinload(Bidang.pemilik))))

        response = await db_session.execute(query)

        return response.scalar_one_or_none()

pelepasan_header = CRUDPelepasanHeader(PelepasanHeader)