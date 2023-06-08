from models.pemilik_model import KontakBase, KontakFullBase
from common.partial import optional
from pydantic import BaseModel

class KontakCreateSch(KontakBase):
    pass

class KontakCreateExtSch(BaseModel):
    nomor_telepon:str | None

class KontakSch(KontakFullBase):
    pass

@optional
class KontakUpdateSch(KontakBase):
    pass