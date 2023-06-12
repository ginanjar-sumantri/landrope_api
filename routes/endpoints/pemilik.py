from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from models.pemilik_model import Pemilik, Kontak, Rekening
from schemas.pemilik_sch import (PemilikSch, PemilikCreateSch, PemilikUpdateSch, PemilikByIdSch)
from schemas.kontak_sch import KontakSch, KontakCreateSch, KontakUpdateSch
from schemas.rekening_sch import RekeningSch, RekeningCreateSch, RekeningUpdateSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.generator import generate_code
from models.code_counter_model import CodeCounterEnum
import crud

#region Pemilik
router_pemilik = APIRouter()

@router_pemilik.post("/create", response_model=PostResponseBaseSch[PemilikCreateSch], status_code=status.HTTP_201_CREATED)
async def create(sch: PemilikCreateSch):
    
    """Create a new object"""
        
    new_obj = await crud.pemilik.create_pemilik(obj_in=sch)
    
    return create_response(data=new_obj)

@router_pemilik.get("", response_model=GetResponsePaginatedSch[PemilikSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.pemilik.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router_pemilik.get("/{id}", response_model=GetResponseBaseSch[PemilikByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.pemilik.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Pemilik, id)

@router_pemilik.put("/{id}", response_model=PutResponseBaseSch[PemilikSch])
async def update(id:UUID, sch:PemilikUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.pemilik.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Pemilik, id)
    
    obj_updated = await crud.pemilik.update(obj_current=obj_current, obj_new=sch)

    await update_kontak(pemilik_id=id, sch=sch)
    await update_rekening(pemilik_id=id, sch=sch)

    return create_response(data=obj_updated)

async def update_kontak(pemilik_id:UUID, sch:PemilikUpdateSch):
    kontaks = await crud.kontak.get_by_pemilik_id(pemilik_id=pemilik_id)
    
    obj_data = list(map(lambda x: x.nomor_telepon, kontaks))
    obj_sch = list(map(lambda x: x.nomor_telepon, sch.kontaks))

    set1 = set(obj_sch)
    set2 = set(obj_data)

    add_kontak = list(set1 - set2)
    remove_kontak = list(set2 - set1)

    for a in add_kontak:
        a_kontak = Kontak(nomor_telepon=a, pemilik_id=pemilik_id)
        await crud.kontak.create(obj_in=a_kontak)
    
    for r in remove_kontak:
        s_kontak = list(filter(lambda x: x.nomor_telepon == r, kontaks))
        r_kontak = s_kontak[0]
        await crud.kontak.remove(id=r_kontak.id)

async def update_rekening(pemilik_id:UUID, sch:PemilikUpdateSch):
    rekenings = await crud.rekening.get_by_pemilik_id(pemilik_id=pemilik_id)

    for r in rekenings:
        obj_remove = list(filter(lambda x: x.nama_pemilik_rekening.strip().lower() == r.nama_pemilik_rekening.strip().lower() 
                                 and x.nomor_rekening.strip() == r.nomor_rekening.strip() 
                                 and x.bank_rekening.strip().lower() == r.bank_rekening.strip().lower(), sch.rekenings))
        
        if obj_remove is None:
            await crud.rekening.remove(id=r.id)
        
    for a in sch.rekenings:
        a_rekening = Rekening(nama_pemilik_rekening=a.nama_pemilik_rekening,
                              nomor_rekening=a.nama_pemilik_rekening,
                              bank_rekening=a.bank_rekening)
        await crud.rekening.create(obj_in=a_rekening)


            


@router_pemilik.delete("/delete", response_model=DeleteResponseBaseSch[PemilikSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID):
    
    """Delete a object"""

    obj_current = await crud.pemilik.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Pemilik, id)
    
    obj_deleted = await crud.pemilik.remove(id=id)

    return obj_deleted
#endregion

#region Kontak
router_kontak = APIRouter()

@router_kontak.post("/create", response_model=PostResponseBaseSch[KontakCreateSch], status_code=status.HTTP_201_CREATED)
async def create(sch: KontakCreateSch):
    
    """Create a new object"""
        
    new_obj = await crud.kontak.create(obj_in=sch)
    
    return create_response(data=new_obj)

@router_kontak.get("", response_model=GetResponsePaginatedSch[KontakSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.kontak.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router_kontak.get("/{id}", response_model=GetResponseBaseSch[KontakSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.kontak.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Kontak, id)

@router_kontak.put("/{id}", response_model=PutResponseBaseSch[KontakSch])
async def update(id:UUID, sch:KontakUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.kontak.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Kontak, id)
    
    obj_updated = await crud.kontak.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

@router_kontak.delete("/delete", response_model=DeleteResponseBaseSch[KontakSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID):
    
    """Delete a object"""

    obj_current = await crud.kontak.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Kontak, id)
    
    obj_deleted = await crud.kontak.remove(id=id)

    return obj_deleted
#endregion

#region Rekening
router_rekening = APIRouter()

@router_rekening.post("/create", response_model=PostResponseBaseSch[RekeningSch], status_code=status.HTTP_201_CREATED)
async def create(sch: RekeningCreateSch):
    
    """Create a new object"""
        
    new_obj = await crud.rekening.create(obj_in=sch)
    
    return create_response(data=new_obj)

@router_rekening.get("", response_model=GetResponsePaginatedSch[RekeningSch])
async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.rekening.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router_rekening.get("/{id}", response_model=GetResponseBaseSch[RekeningSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.rekening.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Rekening, id)

@router_rekening.put("/{id}", response_model=PutResponseBaseSch[RekeningSch])
async def update(id:UUID, sch:RekeningUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.rekening.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Rekening, id)
    
    obj_updated = await crud.rekening.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

@router_rekening.delete("/delete", response_model=DeleteResponseBaseSch[RekeningSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID):
    
    """Delete a object"""

    obj_current = await crud.rekening.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Rekening, id)
    
    obj_deleted = await crud.rekening.remove(id=id)

    return obj_deleted
#endregion
   