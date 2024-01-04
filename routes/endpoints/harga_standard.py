from uuid import UUID
from fastapi import APIRouter, status, Depends, HTTPException
from fastapi_pagination import Params
from sqlmodel import select, or_, cast, String
import crud
from models.master_model import HargaStandard
from models import Planing, Project, Desa
from models.worker_model import Worker
from schemas.harga_standard_sch import (HargaStandardSch, HargaStandardCreateSch, HargaStandardUpdateSch, HargaStandardKjbSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, DeleteResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException)
from common.enum import JenisAlashakEnum
from decimal import Decimal
import json

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[HargaStandardSch], status_code=status.HTTP_201_CREATED)
async def create(sch: HargaStandardCreateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    obj_current = await crud.harga_standard.get_by_planing_id_jenis_alashak(planing_id=sch.planing_id, jenis_alashak=sch.jenis_alashak)
    if obj_current:
        raise HTTPException(status_code=422, detail="Harga dengan planing dan jenis alashak yang sama, sudah ada di database")
    
    new_obj = await crud.harga_standard.create(obj_in=sch, created_by_id=current_worker.id)
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[HargaStandardSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(HargaStandard).outerjoin(HargaStandard.planing
                                ).outerjoin(Planing.project
                                ).outerjoin(Planing.desa)
    if keyword:
        query = query.filter(
            or_(
                Project.name.ilike(f'%{keyword}%'),
                Desa.name.ilike(f'%{keyword}%'),
                cast(HargaStandard.harga, String).ilike(f'%{keyword}%')
            )
        )
    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
                query = query.where(getattr(HargaStandard, key) == value)
    
    query = query.distinct()

    objs = await crud.harga_standard.get_multi_paginated_ordered(params=params, query=query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[HargaStandardSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.harga_standard.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(HargaStandard, id)

@router.get("/desa/{desa_id}", response_model=GetResponseBaseSch[list[HargaStandardKjbSch]])
async def get_by_desa_id(desa_id:UUID):

    """Get an object by id"""

    objs = await crud.harga_standard.get_by_desa_id(desa_id=desa_id)

    result:list[HargaStandardKjbSch] = []
    harga_standard_girik = next((hg for hg in objs if hg.jenis_alashak == JenisAlashakEnum.Girik), None)
    if harga_standard_girik:
        girik = HargaStandardKjbSch(jenis_alashak=harga_standard_girik.jenis_alashak, harga=harga_standard_girik.harga)
        result.append(girik)

    harga_standard_shm = next((hg for hg in objs if hg.jenis_alashak == JenisAlashakEnum.Sertifikat), None)
    if harga_standard_shm:
        shm = HargaStandardKjbSch(jenis_alashak=harga_standard_shm.jenis_alashak, harga=harga_standard_shm.harga)
        result.append(shm)
    
    return create_response(data=result)
    
@router.put("/{id}", response_model=PutResponseBaseSch[HargaStandardSch])
async def update(id:UUID, sch:HargaStandardUpdateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.harga_standard.get(id=id)
    if not obj_current:
        raise IdNotFoundException(HargaStandard, id)
    
    obj = await crud.harga_standard.get_by_planing_id_jenis_alashak(planing_id=sch.planing_id, jenis_alashak=sch.jenis_alashak, id=id)
    if obj:
        raise HTTPException(status_code=422, detail="Harga dengan planing dan jenis alashak yang sama, sudah ada di database")
    
    obj_updated = await crud.harga_standard.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[HargaStandardSch], status_code=status.HTTP_200_OK)
async def delete(
            id:UUID,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Delete a object"""

    obj_current = await crud.harga_standard.get(id=id)
    if not obj_current:
        raise IdNotFoundException(HargaStandard, id)
    
    obj_deleted = await crud.harga_standard.remove(id=id)

    return obj_deleted
