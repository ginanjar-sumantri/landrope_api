from uuid import UUID
from fastapi import APIRouter, status, Depends, Request, HTTPException, Response
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, or_, and_
import crud
from models.termin_model import Termin
from models.worker_model import Worker
from models.invoice_model import Invoice, InvoiceDetail
from models.tahap_model import Tahap
from models.kjb_model import KjbHd
from models.spk_model import Spk
from models.bidang_model import Bidang
from models.code_counter_model import CodeCounterEnum
from schemas.tahap_sch import TahapForTerminByIdSch
from schemas.termin_sch import (TerminSch, TerminCreateSch, TerminUpdateSch, 
                                TerminByIdSch, TerminByIdForPrintOut, TerminBidangForPrintOut, TerminBidangForPrintOutExt,
                                TerminInvoiceforPrintOut, TerminInvoiceHistoryforPrintOut, TerminHistoryForPrintOut,
                                TerminBebanBiayaForPrintOut, TerminUtjHistoryForPrintOut, TerminInvoiceHistoryforPrintOutExt,
                                TerminBebanBiayaForPrintOutExt)
from schemas.invoice_sch import InvoiceCreateSch, InvoiceUpdateSch, InvoiceForPrintOutUtj
from schemas.invoice_detail_sch import InvoiceDetailCreateSch, InvoiceDetailUpdateSch
from schemas.spk_sch import SpkSrcSch, SpkForTerminSch
from schemas.kjb_hd_sch import KjbHdForTerminByIdSch
from schemas.bidang_sch import BidangForUtjSch
from schemas.bidang_komponen_biaya_sch import BidangKomponenBiayaBebanPenjualSch
from schemas.hasil_peta_lokasi_detail_sch import HasilPetaLokasiDetailForUtj
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, ContentNoChangeException)
from common.ordered import OrderEnumSch
from common.enum import JenisBayarEnum, StatusHasilPetaLokasiEnum, SatuanBayarEnum
from common.rounder import RoundTwo
from common.generator import generate_code_month
from services.gcloud_task_service import GCloudTaskService
from decimal import Decimal
from services.pdf_service import PdfService
from jinja2 import Environment, FileSystemLoader
from datetime import date
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

    if sch.jenis_bayar == JenisBayarEnum.UTJ:
        last_number = await generate_code_month(entity=CodeCounterEnum.Utj, with_commit=False, db_session=db_session)

        today = date.today()
        month = roman.toRoman(today.month)
        year = today.year

        sch.code = f"{last_number}/UTJ/LA/{month}/{year}"

    new_obj = await crud.termin.create(obj_in=sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)

    #add invoice
    for invoice in sch.invoices:
        invoice_sch = InvoiceCreateSch(**invoice.dict(), termin_id=new_obj.id)
        invoice_sch.is_void = False
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
                query = query.where(getattr(Termin, key) == value)

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
    
    sch.is_void = obj_current.is_void
    
    obj_updated = await crud.termin.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)

    list_id_invoice = [inv.id for inv in sch.invoices if inv.id != None]
    query_inv = Invoice.__table__.delete().where(and_(~Invoice.id.in_(list_id_invoice), Invoice.termin_id == obj_updated.id))
    await crud.invoice.delete_multiple_where_not_in(query=query_inv, db_session=db_session, with_commit=False)

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
                    kb_payload = {"id" : inv_dt.bidang_komponen_biaya_id}
                    url = f'{request.base_url}landrope/bidang_komponen_biaya/cloud-task-is-not-use'
                    GCloudTaskService().create_task(payload=kb_payload, base_url=url)

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
        spk = SpkForTerminSch(**dict(s))
        total_beban_penjual = await crud.bidang.get_total_beban_penjual_by_bidang_id(bidang_id=spk.bidang_id)
        total_invoice = await crud.bidang.get_total_invoice_by_bidang_id(bidang_id=spk.bidang_id)
        spk.total_beban = total_beban_penjual.total_beban_penjual if total_beban_penjual != None else 0
        spk.total_invoice = total_invoice.total_invoice if total_invoice != None else 0
        spk.sisa_pelunasan = spk.total_harga - (spk.total_beban + spk.total_invoice)

        if jenis_bayar == JenisBayarEnum.LUNAS:
            spk.amount = spk.sisa_pelunasan

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

