from crud.base_crud import CRUDBase
from models.payment_model import Payment
from schemas.payment_sch import PaymentCreateSch, PaymentUpdateSch

class CRUDPayment(CRUDBase[Payment, PaymentCreateSch, PaymentUpdateSch]):
    pass

payment = CRUDPayment(Payment)