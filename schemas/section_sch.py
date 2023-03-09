from models.section_model import SectionBase, SectionFullBase
from common.partial import optional

class SectionCreateSch(SectionBase):
    pass

class SectionSch(SectionFullBase):
    pass

@optional
class SectionUpdateSch(SectionBase):
    pass