from crud.base_crud import CRUDBase
from models.payment_model import PaymentDetail
from schemas.payment_detail_sch import PaymentDetailCreateSch, PaymentDetailUpdateSch

class CRUDPaymentDetail(CRUDBase[PaymentDetail, PaymentDetailCreateSch, PaymentDetailUpdateSch]):
    pass

payment_detail = CRUDPaymentDetail(PaymentDetail)