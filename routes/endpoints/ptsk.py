from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, Response
from fastapi_pagination import Params
import crud
from models.ptsk_model import Ptsk
from schemas.skpt_sch import SkptShpSch
from schemas.ptsk_sch import (PtskSch, PtskCreateSch, PtskUpdateSch, PtskRawSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, ImportResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, ImportFailedException)
from services.geom_service import GeomService
from shapely import wkt, wkb

router = APIRouter()

@router.post("", response_model=PostResponseBaseSch[PtskRawSch], status_code=status.HTTP_201_CREATED)
async def create(sch: PtskCreateSch):
    
    """Create a new object"""
    
    obj_current = await crud.ptsk.get_by_name(name=sch.name)
    if obj_current:
        raise NameExistException(Ptsk, name=sch.name)
    
    new_obj = await crud.ptsk.create(obj_in=sch)
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[PtskRawSch])
async def get_list(params:Params = Depends(), order_by:str=None, keyword:str=None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.ptsk.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[PtskRawSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.ptsk.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Ptsk, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[PtskRawSch])
async def update(id:UUID, sch:PtskUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.ptsk.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Ptsk, id)
    
    obj_updated = await crud.ptsk.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

@router.get("/export/shp", response_class=Response)
async def export_shp(ptsk_id:UUID = None):

    schemas = []
    
    skpts = await crud.skpt.get_by_ptsk_id(ptsk_id=ptsk_id)
    skpt_ids = [i.id for i in skpts]
    results = await crud.skptdt.get_by_ids(list_ids=skpt_ids)

    for data in results:
        sch = SkptShpSch(geom=wkt.dumps(wkb.loads(data.geom.data, hex=True)),
                      code=data.skpt.ptsk.code,
                      name=data.skpt.ptsk.name,
                      kategori=str(data.skpt.kategori),
                      luas=data.luas,
                      no_sk=data.nomor_sk,
                      status=str(data.skpt.status),
                      tgl_sk=data.skpt.tanggal_tahun_SK,
                      jatuhtempo=data.skpt.tanggal_jatuh_tempo,
                      project=data.project_name,
                      desa=data.desa_name)
        schemas.append(sch)

    if results:
        obj_name = results[0].__class__.__name__
        if len(results) == 1:
            obj_name = f"{obj_name}-{results[0].nomor_sk}"

    return GeomService.export_shp_zip(data=schemas, obj_name=obj_name)
