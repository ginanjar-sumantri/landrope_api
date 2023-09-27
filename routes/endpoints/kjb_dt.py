from uuid import UUID
from fastapi import APIRouter, status, Depends, HTTPException
from fastapi_pagination import Params
from sqlmodel import select, or_, and_
from models.kjb_model import KjbDt, KjbHd
from models.request_peta_lokasi_model import RequestPetaLokasi
from models.worker_model import Worker
from schemas.kjb_dt_sch import (KjbDtSch, KjbDtCreateSch, KjbDtUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.enum import StatusPetaLokasiEnum
import crud
import json


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[KjbDtSch], status_code=status.HTTP_201_CREATED)
async def create(sch: KjbDtCreateSch,
                 current_worker:Worker = Depends(crud.worker.get_current_user)):
    
    """Create a new object"""

    alashak = await crud.kjb_dt.get_by_alashak(alashak=sch.alashak)
    if alashak:
        raise HTTPException(status_code=409, detail=f"alashak {sch.alashak} ada di KJB lain ({alashak.kjb_code})")
        
    new_obj = await crud.kjb_dt.create(obj_in=sch, created_by_id=current_worker.id)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[KjbDtSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(KjbDt).select_from(KjbDt
                    ).join(KjbHd, KjbHd.id == KjbDt.kjb_hd_id)
    
    if keyword:
        query = query.filter(
            or_(
                KjbDt.alashak.ilike(f'%{keyword}%'),
                KjbHd.code.ilike(f'%{keyword}%')
            )
        )

    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
                query = query.where(getattr(KjbDt, key) == value)

    objs = await crud.kjb_dt.get_multi_paginated(params=params, query=query)
    return create_response(data=objs)

@router.get("/tanda-terima/notaris", response_model=GetResponsePaginatedSch[KjbDtSch])
async def get_list(
                params: Params=Depends(),
                keyword: str = None):
    
    """Gets a paginated list objects"""
    query = select(KjbDt)

    query = query.select_from(KjbDt
                                     ).outerjoin(RequestPetaLokasi, KjbDt.id == RequestPetaLokasi.kjb_dt_id
                                                 ).where(KjbDt.request_peta_lokasi == None)
    
    if keyword and keyword != "":
        query = query.filter(
                KjbDt.alashak.contains(keyword)
        )

    objs = await crud.kjb_dt.get_multi_paginated(params=params, query=query)
    return create_response(data=objs)

@router.get("/request/petlok", response_model=GetResponsePaginatedSch[KjbDtSch])
async def get_list_for_petlok(kjb_hd_id:UUID | None, no_order:str | None = None, params: Params=Depends()):
    
    """Gets a paginated list objects"""

    query = select(KjbDt
                       ).select_from(KjbDt
                                     ).outerjoin(RequestPetaLokasi, KjbDt.id == RequestPetaLokasi.kjb_dt_id
                                     ).where(and_(
                                                    KjbDt.kjb_hd_id == kjb_hd_id,
                                                    KjbDt.status_peta_lokasi == StatusPetaLokasiEnum.Lanjut_Peta_Lokasi,
                                                    or_(
                                                        RequestPetaLokasi.code == no_order,
                                                        KjbDt.request_peta_lokasi == None
                                                    )
                                                )
                                            )

    objs = await crud.kjb_dt.get_multi_paginated(params=params, query=query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[KjbDtSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.kjb_dt.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(KjbDt, id)

@router.put("/{id}", response_model=PutResponseBaseSch[KjbDtSch])
async def update(id:UUID, sch:KjbDtUpdateSch,
                 current_worker:Worker = Depends(crud.worker.get_current_user)):
    
    """Update a obj by its id"""
        
    obj_current = await crud.kjb_dt.get(id=id)

    alashak = await crud.kjb_dt.get_by_alashak_and_kjb_hd_id(alashak=sch.alashak, kjb_hd_id=sch.kjb_hd_id)
    if alashak :
        raise HTTPException(status_code=409, detail=f"alashak {sch.alashak} ada di KJB lain ({alashak.kjb_code})")

    if not obj_current:
        raise IdNotFoundException(KjbDt, id)
    
    obj_updated = await crud.kjb_dt.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)


   