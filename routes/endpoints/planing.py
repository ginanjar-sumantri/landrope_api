from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, status, UploadFile, File, HTTPException, Response, Request
from fastapi_pagination import Params
from sqlmodel import select
from sqlalchemy.orm import selectinload
from models import Planing, Project, Desa, Worker, Section, ImportLog
from schemas.planing_sch import (PlaningSch, PlaningCreateSch, PlaningUpdateSch, PlaningRawSch, PlaningExtSch, PlaningShpSch)
from schemas.import_log_sch import (ImportLogCreateSch, ImportLogSch, ImportLogCloudTaskSch, ImportLogErrorSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, CodeExistException, NameNotFoundException, DocumentFileNotFoundException)
from common.enum import TaskStatusEnum
from services.geom_service import GeomService
from services.gcloud_storage_service import GCStorageService
from services.gcloud_task_service import GCloudTaskService
from services.helper_service import HelperService
from shapely  import wkt, wkb
from shapely.geometry import shape
from geoalchemy2.shape import to_shape
from common.rounder import RoundTwo
from decimal import Decimal
from datetime import datetime
from itertools import islice
import crud
import time

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[PlaningRawSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: PlaningCreateSch = Depends(PlaningCreateSch.as_form), 
            file:UploadFile = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    
    obj_current = await crud.planing.get_by_project_id_desa_id(project_id=sch.project_id, desa_id=sch.desa_id)
    if obj_current:
        raise NameExistException(Planing, name=sch.name)
    
    project = await crud.project.get(id=sch.project_id)
    if project is None:
        raise IdNotFoundException(Project, id=sch.project_id)
    
    section = await crud.section.get(id=project.section_id)
    if section is None:
        raise IdNotFoundException(Section, id=project.section_id)
    
    desa = await crud.desa.get(id=sch.desa_id)
    if desa is None:
        raise IdNotFoundException(Desa, id=sch.desa_id)
    
    code = section.code + project.code + desa.code
    sch.code = code
    sch.name = project.name + "-" + desa.name + "-" + code
    
    if file:
        geo_dataframe = None
        try:
            geo_dataframe = GeomService.file_to_geodataframe(file=file.file)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Error read file. Detail Error : {str(e)}")


        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry
        
        sch = PlaningSch(**sch.dict())
        sch.luas = RoundTwo(sch.luas)
        sch.geom = GeomService.single_geometry_to_wkt(geo_dataframe.geometry)
        
    new_obj = await crud.planing.create(obj_in=sch, created_by_id=current_worker.id)

    query = select(Planing).where(Planing.id == new_obj.id
                                ).options(selectinload(Planing.project)
                                ).options(selectinload(Planing.desa))

    new_obj = await crud.planing.get(query=query)

    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[PlaningRawSch])
async def get_list(
                params:Params = Depends(), 
                order_by:str = None, 
                keyword:str = None, 
                filter_query:str = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.planing.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query, join=True)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[PlaningRawSch])
async def get_by_id(id:UUID):

    """Get an object by id"""
    
    obj = await crud.planing.get_by_id(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Planing, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[PlaningRawSch])
async def update(
            id:UUID, 
            sch:PlaningUpdateSch = Depends(PlaningUpdateSch.as_form), 
            file:UploadFile = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.planing.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Planing, id)
    
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

        sch.geom = GeomService.single_geometry_to_wkt(geo_dataframe.geometry)
    
    obj_updated = await crud.planing.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)

    query = select(Planing).where(Planing.id == obj_updated.id
                                ).options(selectinload(Planing.project
                                ).options(selectinload(Project.section))
                                ).options(selectinload(Planing.desa))
    
    obj_updated = await crud.planing.get(query=query)

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

    field_values = ["code", "name", "project", "desa", "kecamatan", "kota", "luas"]
    
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
                            name=f"Upload planing Bulking {rows} datas",
                            file_name=file_name,
                            file_path=file_path,
                            total_row=rows,
                            done_count=0)

    new_obj = await crud.import_log.create(obj_in=sch, worker_id=current_worker.id)

    url = f'{request.base_url}landrope/planing/cloud-task-bulk'
    GCloudTaskService().create_task_import_data(import_instance=new_obj, base_url=url)

    return create_response(data=new_obj)

@router.post("/cloud-task-bulk")
async def bulk(payload:ImportLogCloudTaskSch,
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
            name:str = geo_data.get('name', '')
            code:str = geo_data.get('code', '')
            project_name:str = geo_data.get('project', '')
            desa_name:str = geo_data.get('desa')
            kota:str = geo_data.get('kota', '')
            kecamatan:str = geo_data.get('kecamatan', '')
            luas:Decimal = RoundTwo(Decimal(geo_data.get('luas', 0)))

            entity_on_proc = f"{code}-{name}-{project_name}-{desa_name}"
            on_row = i

            on_proc = "[get by name project]"
            project = await crud.project.get_by_name(name=project_name)
            if project is None:
                error_m = f"Project {project_name} not exists in table master. "
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
            desa = await crud.desa.get_by_administrasi(name=desa_name, kota=kota, kecamatan=kecamatan)
            if desa is None:
                error_m = f"Desa {desa_name} kec. {kecamatan} kota {kota} not exists in table master. "
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
            
            code_combine = project.section.code + project.code + desa.code
            name_combine = project.name + "-" + desa.name + "-" + code_combine
            
            on_proc = "[get planing]"
            obj_current = await crud.planing.get_by_project_id_desa_id(project_id=project.id, desa_id=desa.id)

            if obj_current:
                obj_current.geom = wkt.dumps(wkb.loads(obj_current.geom.data, hex=True))
                sch_update = PlaningSch(code=obj_current.code,
                            name=obj_current.name,
                            project_id=project.id,
                            desa_id=desa.id,
                            geom=GeomService.single_geometry_to_wkt(geo_data.geometry),
                            luas=luas)

                await crud.planing.update(obj_current=obj_current, obj_new=sch_update, updated_by_id=log.created_by_id)
            else:
                sch = Planing(code=code_combine,
                                name=name_combine,
                                project_id=project.id,
                                desa_id=desa.id,
                                geom=GeomService.single_geometry_to_wkt(geo_data.geometry),
                                luas=luas,
                                created_at=current_datetime,
                                updated_at=current_datetime)
                
                await crud.planing.create(obj_in=sch, created_by_id=log.created_by_id)

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
    
    results = await crud.planing.get_multi_by_dict(filter_query=filter_query)

    for planing in results:
        data = await crud.planing.get_by_id(id=planing.id)
        sch = PlaningShpSch(
                      geom=wkt.dumps(wkb.loads(data.geom.data, hex=True)),
                      luas=data.luas,
                      name=data.name,
                      code=data.code,
                      project=data.project_name,
                      desa=data.desa_name,
                      section=data.section_name)

        schemas.append(sch)

    if results:
        obj_name = results[0].__class__.__name__
        if len(results) == 1:
            obj_name = f"{obj_name}-{results[0].name}"

    return GeomService.export_shp_zip(data=schemas, obj_name=obj_name)

    