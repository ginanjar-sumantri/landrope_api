from models.master_model import JenisLahanBase, JenisLahan
from common.partial import optional

class JenisLahanCreateSch(JenisLahanBase):
    pass

class JenisLahanSch(JenisLahan):
    pass

@optional
class JenisLahanUpdateSch(JenisLahanBase):
    pass