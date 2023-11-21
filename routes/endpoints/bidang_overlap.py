from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, File, HTTPException
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
import crud
from models import BidangOverlap, Worker, Bidang
from schemas.bidang_overlap_sch import (BidangOverlapSch, BidangOverlapCreateSch, BidangOverlapRawSch, 
                                       BidangOverlapUpdateSch, BidangOverlapExcelSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException)
from common.enum import StatusLuasOverlapEnum
from common.rounder import RoundTwo
from services.geom_service import GeomService
from shapely.geometry import shape
import pandas
from decimal import Decimal
from shapely import wkt, wkb
import geopandas as gpd

router = APIRouter()

@router.post("", response_model=PostResponseBaseSch[BidangOverlapRawSch], status_code=status.HTTP_201_CREATED)
async def create(sch: BidangOverlapCreateSch = Depends(BidangOverlapCreateSch.as_form), file:UploadFile = None):
    
    """Create a new object"""
    
    obj_current = await crud.bidangoverlap.get_by_id_bidang(idbidang=sch.id_bidang)
    if obj_current:
        raise NameExistException(BidangOverlap, name=sch.id_bidang)
    
    if file:
        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry

        sch = BidangOverlapSch(
                        geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
    new_obj = await crud.bidangoverlap.create(obj_in=sch)
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[BidangOverlapRawSch])
async def get_list(params:Params = Depends(), order_by:str=None, keyword:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.bidangoverlap.get_multi_paginate_ordered_with_keyword_dict(params=params, keyword=keyword)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[BidangOverlapRawSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.bidangoverlap.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(BidangOverlap, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[BidangOverlapRawSch])
async def update(id:UUID, sch:BidangOverlapUpdateSch = Depends(BidangOverlapUpdateSch.as_form), file:UploadFile = None):
    
    """Update a obj by its id"""

    obj_current = await crud.bidangoverlap.get(id=id)
    if not obj_current:
        raise IdNotFoundException(BidangOverlap, id)
    
    if file:
        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry

        sch = BidangOverlapSch(id_bidang=sch.id_bidang,
                        nama_pemilik=sch.nama_pemilik,
                        luas_surat=sch.luas_surat,
                        alas_hak=sch.alas_hak,
                        no_peta=sch.no_peta,
                        status=sch.status,
                        planing_id=sch.planing_id,
                        ptsk_id=sch.ptsk_id,
                        geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
    obj_updated = await crud.bidangoverlap.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

@router.post("/import-bidang-overlap")
async def extract_excel(file:UploadFile):

    """Import Excel object"""

    db_session = db.session

    file_content = await file.read()
    df = pandas.read_excel(file_content)
    rows, commit, row = [len(df), False, 1]

    datas = []
    for i, data in df.iterrows():
        sch = BidangOverlapExcelSch(id_bintang=str(data.get('ID BINTANG', '')),
                                    status=str(data.get('STATUS', '')),
                                    id_bidang_damai=str(data.get('ID BID DAMAI', '')),
                                    luas_overlap=Decimal(data.get('LUAS OVERLAP', 0)))
        
        datas.append(sch)
    id_bidang=''
    i = 1
    try:
        for data in datas:
            id_bidang = data.id_bidang_damai
            try:
                bidang_damai = await crud.bidang.get_by_id_bidang_lama_for_import_excel(idbidang_lama=data.id_bidang_damai)
                bidang_damai_id = bidang_damai.id
                bidang_damai_geom = bidang_damai.geom
                if bidang_damai is None:
                    continue
            except:
                continue

            bidang_damai_geom = wkt.dumps(wkb.loads(bidang_damai.geom.data, hex=True))
            bidang_damai_gs = gpd.GeoSeries.from_wkt([bidang_damai_geom])
            gdf1 = gpd.GeoDataFrame(geometry=bidang_damai_gs)

            id_bidang = data.id_bintang
            try:
                bidang_bintang = await crud.bidang.get_by_id_bidang_lama_for_import_excel(idbidang_lama=data.id_bintang)
                if bidang_bintang is None:
                    continue
            except:
                continue

            bidang_bintang_geom = wkt.dumps(wkb.loads(bidang_bintang.geom.data, hex=True))
            bidang_bintang_gs = gpd.GeoSeries.from_wkt([bidang_bintang_geom])
            gdf2 = gpd.GeoDataFrame(geometry=bidang_bintang_gs)


            intersected_geometry = gdf1.geometry.intersection(gdf2.geometry)

            if intersected_geometry[0].geom_type != "Polygon":
                print(intersected_geometry[0].geom_type)
                is_polygon = intersected_geometry.geometry[0].is_ring
                if is_polygon:

                    polygon = GeomService.linestring_to_polygon(shape(intersected_geometry.geometry[0]))
                    intersected_geometry['geometry'] = polygon.geometry
                else:
                    continue
            
            gs_intersect = gpd.GeoSeries(intersected_geometry.geometry)
            if RoundTwo(angka=gs_intersect.area[0]) < 1:
                continue
            
            bidang_overlap_sch = BidangOverlap(code=f"IMPRT_{i}",
                                            parent_bidang_id=bidang_damai.id,
                                            parent_bidang_intersect_id=bidang_bintang.id,
                                            luas=data.luas_overlap,
                                            status_luas=StatusLuasOverlapEnum.Menambah_Luas if data.status == "BINTANG BATAL" else StatusLuasOverlapEnum.Tidak_Menambah_Luas,
                                            geom=GeomService.single_geometry_to_wkt(intersected_geometry.geometry))
            
            await crud.bidangoverlap.create(obj_in=bidang_overlap_sch, db_session=db_session, with_commit=False)

            i = i+1
        
        await db_session.commit()
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"On : {id_bidang}. Detail :{str(e)}")

    return {'message' : 'successfully import'}