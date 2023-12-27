from crud.base_crud import CRUDBase
from models import Gps, Skpt, Planing
from schemas.gps_sch import GpsCreateSch, GpsUpdateSch
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from common.ordered import OrderEnumSch
from geoalchemy2 import functions
from sqlalchemy.orm import load_only, selectinload
from shapely.geometry import shape
from geoalchemy2.shape import from_shape
from typing import List
from uuid import UUID

class CRUDGps(CRUDBase[Gps, GpsCreateSch, GpsUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> Gps | None:
        
        db_session = db_session or db.session
        
        query = select(Gps).where(Gps.id == id)
        query = query.options(selectinload(Gps.skpt
                                        ).options(selectinload(Skpt.ptsk))
                    ).options(selectinload(Gps.planing
                                        ).options(selectinload(Planing.desa))
                    )
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_gps_geometry(self, *, db_session : AsyncSession | None = None) -> List[Gps] | None:
        db_session = db_session or db.session
        query = select(self.model).options(load_only(self.model.id, self.model.geom))
        response =  await db_session.execute(query)
        
        return response.scalars().all()
    
    async def get_intersect_gps(self, *, db_session : AsyncSession | None = None, geom) -> List[Gps] | None:
        g = shape(geom)
        wkb = from_shape(g)
        db_session = db_session or db.session
        query = select(self.model).filter(functions.ST_Intersects(self.model.geom, wkb))
        response =  await db_session.execute(query)
        
        return response.scalars().all()
    
    async def get_filtered_gps(
        self,
        *,
        keyword:str | None = None,
        params: Params | None = Params(),
        order_by: str | None = None,
        order: OrderEnumSch | None = OrderEnumSch.ascendent,
        query: Gps | Select[Gps] | None = None,
        db_session: AsyncSession | None = None,
    ) -> Page[Gps]:
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
                    query = select(self.model).filter(or_(self.model.nama.ilike(f'%{keyword}%'),
                                                          self.model.alas_hak.ilike(f'%{keyword}%'),
                                                          self.model.desa.ilike(f'%{keyword}%'),
                                                          self.model.penunjuk.ilike(f'%{keyword}%'),
                                                          self.model.pic.ilike(f'%{keyword}%'),
                                                          self.model.group.ilike(f'%{keyword}%')
                                                          )).order_by(columns[order_by].asc())
            else:
                if keyword is None:
                    query = select(self.model).order_by(columns[order_by].desc())
                else:
                    query = select(self.model).filter(or_(self.model.nama.ilike(f'%{keyword}%'),
                                                          self.model.alas_hak.ilike(f'%{keyword}%'),
                                                          self.model.desa.ilike(f'%{keyword}%'),
                                                          self.model.penunjuk.ilike(f'%{keyword}%'),
                                                          self.model.pic.ilike(f'%{keyword}%'),
                                                          self.model.group.ilike(f'%{keyword}%')
                                                          )).order_by(columns[order_by].desc())
            
        return await paginate(db_session, query, params)
    


gps = CRUDGps(Gps)