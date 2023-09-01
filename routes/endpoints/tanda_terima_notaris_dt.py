from uuid import UUID
from fastapi import APIRouter, status, Depends, UploadFile, Response
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel.ext.asyncio.session import AsyncSession
from models.bundle_model import BundleHd, BundleDt
from models.dokumen_model import Dokumen
from models.tanda_terima_notaris_model import TandaTerimaNotarisDt, TandaTerimaNotarisHd
from models.worker_model import Worker
from schemas.tanda_terima_notaris_dt_sch import (TandaTerimaNotarisDtSch, TandaTerimaNotarisDtCreateSch, TandaTerimaNotarisDtUpdateSch)
from schemas.dokumen_sch import RiwayatSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, 
                                  DeleteResponseBaseSch, GetResponsePaginatedSch, 
                                  PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException, 
                               ContentNoChangeException, DocumentFileNotFoundException)
from services.helper_service import HelperService
from services.gcloud_storage_service import GCStorageService
from datetime import datetime
import crud
import json


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[TandaTerimaNotarisDtSch], status_code=status.HTTP_201_CREATED)
async def create(sch: TandaTerimaNotarisDtCreateSch = Depends(TandaTerimaNotarisDtCreateSch.as_form), 
                file:UploadFile = None,
                current_worker:Worker = Depends(crud.worker.get_current_user)):
    
    """Create a new object"""

    if sch.meta_data is None or sch.meta_data == "":
        raise ContentNoChangeException(detail="Meta data can't be null")

    file_path = None

    tanda_terima_hd = await crud.tandaterimanotaris_hd.get(id=sch.tanda_terima_notaris_hd_id)
    if not tanda_terima_hd:
        raise IdNotFoundException(TandaTerimaNotarisHd, id)
    
    bundlehd_obj_current = tanda_terima_hd.kjb_dt.bundlehd
    if not bundlehd_obj_current:
        raise IdNotFoundException(BundleHd, tanda_terima_hd.kjb_dt.bundle_hd_id)                                                                        
    
    dokumen = await crud.dokumen.get(id=sch.dokumen_id)
    if dokumen is None:
        raise IdNotFoundException(Dokumen, sch.dokumen_id)
    
    bundledt_obj_current = await crud.bundledt.get_by_bundle_hd_id_and_dokumen_id(bundle_hd_id=bundlehd_obj_current.id, dokumen_id=dokumen.id)
    if not bundledt_obj_current:
        raise ContentNoChangeException(detail=f"Bundle with dokumen {dokumen.name} not exists")
    
    file_name = f'{bundlehd_obj_current.code}-{bundledt_obj_current.code}-{dokumen.name}'

    if dokumen.is_riwayat:
        metadata_dict = json.loads(sch.meta_data.replace("'", "\""))
        key_value = metadata_dict[f'{dokumen.key_riwayat}']

        if key_value is None or key_value == "":
            raise ContentNoChangeException(detail=f"{dokumen.key_riwayat} wajib terisi!")
        
        file_name = f'{bundlehd_obj_current.code}-{bundledt_obj_current.code}-{dokumen.name}-{key_value}'


    if file:
        file_path = await GCStorageService().upload_file_dokumen(file=file, file_name=file_name)
        sch.file_path = file_path
    
    db_session = db.session

    # Merging Data Dokumen dari Tanda Terima Notaris ke Bundle
    await HelperService().merging_to_bundle(bundle_hd_obj=bundlehd_obj_current, dokumen=dokumen, meta_data=sch.meta_data,
                            db_session=db_session, file_path=file_path,
                            worker_id=current_worker.id)
    
    sch.history_data = HelperService().extract_metadata_for_history(sch.meta_data, current_history=None)

    if dokumen.is_riwayat == True:
        sch.riwayat_data = HelperService().extract_metadata_for_riwayat(meta_data=sch.meta_data, 
                                                                    key_riwayat=dokumen.key_riwayat, 
                                                                    current_riwayat=None, 
                                                                    file_path=file_path, 
                                                                    is_default=True)
    sch.tanggal_tanda_terima = tanda_terima_hd.tanggal_tanda_terima
    new_obj = await crud.tandaterimanotaris_dt.create(obj_in=sch, db_session=db_session, with_commit=True, created_by_id=current_worker.id)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[TandaTerimaNotarisDtSch])
