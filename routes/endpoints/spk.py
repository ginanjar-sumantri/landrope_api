from uuid import UUID
from fastapi import APIRouter, status, Depends, HTTPException, Response, BackgroundTasks, UploadFile, Request
from fastapi.responses import StreamingResponse
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_, text, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import cast, Date, exists
from sqlalchemy.orm import selectinload
from models import (Spk, Bidang, HasilPetaLokasi, ChecklistKelengkapanDokumenHd, ChecklistKelengkapanDokumenDt, Worker, Invoice, Termin, Planing)
from models.code_counter_model import CodeCounterEnum
from schemas.spk_sch import (SpkSch, SpkCreateSch, SpkUpdateSch, SpkByIdSch, SpkPrintOut, SpkListSch, SpkVoidSch,
                             SpkDetailPrintOut, SpkRekeningPrintOut, SpkOverlapPrintOut, SpkOverlapPrintOutExt)
from schemas.spk_kelengkapan_dokumen_sch import (SpkKelengkapanDokumenCreateSch, SpkKelengkapanDokumenSch, SpkKelengkapanDokumenUpdateSch)
from schemas.spk_history_sch import SpkHistoryCreateSch
from schemas.bidang_komponen_biaya_sch import BidangKomponenBiayaCreateSch, BidangKomponenBiayaUpdateSch, BidangKomponenBiayaSch
from schemas.bidang_sch import BidangSrcSch, BidangForSPKByIdSch, BidangForSPKByIdExtSch
from schemas.kjb_termin_sch import KjbTerminInSpkSch
from schemas.workflow_sch import WorkflowCreateSch, WorkflowSystemCreateSch, WorkflowSystemAttachmentSch, WorkflowUpdateSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.enum import (JenisBayarEnum, StatusSKEnum, JenisBidangEnum, 
                        SatuanBayarEnum, WorkflowEntityEnum, WorkflowLastStatusEnum, 
                        StatusPembebasanEnum, jenis_bayar_to_spk_status_pembebasan, jenis_bayar_to_text, JenisAlashakEnum)
