from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlalchemy import exc
from crud.base_crud import CRUDBase
from models.termin_rfp_payment_model import TerminRfpPayment
from schemas.rfp_sch import RfpCreateResponseSch

class CRUDTerminRfpPayment(CRUDBase[TerminRfpPayment, TerminRfpPayment, TerminRfpPayment]):
    async def create_(self, *, 
                     sch: RfpCreateResponseSch
                     ) -> TerminRfpPayment :
        
        db_session = db.session

        db_obj = TerminRfpPayment(termin_id=sch.client_ref_no, rfp_id=sch.id, status=sch.last_status, payment_id=None) #type ignore
        
        try:
            db_session.add(db_obj)
            await db_session.commit()
        except exc.IntegrityError:
            await db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
        
        
        await db_session.refresh(db_obj)
        return db_obj


termin_rfp_payment = CRUDTerminRfpPayment(TerminRfpPayment)
