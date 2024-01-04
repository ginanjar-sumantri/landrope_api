from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

from models.base_model import BaseUUIDModel


class WorkerRoleLink(SQLModel, table=True):
    worker_id: Optional[UUID] = Field(default=None, foreign_key='worker.id', primary_key=True)
    role_id: Optional[UUID] = Field(default=None, foreign_key='role.id', primary_key=True)


class RoleBase(SQLModel):
    name: str = Field(nullable=False, max_length=50)


class RoleFullBase(RoleBase, BaseUUIDModel):
    pass


class Role(RoleFullBase, table=True):
    workers: List['Worker'] = Relationship(
        back_populates='roles', link_model=WorkerRoleLink, sa_relationship_kwargs={'lazy': 'selectin'})


class WorkerBase(SQLModel):
    name: str = Field(nullable=False, max_length=100)
    email: EmailStr = Field(nullable=False)
    oauth_id: Optional[UUID] | None = Field(nullable=True)
    is_active: bool = Field(default=True)


class WorkerFullBase(BaseUUIDModel, WorkerBase):
    pass


class Worker(WorkerFullBase, table=True):
    roles: List[Role] = Relationship(back_populates='workers',
                                     link_model=WorkerRoleLink,
                                     sa_relationship_kwargs={'lazy': 'selectin'})

    @property
    def get_roles_name(self) -> list[str]:
        return_list = []
        for i in self.roles:
            return_list.append(i.name)
        return return_list

    @property
    def is_admin(self) -> bool:
        return True if "ADMIN" in self.get_roles_name or "SUPER_ADMIN" in self.get_roles_name else False

    @property
    def is_super_admin(self) -> bool:
        return True if "SUPER_ADMIN" in self.get_roles_name else False
    
    @property
    def is_analyst(self) -> bool:
        return True if "ANALYST_LEADER" in self.get_roles_name or "ANALYST_MASTER_DATA" in self.get_roles_name or "ANALYST" in self.get_roles_name else False
 