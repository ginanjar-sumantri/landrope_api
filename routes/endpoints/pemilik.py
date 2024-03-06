from uuid import UUID
from fastapi import APIRouter, status, Depends, UploadFile, Request, HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params
from models.pemilik_model import Pemilik, Kontak, Rekening
from models.worker_model import Worker
from models.import_log_model import ImportLog, ImportLogError
from schemas.pemilik_sch import (PemilikSch, PemilikCreateSch, PemilikUpdateSch, PemilikByIdSch)
from schemas.kontak_sch import KontakSch, KontakCreateSch, KontakUpdateSch
from schemas.rekening_sch import RekeningSch, RekeningCreateSch, RekeningUpdateSch
from schemas.import_log_sch import ImportLogCreateSch, ImportLogSch, ImportLogCloudTaskSch
from schemas.import_log_error_sch import ImportLogErrorSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, 
                                  DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, FileNotFoundException)
from services.gcloud_storage_service import GCStorageService
from services.gcloud_task_service import GCloudTaskService
from common.enum import TaskStatusEnum
import crud
import pandas

#region Pemilik
router_pemilik = APIRouter()

@router_pemilik.post("/create", response_model=PostResponseBaseSch[PemilikSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: PemilikCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    pemilik_current = await crud.pemilik.get_by_name(name=sch.name)
    if pemilik_current:
        raise HTTPException(status_code=422, detail="Nama pemilik tersebut sudah ada")
        
    new_obj = await crud.pemilik.create_pemilik(obj_in=sch, created_by_id=current_worker.id)
    
    return create_response(data=new_obj)

@router_pemilik.get("", response_model=GetResponsePaginatedSch[PemilikSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.pemilik.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router_pemilik.get("/{id}", response_model=GetResponseBaseSch[PemilikByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.pemilik.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Pemilik, id)

@router_pemilik.put("/{id}", response_model=PutResponseBaseSch[PemilikSch])
async def update(
            id:UUID, 
            sch:PemilikUpdateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.pemilik.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Pemilik, id)
    
    pemilik_current = await crud.pemilik.get_by_name(name=sch.name)
    if pemilik_current:
        raise HTTPException(status_code=422, detail="Nama pemilik tersebut sudah ada")
    
    obj_updated = await crud.pemilik.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)

    await update_kontak(pemilik_id=id, sch=sch)
    await update_rekening(pemilik_id=id, sch=sch)

    return create_response(data=obj_updated)

async def update_kontak(pemilik_id:UUID, sch:PemilikUpdateSch):
    kontaks = await crud.kontak.get_by_pemilik_id(pemilik_id=pemilik_id)
    
    obj_data = list(map(lambda x: x.nomor_telepon, kontaks))
    obj_sch = list(map(lambda x: x.nomor_telepon, sch.kontaks))

    set1 = set(obj_sch)
    set2 = set(obj_data)

    add_kontak = list(set1 - set2)
    remove_kontak = list(set2 - set1)

    for a in add_kontak:
        a_kontak = Kontak(nomor_telepon=a, pemilik_id=pemilik_id)
        await crud.kontak.create(obj_in=a_kontak)
    
    for r in remove_kontak:
        s_kontak = list(filter(lambda x: x.nomor_telepon == r, kontaks))
        r_kontak = s_kontak[0]
        await crud.kontak.remove(id=r_kontak.id)

async def update_rekening(pemilik_id:UUID, sch:PemilikUpdateSch):
    rekenings = await crud.rekening.get_by_pemilik_id(pemilik_id=pemilik_id)

    for r in rekenings:
        obj_remove = next((x for x in sch.rekenings if x.nama_pemilik_rekening.strip().lower() == r.nama_pemilik_rekening.strip().lower() 
                                 and x.nomor_rekening.strip() == r.nomor_rekening.strip() 
                                 and x.bank_rekening.strip().lower() == r.bank_rekening.strip().lower()), None)

        if obj_remove is None:
            await crud.rekening.remove(id=r.id)
        
    for a in sch.rekenings:
        obj_add = next((x for x in rekenings if x.nama_pemilik_rekening.strip().lower() == a.nama_pemilik_rekening.strip().lower() 
                                 and x.nomor_rekening.strip() == a.nomor_rekening.strip() 
                                 and x.bank_rekening.strip().lower() == a.bank_rekening.strip().lower()), None)
        
        if obj_add:
            continue

        a_rekening = Rekening(nama_pemilik_rekening=a.nama_pemilik_rekening,
                              nomor_rekening=a.nomor_rekening,
                              bank_rekening=a.bank_rekening,
                              pemilik_id=pemilik_id)
        await crud.rekening.create(obj_in=a_rekening)

@router_pemilik.post(
        "/bulk",
        response_model=PostResponseBaseSch[ImportLogSch],
        status_code=status.HTTP_201_CREATED
)
async def create_bulking_task(
    file:UploadFile,
    request: Request,
    current_worker: Worker = Depends(crud.worker.get_current_user)
    ):

    """Create a new task for import"""

    df = pandas.read_excel(file.file)
    rows = df.shape[0]
    
    file.file.seek(0)
    file_path, file_name = await GCStorageService().upload_excel(file=file)

    sch = ImportLogCreateSch(status=TaskStatusEnum.OnProgress,
                            name=f"Upload Pemilik Bulking {rows} datas",
                            file_name=file_name,
                            file_path=file_path,
                            total_row=rows,
                            done_count=0)

    new_obj = await crud.import_log.create(obj_in=sch, worker_id=current_worker.id)
    url = f'{request.base_url}landrope/bidang/cloud-task-bulk'
    GCloudTaskService().create_task_import_data(import_instance=new_obj, base_url=url)

    return create_response(data=new_obj)

@router_pemilik.post("/cloud-task-bulk")
async def bulk_create(payload:ImportLogCloudTaskSch,
                      request:Request):
    
    """Runing cloud task"""
    log = await crud.import_log.get(id=payload.import_log_id)
    if log is None:
        raise IdNotFoundException(ImportLog, payload.import_log_id)
    
    file = await GCStorageService().download_dokumen(payload.file_path)
    if not file:
        error_m = f"File {payload.file_path} not found"
        log_error = ImportLogErrorSch(error_message=error_m,
                                        import_log_id=log.id)

        log_error = await crud.import_log_error.create(obj_in=log_error)
        raise FileNotFoundException()
    
    df = pandas.read_excel(file)
    data = df.to_dict()
    
    start:int = log.done_count
    count:int = log.done_count
    null_values = ["", "None", "nan", None]

    if log.done_count > 0:
        start = log.done_count

@router_pemilik.post("/test-upload-excel")
async def extract_excel(file:UploadFile):
    file_content = await file.read()
    df = pandas.read_excel(file_content)
    data = df.to_dict()

    for i, data in df.iterrows():
        print(data.to_dict())

    return data


@router_pemilik.delete("/delete", response_model=DeleteResponseBaseSch[PemilikSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Delete a object"""

    obj_current = await crud.pemilik.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Pemilik, id)
    
    obj_deleted = await crud.pemilik.remove(id=id)

    return obj_deleted
#endregion

#region Kontak
router_kontak = APIRouter()

@router_kontak.post("/create", response_model=PostResponseBaseSch[KontakCreateSch], status_code=status.HTTP_201_CREATED)
async def create(sch: KontakCreateSch):
    
    """Create a new object"""
        
    new_obj = await crud.kontak.create(obj_in=sch)
    
    return create_response(data=new_obj)

@router_kontak.get("", response_model=GetResponsePaginatedSch[KontakSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.kontak.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router_kontak.get("/{id}", response_model=GetResponseBaseSch[KontakSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.kontak.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Kontak, id)

@router_kontak.put("/{id}", response_model=PutResponseBaseSch[KontakSch])
async def update(id:UUID, sch:KontakUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.kontak.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Kontak, id)
    
    obj_updated = await crud.kontak.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

@router_kontak.delete("/delete", response_model=DeleteResponseBaseSch[KontakSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID):
    
    """Delete a object"""

    obj_current = await crud.kontak.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Kontak, id)
    
    obj_deleted = await crud.kontak.remove(id=id)

    return obj_deleted
#endregion

#region Rekening
router_rekening = APIRouter()

@router_rekening.post("/create", response_model=PostResponseBaseSch[RekeningSch], status_code=status.HTTP_201_CREATED)
async def create(sch: RekeningCreateSch):
    
    """Create a new object"""
        
    new_obj = await crud.rekening.create(obj_in=sch)
    
    return create_response(data=new_obj)

@router_rekening.get("", response_model=GetResponsePaginatedSch[RekeningSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.rekening.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router_rekening.get("/{id}", response_model=GetResponseBaseSch[RekeningSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.rekening.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Rekening, id)

@router_rekening.put("/{id}", response_model=PutResponseBaseSch[RekeningSch])
async def update(id:UUID, sch:RekeningUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.rekening.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Rekening, id)
    
    obj_updated = await crud.rekening.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

@router_rekening.delete("/delete", response_model=DeleteResponseBaseSch[RekeningSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID):
    
    """Delete a object"""

    obj_current = await crud.rekening.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Rekening, id)
    
    obj_deleted = await crud.rekening.remove(id=id)

    return obj_deleted
#endregion
   