@router.get("/search/komponen_biaya", response_model=GetResponseBaseSch[list[BidangKomponenBiayaBebanPenjualSch]])
async def get_list_komponen_biaya_by_bidang_id_and_invoice_id(
                bidang_id:UUID,
                invoice_id:UUID,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""
    
    objs = await crud.bidang_komponen_biaya.get_multi_beban_penjual_by_invoice_id(invoice_id=invoice_id)
    if bidang_id:
        objs_2 = await crud.bidang_komponen_biaya.get_multi_beban_penjual_by_bidang_id(bidang_id=bidang_id)
        objs = objs + objs_2

    return create_response(data=objs)

@router.get("/search/komponen_biaya/bidang/{id}", response_model=GetResponseBaseSch[list[BidangKomponenBiayaBebanPenjualSch]])
async def get_list_komponen_biaya_by_bidang_id(
                id:UUID,
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

@router.get("/print-out/{id}")
async def printout(id:UUID | str,
                        current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Print out DP Pelunasan"""

    obj = await crud.termin.get_by_id_for_printout(id=id)
    if obj is None:
        raise IdNotFoundException(Termin, id)
    
    termin_header = TerminByIdForPrintOut(**dict(obj))
    
    bidangs = []
    no = 1
    obj_bidangs_on_tahap = await crud.termin.get_bidang_tahap_by_id_for_printout(id=id)
    for bd in obj_bidangs_on_tahap:
        bidang = TerminBidangForPrintOutExt(**dict(bd))
        bidang.total_hargaExt = "{:,.2f}".format(bidang.total_harga)
        bidang.harga_transaksiExt = "{:,.2f}".format(bidang.harga_transaksi)
        bidang.no = no
        bidangs.append(bidang)
        no = no + 1
    
    array_total_luas_surat = numpy.array([b.luas_surat for b in obj_bidangs_on_tahap])
    total_luas_surat = numpy.sum(array_total_luas_surat)
    total_luas_surat = "{:,.0f}".format(total_luas_surat)

    array_total_luas_ukur = numpy.array([b.luas_ukur for b in obj_bidangs_on_tahap])
    total_luas_ukur = numpy.sum(array_total_luas_ukur)
    total_luas_ukur = "{:,.0f}".format(total_luas_ukur)

    array_total_luas_gu_perorangan = numpy.array([b.luas_gu_perorangan for b in obj_bidangs_on_tahap])
    total_luas_gu_perorangan = numpy.sum(array_total_luas_gu_perorangan)
    total_luas_gu_perorangan = "{:,.0f}".format(total_luas_gu_perorangan)

    array_total_luas_nett = numpy.array([b.luas_nett for b in obj_bidangs_on_tahap])
    total_luas_nett = numpy.sum(array_total_luas_nett)
    total_luas_nett = "{:,.0f}".format(total_luas_nett)

    array_total_luas_pbt_perorangan = numpy.array([b.luas_pbt_perorangan for b in obj_bidangs_on_tahap])
    total_luas_pbt_perorangan = numpy.sum(array_total_luas_pbt_perorangan)
    total_luas_pbt_perorangan = "{:,.0f}".format(total_luas_pbt_perorangan)

    array_total_luas_bayar = numpy.array([b.luas_bayar for b in obj_bidangs_on_tahap])
    total_luas_bayar = numpy.sum(array_total_luas_bayar)
    total_luas_bayar = "{:,.0f}".format(total_luas_bayar)

    array_total_harga = numpy.array([b.total_harga for b in obj_bidangs_on_tahap])
    total_harga = numpy.sum(array_total_harga)
    total_harga = "{:,.2f}".format(total_harga)

    invoices = []
    list_bidang_id = []
    obj_invoices_on_termin = await crud.termin.get_invoice_by_id_for_printout(id=id)
    for inv in obj_invoices_on_termin:
        invoice = TerminInvoiceforPrintOut(**dict(inv))
        invoices.append(invoice)
        list_bidang_id.append(str(invoice.bidang_id))

    invoices_history = []
    obj_invoices_history = await crud.termin.get_history_invoice_by_bidang_ids_for_printout(list_id=list_bidang_id, termin_id=id)
    for his in obj_invoices_history:
        history = TerminInvoiceHistoryforPrintOutExt(**dict(his))
        history.amountExt = "{:,.2f}".format(history.amount)
        invoices_history.append(history)
    
    # utj_history = []
    # bidang_ids:str = ""
    # for bidang_id in list_bidang_id:
    #     bidang_ids += f"'{bidang_id}',"
    # bidang_ids = bidang_ids[0:-1]
    # obj_utj_history = await crud.termin.get_history_utj_by_bidang_ids_for_printout(ids=bidang_ids)
    # if obj_utj_history:
    #     utj_history = TerminUtjHistoryForPrintOut(**dict(obj_utj_history))


    # termins_history = []
    # obj_termins_history = await crud.termin.get_history_termin_by_tahap_id_for_printout(tahap_id=termin_header.tahap_id, termin_id=termin_header.id)
    # for t_his in obj_termins_history:
    #     termin_history = TerminHistoryForPrintOut(**dict(t_his))
    #     termins_history.append(termin_history)

    komponen_biayas = []
    obj_komponen_biayas = await crud.termin.get_beban_biaya_by_id_for_printout(id=id)
    for bb in obj_komponen_biayas:
        beban_biaya = TerminBebanBiayaForPrintOutExt(**dict(bb))
        beban_biaya.beban_biaya_name = f"{beban_biaya.beban_biaya_name} {beban_biaya.tanggungan}"
        beban_biaya.amountExt = "{:,.2f}".format(beban_biaya.amount)
        komponen_biayas.append(beban_biaya)
    
    # filename:str = "spk_clear.html" if obj.jenis_bayar != JenisBayarEnum.PAJAK else "spk_pajak_overlap.html"
    
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("memo_tanah.html")

    render_template = template.render(code=termin_header.code or "",
                                      created_at=termin_header.created_at.date(),
                                      nomor_tahap=termin_header.nomor_tahap,
                                      project_name=termin_header.project_name,
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
                                      tanggal_transaksi=termin_header.tanggal_transaksi,
                                      jenis_bayar=termin_header.jenis_bayar,
                                      amount="{:,.2f}".format(termin_header.amount)
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
    invoices = await crud.invoice.get_invoice_by_termin_id_for_printout_utj(termin_id=id)
    for inv in invoices:
        invoice = InvoiceForPrintOutUtj(**dict(inv))
        invoice.amountExt = "{:,.2f}".format(invoice.amount)
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

    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("utj.html")

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



    
