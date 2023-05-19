from crud.base_crud import CRUDBase
from models.worker_model import Role
from schemas.role_sch import RoleCreateSch, RoleUpdateSch


class CRUDRole(CRUDBase[Role, RoleCreateSch, RoleUpdateSch]):
    pass


role = CRUDRole(Role)
