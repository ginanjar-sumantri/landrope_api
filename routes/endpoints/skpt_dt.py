from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, File, Response, HTTPException, Request
from fastapi_pagination import Params
from sqlmodel import select
from sqlalchemy.orm import selectinload
import crud
from models.planing_model import Planing
from models.project_model import Project
from models.desa_model import Desa
from models.skpt_model import Skpt, SkptDt
from models.worker_model import Worker
from models.import_log_model import ImportLog, ImportLogError
from schemas.skpt_sch import SkptSch, SkptShpSch
from schemas.skpt_dt_sch import SkptDtCreateSch, SkptDtUpdateSch, SkptDtSch, SkptDtRawSch
from schemas.ptsk_sch import (PtskSch)
from schemas.import_log_sch import (ImportLogCreateSch, ImportLogSch, ImportLogCloudTaskSch, ImportLogErrorSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, ImportResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameNotFoundException, ImportFailedException, DocumentFileNotFoundException)
from services.geom_service import GeomService
from services.gcloud_storage_service import GCStorageService
from services.gcloud_task_service import GCloudTaskService
from services.helper_service import HelperService
from shapely import wkt, wkb
from shapely.geometry import shape
from common.rounder import RoundTwo
from common.enum import StatusSKEnum, KategoriSKEnum, TaskStatusEnum
from decimal import Decimal
from datetime import datetime, date
from itertools import islice
import time

router = APIRouter()

