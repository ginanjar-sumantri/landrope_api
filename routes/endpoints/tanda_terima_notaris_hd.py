from uuid import UUID
from fastapi import APIRouter, status, Depends, UploadFile, Response, HTTPException, BackgroundTasks
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, or_, func
from sqlmodel.ext.asyncio.session import AsyncSession
from models.tanda_terima_notaris_model import TandaTerimaNotarisHd
from models.kjb_model import KjbDt
from models.worker_model import Worker
from models.notaris_model import Notaris
from models import BundleHd
from schemas.tanda_terima_notaris_hd_sch import (TandaTerimaNotarisHdSch, TandaTerimaNotarisHdCreateSch, TandaTerimaNotarisHdUpdateSch)
from schemas.bundle_hd_sch import BundleHdCreateSch
from schemas.kjb_dt_sch import KjbDtUpdateSch, KjbDtListSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ContentNoChangeException, 
                               ImportFailedException, DocumentFileNotFoundException)
from common.enum import StatusPetaLokasiEnum
from services.gcloud_storage_service import GCStorageService
from services.helper_service import HelperService, BundleHelper
from typing import Dict, Any
import uuid
import crud
import json


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[TandaTerimaNotarisHdSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: TandaTerimaNotarisHdCreateSch=Depends(TandaTerimaNotarisHdCreateSch.as_form), 
            file:UploadFile = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    kjb_dt = await crud.kjb_dt.get_by_id(id=sch.kjb_dt_id)

    if not kjb_dt:
        raise IdNotFoundException(KjbDt, sch.kjb_dt_id)
    
    if kjb_dt.status_peta_lokasi is not None:
        if kjb_dt.status_peta_lokasi != sch.status_peta_lokasi:
            raise ContentNoChangeException(detail=f"""status peta lokasi tidak dapat berubah dari 
                                           {str(kjb_dt.status_peta_lokasi)} ke {str(sch.status_peta_lokasi)}""")

    db_session = db.session

    if file:
        file_path = await GCStorageService().upload_file_dokumen(file=file, file_name=f'TTN-{uuid.uuid4().hex}')
        sch.file_path = file_path
    
    kjb_dt_update = KjbDtUpdateSch.from_orm(kjb_dt)

    bundle:BundleHd = None
    ## if kjb detail is not match with bundle, then match bundle with kjb detail
    if kjb_dt.bundle_hd_id is None and sch.status_peta_lokasi == StatusPetaLokasiEnum.Lanjut_Peta_Lokasi :
        ## Match bundle with kjb detail by alashak
        ## When bundle not exists create new bundle and match id bundle to kjb detail
        ## When bundle exists match match id bundle to kjb detail
        
        bundle = await crud.bundlehd.get_by_keyword(keyword=kjb_dt.alashak)
        if bundle is None:
            planing = await crud.planing.get_by_project_id_desa_id(project_id=sch.project_id, desa_id=sch.desa_id)
            if planing:
                planing_id = planing.id
            else:
                planing_id = None

            bundle_sch = BundleHdCreateSch(planing_id=planing_id, keyword=kjb_dt.alashak)
            bundle = await crud.bundlehd.create_and_generate(obj_in=bundle_sch)
            # bundle = await crud.bundlehd.get_by_id(id=bundle.id)
        
        kjb_dt_update.bundle_hd_id = bundle.id
        bundle = await crud.bundlehd.get_by_id(id=bundle.id)
    else:
        bundle = await crud.bundlehd.get_by_id(id=kjb_dt.bundle_hd_id)

    kjb_dt_update.luas_surat_by_ttn = sch.luas_surat if sch.luas_surat != None else kjb_dt_update.luas_surat
    kjb_dt_update.desa_by_ttn_id = sch.desa_id if sch.desa_id != None else kjb_dt_update.desa_by_ttn_id
    kjb_dt_update.project_by_ttn_id = sch.project_id if sch.project_id != None else kjb_dt_update.project_by_ttn_id
    kjb_dt_update.status_peta_lokasi = sch.status_peta_lokasi if sch.status_peta_lokasi != None else kjb_dt_update.status_peta_lokasi
    kjb_dt_update.pemilik_id = sch.pemilik_id if sch.pemilik_id != None else kjb_dt_update.pemilik_id
    kjb_dt_update.group = sch.group if sch.group != None else kjb_dt_update.group

    if bundle:
        #update bundle alashak & penjual for default if metadata not exists
        await BundleHelper().merge_alashak(bundle=bundle, alashak=kjb_dt.alashak, worker_id=current_worker.id, db_session=db_session)
        await BundleHelper().merge_kesepakatan_jual_beli(bundle=bundle, worker_id=current_worker.id, kjb_dt_id=kjb_dt.id, db_session=db_session, pemilik_id=kjb_dt_update.pemilik_id)
        await BundleHelper().merge_tanda_terima_notaris(bundle=bundle, nomor_ttn=sch.nomor_tanda_terima, tanggal=sch.tanggal_tanda_terima, file_path=sch.file_path, worker_id=current_worker.id, db_session=db_session)

    await crud.kjb_dt.update(obj_current=kjb_dt, obj_new=kjb_dt_update, db_session=db_session, with_commit=False)
    new_obj = await crud.tandaterimanotaris_hd.create(obj_in=sch, db_session=db_session, with_commit=True, created_by_id=current_worker.id)
    new_obj = await crud.tandaterimanotaris_hd.get_by_id(id=new_obj.id)

    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[TandaTerimaNotarisHdSch])
