from uuid import UUID
from fastapi import APIRouter, status, Depends, HTTPException, Response
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_, text, or_
from models import (Spk, Bidang, HasilPetaLokasi, ChecklistKelengkapanDokumenHd, ChecklistKelengkapanDokumenDt, Worker)
from models.code_counter_model import CodeCounterEnum
from schemas.spk_sch import (SpkSch, SpkCreateSch, SpkUpdateSch, SpkByIdSch, SpkPrintOut, 
                             SpkDetailPrintOut, SpkRekeningPrintOut, SpkOverlapPrintOut, SpkOverlapPrintOutExt)
from schemas.spk_kelengkapan_dokumen_sch import SpkKelengkapanDokumenCreateSch, SpkKelengkapanDokumenSch, SpkKelengkapanDokumenUpdateSch
from schemas.bidang_komponen_biaya_sch import BidangKomponenBiayaCreateSch, BidangKomponenBiayaUpdateSch, BidangKomponenBiayaSch
from schemas.bidang_sch import BidangSrcSch, BidangForSPKByIdSch, BidangForSPKByIdExtSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.enum import JenisBayarEnum, StatusSKEnum, JenisBidangEnum, SatuanBayarEnum
from common.exceptions import (IdNotFoundException)
from common.generator import generate_code
from services.pdf_service import PdfService
from jinja2 import Environment, FileSystemLoader
import crud
import json

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[SpkSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: SpkCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    db_session = db.session

    sch.code = await generate_code(entity=CodeCounterEnum.Spk, db_session=db_session, with_commit=False)
    
    new_obj = await crud.spk.create(obj_in=sch, created_by_id=current_worker.id, with_commit=False)

    for komponen_biaya in sch.spk_beban_biayas:
        komponen_biaya_current = await crud.bidang_komponen_biaya.get_by_bidang_id_and_beban_biaya_id(bidang_id=new_obj.bidang_id, 
                                                                                                      beban_biaya_id=komponen_biaya.beban_biaya_id)
        
        if komponen_biaya_current:
            komponen_biaya_updated = BidangKomponenBiayaUpdateSch(**komponen_biaya_current.dict())
            komponen_biaya_updated.is_void, komponen_biaya_updated.is_paid, komponen_biaya_updated.is_use, komponen_biaya_updated.remark = [komponen_biaya_current.is_void, komponen_biaya_current.is_paid, komponen_biaya_current.is_use, komponen_biaya.remark]
            await crud.bidang_komponen_biaya.update(obj_current=komponen_biaya_current, obj_new=komponen_biaya_updated,
                                                    db_session=db_session, with_commit=False,
                                                    updated_by_id=current_worker.id)
        else:
            komponen_biaya_sch = BidangKomponenBiayaCreateSch(bidang_id=new_obj.bidang_id, 
                                                        beban_biaya_id=komponen_biaya.beban_biaya_id, 
                                                        beban_pembeli=komponen_biaya.beban_pembeli,
                                                        is_void=False,
                                                        is_paid=False,
                                                        is_use=False,
                                                        remark=komponen_biaya.remark)
            
            await crud.bidang_komponen_biaya.create(obj_in=komponen_biaya_sch, created_by_id=current_worker.id, with_commit=False)

    for kelengkapan_dokumen in sch.spk_kelengkapan_dokumens:
        kelengkapan_dokumen_sch = SpkKelengkapanDokumenCreateSch(spk_id=new_obj.id, bundle_dt_id=kelengkapan_dokumen.bundle_dt_id, tanggapan=kelengkapan_dokumen.tanggapan)
        await crud.spk_kelengkapan_dokumen.create(obj_in=kelengkapan_dokumen_sch, created_by_id=current_worker.id, with_commit=False)
    
    await db_session.commit()
    await db_session.refresh(new_obj)

    new_obj = await crud.spk.get_by_id(id=new_obj.id)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[SpkSch])
