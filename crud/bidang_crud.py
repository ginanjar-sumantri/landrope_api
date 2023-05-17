from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.bidang_model import Bidang, TipeBidangEnum
from schemas.bidang_sch import BidangCreateSch, BidangUpdateSch, BidangSch, BidangExtSch
from typing import List
from sqlalchemy.orm import load_only

class CRUDBidang(CRUDBase[Bidang, BidangCreateSch, BidangUpdateSch]):
    async def get_by_id_bidang(
        self, *, idbidang: str, db_session: AsyncSession | None = None
    ) -> Bidang:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Bidang).where(Bidang.id_bidang == idbidang))
        return obj.scalar_one_or_none()
    
    async def get_filtered_bidang(
        self,
        *,
        keyword:str | None = None,
        type: TipeBidangEnum | None = TipeBidangEnum.Bidang,
        params: Params | None = Params(),
        order_by: str | None = None,
        order: OrderEnumSch | None = OrderEnumSch.ascendent,
        query: Bidang | Select[Bidang] | None = None,
        db_session: AsyncSession | None = None,
    ) -> Page[Bidang]:
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
                    query = select(self.model).where(self.model.tipe_bidang == type).order_by(columns[order_by].asc())
                else:
                    query = select(self.model).where(self.model.tipe_bidang == type).filter(or_(self.model.id_bidang.ilike(f'%{keyword}%'),
                                                          self.model.alas_hak.ilike(f'%{keyword}%'),
                                                          self.model.nama_pemilik.ilike(f'%{keyword}%'),
                                                          self.model.no_peta.ilike(f'%{keyword}%'))).order_by(columns[order_by].asc())
            else:
                if keyword is None:
                    query = select(self.model).where(self.model.tipe_bidang == type).order_by(columns[order_by].desc())
                else:
                    query = select(self.model).where(self.model.tipe_bidang == type).filter(or_(self.model.id_bidang.ilike(f'%{keyword}%'),
                                                          self.model.alas_hak.ilike(f'%{keyword}%'),
                                                          self.model.nama_pemilik.ilike(f'%{keyword}%'),
                                                          self.model.no_peta.ilike(f'%{keyword}%'))).order_by(columns[order_by].desc())
            
        return await paginate(db_session, query, params)
    
    async def get_filtered_bidang_by_dict(
        self,
        *,
        keyword:str | None = None,
        filter_query: dict = {},
        params: Params | None = Params(),
        order_by: str | None = None,
        order: OrderEnumSch | None = OrderEnumSch.ascendent,
        query: Bidang | Select[Bidang] | None = None,
        db_session: AsyncSession | None = None,
    ) -> Page[Bidang]:
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
        
        attrs = list(self.model().__dict__.keys())

        if query is None:
            query = select(self.model)

            if filter_query is not None:
                for key, value in filter_query.items():
                    query = query.where(getattr(self.model, key) == value)
            
            if keyword:
                    query = query.filter(or_(self.model.id_bidang.ilike(f'%{keyword}%'),
                                                          self.model.alas_hak.ilike(f'%{keyword}%'),
                                                          self.model.nama_pemilik.ilike(f'%{keyword}%'),
                                                          self.model.no_peta.ilike(f'%{keyword}%')))

            if order == OrderEnumSch.ascendent:
                query = query.order_by(columns[order_by].asc())
            else:
                query = query.order_by(columns[order_by].desc())
            
        return await paginate(db_session, query, params)

bidang = CRUDBidang(Bidang)