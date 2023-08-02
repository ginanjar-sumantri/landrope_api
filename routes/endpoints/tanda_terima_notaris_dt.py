from uuid import UUID
from fastapi import APIRouter, status, Depends, UploadFile, Response
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from models.bundle_model import BundleHd, BundleDt
from models.tanda_terima_notaris_model import TandaTerimaNotarisDt, TandaTerimaNotarisHd
from schemas.tanda_terima_notaris_dt_sch import (TandaTerimaNotarisDtSch, TandaTerimaNotarisDtCreateSch, TandaTerimaNotarisDtUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, 
                                  DeleteResponseBaseSch, GetResponsePaginatedSch, 
                                  PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException, 
                               ContentNoChangeException, DocumentFileNotFoundException)
from services.gcloud_storage_service import GCStorageService
from datetime import datetime
import crud
import json


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[TandaTerimaNotarisDtSch], status_code=status.HTTP_201_CREATED)
async def create(sch: TandaTerimaNotarisDtCreateSch = Depends(TandaTerimaNotarisDtCreateSch.as_form), 
                file:UploadFile = None):
    
    """Create a new object"""
    file_path = None
    tanda_terima_hd = await crud.tandaterimanotaris_hd.get(id=sch.tanda_terima_notaris_hd_id)
    if not tanda_terima_hd:
        raise IdNotFoundException(TandaTerimaNotarisHd, id)
    
    bundlehd_obj_current = tanda_terima_hd.kjb_dt.bundlehd
    if not bundlehd_obj_current:
        raise IdNotFoundException(BundleHd, tanda_terima_hd.kjb_dt.bundle_hd_id)

    if sch.meta_data is None or sch.meta_data == "":
        raise ContentNoChangeException(detail="Meta data can't be null")
    
    dokumen = await crud.dokumen.get(id=sch.dokumen_id)

    ## Memeriksa apakah ada key "Nomor" dalam metadata
    o_json = eval(sch.meta_data)
    Nomor = ""
    if "Nomor" in o_json:
        Nomor = o_json['Nomor']
    
    db_session = db.session

    # Memeriksa apakah dokumen yang dimaksud eksis di bundle detail (bisa jadi dokumen baru di master dan belum tergenerate)
    bundledt_obj_current = next((x for x in bundlehd_obj_current.bundledts if x.dokumen_id == sch.dokumen_id and x.bundle_hd_id == bundlehd_obj_current.id), None)
    if bundledt_obj_current is None:
        code = bundlehd_obj_current.code + dokumen.code
        history_data = {'history':[{'tanggal': str(datetime.now()),'nomor': Nomor,'meta_data': eval(sch.meta_data)}]}

        if file:
            file_path = await GCStorageService().upload_file_dokumen(file=file)
            sch.file_path = file_path

        new_dokumen = BundleDt(code=code, 
                               dokumen_id=dokumen.id, 
                               meta_data=sch.meta_data, 
                               history_data=str(history_data), 
                               bundle_hd_id=bundlehd_obj_current.id, 
                               file_path=file_path)

        bundledt_obj_current = await crud.bundledt.create(obj_in=new_dokumen, db_session=db_session, with_commit=False)
    else:
        file_path = bundledt_obj_current.file_path

        if bundledt_obj_current.history_data is None or bundledt_obj_current.history_data == "":
            history_data = {'history':[{'tanggal': str(datetime.now()),'nomor': Nomor,'meta_data': eval(sch.meta_data)}]}
        
        else:
            history_data = eval(bundledt_obj_current.history_data)
            new_metadata = {'tanggal': str(datetime.now()), 'nomor': Nomor, 'meta_data': eval(sch.meta_data)}
            history_data['history'].append(new_metadata)
        
        if file:
            file_path = await GCStorageService().upload_file_dokumen(file=file)
            sch.file_path = file_path

        bundledt_obj_updated = bundledt_obj_current
        bundledt_obj_updated.meta_data = sch.meta_data
        bundledt_obj_updated.history_data = str(history_data)
        bundledt_obj_updated.file_path = file_path

        bundledt_obj_current = await crud.bundledt.update(obj_current=bundledt_obj_current, obj_new=bundledt_obj_updated, db_session=db_session, with_commit=False)
    
    #updated bundle header keyword when dokumen metadata is_keyword true
    if dokumen.is_keyword:
        metadata = sch.meta_data.replace("'",'"')
        obj_json = json.loads(metadata)

        # values = []
        # for data in obj_json['history']:
        #     value = data['meta_data'][f'{dokumen.key_field}']
        #     values.append(value)

        metadata_keyword = obj_json[f'{dokumen.key_field}']

        if metadata_keyword not in bundlehd_obj_current.keyword:
            
            edit_keyword_hd = bundlehd_obj_current
            if bundlehd_obj_current.keyword is None or bundlehd_obj_current.keyword == "":
                edit_keyword_hd.keyword = metadata_keyword
            else:
                edit_keyword_hd.keyword = f"{bundlehd_obj_current.keyword},{metadata_keyword}"
                await crud.bundlehd.update(obj_current=bundlehd_obj_current, obj_new=edit_keyword_hd, db_session=db_session, with_commit=False)

    new_obj = await crud.tandaterimanotaris_dt.create(obj_in=sch, db_session=db_session, with_commit=True)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[TandaTerimaNotarisDtSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.tandaterimanotaris_dt.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[TandaTerimaNotarisDtSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.tandaterimanotaris_dt.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(TandaTerimaNotarisDt, id)

@router.put("/{id}", response_model=PutResponseBaseSch[TandaTerimaNotarisDtSch])
async def update(id:UUID, 
                 sch:TandaTerimaNotarisDtUpdateSch = Depends(TandaTerimaNotarisDtUpdateSch.as_form),
                 file:UploadFile = None):
    
    """Update a obj by its id"""

    if sch.meta_data is None or sch.meta_data == "":
        raise ContentNoChangeException(detail="Meta data can't be null")

    obj_current = await crud.tandaterimanotaris_dt.get(id=id)

    if not obj_current:
        raise IdNotFoundException(TandaTerimaNotarisDt, id)
    
    tanda_terima_hd = await crud.tandaterimanotaris_hd.get(id=sch.tanda_terima_notaris_hd_id)
    if not tanda_terima_hd:
        raise IdNotFoundException(TandaTerimaNotarisHd, id)
    
    bundlehd_obj_current = tanda_terima_hd.kjb_dt.bundlehd
    if not bundlehd_obj_current:
        raise IdNotFoundException(BundleHd, tanda_terima_hd.kjb_dt.bundle_hd_id)
    
    dokumen = await crud.dokumen.get(id=sch.dokumen_id)
    
    ## Memeriksa apakah ada key "Nomor" dalam metadata
    o_json = eval(sch.meta_data)
    Nomor = ""
    if "Nomor" in o_json:
        Nomor = o_json['Nomor']
    
    if obj_current.history_data is None:
        history_data = {'history':[{'tanggal': str(datetime.now()),'nomor': Nomor,'meta_data': eval(sch.meta_data)}]}
    else:
        history_data = eval(obj_current.history_data)
        new_metadata = {'tanggal': str(datetime.now()), 'nomor': Nomor, 'meta_data': eval(sch.meta_data)}
        history_data['history'].append(new_metadata)

    sch.history_data = str(history_data)

    db_session = db.session

    bundledt_obj_current = next((x for x in bundlehd_obj_current.bundledts if x.dokumen_id == sch.dokumen_id and x.bundle_hd_id == bundlehd_obj_current.id), None)
    
    file_path = bundledt_obj_current.file_path
    
    if bundledt_obj_current.history_data is None or bundledt_obj_current.history_data == "":
        history_data = {'history':[{'tanggal': str(datetime.now()),'nomor': Nomor,'meta_data': eval(sch.meta_data)}]}
        
    else:
        history_data = eval(bundledt_obj_current.history_data)
        new_metadata = {'tanggal': str(datetime.now()), 'nomor': Nomor, 'meta_data': eval(sch.meta_data)}
        history_data['history'].append(new_metadata)
    
    if file:
            file_path = await GCStorageService().upload_file_dokumen(file=file, obj_current=bundledt_obj_current)
            sch.file_path = file_path

    bundledt_obj_updated = bundledt_obj_current
    bundledt_obj_updated.meta_data = sch.meta_data
    bundledt_obj_updated.history_data = str(history_data)
    bundledt_obj_updated.file_path = file_path

    await crud.bundledt.update(obj_current=bundledt_obj_current, obj_new=bundledt_obj_updated, db_session=db_session, with_commit=False)

    #updated bundle header keyword when dokumen metadata is_keyword true
    if dokumen.is_keyword:
        metadata = sch.meta_data.replace("'",'"')
        obj_json = json.loads(metadata)

        metadata_keyword = obj_json[f'{dokumen.key_field}']

        if metadata_keyword not in bundlehd_obj_current.keyword:
            
            edit_keyword_hd = bundlehd_obj_current
            if bundlehd_obj_current.keyword is None or bundlehd_obj_current.keyword == "":
                edit_keyword_hd.keyword = metadata_keyword
            else:
                edit_keyword_hd.keyword = f"{bundlehd_obj_current.keyword},{metadata_keyword}"
                await crud.bundlehd.update(obj_current=bundlehd_obj_current, obj_new=edit_keyword_hd, db_session=db_session, with_commit=False)

    obj_updated = await crud.tandaterimanotaris_dt.update(obj_current=obj_current, obj_new=sch, db_session=db_session, with_commit=True)

    return create_response(data=obj_updated)

@router.get("/download-file/{id}")
async def download_file(id:UUID):
    """Download File Dokumen"""

    obj_current = await crud.tandaterimanotaris_dt.get(id=id)
    if not obj_current:
        raise IdNotFoundException(BundleDt, id)

    try:
        file_bytes = await GCStorageService().download_dokumen(file_path=obj_current.file_path)
    except Exception as e:
        raise DocumentFileNotFoundException(dokumenname=obj_current.dokumen_name)
    
    ext = obj_current.file_path.split('.')[-1]

    # return FileResponse(file, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={obj_current.id}.{ext}"})
    response = Response(content=file_bytes, media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename={obj_current.id}.{ext}"
    return response


@router.get("extract_dictionary")
async def extract_dict(value:str | None = None):
    metadata = eval(value)
    curr_datetime = datetime.now()

    if "Nomor" in metadata:
            Nomor = metadata['Nomor']
    
    history_data = {'history':[{'tanggal': str(curr_datetime),'nomor': Nomor,'meta_data': metadata}]}
    new_metadata = {'tanggal': str(curr_datetime), 'nomor': 'AJB 789', 'meta_data': metadata}
    history_data['history'].append(new_metadata)


    return str(history_data)


   