from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from crud.base_crud import CRUDBase
from models import UtjKhusus, Termin, UtjKhususDetail, KjbDt, HasilPetaLokasi, KjbHd
from schemas.utj_khusus_sch import UtjKhususCreateSch, UtjKhususUpdateSch
from uuid import UUID

class CRUDUtjKhusus(CRUDBase[UtjKhusus, UtjKhususCreateSch, UtjKhususUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> UtjKhusus | None:
        
        db_session = db_session or db.session
        
        query = select(UtjKhusus).where(UtjKhusus.id == id
                                ).options(selectinload(UtjKhusus.kjb_hd
                                                ).options(selectinload(KjbHd.desa))
                                ).options(selectinload(UtjKhusus.payment)
                                ).options(selectinload(UtjKhusus.termin
                                                ).options(selectinload(Termin.invoices))
                                ).options(selectinload(UtjKhusus.details
                                                ).options(selectinload(UtjKhususDetail.kjb_dt
                                                                ).options(selectinload(KjbDt.hasil_peta_lokasi
                                                                                ).options(selectinload(HasilPetaLokasi.bidang))
                                                                ).options(selectinload(KjbDt.desa)
                                                                ).options(selectinload(KjbDt.pemilik))
                                                )
                                )
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()

utj_khusus = CRUDUtjKhusus(UtjKhusus)