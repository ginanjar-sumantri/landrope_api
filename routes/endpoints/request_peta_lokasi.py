from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from models.request_peta_lokasi_model import RequestPetaLokasi
from models.kjb_model import KjbDt
from schemas.request_peta_lokasi_sch import (RequestPetaLokasiSch, RequestPetaLokasiHdSch, 
                                             RequestPetaLokasiCreateSch, RequestPetaLokasiCreatesSch, 
                                             RequestPetaLokasiUpdateSch, RequestPetaLokasiUpdateExtSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from datetime import datetime
import crud
import string
import random


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[RequestPetaLokasiSch], status_code=status.HTTP_201_CREATED)
async def create(sch: RequestPetaLokasiCreateSch):
    
    """Create a new object"""
        
    new_obj = await crud.request_peta_lokasi.create(obj_in=sch)
    
    return create_response(data=new_obj)

@router.post("/creates")
async def creates(sch: RequestPetaLokasiCreatesSch):

    datas = []
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    current_datetime = datetime.now()
    for id in sch.kjb_dt_ids:
        kjb_dt = await crud.kjb_dt.get(id=id)

        if kjb_dt is None:
            raise IdNotFoundException(KjbDt, id)
        
        data = RequestPetaLokasi(code=code,
                                 kjb_dt_id=id,
                                 remark=sch.remark,
                                 tanggal=sch.tanggal,
                                 created_at=current_datetime,
                                 updated_at=current_datetime)
        datas.append(data)
    
    if len(datas) > 0:
        objs = await crud.request_peta_lokasi.create_all(obj_ins=datas)

    return {"result" : status.HTTP_200_OK, "message" : "Data created correctly"}

@router.get("/header", response_model=GetResponsePaginatedSch[RequestPetaLokasiHdSch])
async def get_list_header(params: Params=Depends(), keyword:str = None):
    
    """Gets a paginated list objects"""

    objs = await crud.request_peta_lokasi.get_multi_paginated(params=params, keyword=keyword)
    return create_response(data=objs)

@router.get("", response_model=GetResponsePaginatedSch[RequestPetaLokasiSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.request_peta_lokasi.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query, join=True)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[RequestPetaLokasiSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.request_peta_lokasi.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(RequestPetaLokasi, id)

@router.put("/{id}", response_model=PutResponseBaseSch[RequestPetaLokasiSch])
async def update(sch:RequestPetaLokasiUpdateExtSch):
    
    """Update a obj by its id"""

    obj_currents = await crud.request_peta_lokasi.get_all_by_code(code=sch.code)

    for i in obj_currents:
        if i.kjb_dt_id not in sch.kjb_dt_ids:
            await crud.request_peta_lokasi.remove(id=i.kjb_dt_id)
    
    for j in sch.kjb_dt_ids:
        if j not in obj_currents["id"]:
            new_obj = RequestPetaLokasi(code=sch.code,
                                 kjb_dt_id=j,
                                 remark=sch.remark,
                                 tanggal=sch.tanggal)
            await crud.request_peta_lokasi.create(obj_in=new_obj)
        else:
            obj_current = next((x for x in obj_currents if x.kjb_dt_id == j), None)
            obj_updated = RequestPetaLokasiUpdateSch(code=sch.code,
                                                     tanggal=sch.tanggal,
                                                     remark=sch.remark,
                                                     kjb_dt_id=j)
            
            await crud.request_peta_lokasi.update(obj_current=obj_current, obj_new=obj_updated)

    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[RequestPetaLokasiSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID):
    
    """Delete a object"""

    obj_current = await crud.request_peta_lokasi.get(id=id)
    if not obj_current:
        raise IdNotFoundException(RequestPetaLokasi, id)
    
    obj_deleted = await crud.request_peta_lokasi.remove(id=id)

    return obj_deleted

   