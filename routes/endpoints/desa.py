from fastapi import APIRouter, Depends, status, UploadFile, File, HTTPException, Response, Request
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, or_
from models import Desa, Planing, Project
from models.import_log_model import ImportLog
from models.worker_model import Worker
from models.code_counter_model import CodeCounterEnum
from schemas.desa_sch import (DesaSch, DesaRawSch, DesaCreateSch, DesaUpdateSch, DesaExportSch, DesaForTreeReportSch)
from schemas.import_log_sch import (ImportLogCreateSch, ImportLogSch, ImportLogCloudTaskSch, ImportLogErrorSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, NameNotFoundException, DocumentFileNotFoundException    )
from common.generator import generate_code
from common.rounder import RoundTwo
from common.enum import TaskStatusEnum
from services.geom_service import GeomService
from services.gcloud_task_service import GCloudTaskService
from services.gcloud_storage_service import GCStorageService
from services.helper_service import HelperService
from shapely.geometry import shape
from decimal import Decimal
from datetime import datetime
from shapely import wkt, wkb
from uuid import UUID
from itertools import islice
import crud
import time
import json

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[DesaRawSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: DesaCreateSch = Depends(DesaCreateSch.as_form), 
            file:UploadFile = File(),
            current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Create a new object"""
    
    obj_current = await crud.desa.get_by_name(name=sch.name)
    if obj_current:
        raise NameExistException(Desa, name=sch.name)
    db_session = db.session

    sch.code = await generate_code(entity=CodeCounterEnum.Desa, db_session=db_session, with_commit=False)

    if file:
        geo_dataframe = None
        try:
            geo_dataframe = GeomService.file_to_geodataframe(file=file.file)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Error read file. Detail Error : {str(e)}")

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry
        
        sch = DesaSch(**sch.dict())
        sch.geom = GeomService.single_geometry_to_wkt(geo_dataframe.geometry)
    
    new_obj = await crud.desa.create(obj_in=sch, created_by_id=current_worker.id, db_session=db_session)

    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[DesaRawSch])
async def get_list(
            project_id:UUID|None = None,
            params:Params = Depends(), 
            order_by:str=None, 
            keyword:str=None, 
            filter_query:str=None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(Desa)
    
    if project_id:
        query = query.join(Planing, Planing.desa_id == Desa.id
                    ).join(Project, Project.id == Planing.project_id
                    ).where(Project.id == project_id)
    
    if keyword:
        query = query.filter(
            or_(
                Desa.code.ilike(f'%{keyword}%'),
                Desa.name.ilike(f'%{keyword}%')
            )
        )
    
    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
                query = query.where(getattr(Desa, key) == value)

    objs = await crud.desa.get_multi_paginated_ordered(params=params, query=query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[DesaRawSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.desa.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Desa, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[DesaRawSch])
async def update(id:UUID, sch:DesaUpdateSch = Depends(DesaUpdateSch.as_form), file:UploadFile = None,
                 current_worker:Worker = Depends(crud.worker.get_current_user)):
    
    """Update a obj by its id"""

    obj_current = await crud.desa.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Desa, id)
    
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
        
        sch = DesaSch(name=sch.name, 
                      code=sch.code,
                      kecamatan=sch.kecamatan,
                      kota=sch.kota, 
                      luas=RoundTwo(sch.luas), 
                      geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
    obj_updated = await crud.desa.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
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

    field_values = ["code", "name", "kota", "kecamatan", "luas"]
    
    try:
        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error read file. Detail Error : {str(e)}")
    
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
                            name=f"Upload Desa Bulking {rows} datas",
                            file_name=file_name,
                            file_path=file_path,
                            total_row=rows,
                            done_count=0)

    new_obj = await crud.import_log.create(obj_in=sch, worker_id=current_worker.id)

    url = f'{request.base_url}landrope/desa/cloud-task-bulk'
    GCloudTaskService().create_task_import_data(import_instance=new_obj, base_url=url)

    return create_response(data=new_obj)

@router.post("/cloud-task-bulk")
async def bulk(payload:ImportLogCloudTaskSch,
               request:Request):

    """Create bulk or import data"""
    
    entity_on_proc:str = ""
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
            code:str = geo_data['code']
            name:str = geo_data['name']
            kota:str = geo_data['kota']
            kecamatan:str = geo_data['kecamatan']
            luas:Decimal = RoundTwo(Decimal(geo_data['luas']))

            entity_on_proc = f"{code}-{name}-{kota}-{kecamatan}"
            on_row = i

            on_proc = "[get by administrasi]"
            obj_current = await crud.desa.get_by_administrasi(name=name, kota=kota, kecamatan=kecamatan)
            
            if obj_current:
                obj_current.geom = wkt.dumps(wkb.loads(obj_current.geom.data, hex=True))
                sch_update = DesaSch(name=obj_current.name, 
                        code=obj_current.code,
                        kecamatan=kecamatan,
                        kota=kota, 
                        luas=luas, 
                        geom=GeomService.single_geometry_to_wkt(geo_data.geometry))
                
                await crud.desa.update(obj_current=obj_current, obj_new=sch_update, updated_by_id=log.created_by_id)
            
            else:
                db_session = db.session
                on_proc = "[generate code]"
                code = await generate_code(entity=CodeCounterEnum.Desa, db_session=db_session, with_commit=False)

                sch = Desa(
                            name=name,
                            code=code,
                            kecamatan=kecamatan,
                            kota=kota, 
                            luas=luas,
                            geom=GeomService.single_geometry_to_wkt(geo_data.geometry))
                
                await crud.desa.create(obj_in=sch, created_by_id=log.created_by_id, db_session=db_session)

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
                url = f'{request.base_url}landrope/desa/cloud-task-bulk'
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

# @router.post("/cloud-task-bulk")
# async def bulk(file:UploadFile=File(),
#                current_worker:Worker = Depends(crud.worker.get_active_worker)):

#     """Create bulk or import data"""
#     # try:
#     datas = []
#     current_datetime = datetime.now()
#     geo_dataframe = GeomService.file_to_geodataframe(file=file.file)
    
    
#     for i, geo_data in geo_dataframe.iterrows():
#         code:str = geo_data['code']
#         name:str = geo_data['name']
#         kota:str = geo_data['kota']
#         kecamatan:str = geo_data['kecamatan']
#         luas:Decimal = RoundTwo(Decimal(geo_data['luas']))

#         obj_current = await crud.desa.get_by_administrasi(name=name, kota=kota, kecamatan=kecamatan)
        
#         if obj_current:
#             obj_current.geom = wkt.dumps(wkb.loads(obj_current.geom.data, hex=True))
#             sch_update = DesaSch(name=obj_current.name, 
#                     code=obj_current.code,
#                     kecamatan=kecamatan,
#                     kota=kota, 
#                     luas=luas, 
#                     geom=GeomService.single_geometry_to_wkt(geo_data.geometry))
            
#             await crud.desa.update(obj_current=obj_current, obj_new=sch_update, updated_by_id=current_worker.id)
#             continue

#         db_session = db.session
#         code = await generate_code(entity=CodeCounterEnum.Desa, db_session=db_session, with_commit=False)

#         sch = Desa(
#                     name=name,
#                     code=code,
#                     kecamatan=kecamatan,
#                     kota=kota, 
#                     luas=luas,
#                     geom=GeomService.single_geometry_to_wkt(geo_data.geometry))
        
#         await crud.desa.create(obj_in=sch, created_by_id=current_worker.id, db_session=db_session)
            
#             # datas.append(sch)

#         # if len(datas) > 0:    
#         #     await crud.desa.create_all(obj_ins=datas)

#     # except:
#     #     raise HTTPException(status_code=422, detail="Failed import data")
    
#     return {"result" : status.HTTP_200_OK, "message" : "Successfully upload"}

@router.get("/export/shp", response_class=Response)
async def export_shp(
                filter_query:str = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):

    schemas = []
    
    results = await crud.desa.get_multi_by_dict(filter_query=filter_query)

    for data in results:
        
        sch = DesaExportSch(
                      geom=wkt.dumps(wkb.loads(data.geom.data, hex=True)),
                      name=data.name,
                      code=data.code,
                      kecamatan=data.kecamatan,
                      kota=data.kota,
                      luas=data.luas)

        schemas.append(sch)

    if results:
        obj_name = results[0].__class__.__name__
        if len(results) == 1:
            obj_name = f"{obj_name}-{results[0].name}"

    return GeomService.export_shp_zip(data=schemas, obj_name=obj_name)
    
@router.get("/report/map", response_model=GetResponseBaseSch[list[DesaForTreeReportSch]])
async def get_list_for_report_map(project_id:UUID,
                                  current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Get for tree report map"""
    
    objs = await crud.desa.get_all_ptsk_tree_report_map(project_id=project_id)

    return create_response(data=objs)
