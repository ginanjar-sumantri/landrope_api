from sqlmodel import SQLModel
from uuid import UUID

class OutStandingSch(SQLModel):
    tipe_worklist:str|None
    total:int|None