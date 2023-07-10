from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from models.tanda_terima_notaris_model import TandaTerimaNotarisHd
from models.kjb_model import KjbDt
from schemas.tanda_terima_notaris_hd_sch import (TandaTerimaNotarisHdSch, TandaTerimaNotarisHdCreateSch, TandaTerimaNotarisHdUpdateSch)
from schemas.bundle_hd_sch import BundleHdCreateSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ContentNoChangeException, ImportFailedException)
from common.generator import generate_code
from models.code_counter_model import CodeCounterEnum
from common.enum import StatusPetaLokasiEnum
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[TandaTerimaNotarisHdSch], status_code=status.HTTP_201_CREATED)
async def create(sch: TandaTerimaNotarisHdCreateSch):
    
    """Create a new object"""

    kjb_dt = await crud.kjb_dt.get(id=sch.kjb_dt_id)

    if not kjb_dt:
        raise IdNotFoundException(KjbDt, sch.kjb_dt_id)
    
    if kjb_dt.status_peta_lokasi is not None:
        if kjb_dt.status_peta_lokasi != sch.status_peta_lokasi:
            raise ContentNoChangeException(detail=f"""status peta lokasi tidak dapat berubah dari 
                                           {str(kjb_dt.status_peta_lokasi)} ke {str(sch.status_peta_lokasi)}""")
        
    new_obj = await crud.tandaterimanotaris_hd.create(obj_in=sch)

    if sch.status_peta_lokasi is not StatusPetaLokasiEnum.Lanjut_Peta_Lokasi:
        return create_response(data=new_obj)
    
    kjb_dt_update = kjb_dt

    
    ## if kjb detail is not match with bundle, then match bundle with kjb detail
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

            bundle_sch = BundleHdCreateSch(planing_id=planing_id)
            bundle = await crud.bundlehd.create_and_generate(obj_in=bundle_sch)
        
        kjb_dt_update.bundle_hd_id = bundle.id
    
    kjb_dt_update.luas_surat_by_ttn = new_obj.luas_surat
    kjb_dt_update.desa_by_ttn_id = new_obj.desa_id
    kjb_dt_update.project_by_ttn_id = new_obj.project_id
    kjb_dt_update.status_peta_lokasi = sch.status_peta_lokasi
    kjb_dt_update.pemilik_id = new_obj.pemilik_id

    await crud.kjb_dt.update(obj_current=kjb_dt, obj_new=kjb_dt_update)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[TandaTerimaNotarisHdSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.tandaterimanotaris_hd.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[TandaTerimaNotarisHdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.tandaterimanotaris_hd.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(TandaTerimaNotarisHd, id)

@router.put("/{id}", response_model=PutResponseBaseSch[TandaTerimaNotarisHdSch])
async def update(id:UUID, sch:TandaTerimaNotarisHdUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.tandaterimanotaris_hd.get(id=id)

    if not obj_current:
        raise IdNotFoundException(TandaTerimaNotarisHd, id)
    
    kjb_dt = await crud.kjb_dt.get(id=sch.kjb_dt_id)

    if not kjb_dt:
        raise IdNotFoundException(KjbDt, sch.kjb_dt_id)
    
    obj_updated = await crud.tandaterimanotaris_hd.update(obj_current=obj_current, obj_new=sch)

    if kjb_dt.status_peta_lokasi is not StatusPetaLokasiEnum.Lanjut_Peta_Lokasi:
        return create_response(data=obj_updated)
    
    kjb_dt_update = kjb_dt
    ## if kjb detail is not match with bundle, then match bundle with kjb detail
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

            bundle_sch = BundleHdCreateSch(planing_id=planing_id)
            bundle = await crud.bundlehd.create_and_generate(obj_in=bundle_sch)

        kjb_dt_update.bundle_hd_id = bundle.id
    
    kjb_dt_update.luas_surat_by_ttn = obj_updated.luas_surat
    kjb_dt_update.desa_by_ttn_id = obj_updated.desa_id
    kjb_dt_update.project_by_ttn_id = obj_updated.project_id
    kjb_dt_update.status_peta_lokasi = sch.status_peta_lokasi
    kjb_dt_update.pemilik_id = obj_updated.pemilik_id

    await crud.kjb_dt.update(obj_current=kjb_dt, obj_new=kjb_dt_update)

    return create_response(data=obj_updated)


   