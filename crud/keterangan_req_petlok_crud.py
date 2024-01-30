from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from fastapi_async_sqlalchemy import db
from crud.base_crud import CRUDBase
from models.master_model import KeteranganReqPetlok
from schemas.keterangan_req_petlok_sch import KeteranganReqPetlokCreateSch, KeteranganReqPetlokUpdateSch
from typing import List
from uuid import UUID


class CRUDKeteranganReqPetlok(CRUDBase[KeteranganReqPetlok, KeteranganReqPetlokCreateSch, KeteranganReqPetlokUpdateSch]):
    pass

keterangan_req_petlok = CRUDKeteranganReqPetlok(KeteranganReqPetlok)