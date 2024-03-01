import json
import crud
import time
from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, Response, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, or_, and_, func
from sqlalchemy import text, cast, String
from models import Bidang, Planing, Project, Desa, Pemilik, Tahap, TahapDetail, Invoice, PaymentDetail, InvoiceDetail, BidangKomponenBiaya, Termin
from models.worker_model import Worker
from models.master_model import JenisSurat
from models.hasil_peta_lokasi_model import HasilPetaLokasi
from models.import_log_model import ImportLog
from schemas.import_log_sch import ImportLogCreateSch, ImportLogSch, ImportLogCloudTaskSch
from schemas.import_log_error_sch import ImportLogErrorSch
from schemas.bidang_sch import (BidangSch, BidangCreateSch, BidangUpdateSch, BidangListSch, BidangFilterJson, BidangParameterDownload,
                                BidangRawSch, BidangShpSch, BidangByIdSch, BidangForOrderGUById, BidangForTreeReportSch)
from schemas.bidang_history_sch import MetaDataSch
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch,
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, ContentNoChangeException,
                               ImportFailedException, DocumentFileNotFoundException)
from common.generator import generate_id_bidang
from common.rounder import RoundTwo
from common.enum import TaskStatusEnum, StatusBidangEnum, JenisBidangEnum, JenisAlashakEnum, HasilAnalisaPetaLokasiEnum, JenisBayarEnum
from services.geom_service import GeomService
from services.gcloud_task_service import GCloudTaskService
from services.gcloud_storage_service import GCStorageService
from services.helper_service import HelperService, KomponenBiayaHelper
from shapely.geometry import shape
from shapely import wkt, wkb
from decimal import Decimal
from datetime import datetime
from itertools import islice
from io import BytesIO
import pandas as pd



