from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_, func
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models import InvoiceDetail, Invoice, BidangKomponenBiaya, Termin
from schemas.invoice_detail_sch import InvoiceDetailCreateSch, InvoiceDetailUpdateSch
from typing import List
from uuid import UUID

class CRUDInvoiceDetail(CRUDBase[InvoiceDetail, InvoiceDetailCreateSch, InvoiceDetailUpdateSch]):
    async def get_multi_by_ids_not_in(self, 
                            *,
                            invoice_id:UUID | None = None,
                            list_ids:List[UUID] | None = None,
                            db_session : AsyncSession | None = None
                            ) -> List[InvoiceDetail] | None:
        
        db_session = db_session or db.session

        query = select(self.model).where(and_(~self.model.id.in_(id for id in list_ids), self.model.invoice_id == invoice_id))

        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_multi_by_invoice_ids(self, 
                            *,
                            list_ids:List[UUID] | None = None,
                            beban_biaya_id:UUID,
                            termin_id:UUID,
                            db_session : AsyncSession | None = None
                            ) -> List[InvoiceDetail] | None:
        
        db_session = db_session or db.session

        query = select(InvoiceDetail).join(Invoice, Invoice.id == InvoiceDetail.invoice_id
                                    ).join(BidangKomponenBiaya, BidangKomponenBiaya.id == InvoiceDetail.bidang_komponen_biaya_id
                                    ).join(Termin, Termin.id == Invoice.termin_id
                                    ).where(and_(Invoice.id.in_(list_ids)),
                                                BidangKomponenBiaya.beban_biaya_id == beban_biaya_id,
                                                BidangKomponenBiaya.beban_pembeli == True,
                                                Termin.id == termin_id
                                                ).distinct()

        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_multi_by_invoice_id(self, 
                            *,
                            invoice_id:UUID | None = None,
                            db_session : AsyncSession | None = None
                            ) -> List[InvoiceDetail] | None:
        
        db_session = db_session or db.session

        query = select(InvoiceDetail).join(Invoice, Invoice.id == InvoiceDetail.invoice_id
                                ).where(InvoiceDetail.invoice_id == invoice_id)

        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_multi_by_invoice_id_and_bidang_komponen_biaya_id(self, 
                            *,
                            invoice_id:UUID,
                            bidang_komponen_biaya_id: UUID,
                            db_session : AsyncSession | None = None
                            ) -> List[InvoiceDetail] | None:
        
        db_session = db_session or db.session

        query = select(InvoiceDetail).join(Invoice, Invoice.id == InvoiceDetail.invoice_id
                                ).where(and_(InvoiceDetail.invoice_id == invoice_id, InvoiceDetail.bidang_komponen_biaya_id == bidang_komponen_biaya_id))

        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_for_calculate_estimated_amount(self, 
                            *,
                            invoice_id:UUID,
                            bidang_komponen_biaya_id: UUID,
                            invoice_dt_id: UUID | None = None,
                            db_session : AsyncSession | None = None
                            ) -> List[InvoiceDetail] | None:
        
        db_session = db_session or db.session

        query = select(InvoiceDetail).join(Invoice, Invoice.id == InvoiceDetail.invoice_id
                                ).join(Termin, Termin.id == Invoice.termin_id
                                ).where(and_(InvoiceDetail.invoice_id == invoice_id, 
                                            InvoiceDetail.bidang_komponen_biaya_id == bidang_komponen_biaya_id,
                                            func.coalesce(Invoice.is_void, False) == False,
                                            func.coalesce(Termin.is_void, False) == False))
        
        if invoice_dt_id:
            query = query.filter(InvoiceDetail.id != invoice_dt_id)

        response =  await db_session.execute(query)
        return response.scalars().all()
    

    # FOR TERMIN UPDATE FUNCTION
    async def get_ids_by_invoice_ids(self, 
                            *,
                            list_ids:List[UUID] | None = None,
                            db_session : AsyncSession | None = None
                            ) -> List[UUID] | None:
        
        db_session = db_session or db.session

        query = select(InvoiceDetail).where(InvoiceDetail.invoice_id.in_(list_ids))

        response =  await db_session.execute(query)
        result = response.scalars().all()
        
        datas = [data.id for data in result]
        return datas
    
    async def get_by_invoice_id_and_beban_biaya_id_and_termin_id(self, 
                            *,
                            invoice_id:UUID | None = None,
                            beban_biaya_id:UUID,
                            termin_id:UUID,
                            db_session : AsyncSession | None = None
                            ) -> InvoiceDetail | None:
        
        db_session = db_session or db.session

        query = select(InvoiceDetail).join(Invoice, Invoice.id == InvoiceDetail.invoice_id
                                    ).join(BidangKomponenBiaya, BidangKomponenBiaya.id == InvoiceDetail.bidang_komponen_biaya_id
                                    ).join(Termin, Termin.id == Invoice.termin_id
                                    ).where(and_(Invoice.id == invoice_id,
                                                BidangKomponenBiaya.beban_biaya_id == beban_biaya_id,
                                                BidangKomponenBiaya.beban_pembeli == True,
                                                Termin.id == termin_id)
                                                ).distinct()

        response =  await db_session.execute(query)
        return response.scalar_one_or_none()

    async def get_multi_by_termin_id_and_beban_biaya_id(self, *, termin_id:UUID, beban_biaya_id:UUID, db_session:AsyncSession | None = None) -> list[InvoiceDetail] | None:
        db_session = db_session or db.session

        query = select(InvoiceDetail).join(InvoiceDetail.invoice
                                    ).join(Invoice.termin
                                    ).join(InvoiceDetail.bidang_komponen_biaya
                                    ).where(and_(Termin.id == termin_id, 
                                                BidangKomponenBiaya.beban_biaya_id == beban_biaya_id, 
                                                Invoice.is_void != True))
        
        response = await db_session.execute(query)
        return response.scalars().all()
    
    async def get_multi_by_termin_id_and_beban_biaya_id_and_bidang_id(self, *, termin_id:UUID, beban_biaya_id:UUID, bidang_id:UUID, db_session:AsyncSession | None = None) -> list[InvoiceDetail] | None:
        db_session = db_session or db.session

        query = select(InvoiceDetail).join(InvoiceDetail.invoice
                                    ).join(Invoice.termin
                                    ).join(InvoiceDetail.bidang_komponen_biaya
                                    ).where(and_(Termin.id == termin_id, 
                                                BidangKomponenBiaya.beban_biaya_id == beban_biaya_id, 
                                                Invoice.is_void != True,
                                                Invoice.bidang_id == bidang_id))
        
        response = await db_session.execute(query)
        return response.scalars().all()
    
    async def get_by_komponen_biaya_id_and_termin_is_draft(self, 
                            *,
                            id:UUID | None = None,
                            db_session : AsyncSession | None = None
                            ) -> InvoiceDetail | None:
        
        db_session = db_session or db.session

        query = select(InvoiceDetail).where()

        response =  await db_session.execute(query)
        return response.scalar_one_or_none()

    # FOR SPK PELUNASAN
    async def get_multi_beban_penjual_has_use_and_not_paid_by_bidang_id(self, *, bidang_id:UUID) -> list[InvoiceDetail] | None:

        db_session = db.session
        query = select(InvoiceDetail).join(Invoice, Invoice.id == InvoiceDetail.invoice_id
                                    ).join(BidangKomponenBiaya, BidangKomponenBiaya.id == InvoiceDetail.bidang_komponen_biaya_id
                                    ).where(and_(
                                        Invoice.is_void == False,
                                        BidangKomponenBiaya.is_paid == False,
                                        BidangKomponenBiaya.beban_pembeli == False,
                                        BidangKomponenBiaya.is_void == False,
                                        BidangKomponenBiaya.is_retur == False,
                                        Invoice.bidang_id == bidang_id
                                    ))
        
        response = await db_session.execute(query)
        return response.scalars().all()

invoice_detail = CRUDInvoiceDetail(InvoiceDetail)