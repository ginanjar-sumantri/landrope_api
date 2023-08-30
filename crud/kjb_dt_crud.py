from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_, func
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from common.enum import StatusPetaLokasiEnum
from crud.base_crud import CRUDBase
from models.kjb_model import KjbHd, KjbDt
from models.request_peta_lokasi_model import RequestPetaLokasi
from schemas.kjb_dt_sch import KjbDtCreateSch, KjbDtUpdateSch
from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy import exc


class CRUDKjbDt(CRUDBase[KjbDt, KjbDtCreateSch, KjbDtUpdateSch]):
    async def get_multi_for_petlok(self, *,
                                    params: Params | None = Params(),
                                    kjb_hd_id:UUID | None,
                                    no_order:str | None,
                                    db_session : AsyncSession | None = None) -> List[KjbDt] | None:
        db_session = db_session or db.session

        if no_order is None:
            no_order = ""

        query = select(self.model
                       ).select_from(self.model
                                     ).outerjoin(RequestPetaLokasi, self.model.id == RequestPetaLokasi.kjb_dt_id
                                     ).where(and_(
                                                    self.model.kjb_hd_id == kjb_hd_id,
                                                    self.model.status_peta_lokasi == StatusPetaLokasiEnum.Lanjut_Peta_Lokasi,
                                                    or_(
                                                        RequestPetaLokasi.code == no_order,
                                                        self.model.request_peta_lokasi == None
                                                    )
                                                )
                                            )
        
        
        return await paginate(db_session, query, params)
    
    async def get_multi_for_tanda_terima_notaris(
                        self, *, 
                        params: Params | None = Params(),
                        db_session: AsyncSession | None = None) -> Page[KjbDt]:
        
        db_session = db_session or db.session

        query = select(self.model
                       ).select_from(self.model
                                     ).outerjoin(RequestPetaLokasi, self.model.id == RequestPetaLokasi.kjb_dt_id
                                                 ).where(self.model.request_peta_lokasi == None)

        return await paginate(db_session, query, params)

    async def get_by_alashak(self, *, alashak:str, db_session: AsyncSession | None = None) -> KjbDt | None:
        db_session = db_session or db.session
        query = select(self.model).where(func.lower(func.trim(func.replace(self.model.alashak, ' ', ''))) == alashak.strip().lower().replace(' ', ''))
        response = await db_session.execute(query)

        return response.scalars().first()
    
kjb_dt = CRUDKjbDt(KjbDt)