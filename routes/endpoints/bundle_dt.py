from uuid import UUID
from fastapi import APIRouter, status, Depends, UploadFile, Response, HTTPException
from fastapi.responses import FileResponse
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel.ext.asyncio.session import AsyncSession
from models.bundle_model import BundleDt
from models.dokumen_model import Dokumen
from models.worker_model import Worker
from schemas.bundle_dt_sch import (BundleDtSch, BundleDtUpdateSch)
from schemas.dokumen_sch import RiwayatSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, DocumentFileNotFoundException, ContentNoChangeException)
from services.gcloud_storage_service import GCStorageService
from services.helper_service import HelperService
from datetime import datetime
import crud
import json

router = APIRouter()

@router.get("", response_model=GetResponsePaginatedSch[BundleDtSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.bundledt.get_multi_paginate_ordered_with_keyword_dict(params=params, 
                                                                            order_by=order_by, 
                                                                            keyword=keyword, 
                                                                            filter_query=filter_query,
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
            await update_keyword(meta_data=sch.meta_data, 
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

async def update_keyword(meta_data:str|None,
                        bundle_hd_id:UUID|None,
                        key_field:str|None,
                        worker_id:UUID|None,
                        db_session : AsyncSession | None = None):
    
    obj_json = json.loads(meta_data.replace("'", '"'))
    current_bundle_hd = await crud.bundlehd.get(id=bundle_hd_id)

    metadata_keyword = obj_json[f'{key_field}']
    if metadata_keyword:
        # periksa apakah keyword belum eksis di bundle hd
        if metadata_keyword not in current_bundle_hd.keyword:
            edit_keyword_hd = current_bundle_hd
            if current_bundle_hd.keyword is None or current_bundle_hd.keyword == "":
                edit_keyword_hd.keyword = metadata_keyword
            else:
                edit_keyword_hd.keyword = f"{current_bundle_hd.keyword},{metadata_keyword}"
                
                await crud.bundlehd.update(obj_current=current_bundle_hd, 
                                            obj_new=edit_keyword_hd, 
                                            db_session=db_session, 
                                            with_commit=False,
                                            updated_by_id=worker_id)


# @router.put("add-riwayat/{id}", response_model=PutResponseBaseSch[BundleDtSch])
# async def add_riwayat(id:UUID, 
#                       sch:RiwayatSch = Depends(RiwayatSch.as_form), 
#                       file:UploadFile = None,
#                       ):
#     """Update a riwayat obj"""

#     obj_current = await crud.bundledt.get(id=id)
#     if not obj_current:
#         raise IdNotFoundException(BundleDt, id)
    
#     if sch.meta_data is None or sch.meta_data == "":
#         raise ContentNoChangeException(detail="No meta data is null")
    
#     dokumen = await crud.dokumen.get(id=obj_current.dokumen_id)
    
#     metadata_dict = json.loads(sch.meta_data.replace("'", '"'))
#     key_value = metadata_dict[f'{dokumen.key_riwayat}']

#     if key_value is None or key_value == "":
#         raise ContentNoChangeException(detail=f"{dokumen.key_riwayat} harus diisi!")
    
#     file_path = None
#     if file:
#         file_path = await GCStorageService().upload_file_dokumen(file=file, file_name=f'{id}-{obj_current.dokumen_name}-{key_value}')

#     riwayat_data = eval(obj_current.riwayat_data.replace('null', 'None'))
#     new_riwayat_obj = {
#                         'tanggal':str(datetime.now()), 
#                         'key_value':key_value, 
#                         'file_path':file_path, 
#                         'is_default':False, 
#                         'meta_data': metadata_dict }
    
#     riwayat_data['riwayat'].append(new_riwayat_obj)
#     riwayat_data = json.dumps(riwayat_data)

#     obj_updated = obj_current
#     obj_updated.riwayat_data = str(riwayat_data).replace('None', 'null').replace('"', "'")

#     obj = await crud.bundledt.update(obj_current=obj_current, 
#                                              obj_new=obj_updated,
#                                              updated_by_id=None)

#     return create_response(data=obj)

@router.put("/update-riwayat/{id}", response_model=PutResponseBaseSch[BundleDtSch])
async def update_riwayat(id:UUID, 
                        sch:RiwayatSch = Depends(RiwayatSch.as_form), 
                        file:UploadFile = None,
                        ):
    
    obj_current = await crud.bundledt.get(id=id)
    if not obj_current:
        raise IdNotFoundException(BundleDt, id)
    
    dokumen = await crud.dokumen.get(id=obj_current.dokumen_id)
    
    metadata_dict = json.loads(sch.meta_data.replace("'", '"'))
    key_value = metadata_dict[f'{dokumen.key_riwayat}']

    if key_value is None or key_value == "":
            raise ContentNoChangeException(detail=f"{dokumen.key_riwayat} wajib terisi!")

    riwayat_data = json.loads(obj_current.riwayat_data.replace("'", "\""))

    current_dict_riwayat = next((x for x in riwayat_data["riwayat"] if x["key_value"] == sch.key_value), None)
    if current_dict_riwayat is None:
        raise ContentNoChangeException(detail=f"Riwayat {sch.key_value} tidak ditemukan")
    
    file_path = None
    if file:
        file_path = await GCStorageService().upload_file_dokumen(file=file, file_name=f'{id}-{obj_current.dokumen_name}-{key_value}')
    else:
        file_path = sch.file_path
    
    obj_updated = obj_current
    
    if sch.is_default == True:
        obj_updated.file_path = file_path
        obj_updated.meta_data = sch.meta_data

        for i, item in enumerate(riwayat_data["riwayat"]):
            item["is_default"] = False
    
    new_riwayat_obj = {
                        'tanggal':str(datetime.now()), 
                        'key_value':key_value, 
                        'file_path':file_path, 
                        'is_default':sch.is_default, 
                        'meta_data': metadata_dict
                      }
    
    for i, item in enumerate(riwayat_data["riwayat"]):
        if item.get("key_value") == sch.key_value:
            riwayat_data["riwayat"][i] = new_riwayat_obj
            break
    
    riwayat_data = json.dumps(riwayat_data)
    obj_updated.riwayat_data = str(riwayat_data).replace('None', 'null').replace('"', "'")

    obj = await crud.bundledt.update(obj_current=obj_current, obj_new=obj_updated)

    
    return create_response(data=obj)

@router.put("/delete-riwayat/{id}", response_model=PutResponseBaseSch[BundleDtSch])
async def delete_riwayat(id:UUID, 
                        sch:RiwayatSch):
    
    obj_current = await crud.bundledt.get(id=id)
    if not obj_current:
        raise IdNotFoundException(BundleDt, id)

    #riwayat_data = eval(obj_current.riwayat_data.replace('null', 'None'))

    riwayat_data = json.loads(obj_current.riwayat_data.replace("'", "\""))

    riwayat_data["riwayat"] = [item for item in riwayat_data["riwayat"] if item["key_value"] != sch.key_value]

    obj_updated = obj_current

    if sch.is_default == True:
        obj_riwayat = riwayat_data["riwayat"][0]
        obj_riwayat["is_default"] = True

        
        obj_updated.file_path = obj_riwayat["file_path"]
        obj_updated.meta_data = str(obj_riwayat["meta_data"])

    riwayat_data = json.dumps(riwayat_data)
    obj_updated.riwayat_data = str(riwayat_data).replace('None', 'null').replace('"', "'")

    obj = await crud.bundledt.update(obj_current=obj_current, obj_new=obj_updated)
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
async def download_file(id:UUID,
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
    
    ext = obj_current.file_path.split('.')[-1]

    # return FileResponse(file, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={obj_current.id}.{ext}"})
    response = Response(content=file_bytes, media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename={id}-{obj_current.dokumen_name}-{key_value}.{ext}"
    return response



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