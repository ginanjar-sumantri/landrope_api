from models.export_log_model import ExportLog, ExportLogBase, ExportLogFullBase
from schemas.import_log_error_sch import ImportLogErrorSch
from common.partial import optional
from sqlmodel import SQLModel, Field
from uuid import UUID

class ExportLogCreateSch(ExportLogBase):
    pass

class ExportLogSch(ExportLogFullBase):
    created_by_name:str | None = Field(alias="created_by_name")

@optional
class ExportLogUpdateSch(ExportLogBase):
    pass