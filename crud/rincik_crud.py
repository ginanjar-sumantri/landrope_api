from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.rincik_model import Rincik
from schemas.rincik_sch import RincikCreateSch, RincikUpdateSch

class CRUDRincik(CRUDBase[Rincik, RincikCreateSch, RincikUpdateSch]):
    async def get_by_id_rincik(
        self, *, idrincik: str, db_session: AsyncSession | None = None
    ) -> Rincik:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Rincik).where(Rincik.id_rincik == idrincik))
        return obj.scalar_one_or_none()
    
    async def get_filtered_rincik(
        self,
        *,
        keyword:str | None = None,
        params: Params | None = Params(),
        order_by: str | None = None,
        order: OrderEnumSch | None = OrderEnumSch.ascendent,
        query: Rincik | Select[Rincik] | None = None,
        db_session: AsyncSession | None = None,
    ) -> Page[Rincik]:
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
                    query = select(self.model).filter(or_(self.model.id_rincik.ilike(f'%{keyword}%'),
                                                          self.model.alas_hak.ilike(f'%{keyword}%'),
                                                          self.model.estimasi_nama_pemilik.ilike(f'%{keyword}%'),
                                                          self.model.no_peta.ilike(f'%{keyword}%'))).order_by(columns[order_by].asc())
            else:
                if keyword is None:
                    query = select(self.model).order_by(columns[order_by].desc())
                else:
                    query = select(self.model).filter(or_(self.model.id_rincik.ilike(f'%{keyword}%'),
                                                          self.model.alas_hak.ilike(f'%{keyword}%'),
                                                          self.model.estimasi_nama_pemilik.ilike(f'%{keyword}%'),
                                                          self.model.no_peta.ilike(f'%{keyword}%'))).order_by(columns[order_by].desc())
            
        return await paginate(db_session, query, params)

rincik = CRUDRincik(Rincik)