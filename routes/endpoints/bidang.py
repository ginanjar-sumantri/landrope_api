import json
import crud
from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, File, Response, HTTPException, Request
from fastapi_pagination import Params
from models.bidang_model import Bidang
from models.worker_model import Worker
from models.import_log_model import ImportLog
from schemas.import_log_sch import ImportLogCreateSch, ImportLogSch, ImportLogCloudTaskSch
from schemas.bidang_sch import (BidangSch, BidangCreateSch, BidangUpdateSch, BidangRawSch, BidangShpSch, BidangExtSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, 
                                  ImportResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, ImportFailedException)
from common.generator import generate_id_bidang
from common.rounder import RoundTwo
from common.enum import TaskStatusEnum, StatusEnum, TipeProsesEnum, TipeBidangEnum
from services.geom_service import GeomService
from services.gcloud_task_service import GCloudTaskService
from services.gcloud_storage_service import GCStorage
from shapely.geometry import shape
from shapely import wkt, wkb
from decimal import Decimal
from datetime import datetime
from itertools import islice



router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[BidangRawSch], status_code=status.HTTP_201_CREATED)
async def create(sch: BidangCreateSch = Depends(BidangCreateSch.as_form), file:UploadFile = None):
    
    """Create a new object"""
    
    obj_current = await crud.bidang.get_by_id_bidang(idbidang=sch.id_bidang)
    if obj_current:
        raise NameExistException(Bidang, name=sch.id_bidang)
    
    sch.id_bidang = await generate_id_bidang(sch.planing_id)
    
    if file:
        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry
        
        sch = BidangSch(id_bidang=sch.id_bidang,
                        nama_pemilik=sch.nama_pemilik,
                        luas_surat=RoundTwo(sch.luas_surat),
                        alas_hak=sch.alas_hak,
                        no_peta=sch.no_peta,
                        category=sch.category,
                        jenis_dokumen=sch.jenis_dokumen,
                        status=sch.status,
                        jenis_lahan_id=sch.jenis_lahan_id,
                        planing_id=sch.planing_id,
                        skpt_id=sch.skpt_id,
                        tipe_proses=sch.tipe_proses,
                        tipe_bidang=sch.tipe_bidang,    
                        geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    else:
        raise ImportFailedException()

    new_obj = await crud.bidang.create(obj_in=sch)

    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[BidangRawSch])
