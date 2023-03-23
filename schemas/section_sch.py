from models.section_model import SectionBase, SectionFullBase
from common.partial import optional
from common.as_form import as_form


class SectionCreateSch(SectionBase):
    pass

class SectionSch(SectionFullBase):
    pass

@optional
class SectionUpdateSch(SectionBase):
    pass