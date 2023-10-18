from uuid import UUID
from fastapi import APIRouter, status, Depends, Request, HTTPException, Response
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, or_, and_
import crud
from models import Termin, Worker, Invoice, InvoiceDetail, Tahap, KjbHd, Spk, Bidang, TerminBayar
from models.code_counter_model import CodeCounterEnum
from schemas.tahap_sch import TahapForTerminByIdSch
from schemas.termin_sch import (TerminSch, TerminCreateSch, TerminUpdateSch, 
                                TerminByIdSch, TerminByIdForPrintOut,
                                TerminBidangIDSch, TerminInvoiceHistoryforPrintOutExt,
                                TerminBebanBiayaForPrintOutExt)
from schemas.termin_bayar_sch import TerminBayarCreateSch, TerminBayarUpdateSch
from schemas.invoice_sch import InvoiceCreateSch, InvoiceUpdateSch, InvoiceForPrintOutUtj, InvoiceForPrintOutExt
from schemas.invoice_detail_sch import InvoiceDetailCreateSch, InvoiceDetailUpdateSch
from schemas.spk_sch import SpkSrcSch, SpkForTerminSch
from schemas.kjb_hd_sch import KjbHdForTerminByIdSch, KjbHdSearchSch
from schemas.bidang_sch import BidangForUtjSch
from schemas.bidang_komponen_biaya_sch import BidangKomponenBiayaBebanPenjualSch, BidangKomponenBiayaUpdateSch
from schemas.hasil_peta_lokasi_detail_sch import HasilPetaLokasiDetailForUtj
from schemas.kjb_harga_sch import KjbHargaAktaSch
from schemas.payment_detail_sch import PaymentDetailForPrintout
from schemas.marketing_sch import ManagerSrcSch, SalesSrcSch
from schemas.rekening_sch import RekeningSch
from schemas.notaris_sch import NotarisSrcSch
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, ContentNoChangeException)
from common.ordered import OrderEnumSch
from common.enum import JenisBayarEnum, StatusHasilPetaLokasiEnum, SatuanBayarEnum
from common.rounder import RoundTwo
from common.generator import generate_code_month
from services.gcloud_task_service import GCloudTaskService
from services.helper_service import HelperService
from decimal import Decimal
from services.pdf_service import PdfService
from jinja2 import Environment, FileSystemLoader
from datetime import date, datetime
import json
import numpy
import roman

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[TerminSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: TerminCreateSch,
            request: Request,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    db_session = db.session
    sch.is_void = False

    today = date.today()
    month = roman.toRoman(today.month)
    year = today.year
    jns_byr:str = ""

    if sch.jenis_bayar == JenisBayarEnum.UTJ or sch.jenis_bayar == JenisBayarEnum.UTJ_KHUSUS:
        jns_byr = JenisBayarEnum.UTJ.value
        last_number = await generate_code_month(entity=CodeCounterEnum.Utj, with_commit=False, db_session=db_session)
        sch.code = f"{last_number}/{jns_byr}/LA/{month}/{year}"
    else:
        last_number = await generate_code_month(entity=CodeCounterEnum.Dp if sch.jenis_bayar == JenisBayarEnum.DP else CodeCounterEnum.Lunas,
                                                with_commit=False, db_session=db_session)
        
        jns_byr = JenisBayarEnum.DP.value if sch.jenis_bayar == JenisBayarEnum.DP else JenisBayarEnum.LUNAS.value
        sch.code = f"{last_number}/{jns_byr}/LA/{month}/{year}"

    new_obj = await crud.termin.create(obj_in=sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)

    #add invoice
    for invoice in sch.invoices:

        last_number = await generate_code_month(entity=CodeCounterEnum.Invoice, with_commit=False, db_session=db_session)
        invoice_sch = InvoiceCreateSch(**invoice.dict(), termin_id=new_obj.id)
        invoice_sch.code = f"INV/{last_number}/{jns_byr}/LA/{month}/{year}"
        invoice_sch.is_void = False
        new_obj_invoice = await crud.invoice.create(obj_in=invoice_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)
        
        #add invoice_detail
        for dt in invoice.details:
            invoice_dtl_sch = InvoiceDetailCreateSch(**dt.dict(), invoice_id=new_obj_invoice.id)
            await crud.invoice_detail.create(obj_in=invoice_dtl_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)
            
            bidang_komponen_biaya_current = await crud.bidang_komponen_biaya.get(id=dt.bidang_komponen_biaya_id)
            sch_komponen_biaya = BidangKomponenBiayaUpdateSch(**bidang_komponen_biaya_current.dict())
            sch_komponen_biaya.is_use = True
            await crud.bidang_komponen_biaya.update(obj_current=bidang_komponen_biaya_current, obj_new=sch_komponen_biaya, with_commit=False, db_session=db_session)
    
    #add termin bayar
    for termin_bayar in sch.termin_bayars:
        termin_bayar_sch = TerminBayarCreateSch(**termin_bayar.dict(), termin_id=new_obj.id)
        await crud.termin_bayar.create(obj_in=termin_bayar_sch,  db_session=db_session, with_commit=False, created_by_id=current_worker.id)
    
    await db_session.commit()
    await db_session.refresh(new_obj)

    new_obj = await crud.termin.get_by_id(id=new_obj.id)

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
        jenis_bayars.append("UTJ_KHUSUS")
    else:
        jenis_bayars.append("DP")
        jenis_bayars.append("LUNAS")

    query = select(Termin).outerjoin(Invoice, Invoice.termin_id == Termin.id
                        ).outerjoin(Tahap, Tahap.id == Termin.tahap_id
                        ).outerjoin(KjbHd, KjbHd.id == Termin.kjb_hd_id
                        ).outerjoin(Spk, Spk.id == Invoice.spk_id
                        ).outerjoin(Bidang, Bidang.id == Invoice.bidang_id
                        ).where(Termin.jenis_bayar.in_(jenis_bayars)).distinct()
    
    if keyword and keyword != '':
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
                query = query.where(getattr(Termin, key) == value)

    objs = await crud.termin.get_multi_paginated_ordered(params=params, order_by="created_at", order=OrderEnumSch.descendent, query=query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[TerminByIdSch])
async def get_by_id(id:UUID,
                    current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Get an object by id"""
    
    obj = await crud.termin.get_by_id(id=id)
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

    obj_current = await crud.termin.get_by_id(id=id)
    if not obj_current:
        raise IdNotFoundException(Termin, id)
    
    sch.is_void = obj_current.is_void
    
    obj_updated = await crud.termin.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

    list_id_invoice = [inv.id for inv in sch.invoices if inv.id != None]
    if len(list_id_invoice) > 0:
        removed_invoice = await crud.invoice.get_invoice_not_in_by_ids(list_ids=list_id_invoice, termin_id=obj_updated.id)
        for ls in removed_invoice:
            if len(ls.payment_details) > 0:
                raise ContentNoChangeException(detail=f"invoice {ls.code} tidak dapat dihapus karena memiliki payment")
            
        if len(removed_invoice) > 0:
            await crud.invoice.remove_multiple_data(list_obj=removed_invoice, db_session=db_session)

    if len(list_id_invoice) == 0 and len(obj_current.invoices) > 0:
        list_id_invoice = [dt.id for dt in obj_current.invoices if dt.id is not None]
        removed_invoice = await crud.invoice.get_by_ids_and_termin_id(list_ids=list_id_invoice, termin_id=obj_updated.id)
        for ls in removed_invoice:
            if len(ls.payment_details) > 0:
                raise ContentNoChangeException(detail=f"invoice {ls.code} tidak dapat dihapus karena memiliki payment")
            
        if len(removed_invoice) > 0:
            await crud.invoice.remove_multiple_data(list_obj=removed_invoice, db_session=db_session)

    for invoice in sch.invoices:
        if invoice.id:
            invoice_current = await crud.invoice.get(id=invoice.id)
            if invoice_current:
                invoice_updated_sch = InvoiceUpdateSch(**invoice.dict())
                invoice_updated_sch.is_void = invoice_current.is_void
                invoice_updated = await crud.invoice.update(obj_current=invoice_current, obj_new=invoice_updated_sch, with_commit=False, db_session=db_session, updated_by_id=current_worker.id)
                
                list_id_invoice_dt = [dt.id for dt in invoice.details if dt.id != None]

                #get invoice detail not exists on update and update komponen is not use
                list_invoice_detail = await crud.invoice_detail.get_multi_by_ids_not_in(list_ids=list_id_invoice_dt)
                for inv_dt in list_invoice_detail:
                    d_bidang_komponen_biaya_current = await crud.bidang_komponen_biaya.get(id=inv_dt.bidang_komponen_biaya_id)
                    d_sch_komponen_biaya = BidangKomponenBiayaUpdateSch(**d_bidang_komponen_biaya_current.dict())
                    d_sch_komponen_biaya.is_use = False
                    await crud.bidang_komponen_biaya.update(obj_current=d_bidang_komponen_biaya_current, obj_new=d_sch_komponen_biaya, with_commit=False, db_session=db_session)
            

                #delete invoice_detail not exists
                query_inv_dtl = InvoiceDetail.__table__.delete().where(and_(~InvoiceDetail.id.in_(list_id_invoice_dt), InvoiceDetail.invoice_id == invoice_current.id))
                await crud.invoice_detail.delete_multiple_where_not_in(query=query_inv_dtl, db_session=db_session, with_commit=False)

                for dt in invoice.details:
                    if dt.id is None:
                        invoice_dtl_sch = InvoiceDetailCreateSch(**dt.dict(), invoice_id=invoice.id)
                        await crud.invoice_detail.create(obj_in=invoice_dtl_sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)
                    else:
                        invoice_dtl_current = await crud.invoice_detail.get(id=dt.id)
                        invoice_dtl_updated_sch = InvoiceDetailUpdateSch(**dt.dict(), invoice_id=invoice_updated.id)
                        await crud.invoice_detail.update(obj_current=invoice_dtl_current, obj_new=invoice_dtl_updated_sch, db_session=db_session, with_commit=False)
                    
                    bidang_komponen_biaya_current = await crud.bidang_komponen_biaya.get(id=dt.bidang_komponen_biaya_id)
                    sch_komponen_biaya = BidangKomponenBiayaUpdateSch(**bidang_komponen_biaya_current.dict())
                    sch_komponen_biaya.is_use = True
                    await crud.bidang_komponen_biaya.update(obj_current=bidang_komponen_biaya_current, obj_new=sch_komponen_biaya, with_commit=False, db_session=db_session)
            
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
    
    list_id_termin_bayar = [bayar.id for bayar in sch.termin_bayars if bayar.id != None]
    if len(list_id_termin_bayar) > 0:
        query_bayar = TerminBayar.__table__.delete().where(and_(~TerminBayar.id.in_(list_id_termin_bayar), TerminBayar.termin_id == obj_updated.id))
        await crud.termin_bayar.delete_multiple_where_not_in(query=query_bayar, db_session=db_session, with_commit=False)

    for termin_bayar in sch.termin_bayars:
        if termin_bayar.id:
            termin_bayar_current = await crud.termin_bayar.get(id=termin_bayar.id)
            termin_bayar_updated = TerminBayarUpdateSch(**termin_bayar.dict(), termin_id=obj_updated.id)
            await crud.termin_bayar.update(obj_current=termin_bayar_current, obj_new=termin_bayar_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)
        else:
            termin_bayar_sch = TerminBayarCreateSch(**termin_bayar.dict(), termin_id=obj_updated.id)
            await crud.termin_bayar.create(obj_in=termin_bayar_sch,  db_session=db_session, with_commit=False, created_by_id=current_worker.id)


    await db_session.commit()
    await db_session.refresh(obj_updated)

    obj_updated = await crud.termin.get_by_id(id=obj_updated.id)

    return create_response(data=obj_updated)

@router.get("/search/tahap/{id}", response_model=GetResponseBaseSch[TahapForTerminByIdSch])
async def get_list_spk_by_tahap_id(
                id:UUID,
                jenis_bayar:JenisBayarEnum,
                termin_id:UUID | None = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    tahap = await crud.tahap.get_by_id_for_termin(id=id)
    obj_return = TahapForTerminByIdSch(**dict(tahap))

    spk_details = await crud.spk.get_multi_by_tahap_id(tahap_id=id, jenis_bayar=jenis_bayar)
    if termin_id:
        exists_spk_details = await crud.spk.get_multi_by_tahap_id_and_termin_id(tahap_id=id, jenis_bayar=jenis_bayar, termin_id=termin_id)
        spk_details = spk_details + exists_spk_details
        
    spkts = []
    for s in spk_details:
        spk = SpkForTerminSch(spk_id=s.id, spk_code=s.code, spk_amount=s.nilai, spk_satuan_bayar=s.satuan_bayar,
                              bidang_id=s.bidang_id, id_bidang=s.id_bidang, alashak=s.alashak, group=s.bidang.group,
                              luas_bayar=s.bidang.luas_bayar, harga_transaksi=s.bidang.harga_transaksi, harga_akta=s.bidang.harga_akta,
                              total_harga=s.bidang.total_harga_transaksi, sisa_pelunasan=s.bidang.sisa_pelunasan, amount=s.spk_amount)

        if jenis_bayar == JenisBayarEnum.LUNAS:
            spk.amount = spk.sisa_pelunasan

        spkts.append(spk)

    obj_return.spkts = spkts
    return create_response(data=obj_return)

@router.get("/search/kjb_hd", response_model=GetResponseBaseSch[list[KjbHdSearchSch]])
async def get_list_kjb_hd(
                keyword:str = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(KjbHd)
    query = query.outerjoin(Termin, Termin.kjb_hd_id == KjbHd.id)
    query = query.filter(Termin.kjb_hd_id == None)
    
    if keyword:
        query = query.filter(KjbHd.code.ilike(f'%{keyword}%'))


    objs = await crud.kjb_hd.get_multi_no_page(query=query)
    return create_response(data=objs)

@router.get("/search/kjb_hd/{id}", response_model=GetResponseBaseSch[KjbHdForTerminByIdSch])
async def get_list_bidang_by_kjb_hd_id(
                id:UUID,
                termin_id:UUID | None = None,
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

@router.get("/search/komponen_biaya", response_model=GetResponseBaseSch[list[BidangKomponenBiayaBebanPenjualSch]])
async def get_list_komponen_biaya_by_bidang_id_and_invoice_id(
                bidang_id:UUID,
                invoice_id:UUID,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""
    
    objs = await crud.bidang_komponen_biaya.get_multi_beban_by_invoice_id(invoice_id=invoice_id)
    if bidang_id:
        objs_2 = await crud.bidang_komponen_biaya.get_multi_beban_by_bidang_id(bidang_id=bidang_id)
        objs = objs + objs_2

    return create_response(data=objs)

@router.get("/search/komponen_biaya/bidang/{id}", response_model=GetResponseBaseSch[list[BidangKomponenBiayaBebanPenjualSch]])
async def get_list_komponen_biaya_by_bidang_id(
                id:UUID,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.bidang_komponen_biaya.get_multi_beban_by_bidang_id(bidang_id=id)

    return create_response(data=objs)

@router.post("/search/notaris", response_model=GetResponseBaseSch[list[NotarisSrcSch]])
async def get_list_manager(
                sch:TerminBidangIDSch,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    list_id = [id.bidang_id for id in sch.bidangs]

    objs = await crud.notaris.get_multi_by_bidang_ids(list_ids=list_id)

    return create_response(data=objs)

@router.post("/search/manager", response_model=GetResponseBaseSch[list[ManagerSrcSch]])
async def get_list_manager(
                sch:TerminBidangIDSch,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    list_id = [id.bidang_id for id in sch.bidangs]

    objs = await crud.manager.get_multi_by_bidang_ids(list_ids=list_id)

    return create_response(data=objs)

@router.post("/search/sales", response_model=GetResponseBaseSch[list[SalesSrcSch]])
async def get_list_sales(
                sch:TerminBidangIDSch,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    list_id = [id.bidang_id for id in sch.bidangs]

    objs = await crud.sales.get_multi_by_bidang_ids(list_ids=list_id)

    return create_response(data=objs)

@router.post("/search/rekening", response_model=GetResponseBaseSch[list[RekeningSch]])
async def get_list_rekening(
                sch:TerminBidangIDSch,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    list_id = [id.bidang_id for id in sch.bidangs]

    objs = await crud.rekening.get_multi_by_bidang_ids(list_ids=list_id)

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

@router.get("/print-out/{id}")
async def printout(id:UUID | str,
                   current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Print out DP Pelunasan"""

    obj = await crud.termin.get_by_id_for_printout(id=id)
    if obj is None:
        raise IdNotFoundException(Termin, id)
    
    termin_header = TerminByIdForPrintOut(**dict(obj))
    date_obj = datetime.strptime(str(termin_header.tanggal_transaksi), "%Y-%m-%d")
    day_of_week = date_obj.strftime("%A")
    hari_transaksi:str|None = HelperService().ToDayName(day_of_week)
    
    obj_bidangs = await crud.invoice.get_invoice_by_termin_id_for_printout(termin_id=id)
   
    bidangs = []
    overlap_exists = False
    for bd in obj_bidangs:
        bidang = InvoiceForPrintOutExt(**dict(bd), total_hargaExt="{:,.0f}".format(bd.total_harga),
                                    harga_transaksiExt = "{:,.0f}".format(bd.harga_transaksi),
                                    luas_suratExt = "{:,.0f}".format(bd.luas_surat),
                                    luas_nettExt = "{:,.0f}".format(bd.luas_nett),
                                    luas_ukurExt = "{:,.0f}".format(bd.luas_ukur),
                                    luas_gu_peroranganExt = "{:,.0f}".format(bd.luas_gu_perorangan),
                                    luas_pbt_peroranganExt = "{:,.0f}".format(bd.luas_pbt_perorangan),
                                    luas_bayarExt = "{:,.0f}".format(bd.luas_bayar))
        
        bidang.overlaps = await crud.bidangoverlap.get_multi_by_bidang_id_for_printout(bidang_id=bd.bidang_id)
        if len(bidang.overlaps) > 0:
            overlap_exists = True

        bidangs.append(bidang)
        
    list_bidang_id = [bd.bidang_id for bd in obj_bidangs]
    
    array_total_luas_surat = numpy.array([b.luas_surat for b in obj_bidangs])
    total_luas_surat = numpy.sum(array_total_luas_surat)
    total_luas_surat = "{:,.0f}".format(total_luas_surat)

    array_total_luas_ukur = numpy.array([b.luas_ukur for b in obj_bidangs])
    total_luas_ukur = numpy.sum(array_total_luas_ukur)
    total_luas_ukur = "{:,.0f}".format(total_luas_ukur)

    array_total_luas_gu_perorangan = numpy.array([b.luas_gu_perorangan for b in obj_bidangs])
    total_luas_gu_perorangan = numpy.sum(array_total_luas_gu_perorangan)
    total_luas_gu_perorangan = "{:,.0f}".format(total_luas_gu_perorangan)

    array_total_luas_nett = numpy.array([b.luas_nett for b in obj_bidangs])
    total_luas_nett = numpy.sum(array_total_luas_nett)
    total_luas_nett = "{:,.0f}".format(total_luas_nett)

    array_total_luas_pbt_perorangan = numpy.array([b.luas_pbt_perorangan for b in obj_bidangs])
    total_luas_pbt_perorangan = numpy.sum(array_total_luas_pbt_perorangan)
    total_luas_pbt_perorangan = "{:,.0f}".format(total_luas_pbt_perorangan)

    array_total_luas_bayar = numpy.array([b.luas_bayar for b in obj_bidangs])
    total_luas_bayar = numpy.sum(array_total_luas_bayar)
    total_luas_bayar = "{:,.0f}".format(total_luas_bayar)

    array_total_harga = numpy.array([b.total_harga for b in obj_bidangs])
    total_harga = numpy.sum(array_total_harga)
    total_harga = "{:,.0f}".format(total_harga)


    invoices_history = []
    obj_invoices_history = await crud.termin.get_history_invoice_by_bidang_ids_for_printout(list_id=list_bidang_id, termin_id=id)
    for his in obj_invoices_history:
        history = TerminInvoiceHistoryforPrintOutExt(**dict(his))
        history.amountExt = "{:,.0f}".format(history.amount)
        invoices_history.append(history)

    komponen_biayas = []
    obj_komponen_biayas = await crud.termin.get_beban_biaya_by_id_for_printout(id=id)
    for bb in obj_komponen_biayas:
        beban_biaya = TerminBebanBiayaForPrintOutExt(**dict(bb))
        beban_biaya.beban_biaya_name = f"{beban_biaya.beban_biaya_name} {beban_biaya.tanggungan}"
        beban_biaya.amountExt = "{:,.0f}".format(beban_biaya.amount)
        komponen_biayas.append(beban_biaya)

    harga_aktas = []
    obj_kjb_hargas = await crud.kjb_harga.get_harga_akta_by_termin_id_for_printout(termin_id=id)
    for hg in obj_kjb_hargas:
        harga_akta = KjbHargaAktaSch(**dict(hg))
        harga_akta.harga_aktaExt = "{:,.0f}".format(hg.harga_akta)
        harga_aktas.append(harga_akta)

    termin_bayars = []
    no = 1
    obj_termin_bayar = await crud.termin_bayar.get_multi_by_termin_id_for_printout(termin_id=id)

    filename = "memo_tanah_overlap.html" if overlap_exists else "memo_tanah.html"
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template(filename)

    render_template = template.render(code=termin_header.code or "",
                                      created_at=termin_header.created_at.date(),
                                      nomor_tahap=termin_header.nomor_tahap,
                                      project_name=termin_header.project_name,
                                      notaris_name=termin_header.notaris_name,
                                      manager_name=termin_header.manager_name.upper(),
                                      sales_name=termin_header.sales_name.upper(),
                                      mediator=termin_header.mediator.upper(),
                                      data=bidangs,
                                      total_luas_surat=total_luas_surat,
                                      total_luas_ukur=total_luas_ukur,
                                      total_luas_gu_perorangan=total_luas_gu_perorangan,
                                      total_luas_nett=total_luas_nett,
                                      total_luas_pbt_perorangan=total_luas_pbt_perorangan,
                                      total_luas_bayar=total_luas_bayar,
                                      total_harga=total_harga,
                                      data_invoice_history=invoices_history,
                                      data_beban_biaya=komponen_biayas,
                                      data_harga_akta=harga_aktas,
                                      data_payment=obj_termin_bayar,
                                      tanggal_transaksi=termin_header.tanggal_transaksi,
                                      hari_transaksi=hari_transaksi,
                                      jenis_bayar=termin_header.jenis_bayar,
                                      amount="{:,.0f}".format(termin_header.amount),
                                      remark=termin_header.remark
                                    )
    
    try:
        doc = await PdfService().get_pdf(render_template)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed generate document")
    
    response = Response(doc, media_type='application/pdf')
    response.headers["Content-Disposition"] = f"attachment; filename={termin_header.project_name}.pdf"
    return response

@router.get("/print-out/utj/{id}")
async def printout(id:UUID | str,
                        current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Print out UTJ"""

    obj = await crud.termin.get_by_id_for_printout(id=id)
    if obj is None:
        raise IdNotFoundException(Termin, id)
    
    termin_header = TerminByIdForPrintOut(**dict(obj))

    data =  []
    no:int = 1
    invoices = await crud.invoice.get_invoice_by_termin_id_for_printout_utj(termin_id=id, jenis_bayar=termin_header.jenis_bayar)
    for inv in invoices:
        invoice = InvoiceForPrintOutUtj(**dict(inv))
        invoice.amountExt = "{:,.0f}".format(invoice.amount)
        invoice.luas_suratExt = "{:,.0f}".format(invoice.luas_surat)
        keterangan:str = ""
        keterangans = await crud.hasil_peta_lokasi_detail.get_keterangan_by_bidang_id_for_printout_utj(bidang_id=inv.bidang_id)
        for k in keterangans:
            kt = HasilPetaLokasiDetailForUtj(**dict(k))
            if kt.keterangan is not None and kt.keterangan != '':
                keterangan += f'{kt.keterangan}, '
        keterangan = keterangan[0:-2]
        invoice.keterangan = keterangan
        invoice.no = no
        no = no + 1

        data.append(invoice)

    array_total_luas_surat = numpy.array([b.luas_surat for b in invoices])
    total_luas_surat = numpy.sum(array_total_luas_surat)
    total_luas_surat = "{:,.0f}".format(total_luas_surat)

    array_total_amount = numpy.array([b.amount for b in invoices])
    total_amount = numpy.sum(array_total_amount)
    total_amount = "{:,.0f}".format(total_amount)

    filename:str = "utj.html" if termin_header.jenis_bayar == "UTJ" else "utj_khusus.html"
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template(filename)

    render_template = template.render(code=termin_header.code,
                                      data=data,
                                      total_luas_surat=total_luas_surat,
                                      total_amount=total_amount)
    
    try:
        doc = await PdfService().get_pdf(render_template)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed generate document")
    
    response = Response(doc, media_type='application/pdf')
    response.headers["Content-Disposition"] = f"attachment; filename={termin_header.code}.pdf"
    return response



    