async def get_list(
                params: Params = Depends(), 
                order_by:str = None, 
                keyword:str = None, 
                filter_query:str = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(TandaTerimaNotarisHd).select_from(TandaTerimaNotarisHd
                                        ).outerjoin(KjbDt, TandaTerimaNotarisHd.kjb_dt_id == KjbDt.id
                                        ).outerjoin(Notaris, TandaTerimaNotarisHd.notaris_id == Notaris.id)
    
    if keyword:
        query = query.filter(
            or_(
                TandaTerimaNotarisHd.nomor_tanda_terima.ilike(f'%{keyword}%'),
                KjbDt.alashak.ilike(f'%{keyword}%'),
                Notaris.name.ilike(f'%{keyword}%'),
                func.replace(TandaTerimaNotarisHd.status_peta_lokasi, '_', ' ').ilike(f'%{keyword}%')
            )
        )
    
    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
                query = query.where(getattr(TandaTerimaNotarisHd, key) == value)
    
    query = query.distinct()

    objs = await crud.tandaterimanotaris_hd.get_multi_paginated_ordered(params=params, query=query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[TandaTerimaNotarisHdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.tandaterimanotaris_hd.get_by_id(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(TandaTerimaNotarisHd, id)

@router.put("/{id}", response_model=PutResponseBaseSch[TandaTerimaNotarisHdSch])
async def update(id:UUID, 
                 sch:TandaTerimaNotarisHdUpdateSch = Depends(TandaTerimaNotarisHdUpdateSch.as_form),
                 file:UploadFile = None,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.tandaterimanotaris_hd.get(id=id)

    if not obj_current:
        raise IdNotFoundException(TandaTerimaNotarisHd, id)
    
    kjb_dt = await crud.kjb_dt.get_by_id(id=sch.kjb_dt_id)

    if not kjb_dt:
        raise IdNotFoundException(KjbDt, sch.kjb_dt_id)
    
    if file:
        file_path = await GCStorageService().upload_file_dokumen(file=file, file_name=f'TTN-{uuid.uuid4().hex}')
        sch.file_path = file_path
    else:
        sch.file_path = obj_current.file_path
    
    db_session = db.session
    obj_updated = await crud.tandaterimanotaris_hd.update(obj_current=obj_current, obj_new=sch, db_session=db_session, with_commit=False, updated_by_id=current_worker.id)
    
    kjb_dt_update = KjbDtUpdateSch.from_orm(kjb_dt)
    ## if kjb detail is not match with bundle, then match bundle with kjb detail
    bundle:BundleHd = None
    if kjb_dt.bundle_hd_id is None :
        ## Match bundle with kjb detail by alashak
        ## When bundle not exists create new bundle and match id bundle to kjb detail
        ## When bundle exists match match id bundle to kjb detail
        
        bundle = await crud.bundlehd.get_by_keyword(keyword=kjb_dt.alashak)
        if bundle is None:
            planing = await crud.planing.get_by_project_id_desa_id(project_id=sch.project_id, desa_id=sch.desa_id)
            if planing:
                planing_id = planing.id
            else:
                planing_id = None

            bundle_sch = BundleHdCreateSch(planing_id=planing_id, keyword=kjb_dt.alashak)
            bundle = await crud.bundlehd.create_and_generate(obj_in=bundle_sch)

        kjb_dt_update.bundle_hd_id = bundle.id
        bundle = await crud.bundlehd.get_by_id(id=bundle.id)
    else:
        bundle = await crud.bundlehd.get_by_id(id=kjb_dt.bundle_hd_id)

    kjb_dt_update.luas_surat_by_ttn = sch.luas_surat if sch.luas_surat != None else kjb_dt_update.luas_surat
    kjb_dt_update.desa_by_ttn_id = sch.desa_id if sch.desa_id != None else kjb_dt_update.desa_by_ttn_id
    kjb_dt_update.project_by_ttn_id = sch.project_id if sch.project_id != None else kjb_dt_update.project_by_ttn_id
    kjb_dt_update.status_peta_lokasi = sch.status_peta_lokasi if sch.status_peta_lokasi != None else kjb_dt_update.status_peta_lokasi
    kjb_dt_update.pemilik_id = sch.pemilik_id if sch.pemilik_id != None else kjb_dt_update.pemilik_id
    kjb_dt_update.group = sch.group if sch.group != None else kjb_dt_update.group

    if bundle:
        #update bundle alashak & penjual for default if metadata not exists
        await BundleHelper().merge_alashak(bundle=bundle, alashak=kjb_dt.alashak, worker_id=current_worker.id, db_session=db_session)
        await BundleHelper().merge_kesepakatan_jual_beli(bundle=bundle, worker_id=current_worker.id, kjb_dt_id=kjb_dt.id, db_session=db_session, pemilik_id=kjb_dt_update.pemilik_id)
        await BundleHelper().merge_tanda_terima_notaris(bundle=bundle, nomor_ttn=sch.nomor_tanda_terima, tanggal=sch.tanggal_tanda_terima, file_path=sch.file_path, worker_id=current_worker.id, db_session=db_session)

    await crud.kjb_dt.update(obj_current=kjb_dt, obj_new=kjb_dt_update, db_session=db_session)

    obj_updated = await crud.tandaterimanotaris_hd.get_by_id(id=obj_updated.id)

    return create_response(data=obj_updated)

@router.get("/download-file/{id}")
async def download_file(
                    id:UUID,
                    current_worker:Worker = Depends(crud.worker.get_active_worker)):
    """Download File Dokumen"""

    obj_current = await crud.tandaterimanotaris_hd.get(id=id)
    if not obj_current:
        raise IdNotFoundException(TandaTerimaNotarisHd, id)
    if obj_current.file_path is None:
        raise DocumentFileNotFoundException(dokumenname=obj_current.nomor_tanda_terima)
    try:
        file_bytes = await GCStorageService().download_dokumen(file_path=obj_current.file_path)
    except Exception as e:
        raise DocumentFileNotFoundException(dokumenname=obj_current.nomor_tanda_terima)
    
    ext = obj_current.file_path.split('.')[-1]

    # return FileResponse(file, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={obj_current.id}.{ext}"})
    response = Response(content=file_bytes, media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename={obj_current.nomor_tanda_terima}-{obj_current.tanggal_tanda_terima}.{ext}"
    return response