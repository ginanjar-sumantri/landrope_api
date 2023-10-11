from sqlmodel.ext.asyncio.session import AsyncSession
from crud.base_crud import CRUDBase
from models import PaymentDetail, Payment, Invoice
from schemas.payment_detail_sch import PaymentDetailCreateSch, PaymentDetailUpdateSch
from uuid import UUID

class CRUDPaymentDetail(CRUDBase[PaymentDetail, PaymentDetailCreateSch, PaymentDetailUpdateSch]):
    # async def get_by_termin_id_for_printout(self, *, 
    #               termin_id: UUID | str,
    #               db_session: AsyncSession | None = None) -> list[KjbHargaAktaSch] | None:
        
    #     db_session = db_session or db.session
    #     query = select(KjbHarga.harga_akta).join(KjbTermin, KjbTermin.kjb_harga_id == KjbHarga.id
    #                             ).join(Spk, Spk.kjb_termin_id == KjbTermin.id
    #                             ).join(Invoice, Invoice.spk_id == Spk.id
    #                             ).join(Termin, Termin.id == Invoice.termin_id
    #                             ).where(Termin.id == termin_id).distinct()
        
    #     response = await db_session.execute(query)

    #     return response.fetchall()
    pass

payment_detail = CRUDPaymentDetail(PaymentDetail)