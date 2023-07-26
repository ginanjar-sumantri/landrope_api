import json
import crud
import time
from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, Response, HTTPException, Request
from fastapi_pagination import Params
from models.bidang_model import Bidang
from models.project_model import Project
from models.desa_model import Desa
from models.planing_model import Planing
from models.worker_model import Worker
from models.pemilik_model import Pemilik
from models.master_model import JenisSurat
from models.import_log_model import ImportLog
from schemas.import_log_sch import ImportLogCreateSch, ImportLogSch, ImportLogCloudTaskSch
from schemas.import_log_error_sch import ImportLogErrorSch
from schemas.bidang_sch import (BidangSch, BidangCreateSch, BidangUpdateSch, BidangRawSch, BidangShpSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch,
                                  PostResponseBaseSch, PutResponseBaseSch,
                                  ImportResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, NameNotFoundException, ImportFailedException)
from common.generator import generate_id_bidang
from common.rounder import RoundTwo
from common.enum import TaskStatusEnum, StatusBidangEnum, JenisBidangEnum, JenisAlashakEnum
from services.geom_service import GeomService
from services.gcloud_task_service import GCloudTaskService
from services.gcloud_storage_service import GCStorage
from shapely.geometry import shape
from shapely import wkt, wkb
from decimal import Decimal
from datetime import datetime
from itertools import islice


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[BidangRawSch], status_code=status.HTTP_201_CREATED)
async def create(sch: BidangCreateSch = Depends(BidangCreateSch.as_form), file:UploadFile = None):

    """Create a new object"""

    obj_current = await crud.bidang.get_by_id_bidang(idbidang=sch.id_bidang)
    if obj_current:
        raise NameExistException(Bidang, name=sch.id_bidang)

    sch.id_bidang = await generate_id_bidang(sch.planing_id)

    if file:
        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry

        sch = BidangSch(**sch.dict())
        sch.geom = GeomService.single_geometry_to_wkt(geo_dataframe.geometry)
    else:
        raise ImportFailedException()

    new_obj = await crud.bidang.create(obj_in=sch)

    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[BidangRawSch])
async def get_list(params:Params = Depends(), order_by:str = None, keyword:str=None, filter_query:str=None):

    """Gets a paginated list objects"""

    objs = await crud.bidang.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[BidangRawSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.bidang.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Bidang, id)

@router.put("/{id}", response_model=PutResponseBaseSch[BidangRawSch])
async def update(id:UUID, sch:BidangUpdateSch = Depends(BidangUpdateSch.as_form), file:UploadFile = None):

    """Update a obj by its id"""

    obj_current = await crud.bidang.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Bidang, id)

    if obj_current.geom :
        obj_current.geom = wkt.dumps(wkb.loads(obj_current.geom.data, hex=True))

    if file:
        # buffer = await file.read()

        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry

        sch = BidangSch(**sch.dict())
        sch.geom = GeomService.single_geometry_to_wkt(geo_dataframe.geometry)

    obj_updated = await crud.bidang.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