@router.post("", response_model=PostResponseBaseSch[SkptDtRawSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: SkptDtCreateSch = Depends(SkptDtCreateSch.as_form), 
            file:UploadFile = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    
    skpt_current = await crud.skpt.get(id=sch.skpt_id)
    if skpt_current is None:
        raise IdNotFoundException(Skpt, id=sch.skpt_id)
    
    planing_current = await crud.planing.get(id=sch.planing_id)
    if planing_current is None:
        raise IdNotFoundException(Planing, id=sch.planing_id)
    
    if file:
        geo_dataframe = None
        try:
            geo_dataframe = GeomService.file_to_geodataframe(file=file.file)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Error read file. Detail Error : {str(e)}")

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry

        sch = SkptDtSch(planing_id=sch.planing_id,
                        skpt_id=sch.skpt_id,
                        luas=RoundTwo(sch.luas),
                      geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
    new_obj = await crud.skptdt.create(obj_in=sch, created_by_id=current_worker.id)

    query = select(SkptDt).where(SkptDt.id == id).options(selectinload(SkptDt.skpt)
                                                        ).options(selectinload(SkptDt.planing
                                                                                ).options(selectinload(Planing.project)
                                                                                ).options(selectinload(Planing.desa))
                                                        )
    
    new_obj = await crud.skptdt.get(query=query)

    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[SkptDtRawSch])
async def get_list(
            params:Params = Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.skptdt.get_multi_paginate_ordered_with_keyword_dict(params=params, 
                                                                        order_by=order_by, 
                                                                        keyword=keyword, 
                                                                        filter_query=filter_query,
                                                                        join=True)
    
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[SkptDtRawSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    query = select(SkptDt).where(SkptDt.id == id).options(selectinload(SkptDt.skpt)
                                                        ).options(selectinload(SkptDt.planing
                                                                                ).options(selectinload(Planing.project)
                                                                                ).options(selectinload(Planing.desa))
                                                        )
    
    obj = await crud.skptdt.get(query=query)

    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Skpt, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[SkptDtRawSch])
async def update(
            id:UUID, 
            sch:SkptDtUpdateSch = Depends(SkptDtUpdateSch.as_form), 
            file:UploadFile = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.skpt.get(id=id)

    if obj_current is None:
        raise IdNotFoundException(Skpt, id)
    
    if obj_current.geom :
        obj_current.geom = wkt.dumps(wkb.loads(obj_current.geom.data, hex=True))
    
    if file:
        geo_dataframe = None
        try:
            geo_dataframe = GeomService.file_to_geodataframe(file=file.file)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Error read file. Detail Error : {str(e)}")
        
        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry
        
        sch = SkptDtSch(planing_id=sch.planing_id,
                        skpt_id=sch.skpt_id,
                        luas=RoundTwo(sch.luas),
                      geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
    obj_updated = await crud.skpt.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)

    query = select(SkptDt).where(SkptDt.id == obj_updated.id).options(selectinload(SkptDt.skpt)
                                                        ).options(selectinload(SkptDt.planing
                                                                                ).options(selectinload(Planing.project)
                                                                                ).options(selectinload(Planing.desa))
                                                        )
    
    obj_updated = await crud.skptdt.get(query=query)

    return create_response(data=obj_updated)

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

    field_values = ["code", "name", "kategori", "luas", "no_sk", "status", "section", 
                        "code_desa", "project", "desa", "tgl_sk", "jatuhtempo"]
    
    try:
        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error read file. Detail = {str(e)}")
    
    error_message = HelperService().CheckField(gdf=geo_dataframe, field_values=field_values)
    if error_message:
        raise HTTPException(status_code=422, detail=f"field '{error_message}' tidak eksis dalam file, field tersebut dibutuhkan untuk import data")
    
    file.file.seek(0)
    rows = GeomService.total_row_geodataframe(file=file.file)
    file.file.seek(0)
    try:
        file_path, file_name = await GCStorageService().upload_zip(file=file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed upload to storage. Detail Error : {str(e)}")
    
    sch = ImportLogCreateSch(status=TaskStatusEnum.OnProgress,
                            name=f"Upload skpt Bulking {rows} datas",
                            file_name=file_name,
                            file_path=file_path,
                            total_row=rows,
                            done_count=0)

    new_obj = await crud.import_log.create(obj_in=sch, worker_id=current_worker.id)

    url = f'{request.base_url}landrope/skptdt/cloud-task-bulk'
    GCloudTaskService().create_task_import_data(import_instance=new_obj, base_url=url)

    return create_response(data=new_obj)

@router.post("/cloud-task-bulk", response_model=ImportResponseBaseSch[SkptDtRawSch], status_code=status.HTTP_201_CREATED)
async def bulk_skpt(payload:ImportLogCloudTaskSch,
               request:Request):

    """Create bulk or import data"""

    entity_on_proc:str = ""
    on_proc:str = ""
    on_row:int = 0
    current_datetime = datetime.now()

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
            shp_data = SkptShpSch(geom=GeomService.single_geometry_to_wkt(geo_data.geometry),
                                    code=geo_data['code'],
                                    name=geo_data['name'],
                                    kategori=geo_data['kategori'],
                                    luas=RoundTwo(Decimal(geo_data['luas'])),
                                    no_sk=geo_data['no_sk'],
                                    status=geo_data['status'],
                                    section=geo_data['section'],
                                #   tgl_sk=geo_data['tgl_sk'],
                                #   jatuhtempo=geo_data['jatuhtempo'],
                                    code_desa=geo_data['code_desa'],
                                    project=geo_data['project'],
                                    desa=geo_data['desa'])
            tgl_sk = str(geo_data['tgl_sk']).lower()
            if tgl_sk != "nan" and tgl_sk != "none":
                shp_data.tgl_sk = date(geo_data['tgl_sk'])
            jatuhtempo = str(geo_data['jatuhtempo']).lower()    
            if jatuhtempo != "nan" and jatuhtempo != "none":
                shp_data.jatuhtempo = date(geo_data['jatuhtempo'])
            
            entity_on_proc = f"{shp_data.name}-{shp_data.code}-{shp_data.no_sk}"
            on_row = i
            
            on_proc = "[get by name project]"
            project = await crud.project.get_by_name(name=shp_data.project)
            if project is None:
                error_m = f"Project {shp_data.project} not exists in table master. "
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
                    break

                continue
            
            on_proc = "[get by name desa]"
            desa = await crud.desa.get_by_name(name=shp_data.desa)
            if desa is None:
                error_m = f"Desa {shp_data.desa} not exists in table master. "
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
                    break
                
                continue
            
            on_proc = "[get planing]"
            planing = await crud.planing.get_by_project_id_desa_id(project_id=project.id, desa_id=desa.id)
            if planing is None:
                error_m = f"Planing {shp_data.project}-{shp_data.desa} not exists in table master. "
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
                    break
                
                continue

            on_proc = "[get by name ptsk]"
            pt = await crud.ptsk.get_by_name(name=shp_data.name)

            if pt is None:
                new_pt =  PtskSch(name=shp_data.name, code= shp_data.code or "")
                
                pt = await crud.ptsk.create(obj_in=new_pt)
            
            sk = None
            if shp_data.no_sk != "nan" and shp_data.no_sk != "None" and shp_data.no_sk != "NaN":
                sk = await crud.skpt.get_by_sk_number(number=shp_data.no_sk)
            
            sk = await crud.skpt.get_by_sk_number_and_ptsk_id(no_sk=shp_data.no_sk, ptsk_id=pt.id)

            if sk is None:
                    new_sk = SkptSch(ptsk_id=pt.id,
                            status=StatusSK(shp_data.status),
                            kategori=KategoriSk(shp_data.kategori),
                            nomor_sk=shp_data.no_sk,
                            tanggal_tahun_SK=shp_data.tgl_sk,
                            tanggal_jatuh_tempo=shp_data.jatuhtempo)
                    
                    sk = await crud.skpt.create(obj_in=new_sk)
            else:
                update_sk = SkptSch(ptsk_id=pt.id,
                            status=StatusSK(shp_data.status),
                            kategori=KategoriSk(shp_data.kategori),
                            nomor_sk=shp_data.no_sk,
                            tanggal_tahun_SK=shp_data.tgl_sk,
                            tanggal_jatuh_tempo=shp_data.jatuhtempo)
                
                sk = await crud.skpt.update(obj_current=sk, obj_new=update_sk)

            data = SkptDt(planing_id=planing.id, 
                                skpt_id=sk.id,
                                luas=shp_data.luas,
                                updated_at=current_datetime,
                                created_at=current_datetime,
                                geom=shp_data.geom)
            
            await crud.skptdt.create(obj_in=data)

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
                break

            # Waktu sekarang
            current_time = time.time()

            # Cek apakah sudah mencapai 1 menit
            elapsed_time = current_time - start_time
            if elapsed_time >= max_duration:
                url = f'{request.base_url}landrope/planing/cloud-task-bulk'
                GCloudTaskService().create_task_import_data(import_instance=log, base_url=url)
                break  # Hentikan looping setelah 7 menit berlalu

            time.sleep(0.2)

        except Exception as e:
            error_m = f"Error on {entity_on_proc}, Process: {on_proc}, Error Detail : {str(e)}"
            log_error = ImportLogErrorSch(row=on_row+1,
                                            error_message=error_m,
                                            import_log_id=log.id)

            log_error = await crud.import_log_error.create(obj_in=log_error)

            raise HTTPException(status_code=422, detail=f"{str(e)}")
    
    return {"result" : status.HTTP_200_OK, "message" : "Successfully upload"}

@router.get("/export/shp", response_class=Response)
async def export_shp(
                filter_query:str = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):

    schemas = []
    
    results = await crud.skptdt.get_multi_by_dict(filter_query=filter_query)

    for skptdt in results:
        data = await crud.skptdt.get_by_id(id=skptdt.id)
        sch = SkptShpSch(geom=wkt.dumps(wkb.loads(data.geom.data, hex=True)),
                      code=data.skpt.ptsk.code,
                      name=data.skpt.ptsk.name,
                      kategori=str(data.skpt.kategori).replace("_", " "),
                      luas=data.luas,
                      no_sk=data.nomor_sk,
                      status=str(data.skpt.status).replace("_", " "),
                      tgl_sk=data.skpt.tanggal_tahun_SK,
                      jatuhtempo=data.skpt.tanggal_jatuh_tempo,
                      section=data.section_name,
                      code_desa=data.desa_code,
                      project=data.project_name,
                      desa=data.desa_name)
        schemas.append(sch)

    if results:
        obj_name = results[0].__class__.__name__
        if len(results) == 1:
            obj_name = f"{obj_name}-{results[0].nomor_sk}"

    return GeomService.export_shp_zip(data=schemas, obj_name=obj_name)

def StatusSK(status:str|None = None):
    if status:
        if status.replace(" ", "").replace("_", "").lower() == "belumil":
            return StatusSKEnum.Belum_IL
        elif status.replace(" ", "").replace("_", "").lower() == "sudahil":
            return StatusSKEnum.Sudah_Il
    else:
        return StatusSKEnum.Belum_IL

def KategoriSk(kategori:str|None = None):
    if kategori:
        if kategori.replace(" ", "").replace("_", "").lower() == KategoriSKEnum.SK_ASG.replace(" ", "").replace("_", "").lower():
            return KategoriSKEnum.SK_ASG
        elif kategori.replace(" ", "").replace("_", "").lower() == KategoriSKEnum.SK_Orang.replace(" ", "").replace("_", "").lower():
            return KategoriSKEnum.SK_Orang
    else:
        return None