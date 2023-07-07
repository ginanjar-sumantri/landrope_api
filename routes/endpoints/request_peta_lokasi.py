from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from models.request_peta_lokasi_model import RequestPetaLokasi
from models.kjb_model import KjbDt
from schemas.request_peta_lokasi_sch import (RequestPetaLokasiSch, RequestPetaLokasiCreateSch, RequestPetaLokasiCreatesSch, RequestPetaLokasiUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from datetime import datetime
import crud


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[RequestPetaLokasiSch], status_code=status.HTTP_201_CREATED)
async def create(sch: RequestPetaLokasiCreateSch):
    
    """Create a new object"""
        
    new_obj = await crud.request_peta_lokasi.create(obj_in=sch)
    
    return create_response(data=new_obj)

@router.post("")
async def creates(sch: RequestPetaLokasiCreatesSch):

    datas = []
    code = ""
    current_datetime = datetime.now()
    for id in sch.kjb_dt_ids:
        kjb_dt = await crud.kjb_dt.get(id=id)

        if kjb_dt is None:
            raise IdNotFoundException(KjbDt, id)
        
        data = RequestPetaLokasi(kjb_dt_id=id,
                                 remark=sch.remark,
                                 tanggal=current_datetime,
                                 created_at=current_datetime,
                                 updated_at=current_datetime)
        datas.append(data)
    
    if len(datas) > 0:
        objs = await crud.request_peta_lokasi.create_all(obj_ins=datas)

    return {"result" : status.HTTP_200_OK, "message" : "Data created correctly"}

        

@router.get("", response_model=GetResponsePaginatedSch[RequestPetaLokasiSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.request_peta_lokasi.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
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
async def update(id:UUID, sch:RequestPetaLokasiUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.request_peta_lokasi.get(id=id)

    if not obj_current:
        raise IdNotFoundException(RequestPetaLokasi, id)
    
    obj_updated = await crud.request_peta_lokasi.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[RequestPetaLokasiSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID):
    
    """Delete a object"""

    obj_current = await crud.request_peta_lokasi.get(id=id)
    if not obj_current:
        raise IdNotFoundException(RequestPetaLokasi, id)
    
    obj_deleted = await crud.request_peta_lokasi.remove(id=id)

    return obj_deleted

   