async def get_list(
                params: Params=Depends(), 
                order_by:str = None, 
                keyword:str = None, 
                filter_query:str=None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(Spk).select_from(Spk
                    ).join(Bidang, Spk.bidang_id == Bidang.id)
    
    if keyword:
        query = query.filter(
            or_(
                Spk.code.ilike(f'%{keyword}%'),
                Bidang.id_bidang.ilike(f'%{keyword}%'),
                Bidang.alashak.ilike(f'%{keyword}%')
            )
        )

    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
                query = query.where(getattr(Spk, key) == value)

    objs = await crud.spk.get_multi_paginated(params=params, query=query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[SpkByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.spk.get_by_id(id=id)

    if not obj:
        raise IdNotFoundException(Spk, id)
    
    bidang_obj = await crud.bidang.get_by_id(id=obj.bidang_id)
    if not bidang_obj:
        raise IdNotFoundException(Bidang, obj.bidang_id)

    harga = await crud.kjb_harga.get_by_kjb_hd_id_and_jenis_alashak(kjb_hd_id=bidang_obj.hasil_peta_lokasi.kjb_dt.kjb_hd_id, jenis_alashak=bidang_obj.jenis_alashak)
    
    ktp_value:str = ""
    ktp_meta_data = await crud.bundledt.get_meta_data_by_dokumen_name_and_bidang_id(dokumen_name='KTP SUAMI', bidang_id=bidang_obj.id)
    if ktp_meta_data:
        if ktp_meta_data.meta_data is not None and ktp_meta_data.meta_data != "":
            metadata_dict = json.loads(ktp_meta_data.meta_data.replace("'", "\""))
            ktp_value = metadata_dict[f'{ktp_meta_data.key_field}']

    npwp_value:str = ""
    npwp_meta_data = await crud.bundledt.get_meta_data_by_dokumen_name_and_bidang_id(dokumen_name='NPWP', bidang_id=bidang_obj.id)
    if npwp_meta_data:
        if npwp_meta_data.meta_data is not None and npwp_meta_data.meta_data != "": 
            metadata_dict = json.loads(npwp_meta_data.meta_data.replace("'", "\""))
            npwp_value = metadata_dict[f'{npwp_meta_data.key_field}']

    bidang_sch = BidangForSPKByIdSch(id=bidang_obj.id,
                                  id_bidang=bidang_obj.id_bidang,
                                  hasil_analisa_peta_lokasi=bidang_obj.hasil_analisa_peta_lokasi,
                                  kjb_no=bidang_obj.hasil_peta_lokasi.kjb_dt.kjb_code,
                                  satuan_bayar=bidang_obj.hasil_peta_lokasi.kjb_dt.kjb_hd.satuan_bayar,
                                  group=bidang_obj.group,
                                  pemilik_name=bidang_obj.pemilik_name,
                                  alashak=bidang_obj.alashak,
                                  desa_name=bidang_obj.desa_name,
                                  project_name=bidang_obj.project_name,
                                  luas_surat=bidang_obj.luas_surat,
                                  luas_ukur=bidang_obj.luas_ukur,
                                  no_peta=bidang_obj.no_peta,
                                  notaris_name=bidang_obj.notaris_name,
                                  ptsk_name=bidang_obj.ptsk_name,
                                  status_sk=bidang_obj.status_sk,
                                  bundle_hd_id=bidang_obj.bundle_hd_id,
                                  ktp=ktp_value,
                                  npwp=npwp_value,
                                  termins=harga.termins)
    
    obj_return = SpkByIdSch(**obj.dict())
    obj_return.bidang = bidang_sch

    komponen_biayas = await crud.bidang_komponen_biaya.get_multi_by_bidang_id(bidang_id=obj.bidang_id)

    list_komponen_biaya = []
    for kb in komponen_biayas:
        komponen_biaya_sch = BidangKomponenBiayaSch(**kb.dict())
        komponen_biaya_sch.beban_biaya_name = kb.beban_biaya_name
        list_komponen_biaya.append(komponen_biaya_sch)
    
    list_kelengkapan_dokumen = []
    for kd in obj.spk_kelengkapan_dokumens:
        kelengkapan_dokumen_sch = SpkKelengkapanDokumenSch(**kd.dict())
        kelengkapan_dokumen_sch.dokumen_name = kd.dokumen_name
        kelengkapan_dokumen_sch.has_meta_data = kd.has_meta_data
        list_kelengkapan_dokumen.append(kelengkapan_dokumen_sch)

    obj_return.spk_beban_biayas = list_komponen_biaya
    obj_return.spk_kelengkapan_dokumens = list_kelengkapan_dokumen
    return create_response(data=obj_return)

@router.put("/{id}", response_model=PutResponseBaseSch[SpkSch])
async def update(id:UUID, sch:SpkUpdateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    db_session = db.session
    obj_current = await crud.spk.get_by_id(id=id)

    if not obj_current:
        raise IdNotFoundException(Spk, id)
    
    obj_updated = await crud.spk.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id, with_commit=False)

    for komponen_biaya in sch.spk_beban_biayas:
        komponen_biaya_current = await crud.bidang_komponen_biaya.get_by_bidang_id_and_beban_biaya_id(bidang_id=obj_updated.bidang_id, 
                                                                                                      beban_biaya_id=komponen_biaya.beban_biaya_id)
        
        if komponen_biaya_current:
            komponen_biaya_updated = BidangKomponenBiayaUpdateSch(**komponen_biaya_current.dict())
            komponen_biaya_updated.is_void, komponen_biaya_updated.is_paid, komponen_biaya_updated.is_use, komponen_biaya_updated.remark = [komponen_biaya_current.is_void, komponen_biaya_current.is_paid, komponen_biaya_current.is_use, komponen_biaya.remark]
            await crud.bidang_komponen_biaya.update(obj_current=komponen_biaya_current, obj_new=komponen_biaya_updated,
                                                    db_session=db_session, with_commit=False,
                                                    updated_by_id=current_worker.id)
        else:
            komponen_biaya_sch = BidangKomponenBiayaCreateSch(bidang_id=obj_updated.bidang_id, 
                                                        beban_biaya_id=komponen_biaya.beban_biaya_id, 
                                                        beban_pembeli=komponen_biaya.beban_pembeli,
                                                        is_void=False,
                                                        is_paid=False,
                                                        is_use=False,
                                                        remark=komponen_biaya.remark)
            
            await crud.bidang_komponen_biaya.create(obj_in=komponen_biaya_sch, created_by_id=current_worker.id, with_commit=False)


    #remove kelengkapan dokumen 
    list_ids = [kelengkapan_dokumen.id for kelengkapan_dokumen in sch.spk_kelengkapan_dokumens if kelengkapan_dokumen.id != None]
    if len(list_ids) > 0:
        kelengkapan_biaya_will_removed = await crud.spk_kelengkapan_dokumen.get_not_in_by_ids(list_ids=list_ids)

        if len(kelengkapan_biaya_will_removed) > 0:
            await crud.spk_kelengkapan_dokumen.remove_multiple_data(list_obj=kelengkapan_biaya_will_removed, db_session=db_session)
    
    elif len(list_ids) == 0 and len(obj_current.spk_kelengkapan_dokumens) > 0:
        await crud.spk_kelengkapan_dokumen.remove_multiple_data(list_obj=obj_current.spk_kelengkapan_dokumens, db_session=db_session)
    
    for kelengkapan_dokumen in sch.spk_kelengkapan_dokumens:
        if kelengkapan_dokumen.id is None:
            kelengkapan_dokumen_sch = SpkKelengkapanDokumenCreateSch(spk_id=id, bundle_dt_id=kelengkapan_dokumen.bundle_dt_id, tanggapan=kelengkapan_dokumen.tanggapan)
            await crud.spk_kelengkapan_dokumen.create(obj_in=kelengkapan_dokumen_sch, created_by_id=current_worker.id, with_commit=False)
        else:
            kelengkapan_dokumen_current = await crud.spk_kelengkapan_dokumen.get(id=kelengkapan_dokumen.id)
            kelengkapan_dokumen_sch = SpkKelengkapanDokumenUpdateSch(spk_id=id, bundle_dt_id=kelengkapan_dokumen.bundle_dt_id, tanggapan=kelengkapan_dokumen.tanggapan)
            await crud.spk_kelengkapan_dokumen.update(obj_current=kelengkapan_dokumen_current, obj_new=kelengkapan_dokumen_sch, updated_by_id=current_worker.id, with_commit=False)

    
    await db_session.commit()
    await db_session.refresh(obj_updated)

    obj_updated = await crud.spk.get_by_id(id=obj_updated.id)

    return create_response(data=obj_updated)

@router.delete("/delete", response_model=DeleteResponseBaseSch[SpkSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Delete a object"""

    obj_current = await crud.spk.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Spk, id)
    
    obj_deleted = await crud.spk.remove(id=id)

    return obj_deleted

@router.get("/search/bidang", response_model=GetResponsePaginatedSch[BidangSrcSch])
async def get_list(
                params: Params=Depends(),
                keyword:str = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(Bidang.id, Bidang.id_bidang).select_from(Bidang
                    ).join(HasilPetaLokasi, Bidang.id == HasilPetaLokasi.bidang_id)
    
    if keyword:
        query = query.filter(Bidang.id_bidang.ilike(f'%{keyword}%'))


    objs = await crud.bidang.get_multi_paginated(params=params, query=query)
    return create_response(data=objs)

@router.get("/search/bidang/{id}", response_model=GetResponseBaseSch[BidangForSPKByIdExtSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.bidang.get_by_id(id=id)

    hasil_peta_lokasi_current = await crud.hasil_peta_lokasi.get_by_bidang_id(bidang_id=obj.id)
    kjb_dt_current = await crud.kjb_dt.get_by_id(id=hasil_peta_lokasi_current.kjb_dt_id)

    harga = await crud.kjb_harga.get_by_kjb_hd_id_and_jenis_alashak(kjb_hd_id=kjb_dt_current.kjb_hd_id, jenis_alashak=obj.jenis_alashak)
    beban = await crud.kjb_bebanbiaya.get_beban_pembeli_by_kjb_hd_id(kjb_hd_id=kjb_dt_current.kjb_hd_id)
    
    ktp_value:str = ""
    ktp_meta_data = await crud.bundledt.get_meta_data_by_dokumen_name_and_bidang_id(dokumen_name='KTP SUAMI', bidang_id=obj.id)
    if ktp_meta_data:
        if ktp_meta_data.meta_data is not None and ktp_meta_data.meta_data != "":
            metadata_dict = json.loads(ktp_meta_data.meta_data.replace("'", "\""))
            ktp_value = metadata_dict[f'{ktp_meta_data.key_field}']

    npwp_value:str = ""
    npwp_meta_data = await crud.bundledt.get_meta_data_by_dokumen_name_and_bidang_id(dokumen_name='NPWP', bidang_id=obj.id)
    if npwp_meta_data:
        if npwp_meta_data.meta_data is not None and npwp_meta_data.meta_data != "": 
            metadata_dict = json.loads(npwp_meta_data.meta_data.replace("'", "\""))
            npwp_value = metadata_dict[f'{npwp_meta_data.key_field}']
    
    kelengkapan_dokumen = await crud.checklist_kelengkapan_dokumen_dt.get_all_for_spk(bidang_id=obj.id)
    
    obj_return = BidangForSPKByIdExtSch(id=obj.id,
                                  id_bidang=obj.id_bidang,
                                  hasil_analisa_peta_lokasi=hasil_peta_lokasi_current.hasil_analisa_peta_lokasi,
                                  kjb_no=kjb_dt_current.kjb_code,
                                  satuan_bayar=kjb_dt_current.kjb_hd.satuan_bayar,
                                  group=obj.group,
                                  pemilik_name=obj.pemilik_name,
                                  alashak=obj.alashak,
                                  desa_name=obj.desa_name,
                                  project_name=obj.project_name,
                                  luas_surat=obj.luas_surat,
                                  luas_ukur=obj.luas_ukur,
                                  no_peta=obj.no_peta,
                                  notaris_name=obj.notaris_name,
                                  ptsk_name=obj.ptsk_name,
                                  status_sk=obj.status_sk,
                                  bundle_hd_id=obj.bundle_hd_id,
                                  beban_biayas=beban,
                                  kelengkapan_dokumens=kelengkapan_dokumen,
                                  ktp=ktp_value,
                                  npwp=npwp_value,
                                  termins=harga.termins)
    
    
    if obj:
        return create_response(data=obj_return)
    else:
        raise IdNotFoundException(Spk, id)

@router.get("/print-out/{id}")
async def printout(id:UUID | str,
                        current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Get for search"""

    obj = await crud.spk.get_by_id_for_printout(id=id)
    if obj is None:
        raise IdNotFoundException(Spk, id)
    
    filename:str = "spk_clear.html" if obj.jenis_bayar != JenisBayarEnum.PAJAK else "spk_pajak_overlap.html"
    
    spk_header = SpkPrintOut(**dict(obj))
    percentage_value:str = ""
    if spk_header.satuan_bayar == SatuanBayarEnum.Percentage:
        percentage_value = f" {spk_header.nilai}%"
    
    spk_details = []
    no = 1
    obj_beban_biayas = []
    if spk_header.jenis_bayar == JenisBayarEnum.PAJAK:
        obj_beban_biayas = await crud.spk.get_beban_biaya_pajak_by_id_for_printout(id=id)
    else:
        obj_beban_biayas = await crud.spk.get_beban_biaya_by_id_for_printout(id=id)

    for bb in obj_beban_biayas:
        beban_biaya = SpkDetailPrintOut(**dict(bb))
        beban_biaya.no = no
        spk_details.append(beban_biaya)
        no = no + 1

    obj_kelengkapans = await crud.spk.get_kelengkapan_by_id_for_printout(id=id)
    for k in obj_kelengkapans:
        kelengkapan = SpkDetailPrintOut(**dict(k))
        kelengkapan.no = no
        spk_details.append(kelengkapan)
        no = no + 1
    
    overlap_details = []
    if obj.jenis_bidang == JenisBidangEnum.Overlap:
        filename:str = "spk_overlap.html" if obj.jenis_bayar != JenisBayarEnum.PAJAK else "spk_pajak_overlap.html"
        obj_overlaps = await crud.spk.get_overlap_by_id_for_printout(id=id)
        for ov in obj_overlaps:
            overlap = SpkOverlapPrintOutExt(**dict(ov))
            overlap.luas_overlapExt = "{:,.2f}".format(overlap.luas_overlap)
            overlap.luas_suratExt = "{:,.2f}".format(overlap.luas_surat)
            overlap.tipe_overlapExt = overlap.tipe_overlap.value.replace('_', ' ')
            overlap_details.append(overlap)

    rekening:str = ""
    if obj.jenis_bayar != JenisBayarEnum.PAJAK:
        rekenings = await crud.spk.get_rekening_by_id_for_printout(id=id)
        for r in rekenings:
            rek = SpkRekeningPrintOut(**dict(r))
            rekening += f"{rek.rekening}, "
        
        rekening = rekening[0:-2]

    
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template(filename)

    akta_peralihan = "PPJB" if spk_header.status_il == StatusSKEnum.Belum_IL else "SPH"

    render_template = template.render(kjb_hd_code=spk_header.kjb_hd_code,
                                      jenisbayar=f'{spk_header.jenis_bayar.value}{percentage_value}',
                                      group=spk_header.group, 
                                      pemilik_name=spk_header.pemilik_name,
                                      alashak=spk_header.alashak,
                                      desa_name=spk_header.desa_name,
                                      luas_surat="{:,.0f}".format(spk_header.luas_surat),
                                      luas_ukur="{:,.0f}".format(spk_header.luas_ukur), 
                                      id_bidang=spk_header.id_bidang,
                                      no_peta=spk_header.no_peta,
                                      notaris_name=spk_header.notaris_name,
                                      project_name=spk_header.project_name, 
                                      ptsk=spk_header.ptsk_name,
                                      status_il=spk_header.status_il.value.replace("_"," "),
                                      hasil_analisa_peta_lokasi=spk_header.analisa.value,
                                      data=spk_details,
                                      data_overlap=overlap_details,
                                      worker_name=spk_header.worker_name, 
                                      manager_name=spk_header.manager_name,
                                      sales_name=spk_header.sales_name,
                                      akta_peralihan=akta_peralihan,
                                      no_rekening=rekening)
    
    try:
        doc = await PdfService().get_pdf(render_template)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed generate document")
    
    response = Response(doc, media_type='application/pdf')
    response.headers["Content-Disposition"] = f"attachment; filename={spk_header.kjb_hd_code}.pdf"
    return response