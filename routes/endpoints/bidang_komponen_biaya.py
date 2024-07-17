from uuid import UUID
from fastapi import APIRouter, status, Depends, HTTPException
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from models.bidang_komponen_biaya_model import BidangKomponenBiaya
from models.worker_model import Worker
from schemas.bidang_komponen_biaya_sch import (BidangKomponenBiayaSch, BidangKomponenBiayaCreateSch, BidangKomponenBiayaUpdateSch, BidangKomponenBiayaListSch)
from schemas.invoice_sch import InvoiceUpdateSch
from schemas.invoice_detail_sch import InvoiceDetailUpdateSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.enum import SatuanBayarEnum, SatuanHargaEnum
from services.helper_service import KomponenBiayaHelper
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[BidangKomponenBiayaSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: BidangKomponenBiayaCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    db_session = db.session
    sch.is_void = False
        
    new_obj = await crud.bidang_komponen_biaya.create(obj_in=sch, created_by_id=current_worker.id, db_session=db_session)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[BidangKomponenBiayaListSch])
async def get_list(
                params: Params=Depends(), 
                order_by:str = None, 
                keyword:str = None, 
                filter_query:str=None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.bidang_komponen_biaya.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[BidangKomponenBiayaSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.bidang_komponen_biaya.get_by_id(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(BidangKomponenBiaya, id)

@router.put("/{id}", response_model=PutResponseBaseSch[BidangKomponenBiayaSch])
async def update(id:UUID, sch:BidangKomponenBiayaUpdateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    db_session = db.session

    obj_current = await crud.bidang_komponen_biaya.get_by_id(id=id)

    if not obj_current:
        raise IdNotFoundException(BidangKomponenBiaya, id)
    
    if obj_current.is_void == False and sch.is_void == True and obj_current.has_invoice_lunas:
        raise HTTPException(status_code=422, detail="Failed updated. Detail : Bidang sudah memiliki pelunasan, komponen tidak dapet divoid.")
    
    if sch.satuan_bayar == SatuanBayarEnum.Amount and sch.satuan_harga == SatuanHargaEnum.Lumpsum:
        sch.estimated_amount = sch.amount
    else:
        formula = obj_current.formula
        sch.estimated_amount = await KomponenBiayaHelper().get_estimated_amount(formula=formula.replace('amount', str(sch.amount or 0)), bidang_id=obj_current.bidang_id, bidang_komponen_biaya_id=obj_current.id)

    # CASE UNTUK MEMO BAYAR YANG DRAFT, OTOMATIS UPDATE INVOICE AMOUNT NETTO DAN INVOICE DETAIL IS RETUR
    if sch.is_retur == True and obj_current.is_retur == False:
        invoice_drafts = await crud.invoice.get_multi_by_bidang_id_and_termin_is_draft(bidang_id=sch.bidang_id)

        for invoice_draft in invoice_drafts:
            invoice_updated = InvoiceUpdateSch.from_orm(invoice_draft)
            invoice_updated.amount_netto = invoice_updated.amount_netto + sch.estimated_amount
            await crud.invoice.update(obj_current=invoice_draft, obj_new=obj_updated, db_session=db_session, with_commit=False)

            invoice_detail_drafts = await crud.invoice_detail.get_multi_by_invoice_id(invoice_id=invoice_draft.id)

            for invoice_detail_draft in invoice_detail_drafts:
                invoice_detail_updated = InvoiceDetailUpdateSch.from_orm(invoice_detail_draft)
                invoice_detail_updated.is_retur = sch.is_retur
                await crud.invoice_detail.update(obj_current=invoice_detail_draft, obj_new=invoice_detail_updated, db_session=db_session, with_commit=False)
    
    elif sch.is_retur == False and obj_current.is_retur == True:

        invoice_drafts = await crud.invoice.get_multi_by_bidang_id_and_termin_is_draft(bidang_id=sch.bidang_id)

        for invoice_draft in invoice_drafts:
            invoice_updated = InvoiceUpdateSch.from_orm(invoice_draft)
            invoice_updated.amount_netto = invoice_updated.amount_netto - sch.estimated_amount
            await crud.invoice.update(obj_current=invoice_draft, obj_new=obj_updated, db_session=db_session, with_commit=False)

            invoice_detail_drafts = await crud.invoice_detail.get_multi_by_invoice_id(invoice_id=invoice_draft.id)

            for invoice_detail_draft in invoice_detail_drafts:
                invoice_detail_updated = InvoiceDetailUpdateSch.from_orm(invoice_detail_draft)
                invoice_detail_updated.is_retur = sch.is_retur
                await crud.invoice_detail.update(obj_current=invoice_detail_draft, obj_new=invoice_detail_updated, db_session=db_session, with_commit=False)
    
    obj_updated = await crud.bidang_komponen_biaya.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id, db_session=db_session)

    return create_response(data=obj_updated)


   