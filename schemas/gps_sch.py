from models.gps_model import GpsBase, GpsRawBase, GpsFullBase
from common.as_form import as_form
from common.partial import optional

@as_form
class GpsCreateSch(GpsBase):
    pass

class GpsRawSch(GpsRawBase):
    pass

class GpsSch(GpsFullBase):
    pass

@as_form
@optional
class GpsUpdateSch(GpsBase):
    pass