from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_, text
from models.spk_model import Spk
from models.bidang_model import Bidang
from models.order_gambar_ukur_model import OrderGambarUkurBidang
from models.hasil_peta_lokasi_model import HasilPetaLokasi
from models.kjb_model import KjbDt, KjbHd
from models.checklist_kelengkapan_dokumen_model import ChecklistKelengkapanDokumenHd, ChecklistKelengkapanDokumenDt
from models.worker_model import Worker
from schemas.spk_sch import (SpkSch, SpkCreateSch, SpkUpdateSch, SpkByIdSch, SpkPrintOut)
from schemas.spk_kelengkapan_dokumen_sch import SpkKelengkapanDokumenCreateSch, SpkKelengkapanDokumenSch, SpkKelengkapanDokumenUpdateSch
from schemas.bidang_komponen_biaya_sch import BidangKomponenBiayaCreateSch
from schemas.bidang_sch import BidangSrcSch, BidangForSPKByIdSch, BidangForSPKByIdExtSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.enum import JenisBayarEnum
from common.exceptions import (IdNotFoundException, NameExistException)
import crud

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[SpkSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: SpkCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    db_session = db.session
    
    new_obj = await crud.spk.create(obj_in=sch, created_by_id=current_worker.id, with_commit=False)

    for komponen_biaya in sch.spk_beban_biayas:
        komponen_biaya_current = await crud.bidang_komponen_biaya.get_by_bidang_id_and_beban_biaya_id(bidang_id=new_obj.bidang_id, 
                                                                                                      beban_biaya_id=komponen_biaya.beban_biaya_id)
        komponen_biaya_sch = BidangKomponenBiayaCreateSch(bidang_id=new_obj.bidang_id, 
                                                       beban_biaya_id=komponen_biaya.beban_biaya_id, 
                                                       beban_pembeli=komponen_biaya.beban_pembeli)
        
        await crud.bidang_komponen_biaya.create(obj_in=komponen_biaya_sch, created_by_id=current_worker.id, with_commit=False)

    for kelengkapan_dokumen in sch.spk_kelengkapan_dokumens:
        kelengkapan_dokumen_sch = SpkKelengkapanDokumenCreateSch(spk_id=new_obj.id, bundle_dt_id=kelengkapan_dokumen.bundle_dt_id, tanggapan=kelengkapan_dokumen.tanggapan)
        await crud.spk_kelengkapan_dokumen.create(obj_in=kelengkapan_dokumen_sch, created_by_id=current_worker.id, with_commit=False)
    
    await db_session.commit()
    await db_session.refresh(new_obj)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[SpkSch])
