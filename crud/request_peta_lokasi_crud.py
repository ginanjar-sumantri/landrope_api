from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.sql import func
from crud.base_crud import CRUDBase
from models.request_peta_lokasi_model import RequestPetaLokasi
from models.kjb_model import KjbDt, KjbHd
from models.desa_model import Desa
from schemas.request_peta_lokasi_sch import RequestPetaLokasiCreateSch, RequestPetaLokasiHdSch, RequestPetaLokasiUpdateSch, RequestPetaLokasiSch
from typing import List
from common.ordered import OrderEnumSch
from uuid import UUID
from datetime import datetime

class CRUDRequestPetaLokasi(CRUDBase[RequestPetaLokasi, RequestPetaLokasiCreateSch, RequestPetaLokasiUpdateSch]):
    async def get_multi_paginated(self, *, params: Params | None = Params(),
                                  order: OrderEnumSch | None = OrderEnumSch.descendent,
                                  keyword:str | None,
                                  db_session: AsyncSession | None = None) -> Page[RequestPetaLokasiHdSch]:
        db_session = db_session or db.session

        columns = RequestPetaLokasi.__table__.columns

        query = select(
            RequestPetaLokasi.code,
            Desa.name.label("desa_name"),
            KjbHd.mediator,
            KjbHd.nama_group.label("group"),
            KjbHd.code.label("kjb_hd_code")
        ).select_from(RequestPetaLokasi
                    ).outerjoin(KjbDt, KjbDt.id == RequestPetaLokasi.kjb_dt_id
                    ).outerjoin(Desa, Desa.id == KjbDt.desa_by_ttn_id
                    ).outerjoin(KjbHd, KjbHd.id == KjbDt.kjb_hd_id).distinct()

        filter_clause = None

        if keyword:
            for attr in columns:
                if not "CHAR" in str(attr.type) or attr.name.endswith("_id") or attr.name == "id":
                    continue

                condition = getattr(self.model, attr.name).ilike(f'%{keyword}%')
                if filter_clause is None:
                    filter_clause = condition
                else:
                    filter_clause = or_(filter_clause, condition)

        if filter_clause is not None:        
            query = query.filter(filter_clause)
        
        if order == OrderEnumSch.ascendent:
            query = query.order_by(columns["code"].asc())
        else:
            query = query.order_by(columns["code"].desc())
        
        return await paginate(db_session, query, params)
    
    async def get_all_by_code(self, *, code: str, db_session : AsyncSession | None = None) -> List[RequestPetaLokasi] | None:
        db_session = db_session or db.session
        query = select(self.model).where(self.model.code == code)
        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_by_kjb_dt_id(self, *, id: UUID | str, db_session: AsyncSession | None = None) -> RequestPetaLokasi | None:
        db_session = db_session or db.session
        query = select(self.model).where(self.model.kjb_dt_id == id)
        response = await db_session.execute(query)

        return response.scalar_one_or_none()

    
request_peta_lokasi = CRUDRequestPetaLokasi(RequestPetaLokasi)