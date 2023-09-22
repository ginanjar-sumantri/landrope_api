from uuid import UUID
from fastapi import APIRouter, status, Depends, Request
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, or_, and_
import crud
from models.termin_model import Termin
from models.worker_model import Worker
from models.invoice_model import Invoice
from models.tahap_model import Tahap, TahapDetail
from models.kjb_model import KjbHd, KjbDt
from models.spk_model import Spk
from models.bidang_model import Bidang
from models.hasil_peta_lokasi_model import HasilPetaLokasi
from schemas.tahap_sch import TahapForTerminByIdSch
from schemas.termin_sch import (TerminSch, TerminCreateSch, TerminUpdateSch, TerminByIdSch)
from schemas.invoice_sch import InvoiceCreateSch, InvoiceUpdateSch
from schemas.invoice_detail_sch import InvoiceDetailCreateSch, InvoiceDetailUpdateSch
from schemas.spk_sch import SpkSrcSch, SpkForTerminSch
from schemas.kjb_hd_sch import KjbHdForTerminByIdSch
from schemas.bidang_sch import BidangForUtjSch
from schemas.bidang_komponen_biaya_sch import BidangKomponenBiayaBebanPenjualSch
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, ContentNoChangeException)
from common.ordered import OrderEnumSch
from common.enum import JenisBayarEnum, StatusHasilPetaLokasiEnum, SatuanBayarEnum
from services.gcloud_task_service import GCloudTaskService
from decimal import Decimal
import json
import numpy

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[TerminSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: TerminCreateSch,
            request: Request,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    db_session = db.session

    new_obj = await crud.termin.create(obj_in=sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)

    #add invoice
    for invoice in sch.invoices:
        invoice_sch = InvoiceCreateSch(**invoice.dict(), termin_id=new_obj.id)
        new_obj_invoice = await crud.invoice.create(obj_in=invoice_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)
        
        #add invoice_detail
        for dt in invoice.details:
            invoice_dtl_sch = InvoiceDetailCreateSch(**dt.dict(), invoice_id=new_obj_invoice.id)
            await crud.invoice_detail.create(obj_in=invoice_dtl_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)
            
            payload = {"id" : dt.bidang_komponen_biaya_id}
            url = f'{request.base_url}landrope/bidang_komponen_biaya/cloud-task-is-use'
            GCloudTaskService().create_task(payload=payload, base_url=url)
    
    await db_session.commit()
    await db_session.refresh(new_obj)

    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[TerminSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None,
            is_utj:bool = False,
            filter_query:str = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    jenis_bayars = []
    if is_utj:
        jenis_bayars.append("UTJ")
    else:
        jenis_bayars.append("DP")
        jenis_bayars.append("LUNAS")

    query = select(Termin).select_from(Termin
                        ).outerjoin(Invoice, Invoice.termin_id == Termin.id
                        ).outerjoin(Tahap, Tahap.id == Termin.tahap_id
                        ).outerjoin(KjbHd, KjbHd.id == Termin.kjb_hd_id
                        ).outerjoin(Spk, Spk.id == Invoice.spk_id
                        ).outerjoin(Bidang, Bidang.id == Invoice.bidang_id
                        ).where(Termin.jenis_bayar.in_(jenis_bayars))
    
    if keyword:
        query = query.filter_by(
            or_(
                Termin.code.ilike(f'%{keyword}%'),
                Termin.jenis_bayar.ilike(f'%{keyword}%'),
                Tahap.nomor_tahap == keyword,
                KjbHd.code.ilike(f'%{keyword}%'),
                Bidang.id_bidang.ilike(f'%{keyword}%'),
                Bidang.alashak.ilike(f'%{keyword}%'),
                Spk.code.ilike(f'%{keyword}%'),
            )
        )

    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
                query = query.where(getattr(KjbHd, key) == value)

    objs = await crud.termin.get_multi_paginated_ordered(params=params, order_by="created_at", order=OrderEnumSch.descendent, query=query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[TerminByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.termin.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Termin, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[TerminSch])
async def update(
            id:UUID,
            request:Request,
            sch:TerminUpdateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    db_session = db.session

    obj_current = await crud.termin.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Termin, id)
    
    obj_updated = await crud.termin.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

    for invoice in sch.invoices:
        if invoice.id:
            invoice_current = await crud.invoice.get(id=invoice.id)
            if invoice_current:
                invoice_updated_sch = InvoiceUpdateSch(**invoice.dict())
                invoice_updated = await crud.invoice.update(obj_current=invoice_current, obj_new=invoice_updated_sch, with_commit=False, db_session=db_session, updated_by_id=current_worker.id)

                #delete invoice_detail not exists
                list_id_invoice_dt = [dt.id for dt in invoice.details if dt.id != None]
                await crud.invoice_detail.delete_multiple_where_not_in(ids=list_id_invoice_dt, db_session=db_session, with_commit=False)

                for dt in invoice.details:
                    if dt.id is None:
                        invoice_dtl_sch = InvoiceDetailCreateSch(**dt.dict(), invoice_id=invoice.id)
                        await crud.invoice_detail.create(obj_in=invoice_dtl_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)
                    else:
                        invoice_dtl_current = await crud.invoice_detail.get(id=dt.id)
                        invoice_dtl_updated_sch = InvoiceDetailUpdateSch(**dt.dict(), invoice_id=invoice_updated.id)
                        await crud.invoice_detail.update(obj_current=invoice_dtl_current, obj_new=invoice_dtl_updated_sch, db_session=db_session, with_commit=False)
                    
                    payload = {"id" : dt.bidang_komponen_biaya_id}
                    url = f'{request.base_url}landrope/bidang_komponen_biaya/cloud-task-is-use'
                    GCloudTaskService().create_task(payload=payload, base_url=url)
            else:
                raise ContentNoChangeException(detail="data invoice tidak ditemukan")
        else:
            invoice_sch = InvoiceCreateSch(**invoice.dict(), termin_id=obj_updated.id)
            new_obj_invoice = await crud.invoice.create(obj_in=invoice_sch, db_session=db_session, with_commit=False)

            #add invoice_detail
            for dt in invoice.details:
                invoice_dtl_sch = InvoiceDetailCreateSch(**dt.dict(), invoice_id=new_obj_invoice.id)
                await crud.invoice_detail.create(obj_in=invoice_dtl_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)

                payload = {"id" : dt.bidang_komponen_biaya_id}
                url = f'{request.base_url}landrope/bidang_komponen_biaya/cloud-task-is-use'
                GCloudTaskService().create_task(payload=payload, base_url=url)

    await db_session.commit()
    await db_session.refresh(obj_updated)

    return create_response(data=obj_updated)

@router.get("/search/tahap/{id}", response_model=GetResponseBaseSch[TahapForTerminByIdSch])
async def get_list_spk_by_tahap_id(
                id:UUID,
                jenis_bayar:JenisBayarEnum,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    tahap = await crud.tahap.get_by_id_for_termin(id=id)
    spk_details = await crud.spk.get_multi_by_tahap_id(tahap_id=id, jenis_bayar=jenis_bayar)

    obj_return = TahapForTerminByIdSch(**dict(tahap))

    spkts = []
    for s in spk_details:
        spk = SpkForTerminSch(**dict(s))
        spkts.append(spk)

    obj_return.spkts = spkts
    return create_response(data=obj_return)

@router.get("/search/kjb_hd/{id}", response_model=GetResponseBaseSch[KjbHdForTerminByIdSch])
async def get_list_bidang_by_kjb_hd_id(
                id:UUID,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    obj = await crud.kjb_hd.get_by_id_for_termin(id=id)
    bidang_details = await crud.bidang.get_multi_by_kjb_hd_id(kjb_hd_id=id)

    obj_return = KjbHdForTerminByIdSch(**dict(obj))

    bidangs = []
    for b in bidang_details:
        bidang = BidangForUtjSch(**dict(b))
        bidangs.append(bidang)

    obj_return.bidangs = bidangs

    return create_response(data=obj_return)

@router.get("/search/komponen_biaya/{id}", response_model=GetResponseBaseSch[list[BidangKomponenBiayaBebanPenjualSch]])
async def get_list_komponen_biaya_by_bidang_id(
                id:UUID,
                invoice_id:UUID,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.bidang_komponen_biaya.get_multi_beban_penjual_by_bidang_id(bidang_id=id)

    return create_response(data=objs)

@router.get("/search/spk", response_model=GetResponsePaginatedSch[SpkSrcSch])
async def get_list_spk_by_tahap_id(
                tahap_id:UUID,
                jenis_bayar:JenisBayarEnum,
                keyword:str = None,
                limit:int = 100,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    list_bidang_id = await crud.tahap_detail.get_bidang_id_by_tahap_id(tahap_id=tahap_id)

    query = select(Spk.id, Spk.code, Bidang.id_bidang).select_from(Spk
                        ).outerjoin(Bidang, Bidang.id == Spk.bidang_id
                        ).outerjoin(Invoice, Invoice.spk_id == Spk.id
                        ).where(
                            and_(
                                Spk.bidang_id.in_(id for id in list_bidang_id),
                                Spk.jenis_bayar == jenis_bayar,
                                or_(
                                    Invoice.spk == None,
                                    Invoice.is_void == True
                                )
                        ))
    
    if keyword:
        query = query.filter(Bidang.id_bidang.ilike(f'%{keyword}%'))


    objs = await crud.spk.get_multi(query=query, limit=limit)
    return create_response(data=objs)

@router.get("/search/spk/{id}", response_model=GetResponseBaseSch[SpkForTerminSch])
async def get_by_id(id:UUID,
                    current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Get an object by id"""

    obj = await crud.spk.get_by_id_for_termin(id=id)

    komponen_biaya_beban_penjuals = await crud.bidang_komponen_biaya.get_multi_beban_penjual_by_bidang_id(bidang_id=obj.bidang_id)
    array_total_beban = numpy.array([kb.total_beban for kb in komponen_biaya_beban_penjuals])
    total_beban_penjual = numpy.sum(array_total_beban)


    obj = SpkForTerminSch(**dict(obj))

    if obj.satuan_bayar == SatuanBayarEnum.Percentage:
        amount = Decimal((obj.spk_amount * obj.total_harga)/100)
        obj.amount = amount

    obj.sisa_pelunasan = obj.total_harga - total_beban_penjual

    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Bidang, id)


