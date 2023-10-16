from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select
from sqlmodel.sql.expression import Select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from crud.base_crud import CRUDBase
from models.tahap_model import Tahap
from models import Planing, Project, Desa, Ptsk, TahapDetail, Bidang, Skpt, BidangKomponenBiaya, BidangOverlap
from schemas.tahap_sch import TahapCreateSch, TahapUpdateSch, TahapForTerminByIdSch, TahapByIdSch
from uuid import UUID

class CRUDTahap(CRUDBase[Tahap, TahapCreateSch, TahapUpdateSch]):
   async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> Tahap | None:
        
        db_session = db_session or db.session
        
        query = select(Tahap).where(Tahap.id == id
                                        ).options(selectinload(Tahap.planing
                                                            ).options(selectinload(Planing.project
                                                                                ).options(selectinload(Project.section))
                                                            ).options(selectinload(Planing.desa))
                                        ).options(selectinload(Tahap.ptsk)
                                        ).options(selectinload(Tahap.details
                                                            ).options(selectinload(TahapDetail.bidang
                                                                                ).options(selectinload(Bidang.planing
                                                                                                    ).options(selectinload(Planing.project)
                                                                                                    ).options(selectinload(Planing.desa))
                                                                                ).options(selectinload(Bidang.skpt
                                                                                                    ).options(selectinload(Skpt.ptsk))
                                                                                ).options(selectinload(Bidang.penampung)
                                                                                ).options(selectinload(Bidang.komponen_biayas
                                                                                                    ).options(selectinload(BidangKomponenBiaya.beban_biaya))
                                                                                ).options(selectinload(Bidang.overlaps
                                                                                                    ).options(selectinload(BidangOverlap.bidang_intersect))
                                                                                ).options(selectinload(Bidang.invoices))
                                                            )
                                        ).options(selectinload(Tahap.sub_project)
                                        ).options(selectinload(Tahap.termins))

        response = await db_session.execute(query)

        return response.scalar_one_or_none()
   
   async def get_by_id_for_termin(self, *, id: UUID | str, db_session: AsyncSession | None = None) -> TahapForTerminByIdSch | None:
        db_session = db_session or db.session

        query = select(Tahap.id,
                       Planing.name.label("planing_name"),
                       Project.name.label("project_name"),
                       Desa.name.label("desa_name"),
                       Ptsk.name.label("ptsk_name"),
                       Tahap.nomor_tahap,
                       Tahap.group
                       ).select_from(Tahap
                           ).outerjoin(Planing, Planing.id == Tahap.planing_id
                           ).outerjoin(Ptsk, Ptsk.id == Tahap.ptsk_id
                           ).join(Project, Project.id == Planing.project_id,
                           ).join(Desa, Desa.id == Planing.desa_id).where(Tahap.id == id)

        response = await db_session.execute(query)

        return response.fetchone()
   
   async def fetch_one_by_id(self, *, id: UUID | str, db_session: AsyncSession | None = None) -> TahapByIdSch | None:
        db_session = db_session or db.session

        query = select(Tahap.id,
                       Tahap.nomor_tahap,
                       Tahap.planing_id,
                       Tahap.ptsk_id,
                       Tahap.group,
                       Planing.name.label("planing_name"),
                       Project.name.label("project_name"),
                       Desa.name.label("desa_name"),
                       Ptsk.name.label("ptsk_name")
                       ).select_from(Tahap
                           ).outerjoin(Planing, Planing.id == Tahap.planing_id
                           ).outerjoin(Ptsk, Ptsk.id == Tahap.ptsk_id
                           ).join(Project, Project.id == Planing.project_id,
                           ).join(Desa, Desa.id == Planing.desa_id).where(Tahap.id == id)

        response = await db_session.execute(query)

        return response.fetchone()

tahap = CRUDTahap(Tahap)