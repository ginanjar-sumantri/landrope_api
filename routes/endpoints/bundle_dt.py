from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from models.bundle_model import BundleDt
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
    
    dokumen = await crud.dokumen.is_dokumen_for_keyword(id=sch.dokumen_id)
    
    #updated bundle header keyword when dokumen metadata is_keyword true
    if dokumen:
        metadata = sch.meta_data.replace("'",'"')
        obj_json = json.loads(metadata)
        current_bundle_hd = await crud.bundlehd.get(id=sch.bundle_hd_id)

        # values = []
        # for data in obj_json['history']:
        #     value = data['meta_data'][f'{dokumen.key_field}']
        #     values.append(value)

        metadata_keyword = obj_json[f'{dokumen.key_field}']

        if metadata_keyword not in current_bundle_hd.keyword:
            
            edit_keyword_hd = current_bundle_hd
            if current_bundle_hd.keyword is None or current_bundle_hd.keyword == "":
                edit_keyword_hd.keyword = metadata_keyword
            else:
                edit_keyword_hd.keyword = f"{current_bundle_hd.keyword},{metadata_keyword}"
                await crud.bundlehd.update(obj_current=current_bundle_hd, obj_new=edit_keyword_hd)
        
    obj_updated = await crud.bundledt.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

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

#     return values            

def is_datetimecheck(value):
    is_datetime = False

    try:
        datetime.strptime(str(value), "%Y-%m-%dT%H:%M:%S.%f")
        is_datetime = True
    except ValueError:
        pass

    return is_datetime