# from uuid import UUID
# from fastapi import APIRouter, Depends, status, UploadFile, File
# from fastapi_pagination import Params
# import crud
# from models.bidang_model import Bidangoverlap
# from schemas.bidangoverlap_sch import (BidangoverlapSch, BidangoverlapCreateSch, BidangoverlapUpdateSch, 
#                                        BidangoverlapRawSch)
# from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
#                                   PostResponseBaseSch, PutResponseBaseSch, create_response)
# from common.exceptions import (IdNotFoundException, NameExistException)
# from services.geom_service import GeomService
# from shapely.geometry import shape

# router = APIRouter()

# @router.post("", response_model=PostResponseBaseSch[BidangoverlapRawSch], status_code=status.HTTP_201_CREATED)
# async def create(sch: BidangoverlapCreateSch = Depends(BidangoverlapCreateSch.as_form), file:UploadFile = None):
    
#     """Create a new object"""
    
#     obj_current = await crud.bidangoverlap.get_by_id_bidang(idbidang=sch.id_bidang)
#     if obj_current:
#         raise NameExistException(Bidangoverlap, name=sch.id_bidang)
    
#     if file:
#         geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

#         if geo_dataframe.geometry[0].geom_type == "LineString":
#             polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
#             geo_dataframe['geometry'] = polygon.geometry

#         sch = BidangoverlapSch(id_bidang=sch.id_bidang,
#                         nama_pemilik=sch.nama_pemilik,
#                         luas_surat=sch.luas_surat,
#                         alas_hak=sch.alas_hak,
#                         no_peta=sch.no_peta,
#                         status=sch.status,
#                         planing_id=sch.planing_id,
#                         ptsk_id=sch.ptsk_id,
#                         geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
#     new_obj = await crud.bidangoverlap.create(obj_in=sch)
#     return create_response(data=new_obj)

# @router.get("", response_model=GetResponsePaginatedSch[BidangoverlapRawSch])
# async def get_list(params:Params = Depends(), order_by:str=None, keyword:str=None):
    
#     """Gets a paginated list objects"""

#     objs = await crud.bidangoverlap.get_filtered_bidangoverlap(params=params, order_by=order_by, keyword=keyword)
#     return create_response(data=objs)

# @router.get("/{id}", response_model=GetResponseBaseSch[BidangoverlapRawSch])
# async def get_by_id(id:UUID):

#     """Get an object by id"""

#     obj = await crud.bidangoverlap.get(id=id)
#     if obj:
#         return create_response(data=obj)
#     else:
#         raise IdNotFoundException(Bidangoverlap, id)
    
# @router.put("/{id}", response_model=PutResponseBaseSch[BidangoverlapRawSch])
# async def update(id:UUID, sch:BidangoverlapUpdateSch = Depends(BidangoverlapCreateSch.as_form), file:UploadFile = None):
    
#     """Update a obj by its id"""

#     obj_current = await crud.bidangoverlap.get(id=id)
#     if not obj_current:
#         raise IdNotFoundException(Bidangoverlap, id)
    
#     if file:
#         geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

#         if geo_dataframe.geometry[0].geom_type == "LineString":
#             polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
#             geo_dataframe['geometry'] = polygon.geometry

#         sch = BidangoverlapSch(id_bidang=sch.id_bidang,
#                         nama_pemilik=sch.nama_pemilik,
#                         luas_surat=sch.luas_surat,
#                         alas_hak=sch.alas_hak,
#                         no_peta=sch.no_peta,
#                         status=sch.status,
#                         planing_id=sch.planing_id,
#                         ptsk_id=sch.ptsk_id,
#                         geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
#     obj_updated = await crud.bidangoverlap.update(obj_current=obj_current, obj_new=sch)
#     return create_response(data=obj_updated)

