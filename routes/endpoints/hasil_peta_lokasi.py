from uuid import UUID
from fastapi import APIRouter, status, Depends, UploadFile, Response
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
                                           HasilPetaLokasiUpdateSch, HasilPetaLokasiUpdateExtSch)
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
from shapely import wkb, wkt
from geoalchemy2 import functions

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[HasilPetaLokasiSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: HasilPetaLokasiCreateExtSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    db_session = db.session

    obj_current = await crud.hasil_peta_lokasi.get_by_kjb_dt_id(kjb_dt_id=sch.kjb_dt_id)
    if obj_current:
        raise ContentNoChangeException(detail="Alashak Sudah input hasil peta lokasi")
    
    # obj_current = await crud.hasil_peta_lokasi.get_by_bidang_id(bidang_id=sch.bidang_id)
    # if obj_current:
    #     raise ContentNoChangeException(detail="Bidang Sudah input hasil peta lokasi")
    
    bidang_current = await crud.bidang.get(id=sch.bidang_id)
    if bidang_current.geom :
        bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))
    
    kjb_dt_current = await crud.kjb_dt.get(id=sch.kjb_dt_id)
    kjb_hd_current = kjb_dt_current.kjb_hd
    tanda_terima_notaris_current = await crud.tandaterimanotaris_hd.get_one_by_kjb_dt_id(kjb_dt_id=kjb_dt_current.id)

    tipe_proses = TipeProsesEnum.Standard
    jenis_bidang = JenisBidangEnum.Standard
    status_bidang = StatusBidangEnum.Deal
    sch.hasil_analisa_peta_lokasi = HasilAnalisaPetaLokasiEnum.Clear

    if sch.status_hasil_peta_lokasi == StatusHasilPetaLokasiEnum.Batal:
        status_bidang = StatusBidangEnum.Batal

    if len(sch.hasilpetalokasidetails) > 0:
        tipe_proses = TipeProsesEnum.Overlap
        jenis_bidang = JenisBidangEnum.Overlap
        sch.hasil_analisa_peta_lokasi = HasilAnalisaPetaLokasiEnum.Overlap

    new_obj = await crud.hasil_peta_lokasi.create(obj_in=sch, created_by_id=current_worker.id, db_session=db_session, with_commit=False)

    draft_header_id = None  
    for dt in sch.hasilpetalokasidetails:

        bidang_overlap_id = None
        if dt.draft_detail_id is not None:
            #input bidang overlap dari hasil analisa
            draft_detail = await crud.draft_detail.get(id=dt.draft_detail_id)
            if draft_detail is None:
                raise ContentNoChangeException(detail="Bidang Overlap tidak exists di Draft Detail")
            
            draft_header_id = draft_detail.draft_id
            
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

        detail_sch = HasilPetaLokasiDetailCreateSch(
            tipe_overlap=dt.tipe_overlap,
            bidang_id=dt.bidang_id,
            hasil_peta_lokasi_id=new_obj.id,
            luas_overlap=dt.luas_overlap,
            keterangan=dt.keterangan,
            status_luas=dt.status_luas,
            bidang_overlap_id=bidang_overlap_id
        )

        await crud.hasil_peta_lokasi_detail.create(obj_in=detail_sch, created_by_id=current_worker.id, db_session=db_session, with_commit=False)

    #update bidang from hasil peta lokasi
    draft = None
    if draft_header_id:
        draft = await crud.draft.get(id=draft_header_id)
    else:
        draft = await crud.draft.get_by_rincik_id(rincik_id=sch.bidang_id)

    bidang_updated = BidangSch(
        tipe_proses=tipe_proses,
        jenis_bidang=jenis_bidang,
        status=status_bidang,
        pemilik_id=sch.pemilik_id,
        luas_surat=sch.luas_surat,
        planing_id=sch.planing_id,
        skpt_id=sch.skpt_id,
        group=kjb_hd_current.nama_group,
        jenis_alashak=kjb_dt_current.jenis_alashak,
        jenis_surat_id=kjb_dt_current.jenis_surat_id,
        alashak=kjb_dt_current.alashak,
        manager_id=kjb_hd_current.manager_id,
        sales_id=kjb_hd_current.sales_id,
        mediator=kjb_hd_current.mediator,
        telepon_mediator=kjb_hd_current.telepon_mediator,
        notaris_id=tanda_terima_notaris_current.notaris_id,
        luas_ukur=sch.luas_ukur,
        luas_nett=sch.luas_nett,
        luas_clear=sch.luas_clear,
        luas_gu_pt=sch.luas_gu_pt,
        luas_gu_perorangan=sch.luas_gu_perorangan,
        geom=wkt.dumps(wkb.loads(draft.geom.data, hex=True)),
        bundle_hd_id=kjb_dt_current.bundle_hd_id)
    
    await crud.bidang.update(obj_current=bidang_current, obj_new=bidang_updated, 
                             db_session=db_session, with_commit=False, updated_by_id=current_worker.id)
    
    #generate kelengkapan dokumen
    master_checklist_dokumens = await crud.checklistdokumen.get_multi_by_jenis_alashak_and_kategori_penjual(
        jenis_alashak=bidang_current.jenis_alashak,
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
            created_by_id=current_worker.id,
            updated_by_id=current_worker.id)
        
        checklist_kelengkapan_dts.append(checklist_kelengkapan_dt)
    
    checklist_kelengkapan_hd = ChecklistKelengkapanDokumenHd(bidang_id=sch.bidang_id, details=checklist_kelengkapan_dts)
    await crud.checklist_kelengkapan_dokumen_hd.create_and_generate(obj_in=checklist_kelengkapan_hd, created_by_id=current_worker.id, db_session=db_session, with_commit=False)
    
    #remove draft
    if draft:
        if len(draft.details) > 0:
            await crud.draft_detail.remove_multiple_data(list_obj=draft.details, db_session=db_session)
        await crud.draft.remove(id=draft.id, db_session=db_session)
    else:
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
            sch:HasilPetaLokasiUpdateExtSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    db_session = db.session
    obj_current = await crud.hasil_peta_lokasi.get(id=id)
    if not obj_current:
        raise IdNotFoundException(HasilPetaLokasi, id)
    
    #remove link bundle dan kelengkapan dokumen jika pada update yg dipilih bidang berbeda
    if obj_current.bidang_id != sch.bidang_id:
        #bidang
        bidang_old = obj_current.bidang
        if bidang_old.geom :
            bidang_old.geom = wkt.dumps(wkb.loads(bidang_old.geom.data, hex=True))

        bidang_old_updated = BidangUpdateSch(bundle_hd_id=None, status=StatusBidangEnum.Belum_Bebas)

        await crud.bidang.update(obj_current=bidang_old, obj_new=bidang_old_updated, db_session=db_session, with_commit=False)

        #kelengkapan dokumen
        hds = []
        checklist_kelengkapan_hd_old = await crud.checklist_kelengkapan_dokumen_hd.get_by_bidang_id(bidang_id=bidang_old.id)
        hds.append(checklist_kelengkapan_hd_old)

        await crud.checklist_kelengkapan_dokumen_dt.remove_multiple_data(list_obj=checklist_kelengkapan_hd_old.details, db_session=db_session)
        await crud.checklist_kelengkapan_dokumen_hd.remove_multiple_data(list_obj=hds, db_session=db_session)
    
    #remove existing data detail dan overlap
    list_overlap = [ov.bidang_overlap for ov in obj_current.details if ov.bidang_overlap != None]

    await crud.hasil_peta_lokasi_detail.remove_multiple_data(list_obj=obj_current.details, db_session=db_session)
    await crud.bidangoverlap.remove_multiple_data(list_obj=list_overlap, db_session=db_session)
    
    tipe_proses = TipeProsesEnum.Standard
    jenis_bidang = JenisBidangEnum.Standard
    status_bidang = StatusBidangEnum.Belum_Bebas
    sch.hasil_analisa_peta_lokasi = HasilAnalisaPetaLokasiEnum.Clear

    if sch.status_hasil_peta_lokasi == StatusHasilPetaLokasiEnum.Batal:
        status_bidang = StatusBidangEnum.Batal

    if len(sch.hasilpetalokasidetails) > 0:
        tipe_proses = TipeProsesEnum.Overlap
        jenis_bidang = JenisBidangEnum.Overlap
        sch.hasil_analisa_peta_lokasi = HasilAnalisaPetaLokasiEnum.Overlap

    #update hasil peta lokasi
    sch_updated = HasilPetaLokasiUpdateSch(**sch.dict())
    sch_updated.file_path = obj_current.file_path
    obj_updated = await crud.hasil_peta_lokasi.update(obj_current=obj_current, obj_new=sch_updated,
                                                       updated_by_id=current_worker.id, db_session=db_session, with_commit=False)
    

    bidang_current = await crud.bidang.get(id=sch.bidang_id)
    if bidang_current.geom :
        bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))
    
    kjb_dt_current = await crud.kjb_dt.get(id=sch.kjb_dt_id)
    kjb_hd_current = kjb_dt_current.kjb_hd
    tanda_terima_notaris_current = await crud.tandaterimanotaris_hd.get_one_by_kjb_dt_id(kjb_dt_id=kjb_dt_current.id)

    draft_header_id = None  
    for dt in sch.hasilpetalokasidetails:

        bidang_overlap_id = None
        if dt.draft_detail_id is not None:
            #input bidang overlap dari hasil analisa

            draft_detail = await crud.draft_detail.get(id=dt.draft_detail_id)
            if draft_detail is None:
                raise ContentNoChangeException(detail="Bidang Overlap tidak exists di Draft Detail")
            
            draft_header_id = draft_detail.draft_id
            
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

        detail_sch = HasilPetaLokasiDetailCreateSch(
            tipe_overlap=dt.tipe_overlap,
            bidang_id=dt.bidang_id,
            hasil_peta_lokasi_id=obj_updated.id,
            luas_overlap=dt.luas_overlap,
            keterangan=dt.keterangan,
            status_luas=dt.status_luas,
            bidang_overlap_id=bidang_overlap_id
        )

        await crud.hasil_peta_lokasi_detail.create(obj_in=detail_sch, created_by_id=current_worker.id, db_session=db_session, with_commit=False)

    #update bidang from hasil peta lokasi
    draft = None
    if draft_header_id:
        draft = await crud.draft.get(id=draft_header_id)
    else:
        draft = await crud.draft.get_by_rincik_id(rincik_id=sch.bidang_id)

    bidang_updated = BidangSch(
        tipe_proses=tipe_proses,
        jenis_bidang=jenis_bidang,
        status=status_bidang,
        pemilik_id=sch.pemilik_id,
        luas_surat=sch.luas_surat,
        planing_id=sch.planing_id,
        skpt_id=sch.skpt_id,
        group=kjb_hd_current.nama_group,
        jenis_alashak=kjb_dt_current.jenis_alashak,
        jenis_surat_id=kjb_dt_current.jenis_surat_id,
        alashak=kjb_dt_current.alashak,
        manager_id=kjb_hd_current.manager_id,
        sales_id=kjb_hd_current.sales_id,
        mediator=kjb_hd_current.mediator,
        telepon_mediator=kjb_hd_current.telepon_mediator,
        notaris_id=tanda_terima_notaris_current.notaris_id,
        luas_ukur=sch.luas_ukur,
        luas_nett=sch.luas_nett,
        luas_clear=sch.luas_clear,
        luas_gu_pt=sch.luas_gu_pt,
        luas_gu_perorangan=sch.luas_gu_perorangan,
        geom=wkt.dumps(wkb.loads(draft.geom.data, hex=True)),
        bundle_hd_id=kjb_dt_current.bundle_hd_id)
    
    await crud.bidang.update(obj_current=bidang_current, obj_new=bidang_updated, 
                             db_session=db_session, with_commit=False, updated_by_id=current_worker.id)
    

    #generate kelengkapan dokumen
    if obj_current.bidang_id != sch.bidang_id:
        master_checklist_dokumens = await crud.checklistdokumen.get_multi_by_jenis_alashak_and_kategori_penjual(
            jenis_alashak=bidang_current.jenis_alashak,
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
                created_by_id=current_worker.id,
                updated_by_id=current_worker.id)
            
            checklist_kelengkapan_dts.append(checklist_kelengkapan_dt)
        
        checklist_kelengkapan_hd = ChecklistKelengkapanDokumenHd(bidang_id=sch.bidang_id, details=checklist_kelengkapan_dts)
        await crud.checklist_kelengkapan_dokumen_hd.create_and_generate(obj_in=checklist_kelengkapan_hd, created_by_id=current_worker.id, db_session=db_session, with_commit=False)
    
    #remove draft
    
    if draft:
        if len(draft.details) > 0:
            await crud.draft_detail.remove_multiple_data(list_obj=draft.details, db_session=db_session)
        await crud.draft.remove(id=draft.id, db_session=db_session)
    else:
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

    status_ = [StatusBidangEnum.Batal, StatusBidangEnum.Belum_Bebas]
    query = select(Bidang.id, Bidang.id_bidang).select_from(Bidang
                    ).where(and_(
                                Bidang.status.in_(status_),
                                Bidang.jenis_bidang != JenisBidangEnum.Bintang
                            ))
    
    if keyword:
        query = query.filter(Bidang.id_bidang.ilike(f'%{keyword}%'))


    objs = await crud.bidang.get_multi_paginated(params=params, query=query)
    return create_response(data=objs)

