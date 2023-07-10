from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.sql import func
from crud.base_crud import CRUDBase
from models.request_peta_lokasi_model import RequestPetaLokasi
from schemas.request_peta_lokasi_sch import RequestPetaLokasiCreateSch, RequestPetaLokasiHdSch, RequestPetaLokasiUpdateSch, RequestPetaLokasiSch
from typing import List

from datetime import datetime

class CRUDRequestPetaLokasi(CRUDBase[RequestPetaLokasi, RequestPetaLokasiCreateSch, RequestPetaLokasiUpdateSch]):
    async def get_multi_paginated(self, *, params: Params | None = Params(),
                                  keyword:str | None,
                                  db_session: AsyncSession | None = None) -> Page[RequestPetaLokasiHdSch]:
        db_session = db_session or db.session

        columns = self.model.__table__.columns

        query = select(self.model.code).distinct()
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

        print(query)
        
        return await paginate(db_session, query, params)

    
request_peta_lokasi = CRUDRequestPetaLokasi(RequestPetaLokasi)