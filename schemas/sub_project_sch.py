from models.project_model import SubProject, SubProjectBase, SubProjectFullBase
from common.partial import optional
from common.as_form import as_form
from sqlmodel import SQLModel, Field
from datetime import date, datetime

class SubProjectCreateSch(SubProjectBase):
   pass

class SubProjectSch(SubProjectFullBase):
    project_name:str|None = Field(alias="project_name")
    last_tahap:int|None = Field(alias="last_tahap")


@optional
class SubProjectUpdateSch(SubProjectBase):
    pass