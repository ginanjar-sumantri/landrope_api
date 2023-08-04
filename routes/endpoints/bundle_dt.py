from uuid import UUID
from fastapi import APIRouter, status, Depends, UploadFile, Response, HTTPException
from fastapi.responses import FileResponse
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel.ext.asyncio.session import AsyncSession
from models.bundle_model import BundleDt
from models.dokumen_model import Dokumen
from models.worker_model import Worker
from schemas.bundle_dt_sch import (BundleDtSch, BundleDtUpdateSch, BundleDtMetaDynSch)
from schemas.dokumen_sch import RiwayatSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, DocumentFileNotFoundException, ContentNoChangeException)
from common.ordered import OrderEnumSch
from services.gcloud_storage_service import GCStorageService
from services.helper_service import HelperService
from datetime import datetime
import crud
import json

router = APIRouter()

@router.get("", response_model=GetResponsePaginatedSch[BundleDtSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None, order:OrderEnumSch = None):
    
    """Gets a paginated list objects"""

    # if order_by == "dokumen_name":
    #     order_by = "dokumen.name"
    objs = await crud.bundledt.get_multi_paginate_ordered_with_keyword_dict(params=params, 
                                                                            order_by=order_by, 
                                                                            keyword=keyword, 
                                                                            filter_query=filter_query,
                                                                            order=order,
                                                                            join=True)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[BundleDtSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.bundledt.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(BundleDt, id)

@router.put("/{id}", response_model=PutResponseBaseSch[BundleDtSch])
async def update(id:UUID, 
                 sch:BundleDtUpdateSch = Depends(BundleDtUpdateSch.as_form), 
                 file:UploadFile = None,
                 current_worker:Worker = Depends(crud.worker.get_current_user)):
    
    """Update a obj by its id"""

    obj_current = await crud.bundledt.get(id=id)
    if not obj_current:
        raise IdNotFoundException(BundleDt, id)
    
    dokumen = await crud.dokumen.get(id=sch.dokumen_id)

    db_session = db.session
    file_path = None
    
    if file:
        file_path = await GCStorageService().upload_file_dokumen(file=file, file_name=f'{id}-{obj_current.dokumen_name}')
        sch.file_path = file_path

    if sch.meta_data is not None or sch.meta_data != "":
        #history
        history_new = HelperService().extract_metadata_for_history(sch.meta_data, obj_current.history_data)
        sch.history_data = history_new

        #riwayat
        if dokumen.is_riwayat == True:
            riwayat_new = HelperService().extract_metadata_for_riwayat(meta_data=sch.meta_data, 
                                                                       key_riwayat=dokumen.key_riwayat, 
                                                                       current_riwayat=obj_current.riwayat_data, 
                                                                       file_path=file_path, 
                                                                       is_default=True)
            sch.riwayat_data = riwayat_new
        
        #updated bundle header keyword when dokumen metadata is_keyword true
        if dokumen.is_keyword == True :
            await HelperService().update_bundle_keyword(meta_data=sch.meta_data, 
                                                        bundle_hd_id=sch.bundle_hd_id, 
                                                        worker_id=current_worker.id, 
                                                        key_field=dokumen.key_field, 
                                                        db_session=db_session)
        
    obj_updated = await crud.bundledt.update(obj_current=obj_current, 
                                             obj_new=sch, 
                                             db_session=db_session, 
                                             updated_by_id=current_worker.id,
                                             with_commit=True)

    return create_response(data=obj_updated)


@router.put("/update-riwayat/{id}", response_model=PutResponseBaseSch[BundleDtSch])
async def update_riwayat(id:UUID, 
                        sch:RiwayatSch = Depends(RiwayatSch.as_form), 
                        file:UploadFile = None,
                        current_worker:Worker = Depends(crud.worker.get_current_user)
                        ):
    
    obj_current = await crud.bundledt.get(id=id)
    if not obj_current:
        raise IdNotFoundException(BundleDt, id)
    
    dokumen = await crud.dokumen.get(id=obj_current.dokumen_id)
    
    riwayat_data, file_path = await HelperService().update_riwayat(current_riwayat_data=obj_current.riwayat_data, 
                                                                   dokumen=dokumen, 
                                                                   sch=sch, 
                                                                   file=file)
    db_session = db.session
    obj_updated = obj_current
    
    if sch.is_default == True:
        obj_updated.file_path = file_path
        obj_updated.meta_data = sch.meta_data

    obj_updated.riwayat_data = riwayat_data

    if dokumen.is_keyword == True :
            await HelperService().update_bundle_keyword(meta_data=sch.meta_data, 
                                                        bundle_hd_id=obj_current.bundle_hd_id, 
                                                        worker_id=current_worker.id, 
                                                        key_field=dokumen.key_field, 
                                                        db_session=db_session)

    obj = await crud.bundledt.update(obj_current=obj_current, obj_new=obj_updated, db_session=db_session, with_commit=True, updated_by_id=current_worker.id)
    
    return create_response(data=obj)

@router.put("/delete-riwayat/{id}", response_model=PutResponseBaseSch[BundleDtSch])
async def delete_riwayat(id:UUID, 
                        sch:RiwayatSch,
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
    return create_response(data=obj)
    
@router.get("/download-file/{id}")
async def download_file(id:UUID):
    """Download File Dokumen"""

    obj_current = await crud.bundledt.get(id=id)
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
    response.headers["Content-Disposition"] = f"attachment; filename={id}-{obj_current.dokumen_name}.{ext}"
    return response

@router.get("/download-file/riwayat/{id}")
async def download_file_riwayat(id:UUID,
                        key_value:str):
    
    """Download File Dokumen Riwayat"""

    obj_current = await crud.bundledt.get(id=id)
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
    response.headers["Content-Disposition"] = f"attachment; filename={id}-{obj_current.dokumen_name}-{key_value}.{ext}"
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


# @router.get("/get/json")
# async def extract_json():
#     str_json = "{'history':[{'tanggal':'2023-06-06 08:15:39','nomor':'AJB 5123','meta_data': {'Nomor':'AJB 5123','Tanggal':'2023-06-28'}}]}".replace("'",'"')

#     obj_json = json.loads(str_json)
#     values = []
#     nomor = 'Nomor'
#     # for item in obj_json:
#     #     for field in item['field']:
#     #         value = field['value']
#     #         is_datetime = is_datetimecheck(value=value)
#     #         if type(field['value']).__name__ in ["str", "string"] and is_datetime == False:
#     #             values.append(str(value))

#     for data in obj_json['history']:
#         value = data['meta_data'][f'{nomor}']
#         values.append(value)

#     return valuess