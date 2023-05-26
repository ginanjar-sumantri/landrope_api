from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.dokumen_model import BundleHd
from schemas.bundle_hd_sch import BundleHdCreateSch, BundleHdUpdateSch

class CRUDBundleHd(CRUDBase[BundleHd, BundleHdCreateSch, BundleHdUpdateSch]):
    pass

bundlehd = CRUDBundleHd(BundleHd)