async def get_list(
                params: Params = Depends(), 
                order_by:str = None, 
                keyword:str = None, 
                filter_query:str = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.tandaterimanotaris_dt.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query, join=True)
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
                 file:UploadFile = None,
                 current_worker:Worker = Depends(crud.worker.get_current_user)):
    
    """Update a obj by its id"""
    if sch.meta_data is None or sch.meta_data == "":
        raise ContentNoChangeException(detail="Meta data can't be null")
    
    file_path = None

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
    if dokumen is None:
        raise IdNotFoundException(Dokumen, sch.dokumen_id)

    bundledt_obj_current = await crud.bundledt.get_by_bundle_hd_id_and_dokumen_id(bundle_hd_id=bundlehd_obj_current.id, dokumen_id=dokumen.id)
    if not bundledt_obj_current:
        raise ContentNoChangeException(detail=f"Bundle with dokumen {dokumen.name} not exists")
    
    file_name = f'{bundlehd_obj_current.code}-{bundledt_obj_current.code}-{dokumen.name}'

    if dokumen.is_riwayat:
        metadata_dict = json.loads(sch.meta_data.replace("'", "\""))
        key_value = metadata_dict[f'{dokumen.key_riwayat}']

        if key_value is None or key_value == "":
            raise ContentNoChangeException(detail=f"{dokumen.key_riwayat} wajib terisi!")
        
        file_name = f'{bundlehd_obj_current.code}-{bundledt_obj_current.code}-{dokumen.name}-{key_value}'

    if file:
        file_path = await GCStorageService().upload_file_dokumen(file=file, file_name=file_name)
        sch.file_path = file_path

    db_session = db.session

    # Merging Data Dokumen dari Tanda Terima Notaris ke Bundle
    await HelperService().merging_to_bundle(bundle_hd_obj=bundlehd_obj_current,
                            dokumen=dokumen,
                            meta_data=sch.meta_data,
                            db_session=db_session,
                            file_path=file_path,
                            worker_id=current_worker.id)
    
    sch.history_data = HelperService().extract_metadata_for_history(sch.meta_data, current_history=None)

    if dokumen.is_riwayat == True:
        sch.riwayat_data = HelperService().extract_metadata_for_riwayat(meta_data=sch.meta_data, 
                                                                    key_riwayat=dokumen.key_riwayat, 
                                                                    current_riwayat=None, 
                                                                    file_path=file_path, 
                                                                    is_default=True)
    

    obj_updated = await crud.tandaterimanotaris_dt.update(obj_current=obj_current, obj_new=sch, db_session=db_session, with_commit=True, updated_by_id=current_worker.id)

    return create_response(data=obj_updated)

