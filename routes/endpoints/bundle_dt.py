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
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, DocumentFileNotFoundException)
from services.gcloud_storage_service import GCStorageService
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
                 current_worker: Worker = Depends(crud.worker.get_current_user)):
    
    """Update a obj by its id"""

    obj_current = await crud.bundledt.get(id=id)
    if not obj_current:
        raise IdNotFoundException(BundleDt, id)
    
    dokumen = await crud.dokumen.get(id=sch.dokumen_id)
    db_session = db.session
    
    if file:
        file_path = await GCStorageService().upload_file_dokumen(file=file, obj_current=obj_current)
        sch.file_path = file_path

    if sch.meta_data is not None or sch.meta_data != "":
        history_new = extract_metadata_for_history(sch.meta_data, obj_current.history_data)
        sch.history_data = history_new
        
        #updated bundle header keyword when dokumen metadata is_keyword true
        if dokumen.is_keyword == True :
            await update_keyword(sch.meta_data, sch.bundle_hd_id, dokumen.key_field, current_worker.id, db_session)
        
    obj_updated = await crud.bundledt.update(obj_current=obj_current, 
                                             obj_new=sch, 
                                             db_session=db_session, 
                                             with_commit=True, 
                                             updated_by_id=current_worker.id)

    return create_response(data=obj_updated)

def extract_metadata_for_history(meta_data:str | None = None,
                                current_history:str | None = None) -> str:
    
    ## Memeriksa apakah ada key "Nomor" dalam metadata
    o_json = json.loads(meta_data.replace("'", '"'))
    Nomor = ""
    if "Nomor" in o_json:
        Nomor = o_json['Nomor']

    if current_history is None:
        history_data = {'history':
                        [{'tanggal': str(datetime.now()),
                          'nomor': Nomor,
                          'meta_data': json.loads(meta_data.replace("'", '"'))}]
                        }
    else:
        history_data = eval(current_history.replace('null', 'None'))
        new_metadata = {'tanggal': str(datetime.now()), 'nomor': Nomor, 'meta_data': json.loads(meta_data.replace("'", '"'))}
        history_data['history'].append(new_metadata)

    result = str(history_data).replace('None', 'null')
    return result

async def extract_metadata_for_riwayat(meta_data:str | None = None,
                                       current_riwayat:str | None = None,
                                       dokumen:Dokumen | None = None,
                                       file_path:str|None = None,
                                       is_default:bool|None = False) -> str:
    
    riwayat_data:str = ""
    metadata_dict = json.loads(meta_data.replace("'", '"'))

    if current_riwayat is None:
        key_riwayat = dokumen.key_riwayat
        key_value = metadata_dict[f'{key_riwayat}']

        new_riwayat_data = {'riwayat':
                            [
                                {
                                 'tanggal':str(datetime.now()), 
                                 'key_value':key_value, 
                                 'file_path':file_path, 
                                 'is_default':is_default, 
                                 'meta_data': metadata_dict
                                }
                            ]}
        riwayat_data = str(new_riwayat_data).replace('None', 'null')

    return riwayat_data
    




async def update_keyword(meta_data:str|None,
                        bundle_hd_id:UUID|None,
                        key_field:str|None,
                        worker_id:UUID|None,
                        db_session : AsyncSession | None = None):
    
    obj_json = json.loads(meta_data)
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