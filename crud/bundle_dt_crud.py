from crud.base_crud import CRUDBase
from models.bundle_model import BundleDt
from schemas.bundle_dt_sch import BundleDtCreateSch, BundleDtUpdateSch

class CRUDBundleDt(CRUDBase[BundleDt, BundleDtCreateSch, BundleDtUpdateSch]):
    pass

bundledt = CRUDBundleDt(BundleDt)