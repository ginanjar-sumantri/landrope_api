from uuid import UUID
from fastapi import APIRouter, status, Depends, UploadFile, Response, Request, HTTPException
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_
import crud
from models.hasil_peta_lokasi_model import HasilPetaLokasi, HasilPetaLokasiDetail
from models.worker_model import Worker
from models.bidang_model import Bidang
from models.bidang_overlap_model import BidangOverlap
from models.checklist_kelengkapan_dokumen_model import ChecklistKelengkapanDokumenHd, ChecklistKelengkapanDokumenDt
from schemas.hasil_peta_lokasi_sch import (HasilPetaLokasiSch, HasilPetaLokasiCreateSch, 
                                           HasilPetaLokasiCreateExtSch, HasilPetaLokasiByIdSch, 
                                           HasilPetaLokasiUpdateSch, HasilPetaLokasiUpdateExtSch,
                                           HasilPetaLokasiTaskUpdateBidang)
from schemas.hasil_peta_lokasi_detail_sch import (HasilPetaLokasiDetailCreateSch, HasilPetaLokasiDetailCreateExtSch,
                                                  HasilPetaLokasiDetailUpdateSch)
from schemas.bidang_overlap_sch import BidangOverlapCreateSch, BidangOverlapSch
from schemas.bidang_sch import BidangSch, BidangUpdateSch, BidangSrcSch
from schemas.bundle_dt_sch import BundleDtCreateSch
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ContentNoChangeException, DocumentFileNotFoundException)
from common.generator import generate_code, CodeCounterEnum
from common.enum import TipeProsesEnum, StatusHasilPetaLokasiEnum, StatusBidangEnum, JenisBidangEnum, HasilAnalisaPetaLokasiEnum
from services.gcloud_storage_service import GCStorageService
from services.gcloud_task_service import GCloudTaskService
from shapely import wkb, wkt
from geoalchemy2 import functions

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[HasilPetaLokasiSch], status_code=status.HTTP_201_CREATED)
async def create(
            request: Request,
            sch: HasilPetaLokasiCreateExtSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    db_session = db.session

    obj_current = await crud.hasil_peta_lokasi.get_by_kjb_dt_id(kjb_dt_id=sch.kjb_dt_id)
    if obj_current:
        raise ContentNoChangeException(detail="Alashak Sudah input hasil peta lokasi")

    sch.hasil_analisa_peta_lokasi = HasilAnalisaPetaLokasiEnum.Clear

    if len(sch.hasilpetalokasidetails) > 0:
        sch.hasil_analisa_peta_lokasi = HasilAnalisaPetaLokasiEnum.Overlap

    new_obj = await crud.hasil_peta_lokasi.create(obj_in=sch, created_by_id=current_worker.id, db_session=db_session, with_commit=False)

    # draft_header_id = None
    
    for dt in sch.hasilpetalokasidetails:
        bidang_overlap_id = None 
        if dt.draft_detail_id is not None:
            #input bidang overlap dari hasil analisa
            draft_detail = await crud.draft_detail.get(id=dt.draft_detail_id)
            if draft_detail is None:
                raise ContentNoChangeException(detail="Bidang Overlap tidak exists di Draft Detail")
            
            # draft_header_id = draft_detail.draft_id
            
            code = await generate_code(entity=CodeCounterEnum.BidangOverlap, db_session=db_session, with_commit=False)
            bidang_overlap_sch = BidangOverlapSch(
                                    code=code,
                                    parent_bidang_id=sch.bidang_id,
                                    parent_bidang_intersect_id=dt.bidang_id,
                                    luas=dt.luas_overlap,
                                    status_luas=dt.status_luas,
                                    geom=wkt.dumps(wkb.loads(draft_detail.geom.data, hex=True)))
            
            new_obj_bidang_overlap = await crud.bidangoverlap.create(obj_in=bidang_overlap_sch, db_session=db_session, 
                                                                     with_commit=False, created_by_id=current_worker.id)
            bidang_overlap_id = new_obj_bidang_overlap.id
            
        
        #input detail hasil peta lokasi
        detail_sch = HasilPetaLokasiDetailCreateSch(**dt.dict())
        detail_sch.hasil_peta_lokasi_id=new_obj.id
        detail_sch.bidang_overlap_id=bidang_overlap_id

        await crud.hasil_peta_lokasi_detail.create(obj_in=detail_sch, created_by_id=current_worker.id, db_session=db_session, with_commit=False)

    payload = HasilPetaLokasiTaskUpdateBidang(bidang_id=str(new_obj.bidang_id),
                                              hasil_peta_lokasi_id=str(new_obj.id),
                                              kjb_dt_id=str(new_obj.kjb_dt_id),
                                              draft_id=str(sch.draft_id))
    
    
    url = f'{request.base_url}landrope/hasilpetalokasi/cloud-task-update-bidang'
    GCloudTaskService().create_task(payload=payload.dict(), base_url=url)

    url2 = f'{request.base_url}landrope/hasilpetalokasi/cloud-task-generate-kelengkapan'
    GCloudTaskService().create_task(payload=payload.dict(), base_url=url2)


    await db_session.commit()
    await db_session.refresh(new_obj)

    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[HasilPetaLokasiSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str=None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.hasil_peta_lokasi.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[HasilPetaLokasiByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.hasil_peta_lokasi.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(HasilPetaLokasi, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[HasilPetaLokasiSch])
async def update(
            id:UUID, 
            request:Request,
            sch:HasilPetaLokasiUpdateExtSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    db_session = db.session
    obj_current = await crud.hasil_peta_lokasi.get(id=id)
    if not obj_current:
        raise IdNotFoundException(HasilPetaLokasi, id)
    
    #remove link bundle dan kelengkapan dokumen jika pada update yg dipilih bidang berbeda
    if obj_current.bidang_id != sch.bidang_id:
        url = f'{request.base_url}landrope/hasilpetalokasi/cloud-task-remove-link-bidang-and-kelengkapan'
        payload = {"bidang_id" : str(obj_current.bidang_id)}
        GCloudTaskService().create_task(payload=payload, base_url=url)

    #remove existing data detail dan overlap
    list_overlap = [ov.bidang_overlap for ov in obj_current.details if ov.bidang_overlap != None]

    await crud.hasil_peta_lokasi_detail.remove_multiple_data(list_obj=obj_current.details, db_session=db_session)
    await crud.bidangoverlap.remove_multiple_data(list_obj=list_overlap, db_session=db_session)
    
    sch.hasil_analisa_peta_lokasi = HasilAnalisaPetaLokasiEnum.Clear

    if len(sch.hasilpetalokasidetails) > 0:
        sch.hasil_analisa_peta_lokasi = HasilAnalisaPetaLokasiEnum.Overlap

    #update hasil peta lokasi
    sch_updated = HasilPetaLokasiUpdateSch(**sch.dict())
    sch_updated.file_path = obj_current.file_path
    obj_updated = await crud.hasil_peta_lokasi.update(obj_current=obj_current, obj_new=sch_updated,
                                                       updated_by_id=current_worker.id, db_session=db_session, with_commit=False)
    

    # draft_header_id = None  
    for dt in sch.hasilpetalokasidetails:
        bidang_overlap_id = None
        if dt.draft_detail_id is not None:
            #input bidang overlap dari hasil analisa

            draft_detail = await crud.draft_detail.get(id=dt.draft_detail_id)
            if draft_detail is None:
                raise ContentNoChangeException(detail="Bidang Overlap tidak exists di Draft Detail")
            
            # draft_header_id = draft_detail.draft_id
            
            code = await generate_code(entity=CodeCounterEnum.BidangOverlap, db_session=db_session, with_commit=False)
            bidang_overlap_sch = BidangOverlapSch(
                                    code=code,
                                    parent_bidang_id=sch.bidang_id,
                                    parent_bidang_intersect_id=dt.bidang_id,
                                    luas=dt.luas_overlap,
                                    status_luas=dt.status_luas,
                                    geom=wkt.dumps(wkb.loads(draft_detail.geom.data, hex=True)))
            
            new_obj_bidang_overlap = await crud.bidangoverlap.create(obj_in=bidang_overlap_sch, db_session=db_session, 
                                                                     with_commit=False, created_by_id=current_worker.id)
            
            bidang_overlap_id = new_obj_bidang_overlap.id
        
        #input detail hasil peta lokasi
        detail_sch = HasilPetaLokasiDetailCreateSch(**dt.dict())
        detail_sch.hasil_peta_lokasi_id=obj_updated.id
        detail_sch.bidang_overlap_id=bidang_overlap_id

        await crud.hasil_peta_lokasi_detail.create(obj_in=detail_sch, created_by_id=current_worker.id, db_session=db_session, with_commit=False)

    payload = HasilPetaLokasiTaskUpdateBidang(bidang_id=str(obj_updated.bidang_id),
                                              hasil_peta_lokasi_id=str(obj_updated.id),
                                              kjb_dt_id=str(obj_updated.kjb_dt_id),
                                              draft_id=str(sch.draft_id))
    
    
    url = f'{request.base_url}landrope/hasilpetalokasi/cloud-task-update-bidang'
    GCloudTaskService().create_task(payload=payload.dict(), base_url=url)

    url2 = f'{request.base_url}landrope/hasilpetalokasi/cloud-task-generate-kelengkapan'
    GCloudTaskService().create_task(payload=payload.dict(), base_url=url2)

    await db_session.commit()
    await db_session.refresh(obj_updated)

    return create_response(data=obj_updated)

@router.put("/upload-dokumen/{id}", response_model=PutResponseBaseSch[HasilPetaLokasiSch])
async def upload_dokumen(
            id:UUID, 
            file: UploadFile = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.hasil_peta_lokasi.get(id=id)
    if not obj_current:
        raise IdNotFoundException(HasilPetaLokasi, id)

    if file:
        file_path = await GCStorageService().upload_file_dokumen(file=file, file_name=f'Hasil Peta Lokasi-{id}-{obj_current.id_bidang}')
        object_updated = HasilPetaLokasiUpdateSch(file_path=file_path)
    
    obj_updated = await crud.hasil_peta_lokasi.update(obj_current=obj_current, obj_new=object_updated, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)

@router.get("/download-file/{id}")
async def download_file(id:UUID):
    """Download File Dokumen"""

    obj_current = await crud.hasil_peta_lokasi.get(id=id)
    if not obj_current:
        raise IdNotFoundException(HasilPetaLokasi, id)
    if obj_current.file_path is None:
        raise DocumentFileNotFoundException(dokumenname=obj_current.alashak_kjb_dt)
    try:
        file_bytes = await GCStorageService().download_dokumen(file_path=obj_current.file_path)
    except Exception as e:
        raise DocumentFileNotFoundException(dokumenname=obj_current.alashak_kjb_dt)
    
    ext = obj_current.file_path.split('.')[-1]

    # return FileResponse(file, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={obj_current.id}.{ext}"})
    response = Response(content=file_bytes, media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename=Hasil Peta Lokasi-{id}-{obj_current.id_bidang}.{ext}"
    return response

@router.get("/search/bidang", response_model=GetResponsePaginatedSch[BidangSrcSch])
async def get_list(
                params: Params=Depends(),
                keyword:str = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    status_ = [StatusBidangEnum.Belum_Bebas]
    query = select(Bidang.id, Bidang.id_bidang).select_from(Bidang
                    ).where(and_(
                                Bidang.status.in_(status_),
                                Bidang.jenis_bidang != JenisBidangEnum.Bintang,
                                Bidang.hasil_peta_lokasi == None
                            ))
    
    if keyword:
        query = query.filter(Bidang.id_bidang.ilike(f'%{keyword}%'))


    objs = await crud.bidang.get_multi_paginated(params=params, query=query)
    return create_response(data=objs)

@router.post("/cloud-task-update-bidang")
async def update_bidang_and_generate_kelengkapan(payload:HasilPetaLokasiTaskUpdateBidang):

    """Task update data bidang from hasil peta lokasi"""
    try:
        db_session = db.session

        hasil_peta_lokasi = await crud.hasil_peta_lokasi.get(id=payload.hasil_peta_lokasi_id)
        kjb_dt_current = await crud.kjb_dt.get(id=payload.kjb_dt_id)
        kjb_hd_current = await crud.kjb_hd.get(id=kjb_dt_current.kjb_hd_id)
        kjb_harga_current = await crud.kjb_harga.get_by_kjb_hd_id_and_jenis_alashak(kjb_hd_id=kjb_dt_current.kjb_hd_id, jenis_alashak=kjb_dt_current.jenis_alashak)
        tanda_terima_notaris_current = await crud.tandaterimanotaris_hd.get_one_by_kjb_dt_id(kjb_dt_id=kjb_dt_current.id)

        draft = await crud.draft.get(id=payload.draft_id)

        bidang_current = await crud.bidang.get(id=payload.bidang_id)
        if bidang_current.geom :
            bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))

        jenis_bidang = JenisBidangEnum.Standard
        status_bidang = StatusBidangEnum.Deal

        if hasil_peta_lokasi.status_hasil_peta_lokasi == StatusHasilPetaLokasiEnum.Batal:
            status_bidang = StatusBidangEnum.Batal

        if hasil_peta_lokasi.hasil_analisa_peta_lokasi == HasilAnalisaPetaLokasiEnum.Overlap:
            jenis_bidang = JenisBidangEnum.Overlap

        bidang_updated = BidangSch(
            jenis_bidang=jenis_bidang,
            status=status_bidang,
            pemilik_id=hasil_peta_lokasi.pemilik_id,
            luas_surat=hasil_peta_lokasi.luas_surat,
            planing_id=hasil_peta_lokasi.planing_id,
            skpt_id=hasil_peta_lokasi.skpt_id,
            group=kjb_hd_current.nama_group,
            jenis_alashak=kjb_dt_current.jenis_alashak,
            jenis_surat_id=kjb_dt_current.jenis_surat_id,
            alashak=kjb_dt_current.alashak,
            manager_id=kjb_hd_current.manager_id,
            sales_id=kjb_hd_current.sales_id,
            mediator=kjb_hd_current.mediator,
            telepon_mediator=kjb_hd_current.telepon_mediator,
            notaris_id=tanda_terima_notaris_current.notaris_id,
            luas_ukur=hasil_peta_lokasi.luas_ukur,
            luas_nett=hasil_peta_lokasi.luas_nett,
            luas_clear=hasil_peta_lokasi.luas_clear,
            luas_gu_pt=hasil_peta_lokasi.luas_gu_pt,
            luas_gu_perorangan=hasil_peta_lokasi.luas_gu_perorangan,
            geom=wkt.dumps(wkb.loads(draft.geom.data, hex=True)),
            bundle_hd_id=kjb_dt_current.bundle_hd_id,
            harga_akta=kjb_harga_current.harga_akta,
            harga_transaksi=kjb_harga_current.harga_transaksi)
        
        await crud.bidang.update(obj_current=bidang_current, 
                                obj_new=bidang_updated, 
                                updated_by_id=hasil_peta_lokasi.updated_by_id,
                                db_session=db_session,
                                with_commit=False)
        
        
            

        #remove draft
        # await crud.draft.remove(id=draft.id, db_session=db_session)
        await db_session.commit()
    except Exception as e:
        raise HTTPException(status_code=422, detail="error update bidang")

    return {"message" : "successfully update bidang and generate kelengkapan dokumen"}

@router.post("/cloud-task-generate-kelengkapan")
async def update_bidang_and_generate_kelengkapan(payload:HasilPetaLokasiTaskUpdateBidang):

    """Task generate checklist kelengkapan dokumen from hasil peta lokasi"""
    db_session = db.session

    hasil_peta_lokasi = await crud.hasil_peta_lokasi.get(id=payload.hasil_peta_lokasi_id)
    kjb_dt_current = await crud.kjb_dt.get(id=payload.kjb_dt_id)
    kjb_hd_current = await crud.kjb_hd.get(id=kjb_dt_current.kjb_hd_id)

    bidang_current = await crud.bidang.get(id=payload.bidang_id)
    if bidang_current.geom :
        bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))

    #generate kelengkapan dokumen
    if hasil_peta_lokasi.status_hasil_peta_lokasi != StatusHasilPetaLokasiEnum.Batal:
        checklist_kelengkapan_dokumen_hd_current = await crud.checklist_kelengkapan_dokumen_hd.get_by_bidang_id(bidang_id=payload.bidang_id)
        if checklist_kelengkapan_dokumen_hd_current:
            await crud.checklist_kelengkapan_dokumen_hd.delete(id=checklist_kelengkapan_dokumen_hd_current.id, with_commit=False, db_session=db_session)

        master_checklist_dokumens = await crud.checklistdokumen.get_multi_by_jenis_alashak_and_kategori_penjual(
            jenis_alashak=kjb_dt_current.jenis_alashak,
            kategori_penjual=kjb_hd_current.kategori_penjual)
        
        checklist_kelengkapan_dts = []
        for master in master_checklist_dokumens:
            bundle_dt_current = await crud.bundledt.get_by_bundle_hd_id_and_dokumen_id(bundle_hd_id=bidang_current.bundle_hd_id, dokumen_id=master.dokumen_id)
            if not bundle_dt_current:
                code = bidang_current.bundlehd.code + master.dokumen.code
                bundle_dt_current = BundleDtCreateSch(code=code, 
                                            dokumen_id=master.dokumen_id,
                                            bundle_hd_id=bidang_current.bundle_hd_id)
                
                bundle_dt_current = await crud.bundledt.create(obj_in=bundle_dt_current, db_session=db_session, with_commit=False)

            checklist_kelengkapan_dt = ChecklistKelengkapanDokumenDt(
                jenis_bayar=master.jenis_bayar,
                dokumen_id=master.dokumen_id,
                bundle_dt_id=bundle_dt_current.id,
                created_by_id=hasil_peta_lokasi.updated_by_id,
                updated_by_id=hasil_peta_lokasi.updated_by_id)
            
            checklist_kelengkapan_dts.append(checklist_kelengkapan_dt)
        
        checklist_kelengkapan_hd = ChecklistKelengkapanDokumenHd(bidang_id=payload.bidang_id, details=checklist_kelengkapan_dts)
        await crud.checklist_kelengkapan_dokumen_hd.create_and_generate(obj_in=checklist_kelengkapan_hd, 
                                                                        created_by_id=hasil_peta_lokasi.updated_by_id, 
                                                                        db_session=db_session, 
                                                                        with_commit=False)
        
    await db_session.commit()

    return {"message" : "successfully generate kelengkapan dokumen"}



@router.post("/cloud-task-remove-link-bidang-and-kelengkapan")
async def remove_link_bidang_and_kelengkapan(bidang_id:UUID):

    """Task Remove link bundle and remove existing kelengkapan dokumen"""

    db_session = db.session

    #bidang
    bidang_old = await crud.bidang.get(id=bidang_id)
    if bidang_old.geom :
        bidang_old.geom = wkt.dumps(wkb.loads(bidang_old.geom.data, hex=True))

    bidang_old_updated = BidangUpdateSch(bundle_hd_id=None, 
                                         status=StatusBidangEnum.Belum_Bebas, 
                                         jenis_bidang=JenisBidangEnum.Standard)

    await crud.bidang.update(obj_current=bidang_old, obj_new=bidang_old_updated, db_session=db_session, with_commit=False)

    #kelengkapan dokumen
    checklist_kelengkapan_hd_old = await crud.checklist_kelengkapan_dokumen_hd.get_by_bidang_id(bidang_id=bidang_old.id)

    await crud.checklist_kelengkapan_dokumen_hd.remove(id=checklist_kelengkapan_hd_old.id)

    return {"message" : "successfully remove link bidang and kelengkapan dokumen"} 