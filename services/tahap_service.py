from fastapi import HTTPException, status
from fastapi_async_sqlalchemy import db

from models import Tahap

from schemas.tahap_sch import TahapCreateSch, TahapUpdateSch
from schemas.tahap_detail_sch import TahapDetailCreateSch, TahapDetailUpdateSch

from uuid import UUID
from shapely import wkb, wkt

import crud



class TahapService:

    async def create_tahap(self, sch: TahapCreateSch, created_by_id: UUID) -> Tahap:

        db_session = db.session

        obj_planing = await crud.planing.get(id=sch.planing_id)
        if not obj_planing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planing not found!")
        
        new_last_tahap = 0
        project_current = await crud.project.get(id=obj_planing.project_id)
        main_project_current = await crud.main_project.get(id=project_current.main_project_id)
        if main_project_current:
            new_last_tahap = (main_project_current.last_tahap or 0) + 1
        else:
            sub_project_current = await crud.sub_project.get(id=sch.sub_project_id)
            if not sub_project_current:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sub Project not found!")
            
            main_project_current = await crud.main_project.get(id=sub_project_current.main_project_id)
            new_last_tahap = (main_project_current.last_tahap or 0) + 1

        main_project_updated = {"last_tahap" : new_last_tahap}

        await crud.section.update(obj_current=main_project_current, obj_new=main_project_updated, 
                                db_session=db_session, with_commit=False, updated_by_id=created_by_id)
        
        sch.nomor_tahap = new_last_tahap

        new_obj = await crud.tahap.create(obj_in=sch, db_session=db_session, with_commit=False, created_by_id=created_by_id)

        for dt in sch.details:
            dt_sch = TahapDetailCreateSch(tahap_id=new_obj.id, bidang_id=dt.bidang_id, is_void=False)
            await crud.tahap_detail.create(obj_in=dt_sch, db_session=db_session, with_commit=False, created_by_id=created_by_id)

            bidang_current = await crud.bidang.get_by_id(id=dt.bidang_id)
            if bidang_current.geom :
                bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))
            if bidang_current.geom_ori:
                bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))
            
            bidang_updated = {
                "luas_bayar" : dt.luas_bayar,
                "harga_akta" : dt.harga_akta,
                "harga_transaksi" : dt.harga_transaksi
            }
            
            await crud.bidang.update(obj_current=bidang_current, obj_new=bidang_updated, with_commit=False, db_session=db_session, updated_by_id=created_by_id)

            # JIKA ADA PERUBAHAN HARGA TRANSAKSI / HARGA AKTA AKAN MENGUPDATE KE KJB DT
            if bidang_current.harga_transaksi != dt.harga_transaksi or bidang_current.harga_akta != dt.harga_akta:
                hasil_peta_lokasi_current = await crud.hasil_peta_lokasi.get_by_bidang_id(bidang_id=dt.bidang_id)
                kjb_dt_current = await crud.kjb_dt.get(id=hasil_peta_lokasi_current.kjb_dt_id)

                kjb_dt_updated = {
                    "harga_akta": dt.harga_akta,
                    "harga_transaksi": dt.harga_transaksi
                }

                await crud.kjb_dt.update(obj_current=kjb_dt_current, obj_new=kjb_dt_updated, with_commit=False, db_session=db_session, updated_by_id=created_by_id)


            for ov in dt.overlaps:
                bidang_overlap_current = await crud.bidangoverlap.get(id=ov.id)
                if bidang_overlap_current.geom :
                    geom_ov = wkt.dumps(wkb.loads(bidang_overlap_current.geom.data, hex=True))
                    bidang_overlap_current.geom = geom_ov
                if bidang_overlap_current.geom_temp :
                    geom_temp_ov = wkt.dumps(wkb.loads(bidang_overlap_current.geom_temp.data, hex=True))
                    bidang_overlap_current.geom_temp = geom_temp_ov

                bidang_overlap_updated = {
                    "is_show": ov.is_show,
                    "kategori": ov.kategori,
                    "luas_bayar": ov.luas_bayar,
                    "harga_transaksi": ov.harga_transaksi
                }
                
                await crud.bidangoverlap.update(obj_current=bidang_overlap_current, obj_new=bidang_overlap_updated,
                                                with_commit=False, db_session=db_session,
                                                updated_by_id=created_by_id)
        try:
            await db_session.commit()
            await db_session.refresh(new_obj)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed Create Tahap")

        return new_obj
    
    async def update_tahap(self, id:UUID, sch: TahapUpdateSch, updated_by_id: UUID) -> Tahap:

        db_session = db.session

        obj_current = await crud.tahap.get(id=id)
        if not obj_current:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tahap not found!")
        
        obj_updated = await crud.tahap.update(obj_current=obj_current, obj_new=sch, db_session=db_session, with_commit=False, updated_by_id=updated_by_id)

        tahap_details = await crud.tahap_detail.get_multi_by_tahap_id(tahap_id=obj_updated.id)
        current_ids = [dt.id for dt in tahap_details]
        update_ids = [dt.id for dt in sch.details]

        for current_id in current_ids:
            if current_id not in update_ids:
                tahap_detail_current = next((tahap_detail for tahap_detail in tahap_details if tahap_detail.id == current_id), None)
                invoices = await crud.invoice.get_multi_invoice_active_by_bidang_id(bidang_id=tahap_detail_current.bidang_id)
                if len(invoices) > 0:
                    bidang = await crud.bidang.get(id=tahap_detail_current.bidang_id)
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Bidang {bidang.id_bidang} tidak dapat dihapus karena memiliki invoice yang aktif")

        # DETAIL
        for dt in sch.details:
            tahap_detail_current = await crud.tahap_detail.get(id=dt.id)
            if tahap_detail_current is None:
                tahap_detail_sch = TahapDetailCreateSch(tahap_id=obj_current.id, bidang_id=dt.bidang_id, is_void=False)
                await crud.tahap_detail.create(obj_in=tahap_detail_sch, db_session=db_session, with_commit=False, created_by_id=updated_by_id)
            else:
                tahap_detail_sch = TahapDetailUpdateSch(**tahap_detail_current.dict())

                await crud.tahap_detail.update(obj_current=tahap_detail_current, obj_new=tahap_detail_sch, with_commit=False, db_session=db_session, updated_by_id=updated_by_id)
            
            bidang_current = await crud.bidang.get_by_id(id=dt.bidang_id)

            # JIKA ADA PERUBAHAN HARGA TRANSAKSI / HARGA AKTA / LUAS BAYAR AKAN
            if bidang_current.harga_transaksi != dt.harga_transaksi or bidang_current.harga_akta != dt.harga_akta or bidang_current.luas_bayar != dt.luas_bayar:
                
                if bidang_current.geom :
                    bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))
                if bidang_current.geom_ori:
                    bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))

                bidang_updated = {
                    "luas_bayar" : dt.luas_bayar,
                    "harga_akta" : dt.harga_akta,
                    "harga_transaksi" : dt.harga_transaksi
                }
                
                await crud.bidang.update(obj_current=bidang_current, obj_new=bidang_updated, with_commit=False, db_session=db_session, updated_by_id=updated_by_id)

                # JIKA ADA PERUBAHAN HARGA TRANSAKSI / HARGA AKTA AKAN MENGUPDATE KE KJB DT
                if bidang_current.harga_transaksi != dt.harga_transaksi or bidang_current.harga_akta != dt.harga_akta:
                    hasil_peta_lokasi_current = await crud.hasil_peta_lokasi.get_by_bidang_id(bidang_id=dt.bidang_id)
                    kjb_dt_current = await crud.kjb_dt.get(id=hasil_peta_lokasi_current.kjb_dt_id)

                    kjb_dt_updated = {
                        "harga_akta": dt.harga_akta,
                        "harga_transaksi": dt.harga_transaksi
                    }

                    await crud.kjb_dt.update(obj_current=kjb_dt_current, obj_new=kjb_dt_updated, with_commit=False, db_session=db_session, updated_by_id=updated_by_id)

            
            for ov in dt.overlaps:
                bidang_overlap_current = await crud.bidangoverlap.get(id=ov.id)
                if bidang_overlap_current.geom :
                    geom_ov = wkt.dumps(wkb.loads(bidang_overlap_current.geom.data, hex=True))
                    bidang_overlap_current.geom = geom_ov
                if bidang_overlap_current.geom_temp :
                    geom_temp_ov = wkt.dumps(wkb.loads(bidang_overlap_current.geom_temp.data, hex=True))
                    bidang_overlap_current.geom_temp = geom_temp_ov
                    
                bidang_overlap_updated = {
                    "is_show": ov.is_show,
                    "kategori": ov.kategori,
                    "luas_bayar": ov.luas_bayar,
                    "harga_transaksi": ov.harga_transaksi
                }
                
                await crud.bidangoverlap.update(obj_current=bidang_overlap_current, obj_new=bidang_overlap_updated,
                                                with_commit=False, db_session=db_session,
                                                updated_by_id=updated_by_id)
        try:
            await db_session.commit()
            await db_session.refresh(obj_updated)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed update Tahap")
        
        return obj_updated