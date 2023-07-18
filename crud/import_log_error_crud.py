from fastapi_async_sqlalchemy import db
from crud.base_crud import CRUDBase
from models.import_log_model import ImportLogError
from schemas.import_log_error_sch import ImportLogErrorCreateSch, ImportLogErrorUpdateSch
from services.gcloud_storage_service import GCStorage
from uuid import UUID
from datetime import datetime

from sqlalchemy import exc
from sqlmodel.ext.asyncio.session import AsyncSession


class CRUDImportLogError(CRUDBase[ImportError, ImportLogErrorCreateSch, ImportLogErrorUpdateSch]):
    pass

import_log_error = CRUDImportLogError(ImportLogError)