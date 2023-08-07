from models.import_log_model import ImportLog, ImportLogBase, ImportLogFullBase
from schemas.import_log_error_sch import ImportLogErrorSch
from common.partial import optional
from sqlmodel import SQLModel, Field
from uuid import UUID

class ImportLogCreateSch(ImportLogBase):
    pass

class ImportLogSch(ImportLogFullBase):
    created_by_name:str | None = Field(alias="created_by_name")
    total_error_log:int | None = Field(alias="total_error_log")

class ImportLogCloudTaskSch(SQLModel):
    import_log_id: UUID = Field(nullable=False)
    file_path: str

class ImportLogByIdSch(ImportLogSch):
    import_log_errors: list[ImportLogErrorSch] | None = None

@optional
class ImportLogUpdateSch(ImportLogBase):
    pass
