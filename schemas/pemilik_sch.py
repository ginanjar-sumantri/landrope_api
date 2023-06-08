from models.pemilik_model import PemilikBase, PemilikFullBase, KontakBase, KontakFullBase, RekeningBase, RekeningFullBase
from common.partial import optional

class PemilikCreateSch(PemilikBase):
    pass

class PemilikSch(PemilikFullBase):
    pass

@optional
class PemilikUpdateSch(PemilikBase):
    pass


class KontakCreateSch(KontakBase):
    pass

class KontakSch(KontakFullBase):
    pass

@optional
class KontakUpdateSch(KontakBase):
    pass


class RekeningCreateSch(RekeningBase):
    pass

class RekeningSch(RekeningFullBase):
    pass

@optional
class RekeningUpdateSch(RekeningBase):
    pass