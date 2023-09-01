from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select
from models.spk_model import Spk
from models.bidang_model import Bidang
from models.order_gambar_ukur_model import OrderGambarUkurBidang
from models.hasil_peta_lokasi_model import HasilPetaLokasi
from models.kjb_model import KjbDt, KjbHd
from models.worker_model import Worker
from schemas.spk_sch import (SpkSch, SpkCreateSch, SpkUpdateSch)
from schemas.bidang_sch import BidangSrcSch, BidangForSPKById
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException)
import crud

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[SpkSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: SpkCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    
    new_obj = await crud.spk.create(obj_in=sch, created_by_id=current_worker.id)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[SpkSch])
async def get_list(
                params: Params=Depends(), 
                order_by:str = None, 
                keyword:str = None, 
                filter_query:str=None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.spk.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[SpkSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.spk.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Spk, id)

@router.put("/{id}", response_model=PutResponseBaseSch[SpkSch])
async def update(id:UUID, sch:SpkUpdateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.spk.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Spk, id)
    
    obj_updated = await crud.spk.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[SpkSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Delete a object"""

    obj_current = await crud.spk.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Spk, id)
    
    obj_deleted = await crud.spk.remove(id=id)

    return obj_deleted

@router.get("/search/bidang", response_model=GetResponsePaginatedSch[BidangSrcSch])
async def get_list(
                params: Params=Depends(),
                keyword:str = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(Bidang.id, Bidang.id_bidang).select_from(Bidang
                    ).join(HasilPetaLokasi, Bidang.id == HasilPetaLokasi.bidang_id)
    
    if keyword:
        query = query.filter(Bidang.id_bidang.ilike(f'%{keyword}%'))


    objs = await crud.bidang.get_multi_paginated(params=params, query=query)
    return create_response(data=objs)

@router.get("/search/bidang/{id}", response_model=GetResponseBaseSch[BidangForSPKById])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.bidang.get(id=id)

    harga = await crud.kjb_harga.get_by_kjb_hd_id_and_jenis_alashak(kjb_hd_id=obj.hasil_peta_lokasi.kjb_dt.kjb_hd_id, jenis_alashak=obj.jenis_alashak)
    
    obj_return = BidangForSPKById(id=obj.id,
                                  id_bidang=obj.id_bidang,
                                  hasil_analisa_peta_lokasi=obj.hasil_analisa_peta_lokasi,
                                  kjb_no=obj.hasil_peta_lokasi.kjb_dt.kjb_code,
                                  satuan_bayar=obj.hasil_peta_lokasi.kjb_dt.kjb_hd.satuan_bayar,
                                  termins=harga.termins)
    
    if obj:
        return create_response(data=obj_return)
    else:
        raise IdNotFoundException(Spk, id)

   