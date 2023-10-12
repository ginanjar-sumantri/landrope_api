
from geojson import FeatureCollection
from fastapi import HTTPException
from fastapi.responses import FileResponse
from shapely.geometry import Polygon, shape, MultiPolygon
from io import BytesIO
from typing import List
from typing import Generic, TypeVar
import zipfile
import tempfile
import os
import pandas as pd
import geopandas
import fiona as fio
import math
import shapely
from shapely import wkb
import pygeos

T = TypeVar('T')

class GeomService(Generic[T]):

    #with fiona
    def file_to_geo_dataframe(file:bytes = None):
        """Convert buffer file data to geodataframe"""
        with fio.BytesCollection(file) as s:
            collections = FeatureCollection([(ss) for ss in s])
            geo_dataframe = geopandas.GeoDataFrame.from_features(features=collections)
            newgeo = GeomService.convert_3D_2D(geo_dataframe.geometry)

            print(newgeo)

            if newgeo.__len__() > 0:
                geo_dataframe.geometry = newgeo

            # geo_dataframe = geo_dataframe.explode(ignore_index=True)

        return geo_dataframe
    
    def file_to_geodataframe(file:BytesIO = None):
        """Convert buffer file data to geodataframe"""
       
        geo_dataframe = geopandas.GeoDataFrame.from_file(file)

        # if "3D" in geo_dataframe.geom_type.unique():
        #     geo_dataframe["geometry"] = geo_dataframe['geometry'].apply(lambda geom: geom.to_2D())

        # newgeo = GeomService.convert_3D_2D(geo_dataframe.geometry)

        # if newgeo.__len__() > 0:

        newgeo = GeomService.drop_z_pygeos(geo_dataframe.geometry)
        geo_dataframe.geometry = newgeo

        return geo_dataframe
    
    def total_row_geodataframe(file:BytesIO = None) -> int:
        """Get total row on file shp with geo data frame"""

        geo_dataframe = geopandas.GeoDataFrame.from_file(file)
        return geo_dataframe.shape[0]
    
    def single_geometry_to_wkt(geometry):
        """Convert geometry geo data frame"""
        return geopandas.GeoSeries(geometry).geometry.to_wkt()[0]
    
    def bulk_geometry_to_wkt(geometry, i):
        """Convert geometry geo data frame"""
        return geopandas.GeoSeries(geometry).geometry.to_wkt()[i]

    def linestring_to_polygon(line:shape):
        """Convert linestring to polygon"""
        coords = [(xy) for xy in tuple(line.coords)]
        polygon = geopandas.GeoSeries(Polygon(coords))

        return polygon
    
    def drop_z_pygeos(ds):
        ''' Drop Z coordinates from GeoSeries, returns GeoSeries
        Requires pygeos to be installed, and such I've added `import pygeos` to check.
        '''
        return geopandas.GeoSeries.from_wkb(ds.to_wkb(output_dimension=2))
    
    def convert_3D_2D(geometry):
        """Takes a GeoSeries of 3D Multi/Polygons (has_z) and returns a list of 2D Multi/Polygons"""
        new_geo = []
        for p in geometry:
            if p.has_z:
                if p.geom_type == 'Polygon':
                    lines = [xy[:2] for xy in list(p.exterior.coords)]
                    new_p = Polygon(lines)
                    new_geo.append(new_p)
                elif p.geom_type == 'LineString':
                    lines = [xy[:2] for xy in list(p.coords)]
                    new_p = Polygon(lines)
                    new_geo.append(new_p)
                elif p.geom_type == 'MultiPolygon':
                    new_multi_p = []
                    for ap in p:
                        lines = [xy[:2] for xy in list(ap.exterior.coords)]
                        new_p = Polygon(lines)
                        new_multi_p.append(new_p)
                    new_geo.append(MultiPolygon(new_multi_p))

        return new_geo


    def from_map_to_wkt(buffer:bytes, content_type:str):
        try:
            if content_type == "application/x-zip-compressed":
                with fio.BytesCollection(buffer) as s:
                    feature = s.next()
                    collections = FeatureCollection([feature])
                    gdf = geopandas.GeoDataFrame.from_features(features=collections)
                    gdf['geometry'] = gdf.geometry.boundary
            
            elif content_type == "application/octet-stream":
                with fio.BytesCollection(buffer) as s :
                    gdf = geopandas.GeoDataFrame.from_features(features=s)
        
            else :
                raise HTTPException(status_code=404, detail="File failed to upload, please make sure again extension file with '.zip' or '.dfx'")
            
            gdf["lat_lon_tuple"] = [[utm_to_latlon(xy, 48) for xy in tuple(geom.coords)] for geom in gdf.geometry]
            polygon = geopandas.GeoSeries(Polygon(xy) for xy in gdf["lat_lon_tuple"])
            geom_wkt = polygon.geometry.to_wkt()[0]
            return geom_wkt
        
        except:
            raise HTTPException(status_code=404, detail="File failed to upload, please make sure again Geometry Type is 'POLYGON' or 'LINESTRING' 2D")
    
    def export_shp_zip(data:List[T]| None, obj_name:str):

        # Mengubah data list object menjadi dictionary dan memasukkan kedalam variable list my_objects
        my_objects = list(map(lambda obj: obj.__dict__, data))

        # Maping pandas dataframe list dictionary my_object
        df = pd.DataFrame.from_dict(my_objects)

        # Convert semua kolom yang tipe datanya bukan string atau geometry. ini diperlukan sebab geodataframe tidak bisa menghandle tipe data selain string dan geometry
        desired_types = ['str' 'geometry']
        df = df.applymap(lambda x: convert_to_string(x) if x not in desired_types else x)

        # Memindahkan semua nilai geometry dalam dataframe['geom'] ke dalam varable gs (digunakan untuk geodataframe)
        gs = geopandas.GeoSeries.from_wkt(df['geom'])

        # Hapus kolom-kolom yang tidak diperlukan
        df = df.drop('geom', axis=1)

        f_updated = df.get("update_at", None)
        if f_updated is not None:
            df = df.drop('updated_at', axis=1)
        
        f_created = df.get("created_at", None)
        if f_created is not None:
            df = df.drop('created_at', axis=1)
            
        # columns_to_drop = [col for col in df.columns if "_id" in col]
        # df = df.drop(columns=columns_to_drop)

        # Memindahkan data dari dataframe dan geometry dari gs ke dalam geodataframe
        gdf = geopandas.GeoDataFrame(df, geometry=gs)

        print(gdf.head())

        tempdir = tempfile.mkdtemp()

        # mengekspor GeoDataFrame ke dalam file shapefile
        output_folder = os.path.join(tempdir, 'shapefile')
        gdf.to_file(filename=output_folder, driver='ESRI Shapefile')

        # membuat file zip dan menambahkan file shapefile ke dalamnya
        output_zip = os.path.join(tempdir, f'{obj_name}.zip')
        with zipfile.ZipFile(output_zip, 'w') as zip:
            zip.write(os.path.join(output_folder, 'shapefile.shp'), 'shapefile.shp')
            zip.write(os.path.join(output_folder, 'shapefile.shx'), 'shapefile.shx')
            zip.write(os.path.join(output_folder, 'shapefile.dbf'), 'shapefile.dbf')

        return FileResponse(output_zip, media_type='application/zip', filename=f'{obj_name}.zip')


