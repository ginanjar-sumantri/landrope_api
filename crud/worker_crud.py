from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPBearer
from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession

import crud
from crud.base_crud import CRUDBase
from models.worker_model import Worker
from schemas.oauth import OauthUser
from schemas.worker_sch import WorkerCreateSch, WorkerUpdateSch
from services.oauth_service import OauthService

token_auth_scheme = HTTPBearer()


class CRUDWorker(CRUDBase[Worker, WorkerCreateSch, WorkerUpdateSch]):
    async def get_by_email(self, *, email: str, db_session: AsyncSession | None = None) -> Worker:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Worker).where(Worker.email == email))
        return obj.scalar_one_or_none()

    # async def get_by_phone(self, *, phone: str, db_session: AsyncSession | None = None) -> Worker:
    #     db_session = db_session or db.session
    #     obj = await db_session.execute(select(Worker).where(Worker.phone == phone))
    #     return obj.scalar_one_or_none()

    # async def get_phone_exclude_me(self, *, phone: str, db_session: AsyncSession | None = None, worker_id: UUID) -> List[Worker] | None:
    #     db_session = db_session or db.session
    #     objs = await db_session.execute(select(Worker).filter(Worker.phone == phone).filter(Worker.id != worker_id))
    #     return objs.scalars().all()

    async def get_email_exclude_me(self, *, email: str, db_session: AsyncSession | None = None, worker_id: UUID) -> List[Worker] | None:
        db_session = db_session or db.session
        objs = await db_session.execute(select(Worker).filter(Worker.email == email).filter(Worker.id != worker_id))
        return objs.scalars().all()

    async def create(self, *, obj_in: WorkerCreateSch, worker_id: UUID | str | None = None, db_session: AsyncSession | None = None, oauth_user: OauthUser | None = None) -> Worker:
        db_session = db_session or db.session
        db_obj = self.model.from_orm(obj_in)
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()
        db_obj.created_by_id = worker_id
        db_obj.updated_by_id = worker_id

        if oauth_user:
            db_obj.oauth_id = oauth_user.id

        try:
            for i in obj_in.roles_id:
                role = crud.role.get(id=i)
                if role:
                    db_obj.roles.append(role)

            for p in obj_in.project_id:
                project = crud.project.get(id=p)
                if project:
                    db_obj.projects.append(project)

            db_session.add(db_obj)
            await db_session.commit()
        except Exception as ex:
            await db_session.rollback()
            raise HTTPException(
                status_code=409,
                detail=str(ex),
            )
        await db_session.refresh(db_obj)
        return db_obj

    async def update(self, *, obj_current: Worker, obj_new: WorkerUpdateSch, db_session: AsyncSession | None = None, worker_id: UUID | str | None = None) -> Worker:
        db_session = db_session or db.session
        obj_data = jsonable_encoder(obj_current)

        if isinstance(obj_new, dict):
            update_data = obj_new
        else:
            update_data = obj_new.dict(
                exclude_unset=True
            )  # This tells Pydantic to not include the values that were not sent
        for field in obj_data:
            if field in update_data:
                setattr(obj_current, field, update_data[field])
            if field == "updated_at":
                setattr(obj_current, field, datetime.utcnow())

        obj_current.updated_by_id = worker_id

        try:
            obj_current.roles = []
            for i in obj_new.roles_id:
                role = await crud.role.get(id=i)
                if role:
                    obj_current.roles.append(role)

            obj_current.projects = []
            for p in obj_new.project_id:
                project = await crud.project.get(id=p)
                if project:
                    obj_current.projects.append(project)
            db_session.add(obj_current)

        except Exception as ex:
            await db_session.rollback()
            raise HTTPException(
                status_code=409,
                detail="Resource already exists",
            )
        await db_session.commit()

        return obj_current

    async def remove(self, *, id: UUID | str, db_session: AsyncSession | None = None, worker_id: UUID) -> Worker:
        db_session = db_session or db.session
        response = await db_session.execute(
            select(self.model).where(self.model.id == id)
        )
        obj = response.scalar_one()
        obj.is_active = False
        obj.updated_by_id = worker_id
        db_session.add(obj)
        await db_session.commit()
        await db_session.refresh(obj)
        return obj

    async def get_current_user(self, token: str = Depends(token_auth_scheme)) -> Worker:
        oauth_user, _ = await OauthService().check_token(token)
        if oauth_user:

            db_session = db.session
            try:
                db_obj = await db_session.execute(select(Worker).where(Worker.oauth_id == oauth_user.user_id))
                worker = db_obj.scalar_one_or_none()
            except Exception as ex:
                await db_session.rollback()
                raise HTTPException(
                    status_code=409,
                    detail=str(ex),
                )
            if worker:
                return worker
            else:
                raise HTTPException(status_code=401, detail='Worker Tidak ditemukan')

        else:
            raise HTTPException(status_code=401, detail='Worker Tidak ditemukan')

    async def get_active_worker(self, token: str = Depends(token_auth_scheme)) -> Worker:
        print("active worker")
        oauth_user, _ = await OauthService().check_token(token)
        if oauth_user:

            db_session = db.session
            try:
                db_obj = await db_session.execute(select(Worker).where(and_(Worker.oauth_id == oauth_user.user_id, Worker.is_active == True)))
                worker = db_obj.scalar_one_or_none()
            except Exception as ex:
                await db_session.rollback()
                raise HTTPException(
                    status_code=409,
                    detail=str(ex),
                )
            if worker:
                return worker
            else:
                raise HTTPException(status_code=401, detail=_)

        else:
            raise HTTPException(status_code=401, detail=_)


worker = CRUDWorker(Worker)