@router.put("/update-riwayat/{id}", response_model=PutResponseBaseSch[TandaTerimaNotarisDtSch])
async def update_riwayat(id:UUID, 
                        sch:RiwayatSch = Depends(RiwayatSch.as_form), 
                        file:UploadFile = None,
                        current_worker:Worker = Depends(crud.worker.get_current_user)):
    
    obj_current = await crud.tandaterimanotaris_dt.get(id=id)
    if not obj_current:
        raise IdNotFoundException(TandaTerimaNotarisDt, id)
    
    tanda_terima_hd = await crud.tandaterimanotaris_hd.get(id=sch.tanda_terima_notaris_hd_id)
    if not tanda_terima_hd:
        raise IdNotFoundException(TandaTerimaNotarisHd, id)
    
    bundlehd_obj_current = tanda_terima_hd.kjb_dt.bundlehd
    if not bundlehd_obj_current:
        raise IdNotFoundException(BundleHd, tanda_terima_hd.kjb_dt.bundle_hd_id)
    
    bundledt_obj_current = await crud.bundledt.get_by_bundle_hd_id_and_dokumen_id(bundle_hd_id=bundlehd_obj_current.id, dokumen_id=obj_current.dokumen_id)
    if not bundledt_obj_current:
        raise ContentNoChangeException(detail="Dokumen yang dimaksud tidak ada dalam bundle")
    
    dokumen = await crud.dokumen.get(id=obj_current.dokumen_id)
    
    db_session = db.session
    # Bundle
    riwayat_data, file_path = await HelperService().update_riwayat(current_riwayat_data=bundledt_obj_current.riwayat_data, 
                                                                   dokumen=dokumen,
                                                                   codedt=bundledt_obj_current.code,
                                                                   codehd=bundlehd_obj_current.code,
                                                                   sch=sch, 
                                                                   file=file,
                                                                   from_notaris=True)
    
    bundledt_obj_updated = bundledt_obj_current
    
    if sch.is_default == True:
        bundledt_obj_updated.file_path = file_path
        bundledt_obj_updated.meta_data = sch.meta_data

    bundledt_obj_updated.riwayat_data = riwayat_data
    
    bundle_dt = await crud.bundledt.update(obj_current=bundledt_obj_current, 
                                           obj_new=bundledt_obj_updated, 
                                           db_session=db_session, 
                                           with_commit=False, 
                                           updated_by_id=current_worker.id)
    if dokumen.is_keyword == True :
            await HelperService().update_bundle_keyword(meta_data=sch.meta_data, 
                                                        bundle_hd_id=bundlehd_obj_current.id, 
                                                        worker_id=current_worker.id, 
                                                        key_field=dokumen.key_field, 
                                                        db_session=db_session)
    #----------
    
    # Tanda Terima Notaris
    riwayat_data, file_path = await HelperService().update_riwayat(current_riwayat_data=obj_current.riwayat_data, 
                                                                   dokumen=dokumen,
                                                                   code=bundledt_obj_current.code,
                                                                   sch=sch, 
                                                                   file=file)
    
    obj_updated = obj_current
    
    if sch.is_default == True:
        obj_updated.file_path = file_path
        obj_updated.meta_data = sch.meta_data

    obj_updated.riwayat_data = riwayat_data

    obj = await crud.tandaterimanotaris_dt.update(obj_current=obj_current, 
                                     obj_new=obj_updated, 
                                     db_session=db_session, 
                                     updated_by_id=current_worker.id)
    #----------
    
    return create_response(data=obj)

@router.put("/delete-riwayat/{id}", response_model=PutResponseBaseSch[TandaTerimaNotarisDtSch])
async def delete_riwayat(id:UUID, 
                        sch:RiwayatSch,
                        current_worker:Worker = Depends(crud.worker.get_current_user)):
    
    obj_current = await crud.tandaterimanotaris_dt.get(id=id)
    if not obj_current:
        raise IdNotFoundException(TandaTerimaNotarisDt, id)
    
    tanda_terima_hd = await crud.tandaterimanotaris_hd.get(id=sch.tanda_terima_notaris_hd_id)
    if not tanda_terima_hd:
        raise IdNotFoundException(TandaTerimaNotarisHd, id)
    
    bundlehd_obj_current = tanda_terima_hd.kjb_dt.bundlehd
    if not bundlehd_obj_current:
        raise IdNotFoundException(BundleHd, tanda_terima_hd.kjb_dt.bundle_hd_id)
    
    bundledt_obj_current = await crud.bundledt.get_by_bundle_hd_id_and_dokumen_id(bundle_hd_id=bundlehd_obj_current.id, dokumen_id=obj_current.dokumen_id)
    if not bundledt_obj_current:
        raise ContentNoChangeException(detail="Dokumen yang dimaksud tidak ada dalam bundle")
    
    # Bundle
    bundle_riwayat_data = json.loads(bundledt_obj_current.riwayat_data.replace("'", "\""))

    bundle_riwayat_data["riwayat"] = [item for item in bundle_riwayat_data["riwayat"] if item["key_value"] != sch.key_value]

    bundledt_obj_updated = bundledt_obj_current

    if len(bundle_riwayat_data["riwayat"]) > 0:
        if sch.is_default == True:
            bundle_obj_riwayat = bundle_riwayat_data["riwayat"][0]
            bundle_obj_riwayat["is_default"] = True
            bundledt_obj_updated.file_path = str(bundle_obj_riwayat["file_path"])
            bundledt_obj_updated.meta_data = str(bundle_obj_riwayat["meta_data"])

        bundle_riwayat_data = json.dumps(bundle_riwayat_data)
        bundledt_obj_updated.riwayat_data = str(bundle_riwayat_data).replace('None', 'null').replace('"', "'")
    else:
        bundledt_obj_updated.file_path = None
        bundledt_obj_updated.meta_data = None
        bundledt_obj_updated.riwayat_data = None
    
    obj = await crud.bundledt.update(obj_current=bundledt_obj_current, obj_new=bundledt_obj_updated, updated_by_id=current_worker.id, with_commit=False)
    #------------------------

    # Tanda Terima Notaris
    riwayat_data = json.loads(obj_current.riwayat_data.replace("'", "\""))

    riwayat_data["riwayat"] = [item for item in riwayat_data["riwayat"] if item["key_value"] != sch.key_value]

    obj_updated = obj_current

    if len(riwayat_data["riwayat"]) > 0:
        if sch.is_default == True:
            obj_riwayat = riwayat_data["riwayat"][0]
            obj_riwayat["is_default"] = True
            obj_updated.file_path = str(obj_riwayat["file_path"])
            obj_updated.meta_data = str(obj_riwayat["meta_data"])

        riwayat_data = json.dumps(riwayat_data)
        obj_updated.riwayat_data = str(riwayat_data).replace('None', 'null').replace('"', "'")
    else:
        obj_updated.file_path = None
        obj_updated.meta_data = None
        obj_updated.riwayat_data = None
    
    obj = await crud.tandaterimanotaris_dt.update(obj_current=obj_current, obj_new=obj_updated, updated_by_id=current_worker.id)
    #------------------------

    return create_response(data=obj)