def convert_to_string(value):
    return str(value)

def utm_to_latlon(coords, zone_number):
    easting = coords[0]
    northing = coords[1]
    return utmToLatLng(zone_number, easting, northing)

def utmToLatLng(zone, easting, northing, northernHemisphere=False):
    if not northernHemisphere:
        northing = 10000000 - northing

    a = 6378137
    e = 0.081819191
    e1sq = 0.006739497
    k0 = 0.9996

    arc = northing / k0
    mu = arc / (a * (1 - math.pow(e, 2) / 4.0 - 3 * math.pow(e, 4) / 64.0 - 5 * math.pow(e, 6) / 256.0))

    ei = (1 - math.pow((1 - e * e), (1 / 2.0))) / (1 + math.pow((1 - e * e), (1 / 2.0)))

    ca = 3 * ei / 2 - 27 * math.pow(ei, 3) / 32.0

    cb = 21 * math.pow(ei, 2) / 16 - 55 * math.pow(ei, 4) / 32
    cc = 151 * math.pow(ei, 3) / 96
    cd = 1097 * math.pow(ei, 4) / 512
    phi1 = mu + ca * math.sin(2 * mu) + cb * math.sin(4 * mu) + cc * math.sin(6 * mu) + cd * math.sin(8 * mu)

    n0 = a / math.pow((1 - math.pow((e * math.sin(phi1)), 2)), (1 / 2.0))

    r0 = a * (1 - e * e) / math.pow((1 - math.pow((e * math.sin(phi1)), 2)), (3 / 2.0))
    fact1 = n0 * math.tan(phi1) / r0

    _a1 = 500000 - easting
    dd0 = _a1 / (n0 * k0)
    fact2 = dd0 * dd0 / 2

    t0 = math.pow(math.tan(phi1), 2)
    Q0 = e1sq * math.pow(math.cos(phi1), 2)
    fact3 = (5 + 3 * t0 + 10 * Q0 - 4 * Q0 * Q0 - 9 * e1sq) * math.pow(dd0, 4) / 24

    fact4 = (61 + 90 * t0 + 298 * Q0 + 45 * t0 * t0 - 252 * e1sq - 3 * Q0 * Q0) * math.pow(dd0, 6) / 720

    lof1 = _a1 / (n0 * k0)
    lof2 = (1 + 2 * t0 + Q0) * math.pow(dd0, 3) / 6.0
    lof3 = (5 - 2 * Q0 + 28 * t0 - 3 * math.pow(Q0, 2) + 8 * e1sq + 24 * math.pow(t0, 2)) * math.pow(dd0, 5) / 120
    _a2 = (lof1 - lof2 + lof3) / math.cos(phi1)
    _a3 = _a2 * 180 / math.pi

    latitude = 180 * (phi1 - fact1 * (fact2 + fact3 + fact4)) / math.pi

    if not northernHemisphere:
        latitude = -latitude

    longitude = ((zone > 0) and (6 * zone - 183.0) or 3.0) - _a3

    return (longitude, latitude)

