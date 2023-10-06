from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, or_
from sqlalchemy.orm import selectinload
from models import Invoice, Worker, Bidang, Termin, PaymentDetail, Payment, InvoiceDetail, BidangKomponenBiaya, Planing, Ptsk, Skpt
from schemas.invoice_sch import (InvoiceSch, InvoiceCreateSch, InvoiceUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, 
                                  DeleteResponseBaseSch, GetResponsePaginatedSch, 
                                  PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from shapely.geometry import shape
from shapely import wkt, wkb
import crud
import json


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[InvoiceSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: InvoiceCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
        
    new_obj = await crud.invoice.create(obj_in=sch, created_by_id=current_worker.id)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[InvoiceSch])
async def get_list(
                params: Params=Depends(), 
                order_by:str = None, 
                keyword:str = None, 
                filter_query:str=None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(Invoice).outerjoin(Bidang, Bidang.id == Invoice.bidang_id
                            ).outerjoin(Termin, Termin.id == Invoice.termin_id
                            ).options(selectinload(Invoice.bidang
                                                        ).options(selectinload(Bidang.skpt
                                                                        ).options(selectinload(Skpt.ptsk))
                                                        ).options(selectinload(Bidang.penampung)
                                                        )
                            ).options(selectinload(Invoice.details
                                                ).options(selectinload(InvoiceDetail.bidang_komponen_biaya
                                                                    ).options(selectinload(BidangKomponenBiaya.beban_biaya))
                                                )
                            ).options(selectinload(Invoice.payment_details
                                                ).options(selectinload(PaymentDetail.payment
                                                                    ).options(selectinload(Payment.giro))
                                                )
                            )
        
    
    if keyword:
        query = query.filter(
            or_(
                Bidang.id_bidang.ilike(f'%{keyword}%'),
                Bidang.alashak.ilike(f'%{keyword}%'),
                Termin.code.ilike(f'%{keyword}%')
            )
        )
    
    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
                query = query.where(getattr(Invoice, key) == value)


    objs = await crud.invoice.get_multi_paginated(params=params, query=query)
    return create_response(data=objs)


@router.get("/{id}", response_model=GetResponseBaseSch[InvoiceSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.invoice.get_by_id(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Invoice, id)

@router.put("/{id}", response_model=PutResponseBaseSch[InvoiceSch])
async def update(id:UUID, sch:InvoiceUpdateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.invoice.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Invoice, id)
    
    obj_updated = await crud.invoice.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[InvoiceSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Delete a object"""

    obj_current = await crud.invoice.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Invoice, id)
    
    obj_deleted = await crud.invoice.remove(id=id)

    return obj_deleted

   