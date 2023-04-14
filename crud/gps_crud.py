from crud.base_crud import CRUDBase
from models.gps_model import Gps
from schemas.gps_sch import GpsCreateSch, GpsUpdateSch

class CRUDGps(CRUDBase[Gps, GpsCreateSch, GpsUpdateSch]):
    pass

gps = CRUDGps(Gps)