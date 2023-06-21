from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from models.tanda_terima_notaris_model import TandaTerimaNotarisHd
from models.kjb_model import KjbDt
from schemas.tanda_terima_notaris_hd_sch import (TandaTerimaNotarisHdSch, TandaTerimaNotarisHdCreateSch, TandaTerimaNotarisHdUpdateSch)
from schemas.bundle_hd_sch import BundleHdCreateSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.generator import generate_code
from models.code_counter_model import CodeCounterEnum
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[TandaTerimaNotarisHdSch], status_code=status.HTTP_201_CREATED)
async def create(sch: TandaTerimaNotarisHdCreateSch):
    
    """Create a new object"""

    kjb_dt = await crud.kjb_dt.get(id=sch.kjb_dt_id)

    if kjb_dt is None :
        raise IdNotFoundException(KjbDt, sch.kjb_dt_id)
        
    new_obj = await crud.tandaterimanotaris_hd.create(obj_in=sch)

    ## if kjb detail is not match with bundle, then match bundle with kjb detail
    if kjb_dt.bundle_hd_id is None :
        ## Match bundle with kjb detail by alashak
        ## When bundle not exists create new bundle and match id bundle to kjb detail
        ## When bundle exists match match id bundle to kjb detail
        
        bundle = await crud.bundlehd.get_by_keyword(keyword=kjb_dt.alashak)
        if bundle is None:
            bundle_sch = BundleHdCreateSch(planing_id=sch.planing_id)
            bundle = await crud.bundlehd.create_and_generate(obj_in=bundle_sch)
        
        kjb_dt_update = kjb_dt
        kjb_dt_update.bundle_hd_id = bundle.id
        kjb_dt_update.luas_surat_by_ttn = new_obj.luas_surat
        kjb_dt_update.planing_by_ttn_id = new_obj.planing_id

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
    
    obj_updated = await crud.tandaterimanotaris_hd.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)


   