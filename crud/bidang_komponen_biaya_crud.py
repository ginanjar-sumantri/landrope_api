from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_, text, func
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models import BidangKomponenBiaya, BebanBiaya, InvoiceDetail, Invoice, Bidang
from schemas.bidang_komponen_biaya_sch import (BidangKomponenBiayaCreateSch, BidangKomponenBiayaUpdateSch, 
                                               BidangKomponenBiayaBebanPenjualSch)
from schemas.beban_biaya_sch import BebanBiayaForSpkSch
from typing import List
from uuid import UUID

class CRUDBidangKomponenBiaya(CRUDBase[BidangKomponenBiaya, BidangKomponenBiayaCreateSch, BidangKomponenBiayaUpdateSch]):
    
    async def get_by_id(
            self, 
            *, 
            id: UUID | str, 
            db_session: AsyncSession | None = None) -> BidangKomponenBiaya | None:
        
        db_session = db_session or db.session

        query = select(self.model).where(self.model.id == id)
        
        query = query.options(selectinload(BidangKomponenBiaya.beban_biaya)
            ).options(selectinload(BidangKomponenBiaya.invoice_details
                                    ).options(selectinload(InvoiceDetail.invoice))
            ).options(selectinload(BidangKomponenBiaya.bidang
                            ).options(selectinload(Bidang.invoices
                                            ).options(selectinload(Invoice.termin))
                            )
            )
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_by_bidang_id_and_beban_biaya_id(
            self, 
            *, 
            bidang_id: UUID | str, 
            beban_biaya_id: UUID | str, 
            db_session: AsyncSession | None = None) -> BidangKomponenBiaya | None:
        db_session = db_session or db.session
        query = select(self.model).where(and_(
                            self.model.bidang_id == bidang_id,
                            self.model.beban_biaya_id == beban_biaya_id
            )).options(selectinload(BidangKomponenBiaya.beban_biaya)
            ).options(selectinload(BidangKomponenBiaya.invoice_details))
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_multi_by_bidang_id(
            self, 
            *, 
            bidang_id: UUID | str,
            pengembalian:bool|None = False,
            pajak:bool|None = False,
            db_session: AsyncSession | None = None
            ) -> List[BidangKomponenBiaya] | None:
        
        db_session = db_session or db.session
        
        query = select(self.model).join(self.model.beban_biaya).where(self.model.bidang_id == bidang_id)

        if pengembalian:
            query = query.filter(self.model.is_retur == True)
        elif pajak:
            query = query.filter(BebanBiaya.is_tax == True)
        
        query = query.filter(self.model.is_void != True)
        query = query.filter(self.model.is_exclude_spk != True)
        
        query = query.options(selectinload(BidangKomponenBiaya.invoice_details
                                    ).options(selectinload(InvoiceDetail.invoice))
                    ).options(selectinload(BidangKomponenBiaya.beban_biaya))

        response = await db_session.execute(query)

        return response.scalars().all()
    
    async def get_multi_by_bidang_ids(
            self, 
            *, 
            list_bidang_id: list[UUID],
            db_session: AsyncSession | None = None
            ) -> List[BidangKomponenBiaya]:
        
        db_session = db_session or db.session
        query = select(self.model).where(and_(
                                            self.model.bidang_id.in_(list_bidang_id),
                                            self.model.is_void != True)
                                        )
        query = query.options(selectinload(BidangKomponenBiaya.invoice_details
                                    ).options(selectinload(InvoiceDetail.invoice))
                    ).options(selectinload(BidangKomponenBiaya.beban_biaya))
        
        response = await db_session.execute(query)

        return response.scalars().all()
    
    
    async def get_multi_beban_by_bidang_id(
            self, 
            *, 
            bidang_id: UUID | str,
            db_session: AsyncSession | None = None
            ) -> List[BidangKomponenBiaya] | None:
        
        db_session = db_session or db.session

        subquery_invoice_detail = (
        select(func.coalesce(func.sum(InvoiceDetail.amount), 0))
        .join(Invoice, Invoice.id == InvoiceDetail.invoice_id)
        .filter(and_(InvoiceDetail.bidang_komponen_biaya_id == BidangKomponenBiaya.id, Invoice.is_void != True))
        .scalar_subquery()  # Menggunakan scalar_subquery untuk hasil subquery sebagai skalar
        )

        query = select(BidangKomponenBiaya)
        query = query.filter(and_(
                                    BidangKomponenBiaya.bidang_id == bidang_id, 
                                    BidangKomponenBiaya.is_void != True,
                                    or_(
                                    (BidangKomponenBiaya.estimated_amount - subquery_invoice_detail) == 0, #outstanding
                                    func.coalesce(BidangKomponenBiaya.paid_amount, 0) == 0,
                                    func.coalesce(BidangKomponenBiaya.estimated_amount, 0) == 0)
                                )
                            )
        
        query = query.options(selectinload(BidangKomponenBiaya.bidang)
                    ).options(selectinload(BidangKomponenBiaya.invoice_details
                                            ).options(selectinload(InvoiceDetail.invoice))
                    ).options(selectinload(BidangKomponenBiaya.beban_biaya)
                    )

        response = await db_session.execute(query)

        return response.scalars().all()
    
    async def get_multi_pengembalian_beban_by_bidang_id(
            self, 
            *, 
            bidang_id: UUID | str,
            db_session: AsyncSession | None = None
            ) -> List[BidangKomponenBiaya] | None:
        
        db_session = db_session or db.session
        
        query = select(BidangKomponenBiaya)
        query = query.filter(and_(
            BidangKomponenBiaya.is_paid == True,
            BidangKomponenBiaya.beban_pembeli == False,
            BidangKomponenBiaya.bidang_id == bidang_id,
            BidangKomponenBiaya.is_retur == True,
            BidangKomponenBiaya.is_void != True
        ))

        query = query.options(selectinload(BidangKomponenBiaya.bidang)
                    ).options(selectinload(BidangKomponenBiaya.invoice_details
                                            ).options(selectinload(InvoiceDetail.invoice))
                    ).options(selectinload(BidangKomponenBiaya.beban_biaya)
                    )

        response = await db_session.execute(query)

        return response.scalars().all()
    
    async def get_multi_beban_biaya_lain_by_bidang_id(
            self, 
            *, 
            bidang_id: UUID | str,
            db_session: AsyncSession | None = None
            ) -> List[BidangKomponenBiayaBebanPenjualSch] | None:
        
        db_session = db_session or db.session

        query = select(BidangKomponenBiaya)
        query = query.filter(and_(
            BidangKomponenBiaya.is_void != True,
            BidangKomponenBiaya.beban_pembeli == True,
            BidangKomponenBiaya.is_add_pay == True,
            BidangKomponenBiaya.bidang_id == bidang_id
        ))

        query = query.options(selectinload(BidangKomponenBiaya.bidang)
                    ).options(selectinload(BidangKomponenBiaya.invoice_details
                                            ).options(selectinload(InvoiceDetail.invoice))
                    ).options(selectinload(BidangKomponenBiaya.beban_biaya)
                    )

        response = await db_session.execute(query)

        return response.scalars().all()

    async def get_multi_beban_by_bidang_id_for_spk(self, 
            *, 
            bidang_id: UUID | str,
            db_session: AsyncSession | None = None
            ) -> List[BebanBiayaForSpkSch] | None:
        
        db_session = db_session or db.session
        query = select(BidangKomponenBiaya)
        query = query.filter(BidangKomponenBiaya.bidang_id == bidang_id)
        query = query.filter(BidangKomponenBiaya.is_exclude_spk != True)
        query = query.options(selectinload(BidangKomponenBiaya.beban_biaya))

        response = await db_session.execute(query)

        return response.scalars().all()

    async def get_multi_beban_by_invoice_id(
            self, 
            *, 
            invoice_id:UUID | str,
            pengembalian:bool | None = None,
            biaya_lain:bool | None = None,
            db_session: AsyncSession | None = None
            ) -> List[BidangKomponenBiaya] | None:
        
        db_session = db_session or db.session

        query = select(BidangKomponenBiaya)
        query = query.join(InvoiceDetail, InvoiceDetail.bidang_komponen_biaya_id == BidangKomponenBiaya.id)
        query = query.join(Invoice, Invoice.id == InvoiceDetail.invoice_id)

        if pengembalian:
            query = query.filter(BidangKomponenBiaya.is_retur == True)
        elif biaya_lain:
            query = query.filter(and_(BidangKomponenBiaya.is_add_pay == True, BidangKomponenBiaya.beban_pembeli == True))
        else:
            query = query.filter(BidangKomponenBiaya.is_void != True)

        query = query.options(selectinload(BidangKomponenBiaya.bidang)
                    ).options(selectinload(BidangKomponenBiaya.invoice_details
                                            ).options(selectinload(InvoiceDetail.invoice))
                    ).options(selectinload(BidangKomponenBiaya.beban_biaya)
                    )
        
        query = query.filter(Invoice.id == invoice_id)

        response = await db_session.execute(query)

        return response.scalars().all()
    
    async def get_multi_not_in_id_removed(self, *, bidang_id:UUID, list_ids: List[UUID | str], db_session : AsyncSession | None = None) -> List[BidangKomponenBiaya] | None:
        db_session = db_session or db.session
        query = select(self.model).where(and_(~self.model.id.in_(list_ids), self.model.bidang_id == bidang_id))
        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_komponen_biaya_add_pay(self, *,
                    list_id:list[UUID]|None = [],
                    bidang_id:UUID,
                    db_session : AsyncSession | None = None
                    ) -> List[BebanBiaya] | None:
        
        db_session = db_session or db.session
        
        query = select(self.model).where(and_(BidangKomponenBiaya.beban_biaya_id.in_(list_id), 
                                                BidangKomponenBiaya.is_add_pay == True,
                                                BidangKomponenBiaya.is_void != True,
                                                BidangKomponenBiaya.bidang_id == bidang_id))

        response =  await db_session.execute(query)
        return response.scalars().all()
    
bidang_komponen_biaya = CRUDBidangKomponenBiaya(BidangKomponenBiaya)