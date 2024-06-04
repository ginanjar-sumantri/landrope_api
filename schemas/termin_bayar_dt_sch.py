from models.termin_model import TerminBayarDt, TerminBayarDtBase, TerminBayarDtFullBase
from sqlmodel import Field, SQLModel
from uuid import UUID
from decimal import Decimal
from pydantic import validator


class TerminBayarDtCreateSch(TerminBayarDtBase):
    pass

class TerminBayarDtExtSch(SQLModel):
    id: UUID | None
    beban_biaya_id: UUID | None


class TerminBayarDtSch(TerminBayarDtFullBase):
    beban_biaya_name: str | None


class TerminBayarDtUpdateSch(TerminBayarDtBase):
    pass