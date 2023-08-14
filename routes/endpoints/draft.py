from uuid import UUID
from fastapi import APIRouter, status, Depends, UploadFile, File
from fastapi_pagination import Params
import crud
from services.geom_service import GeomService
from models.draft_model import Draft, DraftDetail
from models.worker_model import Worker
from schemas.draft_sch import (DraftSch, DraftCreateSch, DraftRawSch, DraftForAnalisaSch)
from schemas.draft_detail_sch import DraftDetailSch
from schemas.response_sch import (PostResponseBaseSch, DeleteResponseBaseSch,  create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from shapely.geometry import shape
import geopandas as gpd
import pandas as pd
from shapely.geometry import polygon
from shapely  import wkt, wkb
from pyproj import CRS
from geoalchemy2.shape import from_shape

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[DraftRawSch], status_code=status.HTTP_201_CREATED)
async def create(
                sch: DraftCreateSch = Depends(DraftCreateSch.as_form), 
                file:UploadFile = File(),
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    if file is not None:

        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry
        
        sch = DraftSch(**sch.dict())
        sch.geom = GeomService.single_geometry_to_wkt(geo_dataframe.geometry)
        
    else:
        raise ImportFailedException()
        
    new_obj = await crud.draft.create(obj_in=sch, created_by_id=current_worker.id)
    
    return create_response(data=new_obj)

@router.post("/analisa", response_model=PostResponseBaseSch[DraftRawSch], status_code=status.HTTP_201_CREATED)
async def create(
                sch: DraftCreateSch = Depends(DraftCreateSch.as_form), 
                file:UploadFile | None = None,
                ):
    
    """Create a new analisa bidang"""
    geom = None
    crs = CRS("EPSG:32748")
    if file is not None:

        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry

        g = shape(geo_dataframe.geometry[0])
        wkb_geom = from_shape(g)
        geom_wkb = wkb_geom
        rincik_geom = GeomService.single_geometry_to_wkt(geo_dataframe.geometry)
        

    else:
        rincik = await crud.bidang.get(id=sch.rincik_id)
        geom_wkb = rincik.geom
        rincik_geom = wkt.dumps(wkb.loads(rincik.geom.data, hex=True))

    rincik_dict = { "id" : sch.rincik_id, "geometry" : rincik_geom}
    data_rincik = [rincik_dict]

    df_rincik = pd.DataFrame(data_rincik)
    gs_rincik = gpd.GeoSeries.from_wkt(df_rincik['geometry'])
    gdf1 = gpd.GeoDataFrame(df_rincik, geometry=gs_rincik)

    draft_details = []

    intersects_bidangs = await crud.bidang.get_intersect_bidang(geom=geom_wkb, id=sch.rincik_id)

    for intersect_bidang in intersects_bidangs:
        bidang_geom = wkt.dumps(wkb.loads(intersect_bidang.geom.data, hex=True))
        bidang_dict = {"id" : intersect_bidang.id, "geometry" : bidang_geom}
        data_bidang = [bidang_dict]

        df_bidang = pd.DataFrame(data_bidang)
        gs_bidang = gpd.GeoSeries.from_wkt(df_bidang['geometry'])
        gdf2 = gpd.GeoDataFrame(df_bidang, geometry=gs_bidang)

        intersected_geometry = gdf1.geometry.intersection(gdf2.geometry)

        if intersected_geometry[0].geom_type != "Polygon":
            is_polygon = intersected_geometry.geometry[0].is_ring
            if is_polygon:

                polygon = GeomService.linestring_to_polygon(shape(intersected_geometry.geometry[0]))
                intersected_geometry['geometry'] = polygon.geometry
            else:
                continue
        
        # gs_intersect = gpd.GeoSeries(intersected_geometry.geometry)
        # print(gs_intersect.area[0])
        
        draft_detail = DraftDetailSch(
            bidang_id=intersect_bidang.id,
            geom=GeomService.single_geometry_to_wkt(intersected_geometry.geometry)
            )
        
        draft_details.append(draft_detail)

    sch = DraftForAnalisaSch(**sch.dict())
    sch.geom = rincik_geom
    sch.details = draft_details

    new_obj = await crud.draft.create_for_analisa(obj_in=sch)
    
    return create_response(data=new_obj)

@router.delete("/delete", response_model=DeleteResponseBaseSch[DraftRawSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Delete a object"""

    obj_current = await crud.draft.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Draft, id)
    
    obj_deleted = await crud.draft.remove(id=id)

    return obj_deleted

from shapely.geometry import Polygon

@router.get("/measure")
async def delete():
    
    polygon = Polygon([(638677.5, 9087677.5), (638677.5, 9097677.5), (648677.5, 9097677.5), (648677.5, 9087677.5), (638677.5, 9087677.5)])

# Menentukan sistem koordinat untuk perhitungan luas dalam meter persegi (EPSG:32748)
    crs = CRS("EPSG:32748")

    # Membuat GeoDataFrame dari poligon
    gdf = gpd.GeoDataFrame({'geometry': [polygon]}, crs=crs)

    # Menghitung luas dalam meter persegi
    area = gdf.geometry.area.values[0]
    print("Luas poligon dalam meter persegi:", area)
   