from common.ordered import OrderEnumSch
from common.exceptions import (IdNotFoundException, DocumentFileNotFoundException)
from common.generator import generate_code
from services.pdf_service import PdfService
from services.history_service import HistoryService
from services.helper_service import HelperService, KomponenBiayaHelper, BundleHelper, BidangHelper
from services.workflow_service import WorkflowService
from services.gcloud_storage_service import GCStorageService
from services.gcloud_task_service import GCloudTaskService
from configs.config import settings
from jinja2 import Environment, FileSystemLoader
from datetime import date
from typing import Dict
import crud
import json
import pandas as pd
import time
from io import BytesIO

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[SpkSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: SpkCreateSch,
            background_task:BackgroundTasks,
            request: Request,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    db_session = db.session

    #Filter
    if sch.jenis_bayar == JenisBayarEnum.BIAYA_LAIN:
        beban_biaya_ids = [x.beban_biaya_id for x in sch.spk_beban_biayas]
        await filter_biaya_lain(beban_biaya_ids=beban_biaya_ids, bidang_id=sch.bidang_id)
    
    # if sch.jenis_bayar == JenisBayarEnum.SISA_PELUNASAN:
    #     await filter_sisa_pelunasan(bidang_id=sch.bidang_id)

    if sch.jenis_bayar in [JenisBayarEnum.DP, JenisBayarEnum.LUNAS, JenisBayarEnum.PELUNASAN]:
        bundle_dt_ids = [dokumen.bundle_dt_id for dokumen in sch.spk_kelengkapan_dokumens]
        await filter_kelengkapan_dokumen(bundle_dt_ids=bundle_dt_ids)
    #EndFilter

    bidang = await crud.bidang.get_by_id(id=sch.bidang_id)

    code = await generate_code(entity=CodeCounterEnum.Spk, db_session=db_session, with_commit=False)
    jenis_bayar = jenis_bayar_to_text.get(sch.jenis_bayar, sch.jenis_bayar)

    sch.code = f"SPK-{jenis_bayar}/{code}/{bidang.id_bidang}"
    
    new_obj = await crud.spk.create(obj_in=sch, created_by_id=current_worker.id, with_commit=False)

    beban_biaya = None
    for komponen_biaya in sch.spk_beban_biayas:
        
        komponen_biaya_current = await crud.bidang_komponen_biaya.get_by_bidang_id_and_beban_biaya_id(bidang_id=new_obj.bidang_id, 
                                                                                                      beban_biaya_id=komponen_biaya.beban_biaya_id)
        
        
        if komponen_biaya_current:
            komponen_biaya_updated = BidangKomponenBiayaUpdateSch(**komponen_biaya_current.dict(exclude={"beban_pembeli", "remark"}), 
                                                                beban_pembeli=komponen_biaya.beban_pembeli,
                                                                remark=komponen_biaya.remark)
            
            
            await crud.bidang_komponen_biaya.update(obj_current=komponen_biaya_current, obj_new=komponen_biaya_updated,
                                                    db_session=db_session, with_commit=False,
                                                    updated_by_id=current_worker.id)
            
        else:
            beban_biaya = await crud.bebanbiaya.get(id=komponen_biaya.beban_biaya_id)
            komponen_biaya_sch = BidangKomponenBiayaCreateSch(bidang_id=new_obj.bidang_id, 
                                                        beban_biaya_id=komponen_biaya.beban_biaya_id, 
                                                        beban_pembeli=komponen_biaya.beban_pembeli,
                                                        is_void=False,
                                                        is_paid=False,
                                                        is_retur=False,
                                                        is_add_pay=beban_biaya.is_add_pay,
                                                        remark=komponen_biaya.remark,
                                                        satuan_bayar=beban_biaya.satuan_bayar,
                                                        satuan_harga=beban_biaya.satuan_harga,
                                                        formula=beban_biaya.formula,
                                                        amount=beban_biaya.amount)
            
            await crud.bidang_komponen_biaya.create(obj_in=komponen_biaya_sch, created_by_id=current_worker.id, with_commit=False)

    for kelengkapan_dokumen in sch.spk_kelengkapan_dokumens:
        kelengkapan_dokumen_sch = SpkKelengkapanDokumenCreateSch(spk_id=new_obj.id, bundle_dt_id=kelengkapan_dokumen.bundle_dt_id, tanggapan=kelengkapan_dokumen.tanggapan)
        await crud.spk_kelengkapan_dokumen.create(obj_in=kelengkapan_dokumen_sch, created_by_id=current_worker.id, with_commit=False)

    if sch.jenis_bayar in [JenisBayarEnum.DP, JenisBayarEnum.LUNAS, JenisBayarEnum.PELUNASAN]:
        status_pembebasan = jenis_bayar_to_spk_status_pembebasan.get(sch.jenis_bayar, None)
        await BidangHelper().update_status_pembebasan(list_bidang_id=[sch.bidang_id], status_pembebasan=status_pembebasan, db_session=db_session)

    #workflow
    if new_obj.jenis_bayar != JenisBayarEnum.PAJAK:
        flow = await crud.workflow_template.get_by_entity(entity=WorkflowEntityEnum.SPK)
        wf_sch = WorkflowCreateSch(reference_id=new_obj.id, entity=WorkflowEntityEnum.SPK, flow_id=flow.flow_id, version=1, last_status=WorkflowLastStatusEnum.ISSUED, step_name="ISSUED")
        
        await crud.workflow.create(obj_in=wf_sch, created_by_id=new_obj.created_by_id, db_session=db_session, with_commit=False)

        GCloudTaskService().create_task(payload={
                                                    "id":str(new_obj.id), 
                                                    "additional_info":new_obj.jenis_bayar
                                                }, 
                                        base_url=f'{request.base_url}landrope/spk/task-workflow')

    await db_session.commit()
    await db_session.refresh(new_obj)

    new_obj = await crud.spk.get_by_id(id=new_obj.id)

    bidang_ids = []
    bidang_ids.append(new_obj.bidang_id)

    background_task.add_task(KomponenBiayaHelper().calculated_all_komponen_biaya, bidang_ids)
    
    return create_response(data=new_obj)

async def filter_biaya_lain(beban_biaya_ids:list[UUID], bidang_id:UUID):

    beban_biaya_add_pays = await crud.bebanbiaya.get_beban_biaya_add_pay(list_id=beban_biaya_ids)
    add_pay_from_master = False
    if len(beban_biaya_add_pays) > 0:
        add_pay_from_master = True 
    
    komponen_biaya_add_pays = await crud.bidang_komponen_biaya.get_komponen_biaya_add_pay(list_id=beban_biaya_ids, bidang_id=bidang_id)
    add_pay_from_komponen = False
    if len(komponen_biaya_add_pays) > 0:
        add_pay_from_komponen = True
    
    if add_pay_from_master == False and add_pay_from_komponen == False:
        raise HTTPException(status_code=422, detail="Bidang tidak memiliki beban biaya lain diluar dari biaya tanah")

async def filter_sisa_pelunasan(bidang_id:UUID):
    bidang = await crud.bidang.get_by_id_for_spk(id=bidang_id)

    if bidang.has_invoice_lunas != True:
        raise HTTPException(status_code=422, detail="Bidang tidak memiliki pembayaran pelunasan")
    
    if bidang.sisa_pelunasan == 0:
        raise HTTPException(status_code=422, detail="Bidang tidak memiliki sisa pelunasan")

async def filter_kelengkapan_dokumen(bundle_dt_ids:list[UUID]):
    bundle_dts = await crud.bundledt.get_by_ids(list_ids=bundle_dt_ids)

    bundle_dt_no_have_metadata = any(bundledt.file_exists == False for bundledt in bundle_dts)
    if bundle_dt_no_have_metadata:
        raise HTTPException(status_code=422, detail="Failed create SPK. Detail : Data bundle untuk kelengkapan spk belum diinput")

@router.get("", response_model=GetResponsePaginatedSch[SpkListSch])
async def get_list(
                start_date:date|None = None,
                end_date:date|None = None,
                outstanding:bool|None = False,
                params: Params=Depends(), 
                order_by:str = None, 
                keyword:str = None, 
                filter_query:str=None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(Spk).join(Bidang, Spk.bidang_id == Bidang.id)
    
    if keyword:
        query = query.filter(
            or_(
                Spk.code.ilike(f'%{keyword}%'),
                Bidang.id_bidang.ilike(f'%{keyword}%'),
                Bidang.alashak.ilike(f'%{keyword}%')
            )
        )

    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
                query = query.where(getattr(Spk, key) == value)
    
    if start_date and end_date:
        query = query.filter(cast(Spk.created_at, Date).between(start_date, end_date))
    
    if outstanding:
        subquery = (
            select(Invoice.spk_id)
            .join(Termin, Termin.id == Invoice.termin_id)
            .filter(Invoice.is_void != True, ~Termin.jenis_bayar.in_(['UTJ', 'UTJ_KHUSUS', 'BEGINNING_BALANCE']))
            .distinct()
        )
        query = query.filter(~Spk.jenis_bayar.in_(['BEGINNING_BALANCE', 'PAJAK']))
        query = query.filter(~Spk.id.in_(subquery))


    query = query.distinct()

    objs = await crud.spk.get_multi_paginated_ordered(params=params, query=query)
    return create_response(data=objs)

@router.get("/export/excel")
async def get_report(
                start_date:date|None = None,
                end_date:date|None = None,
                outstanding:bool|None = False,
                keyword:str = None, 
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    filename:str = ''
    query = select(Spk).select_from(Spk
                    ).join(Bidang, Spk.bidang_id == Bidang.id)
    
    if keyword:
        query = query.filter(
            or_(
                Spk.code.ilike(f'%{keyword}%'),
                Bidang.id_bidang.ilike(f'%{keyword}%'),
                Bidang.alashak.ilike(f'%{keyword}%')
            )
        )
    
    if start_date and end_date:
        query = query.filter(cast(Spk.created_at, Date).between(start_date, end_date))
        filename = str(filename)

    if outstanding:
        subquery = (
            select(Invoice.spk_id)
            .join(Termin, Termin.id == Invoice.termin_id)
            .filter(Invoice.is_void != True, ~Termin.jenis_bayar.in_(['UTJ', 'UTJ_KHUSUS', 'BEGINNING_BALANCE']))
            .distinct()
        )
        query = query.filter(~Spk.jenis_bayar.in_(['BEGINNING_BALANCE', 'PAJAK']))
        query = query.filter(~Spk.id.in_(subquery))

    query = query.distinct()
    query = query.options(selectinload(Spk.bidang
                                ).options(selectinload(Bidang.pemilik)
                                ).options(selectinload(Bidang.planing
                                                ).options(selectinload(Planing.project)
                                                ).options(selectinload(Planing.desa)
                                                )
                                ).options(selectinload(Bidang.manager)
                                )
                    )

    objs = await crud.spk.get_multi_no_page(query=query)

    data = [{"Id Bidang" : spk.id_bidang, 
             "Id Bidang Lama" : spk.id_bidang_lama or '', 
             "Group" : spk.group,
             "Pemilik" : spk.bidang.pemilik_name,
             "Alashak" : spk.alashak,
             "Project" : spk.bidang.project_name, 
             "Desa" : spk.bidang.desa_name,
             "Luas Surat" : spk.bidang.luas_surat, 
             "Jenis Bayar" : spk.jenis_bayar,
             "Manager" : spk.manager_name,
             "Tanggal Buat": spk.created_at, 
             "Created By" : spk.created_name} for spk in objs]

    
    df = pd.DataFrame(data=data)

    output = BytesIO()
    df.to_excel(output, index=False, sheet_name=f'SPK')

    output.seek(0)

    return StreamingResponse(BytesIO(output.getvalue()), 
                            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            headers={"Content-Disposition": "attachment;filename=spk_data.xlsx"})
   
@router.get("/{id}", response_model=GetResponseBaseSch[SpkByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj_return = await get_by_id_spk(id=id)

    return create_response(data=obj_return)

async def get_by_id_spk(id:UUID) -> SpkByIdSch | None:

    obj = await crud.spk.get_by_id(id=id)

    if not obj:
        raise IdNotFoundException(Spk, id)
    
    bidang_obj = await crud.bidang.get_by_id(id=obj.bidang_id)
    if not bidang_obj:
        raise IdNotFoundException(Bidang, obj.bidang_id)

    termins = []
    if bidang_obj.hasil_peta_lokasi:
        harga = await crud.kjb_harga.get_by_kjb_hd_id_and_jenis_alashak(kjb_hd_id=bidang_obj.hasil_peta_lokasi.kjb_dt.kjb_hd_id, jenis_alashak=bidang_obj.jenis_alashak)
        
        for tr in harga.termins:
            if tr.id == obj.kjb_termin_id:
                termin = KjbTerminInSpkSch(**tr.dict(), spk_id=obj.id, spk_code=obj.code)
                termins.append(termin)
            else:
                spk = await crud.spk.get_by_bidang_id_kjb_termin_id(bidang_id=bidang_obj.id, kjb_termin_id=tr.id)
                if spk:
                    termin = KjbTerminInSpkSch(**tr.dict(), spk_id=spk.id, spk_code=spk.code)
                else:
                    termin = KjbTerminInSpkSch(**tr.dict())
                termins.append(termin)

    ktp_value:str | None = await BundleHelper().get_key_value(dokumen_name='KTP SUAMI', bidang_id=bidang_obj.id)
    npwp_value:str | None = await BundleHelper().get_key_value(dokumen_name='NPWP', bidang_id=bidang_obj.id)

    percentage_lunas = None
    if obj.jenis_bayar != JenisBayarEnum.BEGINNING_BALANCE:
        percentage_lunas = await crud.bidang.get_percentage_lunas(bidang_id=bidang_obj.id)
    
    bidang_sch = BidangForSPKByIdSch(id=bidang_obj.id,
                                    jenis_alashak=bidang_obj.jenis_alashak,
                                    id_bidang=bidang_obj.id_bidang,
                                    hasil_analisa_peta_lokasi=bidang_obj.hasil_analisa_peta_lokasi,
                                    kjb_no=bidang_obj.hasil_peta_lokasi.kjb_dt.kjb_code if bidang_obj.hasil_peta_lokasi else None,
                                    satuan_bayar=obj.satuan_bayar,
                                    group=bidang_obj.group,
                                    pemilik_name=bidang_obj.pemilik_name,
                                    alashak=bidang_obj.alashak,
                                    desa_name=bidang_obj.desa_name,
                                    project_name=bidang_obj.project_name,
                                    luas_surat=bidang_obj.luas_surat,
                                    luas_ukur=bidang_obj.luas_ukur,
                                    luas_gu_perorangan=bidang_obj.luas_gu_perorangan,
                                    luas_gu_pt=bidang_obj.luas_gu_pt,
                                    luas_pbt_perorangan=bidang_obj.luas_pbt_perorangan,
                                    luas_pbt_pt=bidang_obj.luas_pbt_pt,
                                    manager_name=bidang_obj.manager_name,
                                    no_peta=bidang_obj.no_peta,
                                    notaris_name=bidang_obj.notaris_name,
                                    ptsk_name=bidang_obj.ptsk_name,
                                    status_sk=bidang_obj.status_sk,
                                    bundle_hd_id=bidang_obj.bundle_hd_id,
                                    ktp=ktp_value,
                                    npwp=npwp_value,
                                    termins=termins,
                                    percentage_lunas=percentage_lunas.percentage_lunas if percentage_lunas else 0)
    
    obj_return = SpkByIdSch(**obj.dict())
    obj_return.bidang = bidang_sch

    pengembalian = False
    if obj.jenis_bayar == JenisBayarEnum.PENGEMBALIAN_BEBAN_PENJUAL:
        pengembalian = True
    
    pajak = False
    if obj.jenis_bayar == JenisBayarEnum.PAJAK:
        pajak = True

    komponen_biayas = await crud.bidang_komponen_biaya.get_multi_by_bidang_id(bidang_id=obj.bidang_id, pengembalian=pengembalian, pajak=pajak)

    list_komponen_biaya = []
    for kb in komponen_biayas:
        komponen_biaya_sch = BidangKomponenBiayaSch(**kb.dict())
        komponen_biaya_sch.beban_biaya_name = kb.beban_biaya_name
        list_komponen_biaya.append(komponen_biaya_sch)
    
    list_kelengkapan_dokumen = []
    for kd in obj.spk_kelengkapan_dokumens:
        kelengkapan_dokumen_sch = SpkKelengkapanDokumenSch(**kd.dict())
        kelengkapan_dokumen_sch.dokumen_name = kd.dokumen_name
        kelengkapan_dokumen_sch.has_meta_data = kd.has_meta_data
        kelengkapan_dokumen_sch.file_path = kd.file_path
        list_kelengkapan_dokumen.append(kelengkapan_dokumen_sch)

    obj_return.spk_beban_biayas = list_komponen_biaya
    obj_return.spk_kelengkapan_dokumens = list_kelengkapan_dokumen
    obj_return.created_name = obj.created_name
    obj_return.updated_name = obj.updated_name

    return obj_return

@router.put("/{id}", response_model=PutResponseBaseSch[SpkSch])
async def update(id:UUID, 
                 sch:SpkUpdateSch,
                 background_task:BackgroundTasks,
                 request:Request,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    db_session = db.session
    obj_current = await crud.spk.get_by_id(id=id)

    if not obj_current:
        raise IdNotFoundException(Spk, id)
        
    #workflow
    if sch.jenis_bayar != JenisBayarEnum.PAJAK:
        msg_error_wf = "SPK Approval Has Been Completed!" if WorkflowLastStatusEnum.COMPLETED else "SPK Approval Need Approval!"
        
        if obj_current.status_workflow not in [WorkflowLastStatusEnum.NEED_DATA_UPDATE, WorkflowLastStatusEnum.REJECTED]:
            raise HTTPException(status_code=422, detail=f"Failed update. Detail : {msg_error_wf}")
        
    #filter
    if sch.jenis_bayar in [JenisBayarEnum.DP, JenisBayarEnum.LUNAS]:
        bundle_dt_ids = [dokumen.bundle_dt_id for dokumen in sch.spk_kelengkapan_dokumens]
        await filter_kelengkapan_dokumen(bundle_dt_ids=bundle_dt_ids)
    #end filter
    
    #schema for history
    spk_history = await get_by_id_spk(id=id)
    await HistoryService().create_history_spk(spk=spk_history, worker_id=current_worker.id, db_session=db_session)

    bidang_current = await crud.bidang.get_by_id_for_spk(id=obj_current.bidang_id)

    if sch.jenis_bayar not in [JenisBayarEnum.BIAYA_LAIN]:
        if bidang_current.has_invoice_lunas:
            raise HTTPException(status_code=422, detail="Failed Update. Detail : Bidang already have Invoice Lunas")
    else:
        beban_biaya_ids = [x.beban_biaya_id for x in sch.spk_beban_biayas]
        await filter_biaya_lain(beban_biaya_ids=beban_biaya_ids, bidang_id=sch.bidang_id)
    
    sch.is_void = obj_current.is_void

    if sch.file:
        file_name=f"SURAT PERINTAH KERJA-{obj_current.code.replace('/', '_')}"
        try:
            file_upload_path = await BundleHelper().upload_to_storage_from_base64(base64_str=sch.file, file_name=file_name)
        except ZeroDivisionError as e:
            raise HTTPException(status_code=422, detail="Failed upload dokumen Memo Pembayaran")
        
        sch.file_upload_path = file_upload_path
    
    obj_updated = await crud.spk.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id, with_commit=False)

    #remove beban biaya
    list_id = [beban_biaya.id for beban_biaya in sch.spk_beban_biayas if beban_biaya.id != None]
    if len(list_id) > 0:
        beban_biaya_will_removed = await crud.bidang_komponen_biaya.get_multi_not_in_id_removed(bidang_id=obj_updated.bidang_id, list_ids=list_id)

        if len(beban_biaya_will_removed) > 0:
            await crud.bidang_komponen_biaya.remove_multiple_data(list_obj=beban_biaya_will_removed, db_session=db_session)
    
    elif len(list_id) == 0:
        list_obj = await crud.bidang_komponen_biaya.get_multi_by_bidang_id(bidang_id=obj_current.bidang_id)
        await crud.bidang_komponen_biaya.remove_multiple_data(list_obj=list_obj, db_session=db_session)

    beban_biaya = None
    for komponen_biaya in sch.spk_beban_biayas:
        komponen_biaya_current = await crud.bidang_komponen_biaya.get_by_bidang_id_and_beban_biaya_id(bidang_id=obj_updated.bidang_id, 
                                                                                                      beban_biaya_id=komponen_biaya.beban_biaya_id)
        
        if komponen_biaya_current:
            komponen_biaya_updated = BidangKomponenBiayaUpdateSch(**komponen_biaya_current.dict())
            komponen_biaya_updated.is_void, komponen_biaya_updated.is_paid, komponen_biaya_updated.beban_pembeli, komponen_biaya_updated.remark = [komponen_biaya_current.is_void, komponen_biaya_current.is_paid, komponen_biaya.beban_pembeli, komponen_biaya.remark]
            await crud.bidang_komponen_biaya.update(obj_current=komponen_biaya_current, obj_new=komponen_biaya_updated,
                                                    db_session=db_session, with_commit=False,
                                                    updated_by_id=current_worker.id)
            beban_biaya = komponen_biaya_current.beban_biaya
        else:
            beban_biaya = await crud.bebanbiaya.get(id=komponen_biaya.beban_biaya_id)
            komponen_biaya_sch = BidangKomponenBiayaCreateSch(bidang_id=obj_updated.bidang_id, 
                                                        beban_biaya_id=komponen_biaya.beban_biaya_id, 
                                                        beban_pembeli=komponen_biaya.beban_pembeli,
                                                        is_void=False,
                                                        is_paid=False,
                                                        is_retur=False,
                                                        is_add_pay=beban_biaya.is_add_pay,
                                                        remark=komponen_biaya.remark,
                                                        satuan_bayar=beban_biaya.satuan_bayar,
                                                        satuan_harga=beban_biaya.satuan_harga,
                                                        amount=beban_biaya.amount)
            
            await crud.bidang_komponen_biaya.create(obj_in=komponen_biaya_sch, created_by_id=current_worker.id, with_commit=False)

    #remove kelengkapan dokumen 
    list_ids = [kelengkapan_dokumen.id for kelengkapan_dokumen in sch.spk_kelengkapan_dokumens if kelengkapan_dokumen.id != None]
    if len(list_ids) > 0:
        kelengkapan_biaya_will_removed = await crud.spk_kelengkapan_dokumen.get_multi_not_in_id_removed(spk_id=obj_updated.id, list_ids=list_ids)

        if len(kelengkapan_biaya_will_removed) > 0:
            await crud.spk_kelengkapan_dokumen.remove_multiple_data(list_obj=kelengkapan_biaya_will_removed, db_session=db_session)
    
    elif len(list_ids) == 0 and len(obj_current.spk_kelengkapan_dokumens) > 0:
        await crud.spk_kelengkapan_dokumen.remove_multiple_data(list_obj=obj_current.spk_kelengkapan_dokumens, db_session=db_session)
    
    for kelengkapan_dokumen in sch.spk_kelengkapan_dokumens:
        if kelengkapan_dokumen.id is None:
            kelengkapan_dokumen_sch = SpkKelengkapanDokumenCreateSch(spk_id=id, bundle_dt_id=kelengkapan_dokumen.bundle_dt_id, tanggapan=kelengkapan_dokumen.tanggapan)
            await crud.spk_kelengkapan_dokumen.create(obj_in=kelengkapan_dokumen_sch, created_by_id=current_worker.id, with_commit=False)
        else:
            kelengkapan_dokumen_current = await crud.spk_kelengkapan_dokumen.get(id=kelengkapan_dokumen.id)
            kelengkapan_dokumen_sch = SpkKelengkapanDokumenUpdateSch(spk_id=id, bundle_dt_id=kelengkapan_dokumen.bundle_dt_id, tanggapan=kelengkapan_dokumen.tanggapan)
            await crud.spk_kelengkapan_dokumen.update(obj_current=kelengkapan_dokumen_current, obj_new=kelengkapan_dokumen_sch, updated_by_id=current_worker.id, with_commit=False)

    #workflow
    if obj_updated.jenis_bayar != JenisBayarEnum.PAJAK:
        wf_current = await crud.workflow.get_by_reference_id(reference_id=obj_updated.id)
        if wf_current:
            if wf_current.last_status != WorkflowLastStatusEnum.REJECTED:
                raise HTTPException(status_code=422, detail="Failed update spk. Detail : Workflow is running")
            
            wf_updated = WorkflowUpdateSch(**wf_current.dict(exclude={"last_status", "step_name"}), last_status=WorkflowLastStatusEnum.ISSUED, step_name="ISSUED")
            await crud.workflow.update(obj_current=wf_current, obj_new=wf_updated, updated_by_id=obj_updated.updated_by_id, db_session=db_session, with_commit=False)
        else:
            flow = await crud.workflow_template.get_by_entity(entity=WorkflowEntityEnum.SPK)
            wf_sch = WorkflowCreateSch(reference_id=obj_updated.id, entity=WorkflowEntityEnum.SPK, flow_id=flow.flow_id, version=1, last_status=WorkflowLastStatusEnum.ISSUED, step_name="ISSUED")
            
            await crud.workflow.create(obj_in=wf_sch, created_by_id=obj_updated.updated_by_id, db_session=db_session, with_commit=False)
        
        GCloudTaskService().create_task(payload={
                                                    "id":str(obj_updated.id), 
                                                    "additional_info":obj_updated.jenis_bayar
                                                }, 
                                        base_url=f'{request.base_url}landrope/spk/task-workflow')

    await db_session.commit()
    await db_session.refresh(obj_updated)

    obj_updated = await crud.spk.get_by_id(id=obj_updated.id)

    bidang_ids = []
    bidang_ids.append(bidang_current.id)

    background_task.add_task(KomponenBiayaHelper().calculated_all_komponen_biaya, bidang_ids)
    background_task.add_task(generate_printout, obj_updated.id)

    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[SpkSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Delete a object"""

    obj_current = await crud.spk.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Spk, id)
    
    obj_deleted = await crud.spk.remove(id=id)

    return obj_deleted

@router.get("/search/bidang", response_model=GetResponsePaginatedSch[BidangSrcSch])
async def get_list(
                params: Params=Depends(),
                keyword:str = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(Bidang.id, Bidang.id_bidang, Bidang.alashak).select_from(Bidang
                    ).join(HasilPetaLokasi, Bidang.id == HasilPetaLokasi.bidang_id)
    
    if keyword:
        query = query.filter(or_(Bidang.id_bidang.ilike(f'%{keyword}%'), 
                                Bidang.alashak.ilike(f'%{keyword}%')))


    objs = await crud.bidang.get_multi_paginated(params=params, query=query)
    return create_response(data=objs)

@router.get("/search/bidang/{id}", response_model=GetResponseBaseSch[BidangForSPKByIdExtSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.bidang.get_by_id(id=id)

    hasil_peta_lokasi_current = await crud.hasil_peta_lokasi.get_by_bidang_id(bidang_id=obj.id)
    kjb_dt_current = await crud.kjb_dt.get_by_id(id=hasil_peta_lokasi_current.kjb_dt_id)
    
    spk_exists_on_bidangs = await crud.spk.get_multi_by_bidang_id(bidang_id=id)
    
    harga = await crud.kjb_harga.get_by_kjb_hd_id_and_jenis_alashak(kjb_hd_id=kjb_dt_current.kjb_hd_id, jenis_alashak=obj.jenis_alashak)
    termins = []
    for tr in harga.termins:
        spk_exists_on_bidang = next((spk_exists for spk_exists in spk_exists_on_bidangs if spk_exists.kjb_termin_id == tr.id), None)
        if spk_exists_on_bidang:
            termin = KjbTerminInSpkSch(**tr.dict(), spk_id=spk_exists_on_bidang.id, spk_code=spk_exists_on_bidang.code)
            termins.append(termin)
        else:
            termin = KjbTerminInSpkSch(**tr.dict())
            termins.append(termin)

    beban = []

    beban = await crud.bidang_komponen_biaya.get_multi_beban_by_bidang_id_for_spk(bidang_id=id)
    if len(beban) == 0:
        beban = await crud.kjb_bebanbiaya.get_kjb_beban_by_kjb_hd_id(kjb_hd_id=kjb_dt_current.kjb_hd_id)
    
    ktp_value:str | None = await BundleHelper().get_key_value(dokumen_name='KTP SUAMI', bidang_id=obj.id)
    npwp_value:str | None = await BundleHelper().get_key_value(dokumen_name='NPWP', bidang_id=obj.id)
    
    kelengkapan_dokumen = await crud.checklist_kelengkapan_dokumen_dt.get_all_for_spk(bidang_id=obj.id)

    percentage_lunas = await crud.bidang.get_percentage_lunas(bidang_id=id)
    
    obj_return = BidangForSPKByIdExtSch(id=obj.id,
                                    jenis_alashak=obj.jenis_alashak,
                                    id_bidang=obj.id_bidang,
                                    hasil_analisa_peta_lokasi=hasil_peta_lokasi_current.hasil_analisa_peta_lokasi,
                                    kjb_no=kjb_dt_current.kjb_code,
                                    satuan_bayar=kjb_dt_current.kjb_hd.satuan_bayar,
                                    group=obj.group,
                                    pemilik_name=obj.pemilik_name,
                                    alashak=obj.alashak,
                                    desa_name=obj.desa_name,
                                    project_name=obj.project_name,
                                    luas_surat=obj.luas_surat,
                                    luas_ukur=obj.luas_ukur,
                                    luas_gu_perorangan=obj.luas_gu_perorangan,
                                    luas_gu_pt=obj.luas_gu_pt,
                                    luas_pbt_perorangan=obj.luas_pbt_perorangan,
                                    luas_pbt_pt=obj.luas_pbt_pt,
                                    manager_name=obj.manager_name,
                                    no_peta=obj.no_peta,
                                    notaris_name=obj.notaris_name,
                                    ptsk_name=obj.ptsk_name,
                                    status_sk=obj.status_sk,
                                    bundle_hd_id=obj.bundle_hd_id,
                                    beban_biayas=beban,
                                    kelengkapan_dokumens=kelengkapan_dokumen,
                                    ktp=ktp_value,
                                    npwp=npwp_value,
                                    sisa_pelunasan=obj.sisa_pelunasan,
                                    termins=termins,
                                    percentage_lunas=percentage_lunas.percentage_lunas if percentage_lunas else 0)
    
    if obj:
        return create_response(data=obj_return)
    else:
        raise IdNotFoundException(Spk, id)

@router.get("/print-out/{id}")
async def printout(id:UUID | str, current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Print out"""

    obj_current = await crud.spk.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Spk, id)
    
    # file_path = obj_current.file_path

    # if file_path is None:
    file_path = await generate_printout(id=id)
    
    try:
        file_bytes = await GCStorageService().download_dokumen(file_path=file_path)
    except Exception as e:
        raise DocumentFileNotFoundException(dokumenname=obj_current.code)
    
    ext = obj_current.file_path.split('.')[-1]

    response = Response(content=file_bytes, media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename={obj_current.code.replace('/', '_')}.{ext}"
    return response

async def generate_printout(id:UUID|str):

    obj = await crud.spk.get_by_id_for_printout(id=id)
    if obj is None:
        raise IdNotFoundException(Spk, id)
    
    bidang = await crud.bidang.get(id=obj.bidang_id)
    
    filename:str = "spk_clear.html" if obj.jenis_bayar != JenisBayarEnum.PAJAK else "spk_pajak_clear.html"
    
    spk_header = SpkPrintOut(**dict(obj))
    remarks = spk_header.remark.splitlines()
    percentage_value:str = ""
    if spk_header.satuan_bayar == SatuanBayarEnum.Percentage and spk_header.jenis_bayar in [JenisBayarEnum.DP, JenisBayarEnum.LUNAS, JenisBayarEnum.PELUNASAN, JenisBayarEnum.TAMBAHAN_DP]:
        percentage_value = f" {spk_header.amount}%"
    
    ktp_value:str | None = await BundleHelper().get_key_value(dokumen_name='KTP PENJUAL', bidang_id=spk_header.bidang_id)
    npwp_value:str | None = await BundleHelper().get_key_value(dokumen_name='NPWP', bidang_id=spk_header.bidang_id)
    kk_value:str | None = await BundleHelper().get_key_value(dokumen_name='KARTU KELUARGA', bidang_id=spk_header.bidang_id)
    nop_value:str | None = await BundleHelper().get_key_value(dokumen_name='SPPT PBB NOP', bidang_id=spk_header.bidang_id)
    
    spk_details = []
    no = 1

    obj_kelengkapans = await crud.spk.get_kelengkapan_by_id_for_printout(id=id)

    #alashak mesti nomor 1
    alashak_kel = next((SpkDetailPrintOut(name=alashak["name"], tanggapan=alashak["tanggapan"]) for alashak in obj_kelengkapans if alashak.name == "ALAS HAK"), None)
    if alashak_kel:
        alashak_kel.no = 1
        alashak_kel.name = f"{alashak_kel.name} ({spk_header.alashak})"
        no = 2
        spk_details.append(alashak_kel)
    
    obj_beban_biayas = []
    obj_beban_biayas = await crud.spk.get_beban_biaya_for_printout(id=id, jenis_bayar=spk_header.jenis_bayar)

    for bb in obj_beban_biayas:
        beban_biaya = SpkDetailPrintOut(**dict(bb))
        if beban_biaya.name == 'PBB 10 Tahun Terakhir s/d Tahun ini' and spk_header.jenis_bayar != JenisBayarEnum.PAJAK:
            continue

        beban_biaya.no = no
        spk_details.append(beban_biaya)
        no += 1
    
    for k in obj_kelengkapans:
        kelengkapan = SpkDetailPrintOut(**dict(k))
        if kelengkapan.name == 'ALAS HAK':
            continue

        if kelengkapan.name == 'AJB':
            bundle_dt_ajb = await crud.bundledt.get(id=kelengkapan.bundle_dt_id)
            riwayat_ajb = json.loads(bundle_dt_ajb.riwayat_data.replace("'", '\"'))
            for data in riwayat_ajb["riwayat"]:
                kelengkapan_ajb = SpkDetailPrintOut(no=no, name=f"AJB {data['key_value']}", tanggapan=kelengkapan.tanggapan)
                spk_details.append(kelengkapan_ajb)
                no += 1
            
            continue

        kelengkapan.no = no
        kelengkapan.tanggapan = kelengkapan.tanggapan or ''
        spk_details.append(kelengkapan)
        no += 1

    pm_1 = await crud.spk.get_pm1(id=id, check_meta_data_exists=False)
    if pm_1["jumlah"] > 0:
        pm_1_lengkap = await crud.spk.get_pm1(id=id, check_meta_data_exists=True)
        if pm_1_lengkap["jumlah"] == 0:
            pm1 = SpkDetailPrintOut(no=no, name="PM1", tanggapan="PM1 Lengkap")
            spk_details.append(pm1)

    overlap_details = []
    if obj.jenis_bidang == JenisBidangEnum.Overlap:
        filename:str = "spk_overlap.html" if obj.jenis_bayar != JenisBayarEnum.PAJAK else "spk_pajak_overlap.html"
        obj_overlaps = await crud.spk.get_overlap_by_id_for_printout(id=id)
        for ov in obj_overlaps:
            overlap = SpkOverlapPrintOutExt(**dict(ov))
            overlap.luas_overlapExt = "{:,.0f}".format(overlap.luas_overlap)
            overlap.luas_suratExt = "{:,.0f}".format(overlap.luas_surat)
            overlap.tipe_overlapExt = overlap.tipe_overlap.value.replace('_', ' ')
            overlap.tahap = overlap.tahap if overlap.tahap != "0" else "-"
            overlap_details.append(overlap)

    rekening:str = ""
    if obj.jenis_bayar != JenisBayarEnum.PAJAK:
        rekenings = await crud.spk.get_rekening_by_id_for_printout(id=id)
        for r in rekenings:
            rek = SpkRekeningPrintOut(**dict(r))
            rekening += f"{rek.rekening}, "
        
        rekening = rekening[0:-2]

    
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template(filename)

    akta_peralihan:str = ""
    if bidang.jenis_alashak == JenisAlashakEnum.Girik:
        akta_peralihan = "PPJB" if spk_header.status_il == StatusSKEnum.Belum_IL else "SPH"
    else:
        akta_peralihan = "PPJB"

    render_template = template.render(kjb_hd_code=spk_header.kjb_hd_code,
                                      jenisbayar=f'{spk_header.jenis_bayar.value if spk_header.jenis_bayar != JenisBayarEnum.SISA_PELUNASAN else "KURANG BAYAR"}{percentage_value}'.replace("_", " "),
                                      jenis_bayar=spk_header.jenis_bayar,
                                      group=spk_header.group, 
                                      pemilik_name=spk_header.pemilik_name,
                                      alashak=spk_header.alashak,
                                      desa_name=spk_header.desa_name,
                                      luas_surat="{:,.0f}".format(spk_header.luas_surat or 0),
                                      luas_ukur="{:,.0f}".format(spk_header.luas_ukur or 0),
                                      luas_gu_perorangan="{:,.0f}".format(spk_header.luas_gu_perorangan or 0),
                                      luas_pbt_perorangan="{:,.0f}".format(spk_header.luas_pbt_perorangan or 0), 
                                      id_bidang=spk_header.id_bidang,
                                      no_peta=spk_header.no_peta,
                                      notaris_name=spk_header.notaris_name,
                                      project_name=spk_header.project_name, 
                                      ptsk=spk_header.ptsk_name,
                                      status_il=spk_header.status_il.replace("_"," ") if spk_header.status_il is not None else "",
                                      hasil_analisa_peta_lokasi=spk_header.analisa.value if spk_header.analisa else '',
                                      data=spk_details,
                                      data_overlap=overlap_details,
                                      worker_name=spk_header.worker_name, 
                                      manager_name=spk_header.manager_name,
                                      sales_name=spk_header.sales_name,
                                      akta_peralihan=akta_peralihan,
                                      no_rekening=rekening,
                                      nop=nop_value,
                                      npwp=npwp_value,
                                      ktp=ktp_value,
                                      kk=kk_value,
                                      remarks=remarks)
    
    try:
        doc = await PdfService().get_pdf(render_template)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed generate document")
    
    obj_current = await crud.spk.get(id=id)

    binary_io_data = BytesIO(doc)
    file = UploadFile(file=binary_io_data, filename=f"{obj_current.code.replace('/', '_')}.pdf")

    try:
        file_path = await GCStorageService().upload_file_dokumen(file=file, file_name=f"{obj_current.code.replace('/', '_')}", is_public=True)

        obj_updated = SpkUpdateSch(**obj_current.dict())
        obj_updated.file_path = file_path
        await crud.spk.update(obj_current=obj_current, obj_new=obj_updated)

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed generate document")
    
    return file_path

@router.put("/void/{id}", response_model=GetResponseBaseSch[SpkByIdSch])
async def void(id:UUID, 
            sch:SpkVoidSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """void a obj by its ids"""
    db_session = db.session

    obj_current = await crud.spk.get_by_id(id=id)

    if not obj_current:
        raise IdNotFoundException(Spk, id)
    
    if obj_current.has_invoice_active:
        raise HTTPException(status_code=422, detail="Failed void. Detail : Spk have invoice active in Memo Pembayaran!")
    
    #schema for history
    spk_history = await get_by_id_spk(id=id)
    await HistoryService().create_history_spk(spk=spk_history, worker_id=current_worker.id, db_session=db_session)
    
    obj_updated = SpkUpdateSch.from_orm(obj_current)
    obj_updated.is_void = True
    obj_updated.void_reason = sch.void_reason
    obj_updated.void_by_id = current_worker.id
    obj_updated.void_at = date.today()

    obj_updated = await crud.spk.update(obj_current=obj_current, obj_new=obj_updated, updated_by_id=current_worker.id, db_session=db_session)

    obj_updated = await crud.spk.get_by_id(id=obj_updated.id)
    return create_response(data=obj_updated) 

@router.post("/workflow")
async def create_workflow():

    body = {
        "client_id": "01HHEH1R23EXMBEKQHHFRZV9Y1",
        "client_ref_no": "4e0a3adb-7a49-43bd-b529-9c2e11479fe4",
        "flow_id": "01HHGRBWDZS7ET737MTSP738QV",
        "additional_info": {},
        "descs": "",
        "attachments": []
    }

    template = await crud.workflow_template.get_by_entity(entity=WorkflowEntityEnum.SPK)
    workflow_sch = WorkflowCreateSch(reference_id='1fa2aa0e-2ecf-4897-883d-873061dce49f', entity=WorkflowEntityEnum.SPK, flow_id=template.flow_id)
    workflow_system_sch = WorkflowSystemCreateSch(client_ref_no=str('1fa2aa0e-2ecf-4897-883d-873061dce49f'), flow_id=template.flow_id, descs=f"Need Approval", attachments=[])
    await crud.workflow.create_(obj_in=workflow_sch, obj_wf=workflow_system_sch)

    return {"result" : "Successfully"}

@router.post("/task-workflow")
async def create_workflow(payload:Dict):
    db_session = db.session
    id = payload.get("id", None)
    additional_info = payload.get("additional_info", None)

    obj = await crud.spk.get(id=id)

    if not obj:
        raise IdNotFoundException(Spk, id)
    
    wf_current = await crud.workflow.get_by_reference_id(reference_id=id)
    if not wf_current:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    trying:int = 0
    while obj.file_path is None:
        await generate_printout(id=id)
        if trying > 7:
            raise HTTPException(status_code=404, detail="File not found")
        obj = await crud.spk.get(id=id)
        time.sleep(2)
        trying += 1

    with_commit:bool = False
    if obj.jenis_bayar in [JenisBayarEnum.DP, JenisBayarEnum.PELUNASAN, JenisBayarEnum.LUNAS]:
        bidang = await crud.bidang.get(id=obj.bidang_id)
        bundle = await crud.bundlehd.get_by_id(id=bidang.bundle_hd_id)
        if bundle:
            await BundleHelper().merge_spk(bundle=bundle, code=obj.code, tanggal=obj.created_at.date(), file_path=obj.file_path, worker_id=obj.updated_by_id, db_session=db_session)
            with_commit = True

    public_url = await GCStorageService().public_url(file_path=obj.file_path)
   
    wf_system_attachment = WorkflowSystemAttachmentSch(name=f"{obj.code}", url=public_url)
    wf_system_sch = WorkflowSystemCreateSch(client_ref_no=str(id), 
                                            flow_id=wf_current.flow_id, 
                                            descs=f"""Dokumen SPK {obj.code} ini membutuhkan Approval dari Anda:<br><br>
                                                    Tanggal: {obj.created_at.date()}<br>
                                                    Dokumen: {obj.code}<br><br>
                                                    Berikut lampiran dokumen terkait : """, 
                                            additional_info={"jenis_bayar" : str(additional_info)}, 
                                            attachments=[vars(wf_system_attachment)],
                                            version=wf_current.version)
    
    body = vars(wf_system_sch)
    response, msg = await WorkflowService().create_workflow(body=body)

    if response is None:
        raise HTTPException(status_code=422, detail=f"Failed to connect workflow system. Detail : {msg}")
    
    wf_updated = WorkflowUpdateSch(**wf_current.dict(exclude={"last_status"}), last_status=response.last_status)
    await crud.workflow.update(obj_current=wf_current, obj_new=wf_updated, updated_by_id=obj.updated_by_id)

    if with_commit:
        await db_session.commit()

    return {"message" : "successfully"}

@router.get("/download-file/{id}")
async def download_file(id:UUID):
    """Download File Dokumen"""

    obj_current = await crud.termin.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Spk, id)
    if obj_current.file_upload_path is None:
        raise DocumentFileNotFoundException(dokumenname=obj_current.code)
    try:
        file_bytes = await GCStorageService().download_dokumen(file_path=obj_current.file_upload_path)
    except Exception as e:
        raise DocumentFileNotFoundException(dokumenname=obj_current.code)
    
    ext = obj_current.file_path.split('.')[-1]

    # return FileResponse(file, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={obj_current.id}.{ext}"})
    response = Response(content=file_bytes, media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename=Hasil Peta Lokasi-{id}-{obj_current.code}.{ext}"
    return response