@router.post(
        "/bulk",
        response_model=PostResponseBaseSch[ImportLogSch],
        status_code=status.HTTP_201_CREATED
)
async def create_bulking_task(
    file:UploadFile,
    request: Request,
    current_worker: Worker = Depends(crud.worker.get_current_user)
    ):

    """Create a new object"""

    rows = GeomService.total_row_geodataframe(file=file.file)
    file.file.seek(0)
    file_path, file_name = await GCStorage().upload_zip(file=file)

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
    try:
        # file = await file.read()

        log = await crud.import_log.get(id=payload.import_log_id)
        if log is None:
            return IdNotFoundException(ImportLog, payload.import_log_id)

        start:int = log.done_count
        count:int = log.done_count

        if log.done_count > 0:
            start = log.done_count

        null_values = ["", "None", "nan", None]

        file = await GCStorage().download_file(payload.file_path)
        if not file:
            return FileNotFoundError()

        geo_dataframe = GeomService.file_to_geodataframe(file)

        start_time = time.time()
        max_duration = 7 * 60

        for i, geo_data in islice(geo_dataframe.iterrows(), start, None):
            luassurat = str(geo_data['luassurat'])
            if luassurat in null_values:
                geo_data['luassurat'] = RoundTwo(Decimal(0))

            shp_data = BidangShpSch(n_idbidang=str(geo_data['n_idbidang']),
                                    o_idbidang=geo_data['o_idbidang'],
                                    pemilik=geo_data['pemilik'],
                                    code_desa=geo_data['code_desa'],
                                    dokumen=geo_data['dokumen'],
                                    sub_surat=geo_data['sub_surat'],
                                    alashak=geo_data['alashak'],
                                    luassurat=geo_data['luassurat'],
                                    kat=geo_data['kat'],
                                    kat_bidang=geo_data['kat_bidang'],
                                    kat_proyek=geo_data['kat_proyek'],
                                    ptsk=geo_data['ptsk'],
                                    penampung=geo_data['penampung'],
                                    no_sk=geo_data['no_sk'],
                                    status_sk=geo_data['status_sk'],
                                    manager=geo_data['manager'],
                                    sales=geo_data['sales'],
                                    mediator=geo_data['mediator'],
                                    proses=geo_data['proses'],
                                    status=geo_data['status'],
                                    group=geo_data['group'],
                                    no_peta=geo_data['no_peta'],
                                    desa=geo_data['desa'],
                                    project=geo_data['project'],
                                    geom=GeomService.single_geometry_to_wkt(geo_data.geometry)
            )

            luas_surat:Decimal = RoundTwo(Decimal(shp_data.luassurat))

            pemilik = None
            pmlk = await crud.pemilik.get_by_name(name=shp_data.pemilik)
            if pmlk:
                pemilik = pmlk.id
            
            jenis_surat = await crud.jenissurat.get_by_jenis_alashak_and_name(jenis_alashak=shp_data.dokumen, name=shp_data.sub_surat)
            if jenis_surat is None:
                jenissurat = None
            else:
                jenissurat = jenis_surat.id

            kategori = None
            kat = await crud.kategori.get_by_name(name=shp_data.kat)
            if kat:
                kategori = kat.id
            
            kategori_sub = None
            kat_sub = await crud.kategori_sub.get_by_name(name=shp_data.kat_bidang)
            if kat_sub:
                kategori_sub = kat_sub.id
            
            kategori_proyek = None
            kat_proyek = await crud.kategori_proyek.get_by_name(name=shp_data.kat_proyek)
            if kat_proyek:
                kategori_proyek = kat_proyek.id
            
            pt = None
            ptsk = await crud.ptsk.get_by_name(name=shp_data.ptsk)
            if ptsk:
                pt = ptsk.id
            
            skpt = None
            no_sk = await crud.skpt.get_by_sk_number(number=shp_data.no_sk)
            if no_sk:
                skpt = no_sk.id
            
            penampung = None
            pt_penampung = await crud.ptsk.get_by_name(name=shp_data.penampung)
            if pt_penampung:
                penampung = pt_penampung.id

            manager = None
            mng = await crud.manager.get_by_name(name=shp_data.manager)
            if mng:
                manager = mng.id
            
            sales = None
            sls = await crud.sales.get_by_name(name=shp_data.sales)
            if sls:
                sales = sls.id

            project = await crud.project.get_by_name(name=shp_data.project)
            if project is None:
                error_m = f"IdBidang {shp_data.o_idbidang} {shp_data.n_idbidang}, Project {shp_data.project} not exists in table master. "
                log_error = ImportLogErrorSch(row=i+1,
                                                error_message=error_m,
                                                import_log_id=log.id)

                log_error = await crud.import_log_error.create(obj_in=log_error)

                raise NameNotFoundException(Project, name=shp_data.project)

            desa = await crud.desa.get_by_name(name=shp_data.desa)
            if desa is None:
                error_m = f"IdBidang {shp_data.o_idbidang} {shp_data.n_idbidang}, Desa {shp_data.desa} code {shp_data.code_desa} not exists in table master. "
                log_error = ImportLogErrorSch(row=i+1,
                                                error_message=error_m,
                                                import_log_id=log.id)

                log_error = await crud.import_log_error.create(obj_in=log_error)

                raise NameNotFoundException(Desa, name=shp_data.desa)

            plan = await crud.planing.get_by_project_id_desa_id(project_id=project.id, desa_id=desa.id)
            if plan is None:
                error_m = f"IdBidang {shp_data.o_idbidang} {shp_data.n_idbidang}, Planing {shp_data.project}-{shp_data.desa} not exists in table master. "
                log_error = ImportLogErrorSch(row=i+1,
                                                error_message=error_m,
                                                import_log_id=log.id)

                log_error = await crud.import_log_error.create(obj_in=log_error)

                raise NameNotFoundException(Planing, name=f"{shp_data.project}-{shp_data.desa}")
                
            if shp_data.n_idbidang in null_values:
                bidang_lama = await crud.bidang.get_by_id_bidang_lama(idbidang_lama=shp_data.o_idbidang)
                if bidang_lama is None and plan is not None:
                    shp_data.n_idbidang = await generate_id_bidang(planing_id=plan.id)
                else:
                    shp_data.n_idbidang = bidang_lama.id_bidang

            sch = BidangSch(id_bidang=shp_data.n_idbidang,
                            id_bidang_lama=shp_data.o_idbidang,
                            no_peta=shp_data.no_peta,
                            pemilik_id=pemilik,
                            jenis_bidang=FindJenisBidang(shp_data.proses),
                            status=FindStatusBidang(shp_data.status),
                            planing_id=plan.id,
                            group=shp_data.group,
                            jenis_alashak=FindJenisAlashak(shp_data.dokumen),
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
                            geom=shp_data.geom)

            obj_current = await crud.bidang.get_by_id_bidang_id_bidang_lama(idbidang=sch.id_bidang, idbidang_lama=sch.id_bidang_lama)
            # obj_current = await crud.bidang.get_by_id_bidang_lama(idbidang_lama=shp_data.o_idbidang)

            if obj_current:
                if obj_current.geom :
                    obj_current.geom = wkt.dumps(wkb.loads(obj_current.geom.data, hex=True))
                obj = await crud.bidang.update(obj_current=obj_current, obj_new=sch)
            else:
                obj = await crud.bidang.create(obj_in=sch)
            
            obj_updated = log
            count = count + 1
            obj_updated.done_count = count

            log = await crud.import_log.update(obj_current=log, obj_new=obj_updated)

            # Waktu sekarang
            current_time = time.time()

            # Cek apakah sudah mencapai 7 menit
            elapsed_time = current_time - start_time
            if elapsed_time >= max_duration:
                url = f'{request.base_url}landrope/bidang/cloud-task-bulk'
                GCloudTaskService().create_task_import_data(import_instance=log, base_url=url)
                break  # Hentikan looping setelah 7 menit berlalu

            time.sleep(0.2)

    except:
        error_m = f"Failed import, please check your data or contact administrator"
        log_error = ImportLogErrorSch(row=i+1,
                                        error_message=error_m,
                                        import_log_id=log.id)

        log_error = await crud.import_log_error.create(obj_in=log_error)
        raise ImportFailedException(filename=log.file_name)

    if log.total_row == log.done_count:
        obj_updated = log
        obj_updated.status = TaskStatusEnum.Done
        obj_updated.completed_at = datetime.now()

        await crud.import_log.update(obj_current=log, obj_new=obj_updated)

    return {'message' : 'successfully import'}

