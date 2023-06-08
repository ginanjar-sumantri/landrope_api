from models.marketing_model import ManagerBase, ManagerFullBase, SalesBase, SalesFullBase
from common.partial import optional

class ManagerCreateSch(ManagerBase):
    pass

class ManagerSch(ManagerFullBase):
    pass

@optional
class ManagerUpdateSch(ManagerBase):
    pass



class SalesCreateSch(SalesBase):
    pass

class SalesSch(SalesFullBase):
    pass

@optional
class SalesUpdateSch(SalesBase):
    pass