from models.project_model import MainProject, MainProjectBase, MainProjectFullBase
from common.partial import optional
from common.as_form import as_form
from sqlmodel import SQLModel, Field
from datetime import date, datetime

class MainProjectCreateSch(MainProjectBase):
    pass


class MainProjectSch(MainProjectFullBase):
    pass


@optional
class MainProjectUpdateSch(MainProjectBase):
    pass