async def get_list(params:Params = Depends(), order_by:str = None, keyword:str=None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.bidang.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
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
    
    if obj_current.geom :
        obj_current.geom = wkt.dumps(wkb.loads(obj_current.geom.data, hex=True))
    
    if file:
        # buffer = await file.read()

        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry

        sch = BidangSch(id_bidang=sch.id_bidang,
                        nama_pemilik=sch.nama_pemilik,
                        luas_surat=RoundTwo(sch.luas_surat),
                        alas_hak=sch.alas_hak,
                        no_peta=sch.no_peta,
                        category=sch.category,
                        jenis_dokumen=sch.jenis_dokumen,
                        status=sch.status,
                        jenis_lahan_id=sch.jenis_lahan_id,
                        planing_id=sch.planing_id,
                        skpt_id=sch.skpt_id,
                        tipe_proses=sch.tipe_proses,
                        tipe_bidang=sch.tipe_bidang,    
                        geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    
    obj_updated = await crud.bidang.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

@router.post(
        "/bulk", 
        response_model=PostResponseBaseSch[ImportLogSch], 
        status_code=status.HTTP_201_CREATED
)
async def create_bulking_task(
    file:UploadFile,
    request: Request,
    # current_worker: Worker = Depends(crud.worker.get_current_user)
    ):
    
    """Create a new object"""

    rows = GeomService.total_row_geodataframe(file.file)

    sch = ImportLogCreateSch(status=TaskStatusEnum.OnProgress,
                             name="Upload Bidang Bulking",
                             total_row=rows,
                             done_count=0)
    
    new_obj = await crud.import_log.create(obj_in=sch, worker_id="be39994c-5122-4227-91d8-a6765640b4d4", file=file)
    
    url = f'{request.base_url}landrope/bidang/cloud-task-bulk'

    GCloudTaskService().create_task_import_data(import_instance=new_obj, base_url=url)

    return create_response(data=new_obj)

@router.post("/cloud-task-bulk", response_model=ImportResponseBaseSch[BidangRawSch], status_code=status.HTTP_201_CREATED)
async def bulk_create(payload:ImportLogCloudTaskSch):

    """Create bulk or import data"""
    # try:
        # file = await file.read()
    
    log = await crud.import_log.get(id=payload.import_log_id)
    if log is None:
        raise IdNotFoundException(ImportLog, payload.import_log_id)
    
    start:int = log.done_count

    file = await GCStorage().download_file(payload.file_path)
    if not file:
        raise FileNotFoundError()
    
    geo_dataframe = GeomService.file_to_geodataframe(file)

    for i, geo_data in islice(geo_dataframe.iterrows(), start, None):

        shp_data = BidangShpSch(n_idbidang=geo_data['n_idbidang'],
                                o_idbidang=geo_data['o_idbidang'],
                                pemilik=geo_data['pemilik'],
                                code_desa=geo_data['code_desa'],
                                dokumen=geo_data['dokumen'],
                                sub_surat=geo_data['sub_surat'],
                                alashak=geo_data['alashak'],
                                luassurat=geo_data['luassurat'],
                                kat=geo_data['kat'],
                                kat_bidang=geo_data['kat_bidang'],
                                ptsk=geo_data['ptsk'],
                                penampung=geo_data['penampung'],
                                no_sk=geo_data['no_sk'],
                                status_sk=geo_data['status_sk'],
                                manager=geo_data['manager'],
                                sales=geo_data['sales'],
                                mediator=geo_data['mediator'],
                                proses=geo_data['proses'],
                                status=geo_data['status'],
                                group=geo_data['group'],
                                no_peta=geo_data['no_peta'],
                                desa=geo_data['desa'],
                                project=geo_data['project'],
                                geom=GeomService.single_geometry_to_wkt(geo_data.geometry)
        )
        
        luas_surat:Decimal = RoundTwo(Decimal(shp_data.luassurat))

        project = await crud.project.get_by_name(name=shp_data.project)            
        desa = await crud.desa.get_by_name(name=shp_data.desa)
        
        if project is None or desa is None:
            plan_id = None
        else:
            plan = await crud.planing.get_by_project_id_desa_id(project_id=project.id, desa_id=desa.id)
            if plan:
                plan_id = plan.id
            else:
                plan_id = None
        
        null_values = ["", "None", "nan", None]

        if shp_data.n_idbidang in null_values:
            bidang_lama = await crud.bidang.get_by_id_bidang_lama(idbidang_lama=shp_data.o_idbidang)
            if bidang_lama is None:
                shp_data.n_idbidang = await generate_id_bidang(planing_id=plan_id)
            else:
                shp_data.n_idbidang = bidang_lama.id_bidang
        
        sch = BidangSch(id_bidang=shp_data.n_idbidang,
                        id_bidang_lama=shp_data.o_idbidang,
                        nama_pemilik=shp_data.pemilik,
                        luas_surat=luas_surat,
                        alas_hak=shp_data.alashak,
                        no_peta=shp_data.no_peta,
                        category=shp_data.kat,
                        jenis_dokumen=None,
                        status=FindStatusBidang(shp_data.status),
                        jenis_lahan_id=None,
                        planing_id=plan_id,
                        skpt_id=None,
                        tipe_proses=FindTipeProses(shp_data.proses),
                        tipe_bidang=FindTipeBidang(shp_data.proses),
                    geom=GeomService.single_geometry_to_wkt(geo_data.geometry))
        
        obj_current = await crud.bidang.get_by_id_bidang_id_bidang_lama(idbidang=sch.id_bidang, idbidang_lama=sch.id_bidang_lama)

        if obj_current:
            if obj_current.geom :
                obj_current.geom = wkt.dumps(wkb.loads(obj_current.geom.data, hex=True))
            obj = await crud.bidang.update(obj_current=obj_current, obj_new=sch)
        else:
            obj = await crud.bidang.create(obj_in=sch)
        
        start = start + 1
        obj_updated = log
        obj_updated.done_count = start

        await crud.import_log(obj_current=log, obj_updated=obj_updated)

    # except:
    #     raise ImportFailedException(filename=file.filename)

    obj_updated = log
    obj_updated.status = TaskStatusEnum.Done
    obj_updated.completed_at = datetime.now()
    
    await crud.import_log(obj_current=log, obj_updated=obj_updated)
    
    return create_response(data=obj)

# @router.post("/bulk", response_model=ImportResponseBaseSch[BidangRawSch], status_code=status.HTTP_201_CREATED)
# async def bulk_create(tipeproses:str, file:UploadFile=File()):

#     """Create bulk or import data"""
#     # try:
#         # file = await file.read()
#     geo_dataframe = GeomService.file_to_geodataframe(file.file)

#     for i, geo_data in geo_dataframe.iterrows():

#         shp_data = BidangShpSch(n_idbidang=geo_data['n_idbidang'],
#                                 o_idbidang=geo_data['o_idbidang'],
#                                 pemilik=geo_data['pemilik'],
#                                 code_desa=geo_data['code_desa'],
#                                 dokumen=geo_data['dokumen'],
#                                 sub_surat=geo_data['sub_surat'],
#                                 alashak=geo_data['alashak'],
#                                 luassurat=geo_data['luassurat'],
#                                 kat=geo_data['kat'],
#                                 kat_bidang=geo_data['kat_bidang'],
#                                 ptsk=geo_data['ptsk'],
#                                 penampung=geo_data['penampung'],
#                                 no_sk=geo_data['no_sk'],
#                                 status_sk=geo_data['status_sk'],
#                                 manager=geo_data['manager'],
#                                 sales=geo_data['sales'],
#                                 mediator=geo_data['mediator'],
#                                 proses=geo_data['proses'],
#                                 status=geo_data['status'],
#                                 group=geo_data['group'],
#                                 no_peta=geo_data['no_peta'],
#                                 desa=geo_data['desa'],
#                                 project=geo_data['project'],
#                                 geom=GeomService.single_geometry_to_wkt(geo_data.geometry)
#         )
        
#         luas_surat:Decimal = RoundTwo(Decimal(shp_data.luassurat))

#         project = await crud.project.get_by_name(name=shp_data.project)            
#         desa = await crud.desa.get_by_name(name=shp_data.desa)
        
#         if project is None or desa is None:
#             plan_id = None
#         else:
#             plan = await crud.planing.get_by_project_id_desa_id(project_id=project.id, desa_id=desa.id)
#             if plan:
#                 plan_id = plan.id
#             else:
#                 plan_id = None
        
#         if shp_data.n_idbidang is None or shp_data.n_idbidang == "nan" or shp_data.n_idbidang == "None":
#             if plan_id:
#                 shp_data.n_idbidang = await generate_id_bidang(planing_id=plan_id)
        
#         sch = BidangSch(id_bidang=shp_data.n_idbidang,
#                         id_bidang_lama=shp_data.o_idbidang,
#                         nama_pemilik=shp_data.pemilik,
#                         luas_surat=luas_surat,
#                         alas_hak=shp_data.alashak,
#                         no_peta=shp_data.no_peta,
#                         category=shp_data.kat,
#                         jenis_dokumen=None,
#                         status=FindStatusBidang(shp_data.status),
#                         jenis_lahan_id=None,
#                         planing_id=plan_id,
#                         skpt_id=None,
#                         tipe_proses=FindTipeProses(shp_data.proses),
#                         tipe_bidang=FindTipeBidang(shp_data.proses),
#                     geom=GeomService.single_geometry_to_wkt(geo_data.geometry))
        
#         obj_current = await crud.bidang.get_by_id_bidang_id_bidang_lama(idbidang=sch.id_bidang, idbidang_lama=sch.id_bidang_lama)
#         if obj_current:
#             obj = await crud.bidang.update(obj_current=obj_current, obj_new=sch)
#         else:
#             obj = await crud.bidang.create(obj_in=sch)

#     # except:
#     #     raise ImportFailedException(filename=file.filename)
    
#     return create_response(data=obj)

@router.get("/export/shp", response_class=Response)
async def export(filter_query:str = None):
    
    results = await crud.bidang.get_multi_by_dict(filter_query=filter_query)
    schemas = []
    for data in results:
        sch = BidangShpSch(n_idbidang=data.id_bidang,
                           o_idbidang=data.id_bidang_lama,
                           pemilik=data.nama_pemilik,
                           code_desa=data.desa_code,
                           dokumen="",
                           sub_surat="",
                           alashak=data.alas_hak,
                           luassurat=data.luas_surat,
                           kat=data.category,
                           kat_bidang="",
                           ptsk=data.ptsk_name,
                           penampung=data.ptsk_name,
                           no_sk=data.nomor_sk,
                           status_sk="",
                           manager="",
                           sales="",
                           mediator="",
                           proses=data.tipe_proses,
                           status=data.status,
                           group="",
                           no_peta=data.no_peta,
                           desa=data.desa_name,
                           project=data.project_name,
                           geom = wkt.dumps(wkb.loads(data.geom.data, hex=True))
                           )
        
        schemas.append(sch)

    if results:
        obj_name = results[0].__class__.__name__
        if len(results) == 1:
            obj_name = f"{obj_name}-{results[0].id_bidang}"

        return GeomService.export_shp_zip(data=schemas, obj_name=obj_name)
    else:
        raise HTTPException(status_code=422, detail="Failed Export, please contact administrator!")

def FindStatusBidang(status:str|None = None):
    if status:
        if status.replace(" ", "").lower() == StatusEnum.Bebas.replace("_", "").lower():
            return StatusEnum.Bebas
        elif status.replace(" ", "").lower() == StatusEnum.Belum_Bebas.replace("_", "").lower():
            return StatusEnum.Belum_Bebas
        elif status.replace(" ", "").lower() == StatusEnum.Batal.replace("_", "").lower():
            return StatusEnum.Batal
        elif status.replace(" ", "").lower() == StatusEnum.Lanjut.replace("_", "").lower():
            return StatusEnum.Lanjut
        elif status.replace(" ", "").lower() == StatusEnum.Pending.replace("_", "").lower():
            return StatusEnum.Pending
        else:
            return StatusEnum.Batal
    else:
        return StatusEnum.Batal

def FindTipeProses(type:str|None = None):
    if type:
        if type.replace(" ", "").lower() == TipeProsesEnum.Bintang.lower():
            return TipeProsesEnum.Bintang
        elif type.replace(" ", "").lower() == TipeProsesEnum.Standard.lower():
            return TipeProsesEnum.Standard
        elif type.replace(" ", "").lower() == TipeProsesEnum.Overlap.lower():
            return TipeProsesEnum.Overlap
        else:
            return TipeProsesEnum.Standard
    else:
        return TipeProsesEnum.Standard

def FindTipeBidang(type:str|None = None):
    if type:
        if type.replace(" ", "").lower() == "Standard".lower() or type.replace(" ", "").lower() == "Bintang".lower():
            return TipeBidangEnum.Bidang
        elif type.replace(" ", "").lower() == "Overlap".lower():
            return TipeBidangEnum.Overlap
    else:
        return TipeBidangEnum.Bidang