@router.get("/export/shp", response_class=Response)
async def export(filter_query:str = None):

    results = await crud.bidang.get_multi_by_dict(filter_query=filter_query)
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
                           geom=wkt.dumps(wkb.loads(data.geom.data, hex=True)))

        schemas.append(sch)

    if results:
        obj_name = results[0].__class__.__name__
        if len(results) == 1:
            obj_name = f"{obj_name}-{results[0].id_bidang}"

        return GeomService.export_shp_zip(data=schemas, obj_name=obj_name)
    else:
        raise HTTPException(status_code=422, detail="Failed Export, please contact administrator!")

def FindStatusBidang(status:str|None = None):
    if status:
        if status.replace(" ", "").lower() == StatusBidangEnum.Bebas.replace("_", "").lower():
            return StatusBidangEnum.Bebas
        elif status.replace(" ", "").lower() == StatusBidangEnum.Belum_Bebas.replace("_", "").lower():
            return StatusBidangEnum.Belum_Bebas
        elif status.replace(" ", "").lower() == StatusBidangEnum.Batal.replace("_", "").lower():
            return StatusBidangEnum.Batal
        elif status.replace(" ", "").lower() == StatusBidangEnum.Lanjut.replace("_", "").lower():
            return StatusBidangEnum.Lanjut
        elif status.replace(" ", "").lower() == StatusBidangEnum.Pending.replace("_", "").lower():
            return StatusBidangEnum.Pending
        else:
            return StatusBidangEnum.Batal
    else:
        return StatusBidangEnum.Batal

def FindJenisBidang(type:str|None = None):
    if type:
        if type.replace(" ", "").lower() == JenisBidangEnum.Bintang.lower():
            return JenisBidangEnum.Bintang
        elif type.replace(" ", "").lower() == JenisBidangEnum.Standard.lower():
            return JenisBidangEnum.Standard
        elif type.replace(" ", "").lower() == JenisBidangEnum.Overlap.lower():
            return JenisBidangEnum.Overlap
        else:
            return None
    else:
        return None

def FindJenisAlashak(type:str|None = None):
    if type:
        if type.replace(" ", "").lower() == JenisAlashakEnum.Girik.lower():
            return JenisAlashakEnum.Girik
        elif type.replace(" ", "").lower() == JenisAlashakEnum.Sertifikat.lower():
            return JenisAlashakEnum.Sertifikat
        else:
            return None
    else:
        return None