@router.get("/download-file/{id}")
async def download_file(
                    id:UUID,
                    current_worker:Worker = Depends(crud.worker.get_active_worker)):
    """Download File Dokumen"""

    obj_current = await crud.tandaterimanotaris_dt.get(id=id)
    if not obj_current:
        raise IdNotFoundException(BundleDt, id)
    
    bundlehd_obj_current = obj_current.kjb_dt.bundlehd
    if not bundlehd_obj_current:
        raise IdNotFoundException(BundleHd, obj_current.kjb_dt.bundle_hd_id)                                                                        
    
    dokumen = await crud.dokumen.get(id=obj_current.dokumen_id)
    if dokumen is None:
        raise IdNotFoundException(Dokumen, obj_current.dokumen_id)
    
    bundledt_obj_current = await crud.bundledt.get_by_bundle_hd_id_and_dokumen_id(bundle_hd_id=bundlehd_obj_current.id, dokumen_id=dokumen.id)
    if not bundledt_obj_current:
        raise ContentNoChangeException(detail=f"Bundle with dokumen {dokumen.name} not exists")
    
    file_name = f'{bundlehd_obj_current.code}-{bundledt_obj_current.code}-{dokumen.name}'

    if dokumen.is_riwayat:
        metadata_dict = json.loads(obj_current.meta_data.replace("'", "\""))
        key_value = metadata_dict[f'{dokumen.key_riwayat}']

        if key_value is None or key_value == "":
            raise ContentNoChangeException(detail=f"{dokumen.key_riwayat} wajib terisi!")
        
        file_name = f'{bundlehd_obj_current.code}-{bundledt_obj_current.code}-{dokumen.name}-{key_value}'

    try:
        file_bytes = await GCStorageService().download_dokumen(file_path=obj_current.file_path)
    except Exception as e:
        raise DocumentFileNotFoundException(dokumenname=obj_current.dokumen_name)
    
    ext = obj_current.file_path.split('.')[-1]

    # return FileResponse(file, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={obj_current.id}.{ext}"})
    response = Response(content=file_bytes, media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename={file_name}.{ext}"
    return response

@router.get("/download-file/riwayat/{id}")
async def download_file_riwayat(id:UUID,
                        key_value:str):
    
    """Download File Dokumen Riwayat"""

    obj_current = await crud.tandaterimanotaris_dt.get(id=id)
    if not obj_current:
        raise IdNotFoundException(TandaTerimaNotarisDt, id)
    
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
    response.headers["Content-Disposition"] = f"attachment; filename={obj_current.tanda_terima_notaris_hd.nomor_tanda_terima}-{key_value}-{obj_current.dokumen_name}.{ext}"
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


   