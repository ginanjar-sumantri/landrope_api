from typing import List, Optional
from uuid import UUID
from typing import Optional
from pydantic import validator
import re

from models.worker_model import Role, Worker, WorkerBase, WorkerFullBase


class WorkerCreateSch(WorkerBase):
    roles_id: List[UUID]


class WorkerSch(WorkerFullBase):
    pass


class WorkerByIdSch(WorkerSch):
    roles: list[Role]


class WorkerUpdateSch(WorkerBase):
    roles_id: List[UUID]