async def get_list(
                params: Params=Depends(), 
                order_by:str = None, 
                keyword:str = None, 
                filter_query:str=None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.spk.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[SpkByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.spk.get(id=id)

    if not obj:
        raise IdNotFoundException(Spk, id)
    
    bidang_obj = await crud.bidang.get(id=obj.bidang_id)
    if not bidang_obj:
        raise IdNotFoundException(Bidang, obj.bidang_id)

    harga = await crud.kjb_harga.get_by_kjb_hd_id_and_jenis_alashak(kjb_hd_id=bidang_obj.hasil_peta_lokasi.kjb_dt.kjb_hd_id, jenis_alashak=bidang_obj.jenis_alashak)
    
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
                                  termins=harga.termins)
    
    obj_return = SpkByIdSch(**obj.dict())
    obj_return.bidang = bidang_sch

    # list_beban_biaya = []
    # for bb in obj.spk_beban_biayas:
    #     beban_biaya_sch = SpkBebanBiayaSch(**bb.dict())
    #     beban_biaya_sch.beban_biaya_name = bb.beban_biaya_name
    #     list_beban_biaya.append(beban_biaya_sch)
    
    list_kelengkapan_dokumen = []
    for kd in obj.spk_kelengkapan_dokumens:
        kelengkapan_dokumen_sch = SpkKelengkapanDokumenSch(**kd.dict())
        kelengkapan_dokumen_sch.dokumen_name = kd.dokumen_name
        kelengkapan_dokumen_sch.has_meta_data = kd.has_meta_data
        list_kelengkapan_dokumen.append(kelengkapan_dokumen_sch)

    # obj_return.spk_beban_biayas = list_beban_biaya
    obj_return.spk_kelengkapan_dokumens = list_kelengkapan_dokumen
    return create_response(data=obj_return)
    
    
    # if obj:
    #     return create_response(data=obj)
    # else:
    #     raise IdNotFoundException(Spk, id)

@router.put("/{id}", response_model=PutResponseBaseSch[SpkSch])
async def update(id:UUID, sch:SpkUpdateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    db_session = db.session
    obj_current = await crud.spk.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Spk, id)
    
    obj_updated = await crud.spk.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id, with_commit=False)

    #remove beban 
    
    # list_ids = [beban.id for beban in sch.spk_beban_biayas if beban.id != None]
    # if len(list_ids) > 0:
    #     beban_biaya_will_removed = await crud.spk_beban_biaya.get_not_in_by_ids(list_ids=list_ids)
    #     if len(beban_biaya_will_removed) > 0:
    #         await crud.spk_beban_biaya.remove_multiple_data(list_obj=beban_biaya_will_removed, db_session=db_session)

    # elif len(list_ids) == 0 and len(obj_current.spk_beban_biayas) > 0:
    #     await crud.spk_beban_biaya.remove_multiple_data(list_obj=obj_current.spk_beban_biayas, db_session=db_session)

    
    # for beban_biaya in sch.spk_beban_biayas:
    #     if beban_biaya.id is None:
    #         beban_biaya_sch = SpkBebanBiayaCreateSch(spk_id=id, beban_biaya_id=beban_biaya.beban_biaya_id, beban_pembeli=beban_biaya.beban_pembeli)
    #         await crud.spk_beban_biaya.create(obj_in=beban_biaya_sch, created_by_id=current_worker.id, with_commit=False)
    #     else:
    #         beban_biaya_current = await crud.spk_beban_biaya.get(id=beban_biaya.id)
    #         beban_biaya_sch = SpkBebanBiayaUpdateSch(spk_id=id, beban_biaya_id=beban_biaya.beban_biaya_id, beban_pembeli=beban_biaya.beban_pembeli)
    #         await crud.spk_beban_biaya.update(obj_current=beban_biaya_current, obj_new=beban_biaya_sch, updated_by_id=current_worker.id, with_commit=False)
    
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

    obj = await crud.bidang.get(id=id)

    harga = await crud.kjb_harga.get_by_kjb_hd_id_and_jenis_alashak(kjb_hd_id=obj.hasil_peta_lokasi.kjb_dt.kjb_hd_id, jenis_alashak=obj.jenis_alashak)
    beban = await crud.kjb_bebanbiaya.get_beban_pembeli_by_kjb_hd_id(kjb_hd_id=obj.hasil_peta_lokasi.kjb_dt.kjb_hd_id)
    
    query_kelengkapan = select(ChecklistKelengkapanDokumenDt
                            ).select_from(ChecklistKelengkapanDokumenDt
                            ).join(ChecklistKelengkapanDokumenHd, ChecklistKelengkapanDokumenDt.checklist_kelengkapan_dokumen_hd_id == ChecklistKelengkapanDokumenHd.id
                            ).where(ChecklistKelengkapanDokumenHd.bidang_id == obj.id)
    
    kelengkapan_dokumen = await crud.checklist_kelengkapan_dokumen_dt.get_all_for_spk(query=query_kelengkapan)
    
    obj_return = BidangForSPKByIdExtSch(id=obj.id,
                                  id_bidang=obj.id_bidang,
                                  hasil_analisa_peta_lokasi=obj.hasil_analisa_peta_lokasi,
                                  kjb_no=obj.hasil_peta_lokasi.kjb_dt.kjb_code,
                                  satuan_bayar=obj.hasil_peta_lokasi.kjb_dt.kjb_hd.satuan_bayar,
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
                                  termins=harga.termins)
    
    
    if obj:
        return create_response(data=obj_return)
    else:
        raise IdNotFoundException(Spk, id)

@router.get("/print-out/{id}")
async def search_for_map(id:UUID | str,
                        current_worker:Worker = Depends(crud.worker.get_active_worker)):

    """Get for search"""

    db_session = db.session

    spk_query = text(f"""
                select
                kh.code As kjb_hd_code,
                b.id_bidang,
                b.alashak,
                b.no_peta,
                b.group,
                b.luas_surat,
                b.luas_ukur,
                p.name As pemilik_name,
                ds.name As desa_name,
                nt.name As notaris_name,
                pr.name As project_name,
                pt.name As ptsk_name,
                hpl.hasil_analisa_peta_lokasi As analisa,
                s.jenis_bayar,
                s.nilai,
                s.satuan_bayar,
                mng.name As manager_name,
                sls.name As sales_name
                from spk s
                left join bidang b on s.bidang_id = b.id
                left join hasil_peta_lokasi hpl on b.id = hpl.bidang_id
                left join kjb_dt kd on hpl.kjb_dt_id = kd.id
                left join kjb_hd kh on kd.kjb_hd_id = kh.id
                left join pemilik p on b.pemilik_id = p.id
                left join planing pl on b.planing_id = pl.id
                left join project pr on pl.project_id = pr.id
                left join desa ds on pl.desa_id = ds.id
                left join notaris nt on b.notaris_id = nt.id
                left join skpt sk on b.skpt_id = sk.id
                left join ptsk pt on sk.ptsk_id = pt.id
                left join manager mng on b.manager_id = mng.id
                left join sales sls on b.sales_id = sls.id
                where s.id = '{str(id)}'
        """)

    result = await db_session.execute(spk_query)
    data = result.fetchone()
    result = SpkPrintOut(kjb_hd_code=data["kjb_hd_code"],
                        id_bidang=data["id_bidang"],
                        alashak=data["alashak"],
                        no_peta=data["no_peta"],
                        group=data["group"],
                        luas_surat=data["luas_surat"],
                        luas_ukur=data["luas_ukur"],
                        pemilik_name=data["pemilik_name"],
                        desa_name=data["desa_name"],
                        project_name=data["project_name"],
                        ptsk_name=data["ptsk_name"],
                        analisa=data["analisa"],
                        jenis_bayar=data["jenis_bayar"],
                        nilai=data["nilai"],
                        satuan_bayar=data["satuan_bayar"],
                        manager_name=data["manager_name"],
                        sales_name=data["sales_name"])
    return result