router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[BidangRawSch], status_code=status.HTTP_201_CREATED)
async def create(sch: BidangCreateSch = Depends(BidangCreateSch.as_form), file:UploadFile = None,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Create a new object"""

    obj_current = await crud.bidang.get_by_id_bidang(idbidang=sch.id_bidang)

    if obj_current:
        raise NameExistException(Bidang, name=sch.id_bidang)
    
    db_session = db.session

    sch.id_bidang = await generate_id_bidang(sch.planing_id, db_session=db_session, with_commit=False)

    jenis_surat = await crud.jenissurat.get(id=sch.jenis_surat_id)
    if jenis_surat is None:
        raise IdNotFoundException(JenisSurat, sch.jenis_surat_id)
    
    sch.jenis_alashak = jenis_surat.jenis_alashak

    if file:
        geo_dataframe = None
        try:
            geo_dataframe = GeomService.file_to_geodataframe(file=file.file)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Error read file. Detail Error : {str(e)}")

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry

        sch = BidangSch(**sch.dict())
        sch.geom = GeomService.single_geometry_to_wkt(geo_dataframe.geometry)
    else:
        raise ImportFailedException()

    new_obj = await crud.bidang.create(obj_in=sch, created_by_id=current_worker.id, db_session=db_session)

    new_obj = await crud.bidang.get_by_id(id=new_obj.id)

    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[BidangRawSch])
async def get_list(
        params:Params = Depends(), 
        order_by:str = None, 
        keyword:str | None= None, 
        filter_query:str | None = None,
        filter_json:str | None = None,
        current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Gets a paginated list objects"""

    query = select(Bidang)
    query = query.outerjoin(Bidang.planing)
    query = query.outerjoin(Bidang.pemilik)
    query = query.outerjoin(Planing.desa)
    query = query.outerjoin(Planing.project)
    query = query.outerjoin(TahapDetail, and_(TahapDetail.bidang_id == Bidang.id, TahapDetail.is_void != True))
    query = query.outerjoin(Tahap, Tahap.id == TahapDetail.tahap_id)

    if keyword:
        query = query.filter(
            or_(
                Bidang.id_bidang.ilike(f'%{keyword}%'),
                Bidang.id_bidang_lama.ilike(f'%{keyword}%'),
                Bidang.alashak.ilike(f'%{keyword}%'),
                Bidang.group.ilike(f'%{keyword}%'),
                Project.name.ilike(f'%{keyword}%'),
                Desa.name.ilike(f'%{keyword}%'),
                Pemilik.name.ilike(f'%{keyword}%'),
                Bidang.no_peta.ilike(f'%{keyword}%'),
                Bidang.status.ilike(f'%{keyword}%'),
                Bidang.group.ilike(f'%{keyword}%'),
                cast(Tahap.nomor_tahap, String).ilike(f'%{keyword}%')
            )
        )
    
    if filter_json:
        json_loads = json.loads(filter_json)
        bidang_filter_json = BidangFilterJson(**dict(json_loads))

        if bidang_filter_json.total_payment or bidang_filter_json.sisa_pelunasan:

            subquery_payment = (
            select(func.coalesce(func.sum(PaymentDetail.amount), 0))
            .join(Invoice, and_(Invoice.id == PaymentDetail.invoice_id, Invoice.is_void != True))
            .join(Termin, and_(Termin.id == Invoice.termin_id, Termin.jenis_bayar != JenisBayarEnum.BIAYA_LAIN))
            .filter(and_(Invoice.bidang_id == Bidang.id, PaymentDetail.is_void != True))
            .scalar_subquery()  # Menggunakan scalar_subquery untuk hasil subquery sebagai skalar
            )

            subquery_beban_biaya = (
                select(func.coalesce(func.sum(InvoiceDetail.amount), 0)
                    ).join(BidangKomponenBiaya, BidangKomponenBiaya.id == InvoiceDetail.bidang_komponen_biaya_id
                    ).join(Invoice, Invoice.id == InvoiceDetail.invoice_id
                    ).filter(and_(Invoice.bidang_id == Bidang.id, 
                                  BidangKomponenBiaya.is_void != True, 
                                  BidangKomponenBiaya.beban_pembeli == False,
                                  BidangKomponenBiaya.is_paid == True,
                                  BidangKomponenBiaya.is_add_pay != True,
                                  BidangKomponenBiaya.is_retur != True))
                    .scalar_subquery()
            )

            if bidang_filter_json.total_payment:
                query = query.filter(or_(cast((subquery_payment + subquery_beban_biaya), String).ilike(f'%{bidang_filter_json.total_payment}%')))
            
            if bidang_filter_json.sisa_pelunasan:
                query = query.filter(or_(
                    cast((((func.coalesce(Bidang.luas_bayar, 0) * func.coalesce(Bidang.harga_transaksi, 0)) - subquery_payment) - subquery_beban_biaya), 
                        String).ilike(f'%{bidang_filter_json.sisa_pelunasan}%'))
                )

        if bidang_filter_json.id_bidang:
            query = query.filter(or_(Bidang.id_bidang.ilike(f'%{bidang_filter_json.id_bidang}%')))
        if bidang_filter_json.id_bidang_lama:
            query = query.filter(or_(Bidang.id_bidang_lama.ilike(f'%{bidang_filter_json.id_bidang_lama}%')))
        if bidang_filter_json.alashak:
            query = query.filter(or_(Bidang.alashak.ilike(f'%{bidang_filter_json.alashak}%')))
        if bidang_filter_json.pemilik_name:
            query = query.filter(or_(Pemilik.name.ilike(f'%{bidang_filter_json.pemilik_name}%')))
        if bidang_filter_json.project_name:
            query = query.filter(or_(Project.name.ilike(f'%{bidang_filter_json.project_name}%')))
        if bidang_filter_json.desa_name:
            query = query.filter(or_(Desa.name.ilike(f'%{bidang_filter_json.desa_name}%')))
        if bidang_filter_json.group:
            query = query.filter(or_(Bidang.group.ilike(f'%{bidang_filter_json.group}%')))
        if bidang_filter_json.no_peta:
            query = query.filter(or_(Bidang.no_peta.ilike(f'%{bidang_filter_json.no_peta}%')))
        if bidang_filter_json.nomor_tahap:
            query = query.filter(or_(cast(Tahap.nomor_tahap, String).ilike(f'%{bidang_filter_json.nomor_tahap}%')))
        if bidang_filter_json.luas_surat:
            query = query.filter(or_(cast(Bidang.luas_surat, String).ilike(f'%{bidang_filter_json.luas_surat}%')))
        if bidang_filter_json.status:
            query = query.filter(or_(func.replace(Bidang.status, '_', '').ilike(f'%{bidang_filter_json.status.replace(" ", "")}%')))
        if bidang_filter_json.total_harga_transaksi:
            query = query.filter(or_(cast((func.coalesce(Bidang.luas_bayar, 0) * func.coalesce(Bidang.harga_transaksi, 0)), String).ilike(f'%{bidang_filter_json.total_harga_transaksi}%')))
        

    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
                query = query.where(getattr(Bidang, key) == value)

    # query = query.distinct()

    objs = await crud.bidang.get_multi_paginated_ordered(query=query, params=params, order_by="updated_at")
    
    return create_response(data=objs)

@router.get("/order_gu", response_model=GetResponsePaginatedSch[BidangRawSch])
async def get_list_for_order_gu(params:Params = Depends(),
                                status_bidang:HasilAnalisaPetaLokasiEnum = None,
                                keyword:str = None):

    """Gets a paginated list objects"""

    query = select(Bidang).select_from(Bidang).join(HasilPetaLokasi, HasilPetaLokasi.bidang_id == Bidang.id
                                                    ).where(HasilPetaLokasi.hasil_analisa_peta_lokasi == status_bidang)

    if keyword:
        query = query.filter(Bidang.id_bidang.ilike(f'%{keyword}%'))

    objs = await crud.bidang.get_multi_paginated(query=query,params=params)

    return create_response(data=objs)
    
@router.get("/{id}", response_model=GetResponseBaseSch[BidangByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.bidang.get_by_id(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Bidang, id)

@router.get("/order_gu/{id}", response_model=GetResponseBaseSch[BidangForOrderGUById])
async def get_for_order_gu_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.bidang.get_by_id(id=id)
    if obj is None:
        raise IdNotFoundException(Bidang, id)
    
    obj_return = BidangForOrderGUById(**dict(obj))
    
    return create_response(data=obj_return)
    
@router.put("/{id}", response_model=PutResponseBaseSch[BidangRawSch])
async def update(id:UUID,
                 background_task:BackgroundTasks,
                 sch:BidangUpdateSch = Depends(BidangUpdateSch.as_form), 
                 file:UploadFile = None,
                 current_worker:Worker = Depends(crud.worker.get_current_user)):

    """Update a obj by its id"""
    try:
        db_session = db.session

        obj_current = await crud.bidang.get_by_id(id=id)
        if not obj_current:
            raise IdNotFoundException(Bidang, id)

        if obj_current.geom :
            obj_current.geom = wkt.dumps(wkb.loads(obj_current.geom.data, hex=True))

        if obj_current.geom_ori :
            obj_current.geom_ori = wkt.dumps(wkb.loads(obj_current.geom_ori.data, hex=True))

        jenis_surat = await crud.jenissurat.get(id=sch.jenis_surat_id)
        if jenis_surat is None:
            raise IdNotFoundException(JenisSurat, sch.jenis_surat_id)

        if file:
            geo_dataframe = None
            try:
                geo_dataframe = GeomService.file_to_geodataframe(file=file.file)
            except Exception as e:
                raise HTTPException(status_code=422, detail=f"Error read file. Detail = {str(e)}")

            if geo_dataframe.geometry[0].geom_type == "LineString":
                polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
                geo_dataframe['geometry'] = polygon.geometry

            sch = BidangSch(**sch.dict())
            sch.geom = GeomService.single_geometry_to_wkt(geo_dataframe.geometry)
        
        sch.jenis_alashak = jenis_surat.jenis_alashak
        sch.bundle_hd_id = obj_current.bundle_hd_id
        sch.status_pembebasan = obj_current.status_pembebasan

        obj_updated = await crud.bidang.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id, db_session=db_session)
        obj_updated = await crud.bidang.get_by_id(id=obj_updated.id)

        background_task.add_task(KomponenBiayaHelper().calculated_all_komponen_biaya(bidang_ids=[obj_updated.id]))
        
        return create_response(data=obj_updated)
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=422, detail=str(e))

@router.post(
        "/bulk",
        response_model=PostResponseBaseSch[ImportLogSch],
        status_code=status.HTTP_201_CREATED
)
async def create_bulking_task(
    file:UploadFile,
    request: Request,
    current_worker: Worker = Depends(crud.worker.get_active_worker)
    ):

    """Create a new object"""

    field_values = ["n_idbidang", "o_idbidang", "pemilik", "code_desa", "dokumen", "sub_surat", "alashak", "luassurat",
                        "kat", "kat_bidang", "kat_proyek", "ptsk", "penampung", "no_sk", "status_sk", "manager", "sales", "mediator", 
                        "proses", "status", "group", "no_peta", "desa", "project", "kota", "kecamatan", "parent_id"]

    # field_values = ["n_idbidang", "o_idbidang", "pemilik", "code_desa", "dokumen", "sub_surat", "alashak", "luassurat",
    #                     "kat", "kat_bidang", "kat_proyek", "ptsk", "penampung", "no_sk", "status_sk", "manager", "sales", "mediator", 
    #                     "proses", "status", "group", "no_peta", "desa", "project"]
    
    geo_dataframe = GeomService.file_to_geodataframe(file=file.file)
    error_message = HelperService().CheckField(gdf=geo_dataframe, field_values=field_values)
    if error_message:
        raise HTTPException(status_code=422, detail=f"field '{error_message}' tidak eksis dalam file, field tersebut dibutuhkan untuk import data")
    
    file.file.seek(0)
    rows = GeomService.total_row_geodataframe(file=file.file)
    file.file.seek(0)
    file_path, file_name = await GCStorageService().upload_zip(file=file)

    sch = ImportLogCreateSch(status=TaskStatusEnum.OnProgress,
                            name=f"Upload Bidang Bulking {rows} datas",
                            file_name=file_name,
                            file_path=file_path,
                            total_row=rows,
                            done_count=0)

    new_obj = await crud.import_log.create(obj_in=sch, worker_id=current_worker.id)

    url = f'{request.base_url}landrope/bidang/cloud-task-bulk'
    GCloudTaskService().create_task_import_data(import_instance=new_obj, base_url=url)

    return create_response(data=new_obj)

@router.post("/cloud-task-bulk")
async def bulk_create(payload:ImportLogCloudTaskSch,
                      request:Request):

    """Create bulk or import data"""
    
    id_bidang_on_proc:str = ""
    on_proc:str = ""
    on_row:int = 0

    log = await crud.import_log.get(id=payload.import_log_id)
    if log is None:
        raise IdNotFoundException(ImportLog, payload.import_log_id)

    start:int = log.done_count
    count:int = log.done_count

    if log.done_count > 0:
        start = log.done_count

    null_values = ["", "None", "nan", None]
    
    file = await GCStorageService().download_file(payload.file_path)
    if not file:
        raise DocumentFileNotFoundException(dokumenname=payload.file_path)

    geo_dataframe = GeomService.file_to_geodataframe(file)

    start_time = time.time()
    max_duration = 1 * 60

    for i, geo_data in islice(geo_dataframe.iterrows(), start, None):
        try:
            luassurat = str(geo_data['luassurat'])
            if luassurat in null_values:
                geo_data['luassurat'] = RoundTwo(Decimal(0))

            shp_data = BidangShpSch(n_idbidang=str(geo_data.get('n_idbidang', '')),
                                    o_idbidang=geo_data.get('o_idbidang', ''),
                                    pemilik=geo_data.get('pemilik', ''),
                                    code_desa=geo_data.get('code_desa', ''),
                                    dokumen=geo_data.get('dokumen', ''),
                                    sub_surat=geo_data.get('sub_surat',''),
                                    alashak=geo_data.get('alashak', ''),
                                    luassurat=geo_data.get('luassurat', ''),
                                    kat=geo_data.get('kat', ''),
                                    kat_bidang=geo_data.get('kat_bidang', ''),
                                    kat_proyek=geo_data.get('kat_proyek', ''),
                                    ptsk=geo_data.get('ptsk', ''),
                                    penampung=geo_data.get('penampung',''),
                                    no_sk=geo_data.get('no_sk', ''),
                                    status_sk=geo_data.get('status_sk', ''),
                                    manager=geo_data.get('manager', ''),
                                    sales=geo_data.get('sales', ''),
                                    mediator=geo_data.get('mediator', ''),
                                    proses=geo_data.get('proses', ''),
                                    status=geo_data.get('status', ''),
                                    group=geo_data.get('group', ''),
                                    no_peta=geo_data.get('no_peta', ''),
                                    desa=geo_data.get('desa', ''),
                                    project=geo_data.get('project', ''),
                                    kota=geo_data.get('kota', ''),
                                    kecamatan=geo_data.get('kecamatan', ''),
                                    parent_id=geo_data.get('parent_id', ''),
                                    geom=GeomService.single_geometry_to_wkt(geo_data.geometry)
            )

            id_bidang_on_proc = shp_data.o_idbidang if shp_data.o_idbidang not in null_values else shp_data.n_idbidang
            on_row = i

            luas_surat:Decimal = RoundTwo(Decimal(shp_data.luassurat))

            kulit_bintang_id = None
            jenis_bidang_shp = HelperService().FindJenisBidang(shp_data.proses)
            if jenis_bidang_shp == JenisBidangEnum.Rincik:
                on_proc = "[get parent bidang rincik]"
                if shp_data.parent_id is None:
                    error_m = f"IdBidang {shp_data.o_idbidang} {shp_data.n_idbidang}, Rincik Bintang tidak memiliki Parent"
                    done, count = await manipulation_import_log(error_m=error_m, i=i, log=log, count=count)
                    # if last row (done)
                    if done:
                        break

                    continue
                else:
                    kulit_bintang = await crud.bidang.get_kulit_bintang(idbidang=shp_data.parent_id)
                    if kulit_bintang is None:
                        error_m = f"IdBidang {shp_data.o_idbidang} {shp_data.n_idbidang}, Parent rincik tidak ditemukan/Jenis Bidang Parent rincik bukan Bintang"
                        done, count = await manipulation_import_log(error_m=error_m, i=i, log=log, count=count)
                        # if last row (done)
                        if done:
                            break

                        continue
                    kulit_bintang_id = kulit_bintang.id

            on_proc = "[get by name pemilik]"
            pemilik = None
            pmlk = await crud.pemilik.get_by_name(name=shp_data.pemilik)
            if pmlk:
                pemilik = pmlk.id
            
            on_proc = "[get by name jenis surat]"
            jenis_surat = await crud.jenissurat.get_by_jenis_alashak_and_name(jenis_alashak=shp_data.dokumen, name=shp_data.sub_surat)
            if jenis_surat is None:
                jenissurat = None
            else:
                jenissurat = jenis_surat.id

            on_proc = "[get by name kategori]"
            kategori = None
            kat = await crud.kategori.get_by_name(name=shp_data.kat)
            if kat:
                kategori = kat.id
            
            on_proc = "[get by name kategori sub]"
            kategori_sub = None
            if kategori:
                kat_sub = await crud.kategori_sub.get_by_name_and_kategori_id(name=shp_data.kat_bidang, kategori_id=kategori)
                if kat_sub:
                    kategori_sub = kat_sub.id
            
            on_proc = "[get by name kategori proyek]"
            kategori_proyek = None
            kat_proyek = await crud.kategori_proyek.get_by_name(name=shp_data.kat_proyek)
            if kat_proyek:
                kategori_proyek = kat_proyek.id
            
            on_proc = "[get by name ptsk]"
            pt = None
            ptsk = await crud.ptsk.get_by_name(name=shp_data.ptsk)
            if ptsk:
                pt = ptsk.id
            
            on_proc = "[get skpt]"
            skpt = None
            if pt:
                no_sk = await crud.skpt.get_by_sk_number_and_ptsk_id_and_status_sk(no_sk=shp_data.no_sk, ptsk_id=pt, status=shp_data.status_sk)
                if no_sk:
                    skpt = no_sk.id
            else:
                error_m = f"IdBidang {shp_data.o_idbidang} {shp_data.n_idbidang}, PTSK {shp_data.ptsk} not exists in table master. "
                done, count = await manipulation_import_log(error_m=error_m, i=i, log=log, count=count)
                # if last row (done)
                if done:
                    break

                continue
            
            on_proc = "[get by name penampung]"
            penampung = None
            pt_penampung = await crud.ptsk.get_by_name(name=shp_data.penampung)
            if pt_penampung:
                penampung = pt_penampung.id

            on_proc = "[get by name manager]"
            manager = None
            mng = await crud.manager.get_by_name(name=shp_data.manager)
            if mng:
                manager = mng.id
            
            on_proc = "[get by name sales]"
            sales = None
            if manager:
                sls = await crud.sales.get_by_name_and_manager_id(name=shp_data.sales, manager_id=manager)
                if sls:
                    sales = sls.id

            on_proc = "[get by name project]"
            project = await crud.project.get_by_name(name=shp_data.project)
            if project is None:
                error_m = f"IdBidang {shp_data.o_idbidang} {shp_data.n_idbidang}, Project {shp_data.project} not exists in table master. "
                done, count = await manipulation_import_log(error_m=error_m, i=i, log=log, count=count)
                # if last row (done)
                if done:
                    break

                continue
            
            on_proc = "[get by administrasi desa]"
            desa = await crud.desa.get_by_administrasi(name=shp_data.desa, kota=shp_data.kota, kecamatan=shp_data.kecamatan)
            # desa = await crud.desa.get_by_name(name=shp_data.desa)
            if desa is None:
                error_m = f"IdBidang {shp_data.o_idbidang} {shp_data.n_idbidang}, Desa {shp_data.desa} kec. {shp_data.kecamatan} kota {shp_data.kota} not exists in table master. "
                done, count = await manipulation_import_log(error_m=error_m, i=i, log=log, count=count)
                # if last row (done)
                if done:
                    break

                continue
            
            on_proc = "[get planing]"
            plan = await crud.planing.get_by_project_id_desa_id(project_id=project.id, desa_id=desa.id)
            if plan is None:
                error_m = f"IdBidang {shp_data.o_idbidang} {shp_data.n_idbidang}, Planing {shp_data.project}-{shp_data.desa} not exists in table master. "
                done, count = await manipulation_import_log(error_m=error_m, i=i, log=log, count=count)
                # if last row (done)
                if done:
                    break

                continue
            
            if shp_data.n_idbidang in null_values:
                on_proc = "[get by idbidang lama]"
                bidang_lama = await crud.bidang.get_by_id_bidang_lama(idbidang_lama=shp_data.o_idbidang)
                if bidang_lama:
                    if bidang_lama.geom :
                        bidang_lama.geom = wkt.dumps(wkb.loads(bidang_lama.geom.data, hex=True))
                    if bidang_lama.geom_ori :
                        bidang_lama.geom_ori = wkt.dumps(wkb.loads(bidang_lama.geom_ori.data, hex=True))
                if bidang_lama is None and plan is not None:
                    on_proc = "[generate id bidang]"
                    shp_data.n_idbidang = await generate_id_bidang(planing_id=plan.id)
                else:
                    shp_data.n_idbidang = bidang_lama.id_bidang

            sch = BidangSch(id_bidang=shp_data.n_idbidang,
                            id_bidang_lama=shp_data.o_idbidang,
                            no_peta=shp_data.no_peta,
                            pemilik_id=pemilik,
                            jenis_bidang=HelperService().FindJenisBidang(shp_data.proses),
                            status=HelperService().FindStatusBidang(shp_data.status),
                            planing_id=plan.id,
                            group=shp_data.group,
                            jenis_alashak=HelperService().FindJenisAlashak(shp_data.dokumen),
                            jenis_surat_id=jenissurat,
                            alashak=shp_data.alashak,
                            kategori_id=kategori,
                            kategori_sub_id=kategori_sub,
                            kategori_proyek_id=kategori_proyek,
                            skpt_id=skpt,
                            penampung_id=penampung,
                            manager_id=manager,
                            sales_id=sales,
                            mediator=shp_data.mediator,
                            luas_surat=luas_surat,
                            parent_id=kulit_bintang_id,
                            geom=shp_data.geom)

            obj_current = await crud.bidang.get_by_id_bidang_id_bidang_lama(idbidang=sch.id_bidang, idbidang_lama=sch.id_bidang_lama)
            # obj_current = await crud.bidang.get_by_id_bidang_lama(idbidang_lama=shp_data.o_idbidang)

            if obj_current:
                if obj_current.geom :
                    if isinstance(obj_current.geom, str):
                        pass
                    else:
                        obj_current.geom = wkt.dumps(wkb.loads(obj_current.geom.data, hex=True))
                if obj_current.geom_ori :
                    if isinstance(obj_current.geom_ori, str):
                        pass
                    else:
                        obj_current.geom_ori = wkt.dumps(wkb.loads(obj_current.geom_ori.data, hex=True))
                obj = await crud.bidang.update(obj_current=obj_current, obj_new=sch, updated_by_id=log.created_by_id)
            else:
                obj = await crud.bidang.create(obj_in=sch, created_by_id=log.created_by_id)
            
            done, count = await manipulation_import_log(error_m=None, i=i, log=log, count=count)
            # if last row (done)
            if done:
                break

            # Waktu sekarang
            current_time = time.time()

            # Cek apakah sudah mencapai 7 menit
            elapsed_time = current_time - start_time
            if elapsed_time >= max_duration:
                url = f'{request.base_url}landrope/bidang/cloud-task-bulk'
                GCloudTaskService().create_task_import_data(import_instance=log, base_url=url)
                break  # Hentikan looping setelah 7 menit berlalu

            time.sleep(0.2)
        except Exception as e:
            error_m = f"Error on {id_bidang_on_proc}, Process: {on_proc}, Error Detail : {str(e)}"
            log_error = ImportLogErrorSch(row=on_row+1,
                                            error_message=error_m,
                                            import_log_id=log.id)

            log_error = await crud.import_log_error.create(obj_in=log_error)

            raise HTTPException(status_code=422, detail=f"{str(e)}")
    
    return {'message' : 'successfully import'}

async def manipulation_import_log(i:int, log:ImportLog, error_m:str|None = None, count:int|None = 0):

    if error_m:
        log_error = ImportLogErrorSch(row=i+1,
                                        error_message=error_m,
                                        import_log_id=log.id)

        log_error = await crud.import_log_error.create(obj_in=log_error)

    obj_updated = log
    count = count + 1
    obj_updated.done_count = count

    log = await crud.import_log.update(obj_current=log, obj_new=obj_updated)

    if log.total_row == log.done_count:
        obj_updated = log
        if log.total_error_log > 0:
            obj_updated.status = TaskStatusEnum.Done_With_Error
        else:
            obj_updated.status = TaskStatusEnum.Done

        obj_updated.completed_at = datetime.now()

        await crud.import_log.update(obj_current=log, obj_new=obj_updated)
        return True, count
    
    return False, count

@router.get("/export/shp", response_class=Response)
async def export_shp(
            filter_query:str = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):

    results = await crud.bidang.get_multi_by_dict(filter_query=filter_query)
    schemas = []
    for bidang in results:
        data = await crud.bidang.get_by_id(id=bidang.id)
        sch = BidangShpSch(n_idbidang=data.id_bidang,
                           o_idbidang=data.id_bidang_lama,
                           pemilik=data.pemilik_name,
                           code_desa=data.desa_code,
                           dokumen=data.jenis_alashak,
                           sub_surat=data.jenis_surat_name,
                           alashak=data.alashak,
                           luassurat=data.luas_surat,
                           kat=data.kategori_name,
                           kat_bidang=data.kategori_sub_name,
                           kat_proyek=data.kategori_proyek_name,
                           ptsk=data.ptsk_name,
                           penampung=data.penampung_name,
                           no_sk=data.no_sk,
                           status_sk=data.status_sk,
                           manager=data.manager_name,
                           sales=data.sales_name,
                           mediator=data.mediator,
                           proses=data.jenis_bidang,
                           status=data.status,
                           group=data.group,
                           no_peta=data.no_peta,
                           desa=data.desa_name,
                           project=data.project_name,
                           kecamatan=data.kecamatan,
                           kota=data.kota,
                           geom=wkt.dumps(wkb.loads(data.geom.data, hex=True)))

        schemas.append(sch)

    if results:
        obj_name = results[0].__class__.__name__
        if len(results) == 1:
            obj_name = f"{obj_name}-{results[0].id_bidang}"

        return GeomService.export_shp_zip(data=schemas, obj_name=obj_name)
    else:
        raise HTTPException(status_code=422, detail="Failed Export, please contact administrator!")
    
@router.post("/export/bulk/shp", response_class=Response)
async def export_shp(
            param:BidangParameterDownload|None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):

    results = await crud.bidang.get_multi_export(param=param)
    schemas = []
    for data in results:
        sch = BidangShpSch(n_idbidang=data.id_bidang,
                           o_idbidang=data.id_bidang_lama,
                           pemilik=data.pemilik_name,
                           code_desa=data.desa_code,
                           dokumen=data.jenis_alashak,
                           sub_surat=data.jenis_surat_name,
                           alashak=data.alashak,
                           luassurat=data.luas_surat,
                           kat=data.kategori_name,
                           kat_bidang=data.kategori_sub_name,
                           kat_proyek=data.kategori_proyek_name,
                           ptsk=data.ptsk_name,
                           penampung=data.penampung_name,
                           no_sk=data.no_sk,
                           status_sk=data.status_sk,
                           manager=data.manager_name,
                           sales=data.sales_name,
                           mediator=data.mediator,
                           proses=data.jenis_bidang,
                           status=data.status,
                           group=data.group,
                           no_peta=data.no_peta,
                           desa=data.desa_name,
                           project=data.project_name,
                           kecamatan=data.kecamatan,
                           kota=data.kota,
                           geom=wkt.dumps(wkb.loads(data.geom.data, hex=True)))

        schemas.append(sch)

    if results:
        obj_name = results[0].__class__.__name__
        if len(results) == 1:
            obj_name = f"{obj_name}-{results[0].id_bidang}"

        return GeomService.export_shp_zip(data=schemas, obj_name=obj_name)
    else:
        raise HTTPException(status_code=422, detail="Failed Export, please contact administrator!")

@router.post("/export/excel")
async def export_excel(param:BidangParameterDownload|None = None,
                       current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Export data to Excel"""

    result = await crud.bidang.get_multi_export(param=param)

    datas = [{"Id Bidang" : bidang.id_bidang,
              "Id Bidang Lama" : bidang.id_bidang_lama,
              "No Peta" : bidang.no_peta,
              "Pemilik" : bidang.pemilik_name,
              "Jenis Bidang" : bidang.jenis_bidang,
              "Status" : bidang.status,
              "Project" : bidang.project_name,
              "Desa" : bidang.desa_name,
              "Sub Project" : bidang.sub_project_name,
              "Group" : bidang.group,
              "Jenis Alashak" : bidang.jenis_alashak,
              "Jenis Surat" : bidang.jenis_surat_name,
              "Alashak" : bidang.alashak,
              "Kategori" : bidang.kategori_name,
              "Kategori Sub" : bidang.kategori_sub_name,
              "Kategori Proyek" : bidang.kategori_proyek_name,
              "Ptsk" : bidang.ptsk_name,
              "No SK" : bidang.no_sk,
              "Status SK" : bidang.status_sk,
              "Penampung" : bidang.penampung_name,
              "Manager" : bidang.manager_name,
              "Sales" : bidang.sales_name,
              "Mediator" : bidang.mediator,
              "Telepon Mediator" : bidang.telepon_mediator,
              "Notaris" : bidang.notaris_name,
              "Tahap" : bidang.nomor_tahap,
              "Luas Surat" : "{:,.2f}".format(bidang.luas_surat or 0),
              "Luas Ukur" : "{:,.2f}".format(bidang.luas_ukur or 0),
              "Luas GU Perorangan" : "{:,.2f}".format(bidang.luas_gu_perorangan or 0),
              "Luas GU PT" : "{:,.2f}".format(bidang.luas_gu_pt or 0),
              "Luas Nett" : "{:,.2f}".format(bidang.luas_nett or 0),
              "Luas Clear" : "{:,.2f}".format(bidang.luas_clear or 0),
              "Luas PBT Perorangan" : "{:,.2f}".format(bidang.luas_pbt_perorangan or 0),
              "Luas PBT PT" : "{:,.2f}".format(bidang.luas_pbt_pt or 0),
              "Luas Bayar" : "{:,.2f}".format(bidang.luas_bayar or 0),
              "Harga Akta" : "{:,.2f}".format(bidang.harga_akta or 0),
              "Harga Transaksi" : "{:,.2f}".format(bidang.harga_transaksi or 0),
              "NJOP" : "{:,.2f}".format(bidang.njop or 0),
              "Total Harga" : "{:,.2f}".format(bidang.total_harga_transaksi or 0),
              "Total Bayar" : "{:,.2f}".format(bidang.total_payment or 0),
              "Sisa Pelunasan" : "{:,.2f}".format(bidang.sisa_pelunasan or 0)
            } for bidang in result]
    
    df = pd.DataFrame(data=datas)

    if current_worker.is_analyst:
        df = df.drop(['Luas Bayar','Harga Akta', 'Harga Transaksi', 'NJOP', 'Total Harga', 'Total Bayar', 'Sisa Pelunasan'], axis=1)
    
    df = df.fillna('')

    output = BytesIO()
    df.to_excel(output, index=False, sheet_name=f'SPK')

    output.seek(0)

    return StreamingResponse(BytesIO(output.getvalue()), 
                            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            headers={"Content-Disposition": "attachment;filename=bidang_data.xlsx"})

    

@router.get("/report/map", response_model=GetResponseBaseSch[list[BidangForTreeReportSch]])
async def get_list_for_report_map(project_id:UUID,
                                  desa_id:UUID,
                                  ptsk_id:UUID,
                                  current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Get for tree report map"""
    
    objs = await crud.bidang.get_all_bidang_tree_report_map(project_id=project_id, desa_id=desa_id, ptsk_id=ptsk_id)

    return create_response(data=objs)

    


