from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select
from sqlmodel.sql.expression import Select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import exc
from sqlalchemy.orm import selectinload
from crud.base_crud import CRUDBase
from models.tahap_model import Tahap
from models import Planing, Project, Desa, Ptsk, TahapDetail, Bidang, Skpt, BidangKomponenBiaya, BidangOverlap, Invoice
from schemas.tahap_sch import TahapCreateSch, TahapUpdateSch, TahapForTerminByIdSch, TahapByIdSch
from uuid import UUID
from datetime import datetime
import crud

class CRUDTahap(CRUDBase[Tahap, TahapCreateSch, TahapUpdateSch]):
#    async def create_(self, *, 
#                      obj_in: TahapCreateSch | Tahap, 
#                      created_by_id : UUID | str | None = None, 
#                      db_session : AsyncSession | None = None,
#                      with_commit: bool | None = True) -> Tahap :
        
#           db_session = db_session or db.session

#           db_obj = self.model.from_orm(obj_in) #type ignore
#           db_obj.created_at = datetime.utcnow()
#           db_obj.updated_at = datetime.utcnow()
#           if created_by_id:
#                db_obj.created_by_id = created_by_id
#                db_obj.updated_by_id = created_by_id

          
#           obj_planing = await crud.planing.get_by_id(id=obj_in.planing_id)
#           if not obj_planing:
#                raise IdNotFoundException(Planing, sch.planing_id)
          
#           try:
#                db_session.add(db_obj)
#                if with_commit:
#                     await db_session.commit()
#           except exc.IntegrityError:
#                await db_session.rollback()
#                raise HTTPException(status_code=409, detail="Resource already exists")
          
#           if with_commit:
#                await db_session.refresh(db_obj)
#           return db_obj
   
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
                                                                                                    ).options(selectinload(BidangOverlap.bidang_intersect)
                                                                                                    ).options(selectinload(BidangOverlap.hasil_peta_lokasi_detail))
                                                                                ).options(selectinload(Bidang.invoices
                                                                                                    ).options(selectinload(Invoice.payment_details)
                                                                                                    ).options(selectinload(Invoice.termin)
                                                                                                    )
                                                                                ).options(selectinload(Bidang.pemilik)
                                                                                ).options(selectinload(Bidang.hasil_peta_lokasi))
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