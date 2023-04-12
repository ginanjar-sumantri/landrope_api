from fastapi import HTTPException
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from fastapi_async_sqlalchemy import db
from fastapi.encoders import jsonable_encoder
from sqlmodel import SQLModel, select, func
from sqlmodel.sql.expression import Select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import exc
from pydantic import BaseModel
from typing import Any, Dict, Generic, List, Type, TypeVar
from datetime import datetime
from uuid import UUID
from common.ordered import OrderEnumSch


ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
SchemaType = TypeVar("SchemaType", bound=BaseModel)
T = TypeVar("T", bound=SQLModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model:Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        **Parameters**
        * `model`: A SQLModel model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    async def get(self, *, id: UUID | str, db_session: AsyncSession | None = None) -> ModelType | None:
        db_session = db_session or db.session
        query = select(self.model).where(self.model.id == id)
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_by_ids(self, *, list_ids: List[UUID | str], db_session : AsyncSession | None = None) -> List[ModelType] | None:
        db_session = db_session or db.session
        query = select(self.model).where(self.model.id.in_(list_ids))
        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_all(self, *, db_session : AsyncSession | None = None) -> List[ModelType] | None:
        db_session = db_session or db.session
        query = select(self.model)
        response =  await db_session.execute(query)
        return response.scalars().all()

    async def get_by_keyword(self, *, keyword:str = None, db_session : AsyncSession | None = None) -> List[ModelType] | None:
        db_session = db_session or db.session
        query = select(self.model).filter(self.model.name.contains(keyword))
        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_count(self, db_session : AsyncSession | None = None) -> ModelType | None:
        db_session = db_session or db.session
        query = select(func.count()).select_from(select(self.model).subquery())
        response = await db_session.execute(query)
        return response.scalar_one()
    
    async def get_multi(self, *, skip : int = 0, limit : int = 100, query : T | Select[T] | None = None, db_session : AsyncSession | None = None
                        ) -> List[ModelType]:
        db_session = db_session or db.session
        if query is None:
            query = select(self.model).offset(skip).limit(limit).order_by(self.model.id)
        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_multi_paginated(self, *, params: Params | None = Params(),
                                  query: T | Select[T] | None = None, 
                                  db_session: AsyncSession | None = None) -> Page[ModelType]:
        db_session = db_session or db.session
        if query is None:
                query = select(self.model)
        return await paginate(db_session, query, params)
    
    async def get_multi_paginated_with_keyword(self, *, params: Params | None = Params(),
                                  keyword:str | None = None,
                                  query: T | Select[T] | None = None, 
                                  db_session: AsyncSession | None = None) -> Page[ModelType]:
        db_session = db_session or db.session
        if query is None:
            if keyword is None:
                query = select(self.model)
            else:
                query = select(self.model).filter(self.model.name.ilike(f'%{keyword}%')) #ilike is not case sensitive
        return await paginate(db_session, query, params)

    async def get_multi_paginated_ordered(
        self,
        *,
        params: Params | None = Params(),
        order_by: str | None = None,
        order: OrderEnumSch | None = OrderEnumSch.ascendent,
        query: T | Select[T] | None = None,
        db_session: AsyncSession | None = None,
    ) -> Page[ModelType]:
        db_session = db_session or db.session

        columns = self.model.__table__.columns

        if order_by not in columns or order_by is None:
            order_by = self.model.id

        if query is None:
            if order == OrderEnumSch.ascendent:
                query = select(self.model).order_by(columns[order_by].asc())
            else:
                query = select(self.model).order_by(columns[order_by].desc())

        return await paginate(db_session, query, params)
    
    async def get_multi_paginated_ordered_with_keyword(
        self,
        *,
        keyword:str | None = None,
        params: Params | None = Params(),
        order_by: str | None = None,
        order: OrderEnumSch | None = OrderEnumSch.ascendent,
        query: T | Select[T] | None = None,
        db_session: AsyncSession | None = None,
    ) -> Page[ModelType]:
        db_session = db_session or db.session

        columns = self.model.__table__.columns

        # if order_by not in columns or order_by is None:
        #     order_by = self.model.id

        find = False
        for c in columns:
            if c.name == order_by:
                find = True
                break
        
        if order_by is None or find == False:
            order_by = "id"

        if query is None:
            if order == OrderEnumSch.ascendent:
                if keyword is None:
                    query = select(self.model).order_by(columns[order_by].asc())
                else:
                    query = select(self.model).filter(self.model.name.ilike(f'%{keyword}%')).order_by(columns[order_by].asc())
            else:
                if keyword is None:
                    query = select(self.model).order_by(columns[order_by].desc())
                else:
                    query = select(self.model).filter(self.model.name.ilike(f'%{keyword}%')).order_by(columns[order_by].desc())
            
        return await paginate(db_session, query, params)

    async def get_multi_ordered(
        self,
        *,
        order_by: str | None = None,
        order: OrderEnumSch | None = OrderEnumSch.ascendent,
        skip: int = 0,
        limit: int = 100,
        db_session: AsyncSession | None = None,
    ) -> List[ModelType]:
        db_session = db_session or db.session

        columns = self.model.__table__.columns

        if order_by not in columns or order_by is None:
            order_by = self.model.id

        if order == OrderEnumSch.ascendent:
            query = (
                select(self.model)
                .offset(skip)
                .limit(limit)
                .order_by(columns[order_by.value].asc())
            )
        else:
            query = (
                select(self.model)
                .offset(skip)
                .limit(limit)
                .order_by(columns[order_by.value].desc())
            )

        response = await db_session.execute(query)
        return response.scalars().all()
    
    async def create(self, *, obj_in: CreateSchemaType | ModelType, created_by_id : UUID | str | None = None, 
                     db_session : AsyncSession | None = None) -> ModelType :
        db_session = db_session or db.session
        db_obj = self.model.from_orm(obj_in) #type ignore
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()
        if created_by_id:
            db_obj.created_by_id = created_by_id
        
        try:
            db_session.add(db_obj)
            await db_session.commit()
        except exc.IntegrityError:
            db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
        
        await db_session.refresh(db_obj)
        return db_obj
    
    async def create_with_dict(self, db_session: AsyncSession | None = None, created_by_id : UUID | str | None = None, **kwargs) -> ModelType:
        db_session = db_session or db.session
        db_obj = self.model(**kwargs)
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()

        if created_by_id:
            db_obj.created_by_id = created_by_id

        try:
            db_session.add(db_obj)
            await db_session.commit()
        except exc.IntegrityError:
            db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
        
        await db_session.refresh(db_obj)

        # if db_obj.geom :
        #     db_obj.geom = to_shape(db_obj.geom).__str__()
            
        return db_obj
    
    async def update(self, *, obj_current : ModelType, obj_new : UpdateSchemaType | Dict[str, Any] | ModelType,
                     db_session : AsyncSession | None = None) -> ModelType :
        db_session =  db_session or db.session
        obj_data = jsonable_encoder(obj_current)

        if isinstance(obj_new, dict):
            update_data =  obj_new
        else:
            update_data = obj_new.dict(exclude_unset=True) #This tell pydantic to not include the values that were not sent
        
        print(update_data)
        for field in obj_data:
            if field in update_data:
                setattr(obj_current, field, update_data[field])
            if field == "updated_at":
                setattr(obj_current, field, datetime.utcnow())
            
        db_session.add(obj_current)
        await db_session.commit()
        await db_session.refresh(obj_current)
        return obj_current
        
    async def remove(self, *, id:UUID | str, db_session : AsyncSession | None = None) -> ModelType:
        db_session = db_session or db.session
        query = select(self.model).where(self.model.id == id)
        response = await db_session.execute(query)

        obj = response.scalar_one()
        await db_session.delete(obj)
        await db_session.commit()
        return obj

