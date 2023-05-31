from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from models.dokumen_model import BundleDt
from schemas.bundle_dt_sch import (BundleDtSch, BundleDtUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.generator import generate_code
from models.code_counter_model import CodeCounterEnum
from datetime import datetime
import crud
import json

router = APIRouter()

@router.get("", response_model=GetResponsePaginatedSch[BundleDtSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.bundledt.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
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
async def update(id:UUID, sch:BundleDtUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.bundledt.get(id=id)

    if not obj_current:
        raise IdNotFoundException(BundleDt, id)
    
    dokumen = await crud.dokumen.is_dokumen_for_keyword(id=sch.dokumen_id)
    
    #updated keyword when dokumen metadata is keyword header
    if dokumen:
        metadata = sch.meta_data.replace("'",'"')
        obj_json = json.loads(metadata)
        current_bundle_hd = await crud.bundlehd.get(id=sch.bundle_hd_id)
        values = []
        for item in obj_json:
            for field in item['field']:
                value = str(field['value'])
                if value in (current_bundle_hd.keyword or ""):
                    continue

                is_datetime = is_datetimecheck(value=value)
                if type(field['value']).__name__ in ["str", "string"] and is_datetime == False:
                    values.append(str(value))
        
        edit_keyword_hd = current_bundle_hd
        edit_keyword_hd.keyword = ','.join(values) if current_bundle_hd.keyword is None else f"{current_bundle_hd.keyword},{','.join(values)}"

        await crud.bundlehd.update(obj_current=current_bundle_hd, obj_new=edit_keyword_hd)
    
    obj_updated = await crud.bundledt.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

# @router.get("/get/json")
# async def extract_json():
#     str_json ="""[{
# 		"tanggal":"2023-05-22T08:06:46.572436",
# 		"field":[{"key":"Nomor","value":"1234"},{"key":"Tanggal","value":"2023-05-22T08:06:46.572436"}]
# 	},
# 	{
# 		"tanggal":"2023-05-22T08:06:46.572436",
# 		"field":[{"key":"Nomor","value":1122},{"key":"Tanggal","value":"2023-05-22T08:06:46.572436"}]
# 	}]"""

#     obj_json = json.loads(str_json)
#     values = []
#     for item in obj_json:
#         for field in item['field']:
#             value = field['value']
#             is_datetime = is_datetimecheck(value=value)
#             if type(field['value']).__name__ in ["str", "string"] and is_datetime == False:
#                 values.append(str(value))

#     return values            

def is_datetimecheck(value):
    is_datetime = False

    try:
        datetime.strptime(str(value), "%Y-%m-%dT%H:%M:%S.%f")
        is_datetime = True
    except ValueError:
        pass

    return is_datetime