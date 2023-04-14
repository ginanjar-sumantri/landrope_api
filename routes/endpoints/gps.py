from uuid import UUID
from fastapi import APIRouter, status, Depends, UploadFile, File
from fastapi_pagination import Params
import crud
from models.gps_model import Gps
from schemas.gps_sch import (GpsSch, GpsRawSch, GpsCreateSch, GpsUpdateSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, ImportFailedException)
from services.geom_service import GeomService
from shapely.geometry import shape

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[GpsRawSch], status_code=status.HTTP_201_CREATED)
async def create(file:UploadFile = File()):
    
    """Create a new object"""
    if file is None:
        ImportFailedException()

    geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

    if geo_dataframe.geometry[0].geom_type == "LineString":
        polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
        geo_dataframe['geometry'] = polygon.geometry
    

    print(geo_dataframe)
    sch = GpsSch(nama=geo_dataframe['nama'][0],
                alas_hak=geo_dataframe['alas_hak'][0],
                luas=geo_dataframe['luas'][0],
                desa=geo_dataframe['desa'][0],
                petunjuk=geo_dataframe['penunjuk_b'][0],
                pic=geo_dataframe['pic'][0],
                group=geo_dataframe['group'][0], 
                geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry)
        )
        
    new_obj = await crud.gps.create(obj_in=sch)
    return create_response(data=new_obj)

# @router.get("", response_model=GetResponsePaginatedSch[JenisLahanSch])
# async def get_list(params: Params=Depends(), order_by:str = None, keyword:str = None):
    
#     """Gets a paginated list objects"""

#     objs = await crud.jenislahan.get_multi_paginated_ordered_with_keyword(params=params, order_by=order_by, keyword=keyword)
#     return create_response(data=objs)

# @router.get("/{id}", response_model=GetResponseBaseSch[JenisLahanSch])
# async def get_by_id(id:UUID):

#     """Get an object by id"""

#     obj = await crud.jenislahan.get(id=id)
#     if obj:
#         return create_response(data=obj)
#     else:
#         raise IdNotFoundException(JenisLahan, id)
    
# @router.put("/{id}", response_model=PutResponseBaseSch[JenisLahanSch])
# async def update(id:UUID, sch:JenisLahanUpdateSch):
    
#     """Update a obj by its id"""

#     obj_current = await crud.jenislahan.get(id=id)
#     if not obj_current:
#         raise IdNotFoundException(JenisLahan, id)
    
#     obj_updated = await crud.jenislahan.update(obj_current=obj_current, obj_new=sch)
#     return create_response(data=obj_updated)
