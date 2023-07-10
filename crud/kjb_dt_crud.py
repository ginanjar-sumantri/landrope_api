from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from common.enum import StatusPetaLokasiEnum
from crud.base_crud import CRUDBase
from models.kjb_model import KjbDt
from schemas.kjb_dt_sch import KjbDtCreateSch, KjbDtUpdateSch
from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy import exc


class CRUDKjbDt(CRUDBase[KjbDt, KjbDtCreateSch, KjbDtUpdateSch]):
    async def get_multi_for_petlok(self, *,
                                    params: Params | None = Params(),
                                    kjb_hd_id:UUID | None,
                                    db_session : AsyncSession | None = None) -> List[KjbDt] | None:
        db_session = db_session or db.session
        query = select(self.model)
        if kjb_hd_id:
            query = query.where(and_(self.model.kjb_hd_id == kjb_hd_id))
            
        query = query.where(and_(self.model.status_peta_lokasi == StatusPetaLokasiEnum.Lanjut_Peta_Lokasi,
                                              self.model.tanda_terima_notaris_hd != None,
                                              self.model.request_peta_lokasi == None))
        return await paginate(db_session, query, params)

kjb_dt = CRUDKjbDt(KjbDt)