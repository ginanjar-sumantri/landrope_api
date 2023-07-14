from models.import_log_model import ImportLog, ImportLogBase, ImportLogFullBase
from common.partial import optional
from sqlmodel import SQLModel, Field
from uuid import UUID

class ImportLogCreateSch(ImportLogBase):
    pass

class ImportLogSch(ImportLogFullBase):
    pass

class ImportLogCloudTaskSch(SQLModel):
    import_log_id: UUID = Field(nullable=False)
    file_path: str

@optional
class ImportLogUpdateSch(ImportLogBase):
    pass