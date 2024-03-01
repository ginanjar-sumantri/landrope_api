from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, Response, BackgroundTasks, HTTPException
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, or_
from sqlalchemy import text
from models.bundle_model import BundleDt
from models.dokumen_model import Dokumen, KategoriDokumen
from models.worker_model import Worker
from schemas.bundle_dt_sch import (BundleDtSch, BundleDtUpdateSch, BundleDtMetaDynSch, BundleDtMetaDokumenRepeatSch)
from schemas.dokumen_sch import RiwayatSch
from schemas.bidang_sch import BidangUpdateSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, DocumentFileNotFoundException, ContentNoChangeException)
from common.ordered import OrderEnumSch
from services.gcloud_storage_service import GCStorageService
from services.helper_service import HelperService, BundleHelper
from datetime import datetime
from decimal import Decimal
from shapely import wkt, wkb
import uuid
import crud
import json

router = APIRouter()

@router.get("", response_model=GetResponsePaginatedSch[BundleDtSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str = None, 
            order:OrderEnumSch = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(BundleDt).select_from(BundleDt
                                            ).outerjoin(Worker, BundleDt.updated_by_id == Worker.id
                                            ).outerjoin(Dokumen, BundleDt.dokumen_id == Dokumen.id
                                            ).outerjoin(KategoriDokumen, Dokumen.kategori_dokumen_id == KategoriDokumen.id)
    
    query = query.filter(Dokumen.is_active != False)
    
    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
            query = query.where(getattr(BundleDt, key) == value)
    
    if keyword:
        query = query.filter(
            or_(
                BundleDt.meta_data.ilike(f'%{keyword}%'),
                BundleDt.code.ilike(f'%{keyword}%'),
                Dokumen.name.ilike(f'%{keyword}%'),
                KategoriDokumen.name.ilike(f'%{keyword}%'),
                Worker.name.ilike(f'%{keyword}%')
            )
        )
    
    columns = BundleDt.__table__.columns
    cls_meta = getattr(BundleDt, 'Meta', None)

    if order_by is not None and order_by not in columns:
        if cls_meta and order_by in cls_meta().order_fields:
            order_by = cls_meta().order_fields[order_by]
        else:
            order_by = 'id'    
    elif order_by is None:
        order_by = 'id'

    if order == OrderEnumSch.ascendent:
        order_by += ' asc'    
    else:
        order_by += ' desc'

    query = query.order_by(text(order_by))
    
    objs = await crud.bundledt.get_multi_paginated_ordered(params=params, query=query)

    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[BundleDtSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.bundledt.get_by_id(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(BundleDt, id)

@router.put("/{id}", response_model=PutResponseBaseSch[BundleDtSch])
async def update(id:UUID, 
                 background_task:BackgroundTasks,
                 sch:BundleDtUpdateSch = Depends(BundleDtUpdateSch.as_form), 
                 file:UploadFile|None = None,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    db_session = db.session

    obj_current = await crud.bundledt.get_by_id(id=id)
    if not obj_current:
        raise IdNotFoundException(BundleDt, id)

    dokumen = await crud.dokumen.get(id=sch.dokumen_id)

    file_name = f'Bundle-{dokumen.name}-{uuid.uuid4().hex}'
    from_new_file:bool = False

    if file:
        sch.file_path = await GCStorageService().upload_file_dokumen(file=file, file_name=file_name)
        from_new_file = True
    elif file is None and sch.file_path is None:
        sch.file_path = obj_current.file_path

    sch.meta_data = sch.meta_data.replace("'", "\"")

    if dokumen.is_multiple != True or dokumen.is_multiple is None:
        #validasi untuk riwayat
        if dokumen.is_riwayat:
            metadata_dict = json.loads(sch.meta_data)
            key_value = metadata_dict.get(dokumen.key_riwayat, None)

            if key_value is None or key_value == "":
                if from_new_file:
                    await GCStorageService().delete_file(file_name=file_name)
                raise ContentNoChangeException(detail=f"{dokumen.key_riwayat} wajib terisi!")
            
            sch.riwayat_data = BundleHelper().extract_metadata_for_riwayat(meta_data=sch.meta_data, key_riwayat=dokumen.key_riwayat, current_riwayat=obj_current.riwayat_data, file_path=sch.file_path, is_default=True)
            
        #updated bundle header keyword when dokumen metadata is_keyword true
        if dokumen.is_keyword == True :
            await BundleHelper().update_bundle_keyword(meta_data=sch.meta_data, bundle_hd_id=sch.bundle_hd_id, key_field=dokumen.key_field, worker_id=current_worker.id, db_session=db_session)
        
    else:
        sch.meta_data = await BundleHelper().multiple_data(meta_data_current=obj_current.meta_data, meta_data_new=sch.meta_data, dokumen=dokumen)
        sch.multiple_count = BundleHelper().multiple_data_count(meta_data=sch.meta_data)

    obj_updated = await crud.bundledt.update(obj_current=obj_current, obj_new=sch, db_session=db_session, updated_by_id=current_worker.id, with_commit=True)
    obj_updated = await crud.bundledt.get_by_id(id=obj_updated.id)

    if obj_updated.dokumen_name == "SPPT PBB NOP":
        background_task.add_task(HelperService().update_nilai_njop_bidang, obj_updated, obj_updated.meta_data)

    return create_response(data=obj_updated)

@router.put("/update-riwayat/{id}", response_model=PutResponseBaseSch[BundleDtSch])
async def update_riwayat(id:UUID,
                        background_task:BackgroundTasks,
                        sch:RiwayatSch = Depends(RiwayatSch.as_form), 
                        file:UploadFile = None,
                        current_worker:Worker = Depends(crud.worker.get_current_user)
                        ):
    
    obj_current = await crud.bundledt.get_by_id(id=id)
    if not obj_current:
        raise IdNotFoundException(BundleDt, id)
    
    dokumen = await crud.dokumen.get(id=obj_current.dokumen_id)
    
    riwayat_data, file_path = await BundleHelper().update_riwayat(current_riwayat_data=obj_current.riwayat_data, 
                                                                   dokumen=dokumen,
                                                                   codehd=obj_current.bundlehd.code,
                                                                   codedt=obj_current.code,
                                                                   sch=sch, 
                                                                   file=file)
    db_session = db.session
    obj_updated = obj_current
    
    if sch.is_default == True:
        obj_updated.file_path = file_path
        obj_updated.meta_data = sch.meta_data

    obj_updated.riwayat_data = riwayat_data

    if dokumen.is_keyword == True :
            await BundleHelper().update_bundle_keyword(meta_data=sch.meta_data, 
                                                        bundle_hd_id=obj_current.bundle_hd_id, 
                                                        worker_id=current_worker.id, 
                                                        key_field=dokumen.key_field, 
                                                        db_session=db_session)

    obj = await crud.bundledt.update(obj_current=obj_current, obj_new=obj_updated, db_session=db_session, with_commit=True, updated_by_id=current_worker.id)
    obj = await crud.bundledt.get_by_id(id=obj.id)

    if sch.is_default and obj.dokumen_name == "SPPT PBB NOP":
        background_task.add_task(HelperService().update_nilai_njop_bidang, obj, obj.meta_data)

    return create_response(data=obj)

@router.put("/delete-riwayat/{id}", response_model=PutResponseBaseSch[BundleDtSch])
async def delete_riwayat(id:UUID, 
                        sch:RiwayatSch,
                        background_task:BackgroundTasks,
                        current_worker:Worker = Depends(crud.worker.get_current_user)):
    
    obj_current = await crud.bundledt.get(id=id)
    if not obj_current:
        raise IdNotFoundException(BundleDt, id)

    riwayat_data = json.loads(obj_current.riwayat_data.replace("'", "\""))

    riwayat_data["riwayat"] = [item for item in riwayat_data["riwayat"] if item["key_value"] != sch.key_value]

    obj_updated = obj_current

    if len(riwayat_data["riwayat"]) > 0:
        if sch.is_default == True:
            obj_riwayat = riwayat_data["riwayat"][0]
            obj_riwayat["is_default"] = True
            obj_updated.file_path = obj_riwayat["file_path"]
            obj_updated.meta_data = str(obj_riwayat["meta_data"])

        riwayat_data = json.dumps(riwayat_data)
        obj_updated.riwayat_data = str(riwayat_data).replace('None', 'null').replace('"', "'")
    else:
        obj_updated.file_path = None
        obj_updated.meta_data = None
        obj_updated.riwayat_data = None

    obj = await crud.bundledt.update(obj_current=obj_current, obj_new=obj_updated, updated_by_id=current_worker.id)
    obj = await crud.bundledt.get_by_id(id=obj.id)

    if obj.dokumen_name == "SPPT PBB NOP":
        background_task.add_task(HelperService().update_nilai_njop_bidang, obj, obj.meta_data)

    return create_response(data=obj)
    
@router.get("/download-file/{id}")
async def download_file(id:UUID):
    """Download File Dokumen"""

    obj_current = await crud.bundledt.get_by_id(id=id)
    if not obj_current:
        raise IdNotFoundException(BundleDt, id)
    if obj_current.file_path is None:
        raise DocumentFileNotFoundException(dokumenname=obj_current.dokumen_name)

    try:
        file_bytes = await GCStorageService().download_dokumen(file_path=obj_current.file_path)
    except Exception as e:
        raise DocumentFileNotFoundException(dokumenname=obj_current.dokumen_name)
    
    ext = obj_current.file_path.split('.')[-1]

    # return FileResponse(file, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={obj_current.id}.{ext}"})
    response = Response(content=file_bytes, media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename={obj_current.bundlehd.code}-{obj_current.code}-{obj_current.dokumen_name}.{ext}"
    return response

@router.get("/download-file/waris/{id}")
async def download_file_waris(id:UUID, meta_data:str):
    """Download File Dokumen"""

    obj_current = await crud.bundledt.get_by_id(id=id)
    if not obj_current:
        raise IdNotFoundException(BundleDt, id)
    if obj_current.meta_data is None:
        raise HTTPException(status_code=422, detail="meta data is null")
    
    meta_data_current = json.loads(obj_current.meta_data)
    meta_data = json.loads(meta_data.replace("'", '\"'))
    
    data_current = next((index for index, data in enumerate(meta_data_current["data"]) if data[obj_current.dokumen.key_field] == meta_data[obj_current.dokumen.key_field]), None)

    if data_current is None:
        raise HTTPException(status_code=422, detail="dokumen yang dimaksud tidak ditemukan dalam meta data")

    file_path = meta_data.get("file", None)
    key_value = meta_data.get(obj_current.dokumen.key_field, uuid.uuid4().hex)
    if file_path is None:
        raise HTTPException(status_code=422, detail="dokumen yang dimaksud tidak memiliki file")

    try:
        file_bytes = await GCStorageService().download_dokumen(file_path=file_path)
    except Exception as e:
        raise DocumentFileNotFoundException(dokumenname=obj_current.dokumen_name)
    
    ext = file_path.split('.')[-1]

    # return FileResponse(file, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={obj_current.id}.{ext}"})
    response = Response(content=file_bytes, media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename={key_value}.{ext}"
    return response

@router.get("/download-file/riwayat/{id}")
async def download_file_riwayat(id:UUID,
                        key_value:str):
    
    """Download File Dokumen Riwayat"""

    obj_current = await crud.bundledt.get_by_id(id=id)
    if not obj_current:
        raise IdNotFoundException(BundleDt, id)
    
    riwayat_data = json.loads(obj_current.riwayat_data.replace("'", '"'))

    riwayat_obj = next((x for x in riwayat_data["riwayat"] if x["key_value"] == key_value), None)
    if riwayat_obj is None:
        raise ContentNoChangeException(detail=f"Riwayat {key_value} tidak ditemukan")
    
    if riwayat_obj["file_path"] is None:
        raise DocumentFileNotFoundException(dokumenname=obj_current.dokumen_name)

    try:
        file_bytes = await GCStorageService().download_dokumen(file_path=riwayat_obj["file_path"])
    except Exception as e:
        raise DocumentFileNotFoundException(dokumenname=obj_current.dokumen_name)
    
    ext = riwayat_obj["file_path"].split('.')[-1]

    # return FileResponse(file, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={obj_current.id}.{ext}"})
    response = Response(content=file_bytes, media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename={obj_current.bundlehd.code}-{obj_current.code}-{obj_current.dokumen_name}-{key_value}.{ext}"
    return response

@router.get("/meta_dyn/{kjb_id}", response_model=GetResponseBaseSch[BundleDtMetaDynSch])
async def get_meta_data_and_dyn_form(kjb_id:UUID,
                                dokumen_id):

    """Get an object by id"""

    obj = await crud.bundledt.get_meta_data_and_dyn_form(id=kjb_id, dokumen_id=dokumen_id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(BundleDt, kjb_id)

@router.get("/search/document-repeat", response_model=GetResponseBaseSch[list[BundleDtMetaDokumenRepeatSch]])
async def search_document_repeat(keyword:str|None = None,
                                dokumen_id:UUID|None = None,
                                limit:int|None = None):

    objs = await crud.bundledt.get_multi_by_meta_data_and_dokumen_id(keyword=keyword,dokumen_id=dokumen_id, limit=limit)

    datas:list[BundleDtMetaDokumenRepeatSch] = []
    for bundle_dt in objs:
        meta_data = json.loads(bundle_dt.meta_data.replace("'", "\""))
        key_value = f"{meta_data.get(bundle_dt.dokumen.key_field, '')}"
        infoes = bundle_dt.dokumen.additional_info.split(',')
        infoe_values = [meta_data.get(key, '') for key in infoes]
        additional_info = "|".join(infoe_values) if len(infoe_values) > 1 else "".join(infoe_values)

        if next((a for a in datas if a.key_value == key_value), None):
            continue

        data = BundleDtMetaDokumenRepeatSch(id=bundle_dt.id,
                                            key_value=key_value,
                                            additional_info=additional_info,
                                            dokumen_name=bundle_dt.dokumen_name)
        
        datas.append(data)

    return create_response(data=datas)



    