# @router.get("/search/bidang/{id}", response_model=GetResponseBaseSch[BidangForSPKByIdExt])
# async def get_by_id(id:UUID):

#     """Get an object by id"""

#     obj = await crud.bidang.get(id=id)

#     harga = await crud.kjb_harga.get_by_kjb_hd_id_and_jenis_alashak(kjb_hd_id=obj.hasil_peta_lokasi.kjb_dt.kjb_hd_id, jenis_alashak=obj.jenis_alashak)
#     beban = await crud.kjb_bebanbiaya.get_beban_pembeli_by_kjb_hd_id(kjb_hd_id=obj.hasil_peta_lokasi.kjb_dt.kjb_hd_id)
    
#     query_kelengkapan = select(ChecklistKelengkapanDokumenDt
#                             ).select_from(ChecklistKelengkapanDokumenDt
#                             ).join(ChecklistKelengkapanDokumenHd, ChecklistKelengkapanDokumenDt.checklist_kelengkapan_dokumen_hd_id == ChecklistKelengkapanDokumenHd.id
#                             ).where(ChecklistKelengkapanDokumenHd.bidang_id == obj.id)
    
#     kelengkapan_dokumen = await crud.checklist_kelengkapan_dokumen_dt.get_all_for_spk(query=query_kelengkapan)
    
