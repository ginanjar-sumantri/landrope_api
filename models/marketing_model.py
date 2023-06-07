from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING


class ManagerBase(SQLModel):
    name:str | None = Field(nullable=False, max_length=200)
    is_active:bool

class ManagerFullBase(BaseUUIDModel, ManagerBase):
    pass

class Manager(ManagerFullBase, table=True):
    salests:list["Sales"] = Relationship(back_populates="manager", sa_relationship_kwargs={'lazy':'select'})


class SalesBase(SQLModel):
    name:str | None = Field(nullable=False, max_length=200)
    is_active:bool

class SalesFullBase(BaseUUIDModel, SalesBase):
    pass

class Sales(SalesFullBase, table=True):
    manager_id:UUID | None = Field(foreign_key="manager.id")

    manager:"Manager" = Relationship(back_populates="salests", sa_relationship_kwargs={'lazy':'selectin'})

    @property
    def manager_name(self) -> str | None :
        return self.manager.name or ""
