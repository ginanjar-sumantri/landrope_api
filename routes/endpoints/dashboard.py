from fastapi import APIRouter, Depends
from fastapi_async_sqlalchemy import db
from sqlmodel import text, select
from schemas.dashboard_sch import OutStandingSch
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, create_response)
import crud

router = APIRouter()

@router.get("/search", response_model=GetResponseBaseSch[list[OutStandingSch]])
async def dashboard_outstanding():

    """Get for search"""
    
    outstanding_gu_pbt = await crud.request_peta_lokasi.get_outstanding_gu_pbt()
    outstanding_spk = await crud.hasil_peta_lokasi.get_ready_spk()
    outstanding_hasil_peta_lokasi = await crud.request_peta_lokasi.get_outstanding_hasil_peta_lokasi()
    outstanding_invoice = await crud.spk.get_outstanding_spk_create_invoice()
    outstanding_payment = await crud.invoice.get_multi_outstanding_invoice()

    data = []
    gu_pt = OutStandingSch(tipe_worklist="outstanding_gu_pbt", total=len(outstanding_gu_pbt))
    data.append(gu_pt)

    ids_ready_spk = [data.id for data in outstanding_spk]
    ids_ready_spk = list(set(ids_ready_spk))
    spk = OutStandingSch(tipe_worklist="outstanding_spk", total=len(ids_ready_spk))
    data.append(spk)
    
    hasil_peta_lokasi = OutStandingSch(tipe_worklist="outstanding_hasil_peta_lokasi", total=len(outstanding_hasil_peta_lokasi))
    data.append(hasil_peta_lokasi)
    invoice = OutStandingSch(tipe_worklist="outstanding_invoice", total=len(outstanding_invoice))
    data.append(invoice)
    payment = OutStandingSch(tipe_worklist="outstanding_payment", total=len(outstanding_payment))
    data.append(payment)

    # result = await db_session.execute(query)
    # data = result.fetchall()
    return create_response(data=data)