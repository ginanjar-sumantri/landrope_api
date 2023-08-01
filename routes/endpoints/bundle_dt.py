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
from common.exceptions import (IdNotFoundException, DocumentFileNotFoundException)
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
                 ):
    
    """Update a obj by its id"""

    obj_current = await crud.bundledt.get(id=id)
    if not obj_current:
        raise IdNotFoundException(BundleDt, id)
    
    dokumen = await crud.dokumen.get(id=sch.dokumen_id)

    db_session = db.session
    file_path = None
    
    if file:
        file_path = await GCStorageService().upload_file_dokumen(file=file, obj_current=obj_current)
        sch.file_path = file_path

    if sch.meta_data is not None or sch.meta_data != "":
        #history
        history_new = HelperService().extract_metadata_for_history(sch.meta_data, obj_current.history_data)
        sch.history_data = history_new

        #riwayat
        if dokumen.is_riwayat == True:
            riwayat_new = HelperService().extract_metadata_for_riwayat(meta_data=sch.meta_data, key_riwayat=dokumen.key_riwayat, current_riwayat=obj_current.riwayat_data, file_path=file_path, is_default=True)
            sch.riwayat_data = riwayat_new
        
        #updated bundle header keyword when dokumen metadata is_keyword true
        if dokumen.is_keyword == True :
            await update_keyword(meta_data=sch.meta_data, bundle_hd_id=sch.bundle_hd_id, worker_id=None, key_field=dokumen.key_field, db_session=db_session)
        
    obj_updated = await crud.bundledt.update(obj_current=obj_current, 
                                             obj_new=sch, 
                                             db_session=db_session, 
                                             with_commit=True, 
                                             )

    return create_response(data=obj_updated)

@router.put("add-riwayat/{id}", response_model=PutResponseBaseSch[BundleDtSch])
async def add_riwayat(id:UUID, sch:RiwayatSch, file:UploadFile | None):
    """Update a riwayat obj"""

    obj_current = await crud.bundledt.get(id=id)
    if not obj_current:
        raise IdNotFoundException(BundleDt, id)
    
    current_riwayat_data =  obj_current.riwayat_data

    
    if file:
        file_path = await GCStorageService().upload_file_dokumen(file=file, obj_current=obj_current)
        sch.file_path = file_path

    
    return create_response(data=obj_current)
    


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
    response.headers["Content-Disposition"] = f"attachment; filename={obj_current.id}.{ext}"
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