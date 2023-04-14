from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, File
from fastapi_pagination import Params
import crud
from models.rincik_model import Rincik, CategoryEnum, JenisDokumenEnum
from schemas.rincik_sch import (RincikSch, RincikCreateSch, RincikUpdateSch, RincikRawSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, 
                                  ImportResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, ImportFailedException)
from services.geom_service import GeomService
from shapely.geometry import shape
from geoalchemy2.shape import to_shape

router = APIRouter()

@router.post("", response_model=PostResponseBaseSch[RincikRawSch], status_code=status.HTTP_201_CREATED)
async def create(sch: RincikCreateSch = Depends(RincikCreateSch.as_form), file:UploadFile = None):
    
    """Create a new object"""
    
    obj_current = await crud.rincik.get_by_id_rincik(idrincik=sch.id_rincik)
    if obj_current:
        raise NameExistException(Rincik, name=sch.id_rincik)
    
    if file:
        buffer = await file.read()

        geo_dataframe = GeomService.file_to_geo_dataframe(buffer)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry

        sch = RincikSch(id_rincik=sch.id_rincik,
                        estimasi_nama_pemilik=sch.estimasi_nama_pemilik,
                        luas=sch.luas,
                        category=sch.category,
                        alas_hak=sch.alas_hak,
                        jenis_dokumen=sch.jenis_dokumen,
                        no_peta=sch.no_peta,
                        jenis_lahan_id=sch.jenis_lahan_id,
                        planing_id=sch.planing_id,
                        ptsk_id=sch.ptsk_id,
                        geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
    new_obj = await crud.rincik.create(obj_in=sch)
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[RincikRawSch])
async def get_list(params:Params = Depends(), order_by:str=None, keyword:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.rincik.get_filtered_rincik(params=params, order_by=order_by, keyword=keyword)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[RincikRawSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.rincik.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Rincik, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[RincikRawSch])
async def update(id:UUID, sch:RincikUpdateSch = Depends(RincikUpdateSch.as_form), file:UploadFile = None):
    
    """Update a obj by its id"""

    obj_current = await crud.rincik.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Rincik, id)
    
    if obj_current.geom:
        obj_current.geom = to_shape(obj_current.geom).__str__()
    
    if file:
        buffer = await file.read()

        geo_dataframe = GeomService.file_to_geo_dataframe(buffer)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry

        sch = RincikSch(id_rincik=sch.id_rincik,
                        estimasi_nama_pemilik=sch.estimasi_nama_pemilik,
                        luas=sch.luas,
                        category=sch.category,
                        alas_hak=sch.alas_hak,
                        jenis_dokumen=sch.jenis_dokumen,
                        no_peta=sch.no_peta,
                        jenis_lahan_id=sch.jenis_lahan_id,
                        planing_id=sch.planing_id,
                        ptsk_id=sch.ptsk_id,
                        geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
    obj_updated = await crud.rincik.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

@router.post("/bulk", response_model=ImportResponseBaseSch[RincikRawSch], status_code=status.HTTP_201_CREATED)
async def bulk_create(file:UploadFile=File()):

    """Create bulk or import data"""

    try:
        # file = await file.read()
        geo_dataframe = GeomService.file_to_geodataframe(file.file)

        projects = await crud.project.get_all()
        desas = await crud.desa.get_all()
        planings = await crud.planing.get_all()

        for i, geo_data in geo_dataframe.iterrows():
            p:str = geo_data['PROJECT']
            d:str = geo_data['DESA']

            project = next((obj for obj in projects 
                            if obj.name.replace(" ", "").lower() == p.replace(" ", "").lower()), None)
            
            # project_filter = list(filter(lambda x: x.name.replace(" ", "").lower() == p.replace(" ", "").lower(), projects))
            # project:project = project_filter[0]
            
            if project is None:
                continue
                # raise HTTPException(status_code=404, detail=f"{p} Not Exists in Project Data Master")
            
            desa = next((obj for obj in desas 
                         if obj.name.replace(" ", "").lower() == d.replace(" ", "").lower()), None)

            # desa_filter = list(filter(lambda x: x.name.replace(" ", "").lower() == d.replace(" ", "").lower(), desas))
            # desa = desa_filter[0]
            if desa is None:
                continue
                # raise HTTPException(status_code=404, detail=f"{d} Not Exists in Desa Data Master")
            
            # plan = next((obj for obj in planings 
            #              if obj.project_id == project.id and obj.desa_id == desa.id), None)

            plan_filter = list(filter(lambda x: [x.project_id == project.id, x.desa_id == desa.id], planings))
            plan = plan_filter[0]
            if plan is None:
                continue
            
            sch = RincikSch(id_rincik=geo_data['IDBIDANG'],
                        estimasi_nama_pemilik=geo_data['NAMA'],
                        luas=geo_data['LUAS'],
                        # category=CategoryEnum.Group_Besar,
                        alas_hak="",
                        # jenis_dokumen=JenisDokumenEnum.AJB,
                        no_peta=geo_data['NO_PETA'],
                        planing_id=plan.id,
                        geom=GeomService.single_geometry_to_wkt(geo_data.geometry))

            obj = await crud.rincik.create(obj_in=sch)

    except:
        raise ImportFailedException(filename=file.filename)
    
    return create_response(data=obj)
