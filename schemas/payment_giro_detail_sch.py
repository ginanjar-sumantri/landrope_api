# from models.payment_model import PaymentGiroDetailBase, PaymentGiroDetailFullBase
# from sqlmodel import SQLModel
# from common.partial import optional
# from decimal import Decimal
# from sqlmodel import Field
# from uuid import UUID
# from datetime import date


# class PaymentGiroDetailCreateSch(PaymentGiroDetailBase):
#     pass

# class PaymentGiroDetailExtSch(SQLModel):
#     giro_id: UUID | None
#     giro_index: UUID | None
#     nomor_giro: str | None
#     tanggal_buka: date | None
#     tanggal_cair: date | None
#     bank_code: str | None
#     payment_date: date | None
#     amount: Decimal | None


# class PaymentGiroDetailSch(PaymentGiroDetailFullBase):
#     pass

# @optional
# class PaymentGiroDetailUpdateSch(PaymentGiroDetailBase):
#     pass