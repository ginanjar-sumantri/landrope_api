from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, File
from fastapi_pagination import Params
import crud
from models.bidang_model import Bidang, StatusEnum, TypeEnum
from schemas.bidang_sch import (BidangSch, BidangCreateSch, BidangUpdateSch, BidangRawSch)
from schemas.rincik_sch import (RincikSch, RincikCreateSch, RincikRawBase)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, 
                                  ImportResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, ImportFailedException)
from services.geom_service import GeomService
from shapely.geometry import shape

router = APIRouter()

@router.post("", response_model=PostResponseBaseSch[BidangRawSch], status_code=status.HTTP_201_CREATED)
async def create(sch: BidangCreateSch = Depends(BidangCreateSch.as_form), file:UploadFile = None):
    
    """Create a new object"""
    
    obj_current = await crud.bidang.get_by_id_bidang(name=sch.id_bidang)
    if obj_current:
        raise NameExistException(Bidang, name=sch.id_bidang)
    
    if file:
        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry

        if sch.rincik_id is None:
            rinciksch = RincikSch(id_rincik=sch.id_rincik,
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
            rincik = await crud.rincik.create(obj_in=rinciksch)
            sch.rincik_id = rincik.id
       

        sch = BidangSch(id_bidang=sch.id_bidang,
                        nama_pemilik=sch.nama_pemilik,
                        luas_surat=sch.luas_surat,
                        alas_hak=sch.alas_hak,
                        no_peta=sch.no_peta,
                        status=sch.status,
                        type=sch.type,
                        planing_id=sch.plan_id,
                        rincik_id=sch.rincik_id,
                        ptsk_id=sch.ptsk_id,
                        geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    else:
        raise ImportFailedException()

    new_obj = await crud.bidang.create(obj_in=sch)

    return create_response(data=new_obj)
    


@router.get("", response_model=GetResponsePaginatedSch[BidangRawSch])
async def get_list(params:Params = Depends(), order_by:str = None, keyword:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.bidang.get_filtered_bidang(params=params, order_by=order_by, keyword=keyword)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[BidangRawSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.bidang.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Bidang, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[BidangRawSch])
async def update(id:UUID, sch:BidangUpdateSch = Depends(BidangUpdateSch.as_form), file:UploadFile = None):
    
    """Update a obj by its id"""

    obj_current = await crud.bidang.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Bidang, id)
    
    if file:
        # buffer = await file.read()

        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry

        sch = BidangSch(id_bidang=sch.id_bidang,
                        nama_pemilik=sch.nama_pemilik,
                        luas_surat=sch.luas_surat,
                        alas_hak=sch.alas_hak,
                        no_peta=sch.no_peta,
                        status=sch.status,
                        type=sch.type,
                        planing_id=sch.plan_id,
                        geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
    obj_updated = await crud.bidang.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

@router.post("/bulk", response_model=ImportResponseBaseSch[BidangRawSch], status_code=status.HTTP_201_CREATED)
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
            
            if project is None:
                continue
                # raise HTTPException(status_code=404, detail=f"{p} Not Exists in Project Data Master")
            
            desa = next((obj for obj in desas 
                         if obj.name.replace(" ", "").lower() == d.replace(" ", "").lower()), None)

            if desa is None:
                continue
                # raise HTTPException(status_code=404, detail=f"{d} Not Exists in Desa Data Master")

            plan_filter = list(filter(lambda x: [x.project_id == project.id, x.desa_id == desa.id], planings))
            plan = plan_filter[0]
            if plan is None:
                continue
            
            sch = BidangSch(id_bidang=geo_data['IDBIDANG'],
                        nama_pemilik=geo_data['NAMA'],
                        luas_surat=geo_data['LUAS'],
                        alas_hak="",
                        no_peta=geo_data['NO_PETA'],
                        status=StatusBidang(geo_data['STATUS']),
                        type=TypeBidang(geo_data['PROSES']),
                        planing_id=plan.id,
                        geom=GeomService.single_geometry_to_wkt(geo_data.geometry))

            obj = await crud.bidang.create(obj_in=sch)

    except:
        raise ImportFailedException(filename=file.filename)
    
    return create_response(data=obj)

def StatusBidang(status:str|None = None):
    if status:
        if status.replace(" ", "").lower() == StatusEnum.Bebas.replace("_", "").lower():
            return StatusEnum.Bebas
        elif status.replace(" ", "").lower() == StatusEnum.Belum_Bebas.replace("_", "").lower():
            return StatusEnum.Belum_Bebas
        elif status.replace(" ", "").lower() == StatusEnum.Batal.replace("_", "").lower():
            return StatusEnum.Batal
        else:
            return StatusEnum.Belum_Bebas
    else:
        return StatusEnum.Belum_Bebas

def TypeBidang(type:str|None = None):
    if type:
        if type.replace(" ", "").lower() == TypeEnum.Bintang.lower():
            return TypeEnum.Bintang
        elif type.replace(" ", "").lower() == TypeEnum.Standard.lower():
            return TypeEnum.Standard
        else:
            return TypeEnum.Standard
    else:
        return TypeEnum.Standard