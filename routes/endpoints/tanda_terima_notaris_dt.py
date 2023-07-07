from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from models.bundle_model import BundleHd, BundleDt
from models.tanda_terima_notaris_model import TandaTerimaNotarisDt, TandaTerimaNotarisHd
from schemas.tanda_terima_notaris_dt_sch import (TandaTerimaNotarisDtSch, TandaTerimaNotarisDtCreateSch, TandaTerimaNotarisDtUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.generator import generate_code
from models.code_counter_model import CodeCounterEnum
import crud
import json


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[TandaTerimaNotarisDtSch], status_code=status.HTTP_201_CREATED)
async def create(sch: TandaTerimaNotarisDtCreateSch):
    
    """Create a new object"""

    tanda_terima_hd = await crud.tandaterimanotaris_hd.get(id=sch.tanda_terima_notaris_hd_id)
    if not tanda_terima_hd:
        raise IdNotFoundException(TandaTerimaNotarisHd, id)
    
    bundlehd_obj_current = tanda_terima_hd.kjb_dt.bundlehd
    if not bundlehd_obj_current:
        raise IdNotFoundException(BundleHd, tanda_terima_hd.kjb_dt.bundle_hd_id)
    
    dokumen = await crud.dokumen.get(id=sch.dokumen_id)

    bundledt_obj_current = next((x for x in bundlehd_obj_current.bundledts if x.dokumen_id == sch.dokumen_id and x.bundle_hd_id == bundlehd_obj_current.id), None)
    if bundledt_obj_current is None:
        code = bundlehd_obj_current.code + dokumen.code
        new_dokumen = BundleDt(code=code, dokumen_id=dokumen.id, meta_data=sch.meta_data, bundle_hd_id=bundlehd_obj_current.id)

        bundledt_obj_current = await crud.bundledt.create(obj_in=new_dokumen)
    else:
        bundledt_obj_updated = bundledt_obj_current
        bundledt_obj_updated.meta_data = sch.meta_data

        await crud.bundledt.update(obj_current=bundledt_obj_current, obj_new=bundledt_obj_updated)
    
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
                await crud.bundlehd.update(obj_current=bundlehd_obj_current, obj_new=edit_keyword_hd)

    new_obj = await crud.tandaterimanotaris_dt.create(obj_in=sch)
    
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
async def update(id:UUID, sch:TandaTerimaNotarisDtUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.tandaterimanotaris_dt.get(id=id)

    if not obj_current:
        raise IdNotFoundException(TandaTerimaNotarisDt, id)
    
    obj_updated = await crud.tandaterimanotaris_dt.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)


   