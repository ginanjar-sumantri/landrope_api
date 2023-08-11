from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
import crud
from models.hasil_peta_lokasi_model import HasilPetaLokasi
from models.worker_model import Worker
from schemas.hasil_peta_lokasi_sch import (HasilPetaLokasiSch, HasilPetaLokasiCreateSch, HasilPetaLokasiByIdSch, HasilPetaLokasiUpdateSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, ContentNoChangeException)

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[HasilPetaLokasiSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: HasilPetaLokasiCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    obj_current = await crud.hasil_peta_lokasi.get_by_kjb_dt_id(kjb_dt_id=sch.kjb_dt_id)
    if obj_current:
        raise ContentNoChangeException(detail="Alashak Sudah input hasil peta lokasi")
    
    obj_current = await crud.hasil_peta_lokasi.get_by_bidang_id(bidang_id=sch.bidang_id)
    if obj_current:
        raise ContentNoChangeException(detail="Bidang Sudah input hasil peta lokasi")
    
    new_obj = await crud.hasil_peta_lokasi.create(obj_in=sch, created_by_id=current_worker.id)
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[HasilPetaLokasiSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str=None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.hasil_peta_lokasi.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[HasilPetaLokasiByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.hasil_peta_lokasi.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(HasilPetaLokasi, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[HasilPetaLokasiSch])
async def update(
            id:UUID, 
            sch:HasilPetaLokasiUpdateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.hasil_peta_lokasi.get(id=id)
    if not obj_current:
        raise IdNotFoundException(HasilPetaLokasi, id)
    
    obj_updated = await crud.hasil_peta_lokasi.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)