#     obj_return = BidangForSPKByIdExt(id=obj.id,
#                                   id_bidang=obj.id_bidang,
#                                   hasil_analisa_peta_lokasi=obj.hasil_analisa_peta_lokasi,
#                                   kjb_no=obj.hasil_peta_lokasi.kjb_dt.kjb_code,
#                                   satuan_bayar=obj.hasil_peta_lokasi.kjb_dt.kjb_hd.satuan_bayar,
#                                   group=obj.group,
#                                   pemilik_name=obj.pemilik_name,
#                                   alashak=obj.alashak,
#                                   desa_name=obj.desa_name,
#                                   project_name=obj.project_name,
#                                   luas_surat=obj.luas_surat,
#                                   luas_ukur=obj.luas_ukur,
#                                   no_peta=obj.no_peta,
#                                   notaris_name=obj.notaris_name,
#                                   ptsk_name=obj.ptsk_name,
#                                   status_sk=obj.status_sk,
#                                   bundle_hd_id=obj.bundle_hd_id,
#                                   beban_biayas=beban,
#                                   kelengkapan_dokumens=kelengkapan_dokumen,
#                                   termins=harga.termins)
    
    
#     if obj:
#         return create_response(data=obj_return)
#     else:
#         raise IdNotFoundException(Spk, id)