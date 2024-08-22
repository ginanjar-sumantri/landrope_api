from fastapi import HTTPException, Request, UploadFile, status
from fastapi_async_sqlalchemy import db
from sqlmodel import delete, and_

from models import (Spk, Worker, SpkKelengkapanDokumen, ChecklistKelengkapanDokumenDt)
from models.code_counter_model import CodeCounterEnum

from common.generator import generate_code
from common.enum import (jenis_bayar_to_text, jenis_bayar_to_spk_status_pembebasan, 
                        JenisBayarEnum, WorkflowEntityEnum, WorkflowLastStatusEnum,
                        SatuanBayarEnum, JenisBidangEnum, StatusSKEnum, JenisAlashakEnum)

from schemas.spk_sch import (SpkCreateSch, SpkUpdateSch, SpkByIdSch, SpkPrintOut, SpkDetailPrintOut, SpkOverlapPrintOutExt, SpkRekeningPrintOut)
from schemas.spk_kelengkapan_dokumen_sch import (SpkKelengkapanDokumenCreateSch, SpkKelengkapanDokumenUpdateSch, SpkKelengkapanDokumenSch)
from schemas.bidang_sch import BidangForSPKByIdSch, BidangForSPKByIdExtSch
from schemas.bidang_komponen_biaya_sch import (BidangKomponenBiayaUpdateSch, BidangKomponenBiayaCreateSch, BidangKomponenBiayaSch)
from schemas.bundle_dt_sch import BundleDtRiwayatSch
from schemas.checklist_kelengkapan_dokumen_dt_sch import ChecklistKelengkapanDokumenDtSch
from schemas.kjb_termin_sch import KjbTerminInSpkSch
from schemas.rekening_sch import RekeningSch
from schemas.workflow_sch import WorkflowCreateSch, WorkflowUpdateSch, WorkflowSystemCreateSch, WorkflowSystemAttachmentSch

from services.helper_service import BidangHelper, BundleHelper
from services.gcloud_task_service import GCloudTaskService
from services.gcloud_storage_service import GCStorageService
from services.history_service import HistoryService
from services.pdf_service import PdfService
from services.encrypt_service import encrypt_id
from services.workflow_service import WorkflowService

from uuid import UUID, uuid4
from io import BytesIO
from jinja2 import Environment, FileSystemLoader
import crud
import json
import logging

class SpkService:

    # INITIALIZE SPK 
    async def init_spk(self, sch:SpkCreateSch | SpkUpdateSch, current_worker:Worker, id_bidang:str, db_session) -> Spk:
        code = await generate_code(entity=CodeCounterEnum.Spk, db_session=db_session, with_commit=False)
        jenis_bayar = jenis_bayar_to_text.get(sch.jenis_bayar, sch.jenis_bayar)
        sch.code = f"SPK-{jenis_bayar}/{code}/{id_bidang}"
        
        new_obj = await crud.spk.create(obj_in=sch, created_by_id=current_worker.id, with_commit=False)
        return new_obj
    
    # INITIALIZE KOMPONEN BIAYA
    async def init_komponen_biaya(self, sch:SpkCreateSch | SpkUpdateSch, current_worker:Worker, db_session):
        bidang_komponen_biayas = await crud.bidang_komponen_biaya.get_multi_by_bidang_id(bidang_id=sch.bidang_id)
        kjb_beban_biayas = await crud.kjb_bebanbiaya.get_kjb_beban_by_bidang_id(bidang_id=sch.bidang_id)
        
        if len(bidang_komponen_biayas) > 0:
            bidang_komponen_biaya_ids = [beban.beban_biaya_id for beban in bidang_komponen_biayas]
            sch_beban_biaya_ids = [beban.beban_biaya_id for beban in sch.spk_beban_biayas if beban.beban_biaya_id not in bidang_komponen_biaya_ids]
            beban_biaya_ids = bidang_komponen_biaya_ids + sch_beban_biaya_ids
        else:
            kjb_beban_biaya_ids = [beban.beban_biaya_id for beban in kjb_beban_biayas]
            sch_beban_biaya_ids = [beban.beban_biaya_id for beban in sch.spk_beban_biayas if beban.beban_biaya_id not in kjb_beban_biaya_ids]
            beban_biaya_ids = kjb_beban_biaya_ids + sch_beban_biaya_ids

        for beban_biaya_id in beban_biaya_ids:
            obj_komponen_biaya_current = await crud.bidang_komponen_biaya.get_by_bidang_id_and_beban_biaya_id(bidang_id=sch.bidang_id, beban_biaya_id=beban_biaya_id)
            sch_komponen_biaya = next((schema for schema in sch.spk_beban_biayas if schema.beban_biaya_id == beban_biaya_id), None)
            kjb_beban_biaya = next((kjb_beban for kjb_beban in kjb_beban_biayas if kjb_beban.beban_biaya_id == beban_biaya_id), None)

            if obj_komponen_biaya_current:
                if sch_komponen_biaya:
                    obj_komponen_biaya_updated = BidangKomponenBiayaUpdateSch(**obj_komponen_biaya_current.dict(exclude={"beban_pembeli", "remark", "is_exclude_spk"}), 
                                                                                beban_pembeli=sch_komponen_biaya.beban_pembeli,
                                                                                is_exclude_spk=False,
                                                                                remark=sch_komponen_biaya.remark)
                else:
                    obj_komponen_biaya_updated = BidangKomponenBiayaUpdateSch(**obj_komponen_biaya_current.dict(exclude={"beban_pembeli", "remark", "is_exclude_spk"}), 
                                                                                beban_pembeli=obj_komponen_biaya_current.beban_pembeli,
                                                                                is_exclude_spk=True,
                                                                                remark=obj_komponen_biaya_current.remark)
                
                await crud.bidang_komponen_biaya.update(obj_current=obj_komponen_biaya_current, 
                                                        obj_new=obj_komponen_biaya_updated,
                                                        db_session=db_session, with_commit=False,
                                                        updated_by_id=current_worker.id)
            else:
                master_beban_biaya = await crud.bebanbiaya.get(id=beban_biaya_id)
                obj_komponen_biaya_new = BidangKomponenBiayaCreateSch(bidang_id=sch.bidang_id, 
                                                            beban_biaya_id=beban_biaya_id, 
                                                            beban_pembeli=sch_komponen_biaya.beban_pembeli if sch_komponen_biaya else kjb_beban_biaya.beban_pembeli,
                                                            is_void=False,
                                                            is_paid=False,
                                                            is_retur=False,
                                                            is_add_pay=master_beban_biaya.is_add_pay,
                                                            remark=sch_komponen_biaya.remark if sch_komponen_biaya else "",
                                                            satuan_bayar=master_beban_biaya.satuan_bayar,
                                                            satuan_harga=master_beban_biaya.satuan_harga,
                                                            formula=master_beban_biaya.formula,
                                                            amount=master_beban_biaya.amount,
                                                            order_number=sch_komponen_biaya.order_number if sch_komponen_biaya else None,
                                                            is_exclude_spk=False if sch_komponen_biaya else True) 
                await crud.bidang_komponen_biaya.create(obj_in=obj_komponen_biaya_new, created_by_id=current_worker.id, with_commit=False)

    # INITIALIZE SPK KELENGKAPAN DOKUMEN
    async def init_spk_kelengkapan_dokumen(self, spk_id:UUID, sch:SpkCreateSch | SpkUpdateSch, current_worker:Worker, db_session):
        for kelengkapan_dokumen in sch.spk_kelengkapan_dokumens:
            if kelengkapan_dokumen.id is None:
                kelengkapan_dokumen_sch = SpkKelengkapanDokumenCreateSch(spk_id=spk_id, order_number=kelengkapan_dokumen.order_number, bundle_dt_id=kelengkapan_dokumen.bundle_dt_id, tanggapan=kelengkapan_dokumen.tanggapan, field_value=kelengkapan_dokumen.field_value, key_value=kelengkapan_dokumen.key_value)
                await crud.spk_kelengkapan_dokumen.create(obj_in=kelengkapan_dokumen_sch, created_by_id=current_worker.id, with_commit=False)
            else:
                kelengkapan_dokumen_current = await crud.spk_kelengkapan_dokumen.get(id=kelengkapan_dokumen.id)
                kelengkapan_dokumen_sch = SpkKelengkapanDokumenUpdateSch(spk_id=spk_id, order_number=kelengkapan_dokumen.order_number, bundle_dt_id=kelengkapan_dokumen.bundle_dt_id, tanggapan=kelengkapan_dokumen.tanggapan, field_value=kelengkapan_dokumen.field_value, key_value=kelengkapan_dokumen.key_value)
                await crud.spk_kelengkapan_dokumen.update(obj_current=kelengkapan_dokumen_current, obj_new=kelengkapan_dokumen_sch, updated_by_id=current_worker.id, with_commit=False)

    # CREATE SPK, SPK KELENGKAPAN DOKUMEN, KOMPONEN BIAYA BIDANG
    async def create_spk(self, sch:SpkCreateSch, current_worker:Worker, request:Request) -> Spk:
        
        db_session = db.session

        bidang = await crud.bidang.get(id=sch.bidang_id)

        if bidang.skpt_id == None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"PTSK pada bidang {bidang.id_bidang} belum ditentukan, mohon lakukan update pada modul Input Hasil Peta Lokasi")

        new_obj = await self.init_spk(sch=sch, current_worker=current_worker, id_bidang=bidang.id_bidang, db_session=db_session)

        await self.init_komponen_biaya(sch=sch, current_worker=current_worker, db_session=db_session)

        await self.init_spk_kelengkapan_dokumen(sch=sch, spk_id=new_obj.id, current_worker=current_worker, db_session=db_session)

        if (sch.is_draft or False) is False:
            # UPDATE STATUS PEMBEBASAN BIDANG
            if sch.jenis_bayar in [JenisBayarEnum.DP, JenisBayarEnum.LUNAS, JenisBayarEnum.PELUNASAN]:
                status_pembebasan = jenis_bayar_to_spk_status_pembebasan.get(sch.jenis_bayar, None)
                await BidangHelper().update_status_pembebasan(list_bidang_id=[sch.bidang_id], status_pembebasan=status_pembebasan, db_session=db_session)

            # CREATE WORKFLOW
            if new_obj.jenis_bayar != JenisBayarEnum.PAJAK:
                flow = await crud.workflow_template.get_by_entity(entity=WorkflowEntityEnum.SPK)
                wf_sch = WorkflowCreateSch(reference_id=new_obj.id, entity=WorkflowEntityEnum.SPK, 
                                            flow_id=flow.flow_id, version=1, 
                                            last_status=WorkflowLastStatusEnum.ISSUED, step_name="ISSUED")
                
                await crud.workflow.create(obj_in=wf_sch, created_by_id=new_obj.created_by_id, db_session=db_session, with_commit=False)
        
        try:
            await db_session.commit()
            await db_session.refresh(new_obj)

            # CREATE TASK UPLOAD PRINTOUT (STORAGE & BUNDLE)
            payload = {
                "id": str(new_obj.id)
            }

            url = f'{request.base_url}landrope/spk/task-upload-printout'

            GCloudTaskService().create_task(payload=payload, base_url=url)

            # CREATE TASK WORKFLOW SERVICE
            if (sch.is_draft or False) is False and new_obj.jenis_bayar != JenisBayarEnum.PAJAK:
                payload = {
                    "id": str(new_obj.id),
                    "additional_info": new_obj.jenis_bayar
                }

                url = f'{request.base_url}landrope/spk/task-workflow'

                GCloudTaskService().create_task(payload=payload, base_url=url)

        except Exception as e:
            raise HTTPException(status_code=409, detail=str(e.message))

        return new_obj

    # UPDATE SPK, BIDANG KOMPONEN BIAYA, SPK KELENGKAPAN DOKUMEN
    async def update_spk(self, sch:SpkUpdateSch, obj_current:Spk, bidang_id:UUID, current_worker:Worker, request:Request) -> Spk:

        db_session = db.session

        #schema for history
        spk_current_for_history = Spk.from_orm(obj_current) 
        await HistoryService().create_history_spk(spk=spk_current_for_history, worker_id=current_worker.id, db_session=db_session)

        sch.is_void = obj_current.is_void

        if sch.file and (sch.is_draft or False) == False:
            gn_id = uuid4().hex
            file_name=f"SURAT PERINTAH KERJA-{obj_current.code.replace('/', '_')}-{gn_id}"
            try:
                file_upload_path = await BundleHelper().upload_to_storage_from_base64(base64_str=sch.file, file_name=file_name)
            except ZeroDivisionError as e:
                raise HTTPException(status_code=422, detail="Failed upload dokumen Memo Pembayaran")
            
            sch.file_upload_path = file_upload_path

            bidang = await crud.bidang.get(id=bidang_id)
            bundle = await crud.bundlehd.get_by_id(id=bidang.bundle_hd_id)
            if bundle:
                await BundleHelper().merge_spk_signed(bundle=bundle, 
                                                    code=f"{obj_current.code}-{str(obj_current.updated_at.date())}", 
                                                    tanggal=obj_current.created_at.date(), 
                                                    file_path=sch.file_upload_path, 
                                                    worker_id=obj_current.updated_by_id, db_session=db_session)
        
        obj_updated = await crud.spk.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id, with_commit=False)

        await self.init_komponen_biaya(sch=sch, current_worker=current_worker, db_session=db_session)

        await db_session.execute(delete(SpkKelengkapanDokumen).where(and_(SpkKelengkapanDokumen.id.notin_(r.id for r in sch.spk_kelengkapan_dokumens if r.id is not None), 
                                                        SpkKelengkapanDokumen.spk_id == obj_updated.id)))

        await self.init_spk_kelengkapan_dokumen(spk_id=obj_current.id, sch=sch, current_worker=current_worker, db_session=db_session)

        if (sch.is_draft or False) is False:
            if sch.jenis_bayar in [JenisBayarEnum.DP, JenisBayarEnum.LUNAS, JenisBayarEnum.PELUNASAN]:
                status_pembebasan = jenis_bayar_to_spk_status_pembebasan.get(sch.jenis_bayar, None)
                await BidangHelper().update_status_pembebasan(list_bidang_id=[sch.bidang_id], status_pembebasan=status_pembebasan, db_session=db_session)

            # WORKFLOW
            if obj_updated.jenis_bayar != JenisBayarEnum.PAJAK:
                wf_current = await crud.workflow.get_by_reference_id(reference_id=obj_updated.id)
                if wf_current:
                    if wf_current.last_status in [WorkflowLastStatusEnum.REJECTED, WorkflowLastStatusEnum.NEED_DATA_UPDATE]:
                        # REISSUED WORKFLOW
                        wf_updated = WorkflowUpdateSch(**wf_current.dict(exclude={"last_status", "step_name"}), last_status=WorkflowLastStatusEnum.ISSUED, step_name="ISSUED" if WorkflowLastStatusEnum.REJECTED else "On Progress Update Data")
                        await crud.workflow.update(obj_current=wf_current, obj_new=wf_updated, updated_by_id=obj_updated.updated_by_id, db_session=db_session, with_commit=False)
                else:
                    flow = await crud.workflow_template.get_by_entity(entity=WorkflowEntityEnum.SPK)
                    wf_sch = WorkflowCreateSch(reference_id=obj_updated.id, entity=WorkflowEntityEnum.SPK, flow_id=flow.flow_id, version=1, last_status=WorkflowLastStatusEnum.ISSUED, step_name="ISSUED")
                    
                    await crud.workflow.create(obj_in=wf_sch, created_by_id=obj_updated.updated_by_id, db_session=db_session, with_commit=False)
        try:
            await db_session.commit()
            await db_session.refresh(obj_updated)

            # CREATE TASK UPLOAD PRINTOUT (STORAGE & BUNDLE)
            payload = {
                "id": str(obj_updated.id)
            }

            url = f'{request.base_url}landrope/spk/task-upload-printout'

            GCloudTaskService().create_task(payload=payload, base_url=url)

            # CREATE TASK WORKFLOW
            if (sch.is_draft or False) is False and obj_updated.jenis_bayar != JenisBayarEnum.PAJAK:
                payload = {
                    "id":str(obj_updated.id), 
                    "additional_info":obj_updated.jenis_bayar
                }

                url = f'{request.base_url}landrope/spk/task-workflow'

                GCloudTaskService().create_task(payload=payload, base_url=url)
        
        except Exception as e:
            raise HTTPException(status_code=409, detail=str(e.message))

        return obj_updated

    # GET BY ID SPK
    async def get_by_id_spk(self, id:UUID) -> SpkByIdSch | None:

        obj = await crud.spk.get_by_id(id=id)

        if not obj:
            raise HTTPException(status_code=404, detail="SPK not found!")
        
        bidang_obj = await crud.bidang.get_by_id(id=obj.bidang_id)
        if not bidang_obj:
            raise HTTPException(status_code=404, detail="SPK not found!")
        
        termins = []
        if bidang_obj.hasil_peta_lokasi:
            # harga = await crud.kjb_harga.get_by_kjb_hd_id_and_jenis_alashak(kjb_hd_id=bidang_obj.hasil_peta_lokasi.kjb_dt.kjb_hd_id, 
            #                                         jenis_alashak=bidang_obj.jenis_alashak if (bidang_obj.is_ptsl or False) == False else JenisAlashakEnum.Girik)

            harga = await crud.kjb_harga.get_by_kjb_hd_id_and_jenis_alashak(kjb_hd_id=bidang_obj.hasil_peta_lokasi.kjb_dt.kjb_hd_id, jenis_alashak=bidang_obj.jenis_alashak)
            
            if harga is None:
                raise HTTPException(status_code=404, detail="KJB Harga not Found")
            
            for tr in harga.termins:
                if tr.id == obj.kjb_termin_id:
                    termin = KjbTerminInSpkSch(**tr.dict(), spk_id=obj.id, spk_code=obj.code)
                    termins.append(termin)
                else:
                    spk = await crud.spk.get_by_bidang_id_kjb_termin_id(bidang_id=bidang_obj.id, kjb_termin_id=tr.id)
                    if spk:
                        termin = KjbTerminInSpkSch(**tr.dict(), spk_id=spk.id, spk_code=spk.code)
                    else:
                        termin = KjbTerminInSpkSch(**tr.dict())
                    termins.append(termin)

        ktp_value:str | None = await BundleHelper().get_key_value(dokumen_name='KTP PENJUAL', bidang_id=bidang_obj.id)
        npwp_value:str | None = await BundleHelper().get_key_value(dokumen_name='NPWP', bidang_id=bidang_obj.id)
        sppt_pbb_nop_value:str | None = await BundleHelper().get_key_value(dokumen_name='SPPT PBB NOP', bidang_id=bidang_obj.id)

        percentage_lunas = None
        if obj.jenis_bayar != JenisBayarEnum.BEGINNING_BALANCE:
            percentage_lunas = await crud.bidang.get_percentage_lunas(bidang_id=bidang_obj.id)
        
        bidang_sch = BidangForSPKByIdSch(id=bidang_obj.id,
                                        jenis_alashak=bidang_obj.jenis_alashak,
                                        id_bidang=bidang_obj.id_bidang,
                                        hasil_analisa_peta_lokasi=bidang_obj.hasil_analisa_peta_lokasi,
                                        kjb_no=bidang_obj.hasil_peta_lokasi.kjb_dt.kjb_code if bidang_obj.hasil_peta_lokasi else None,
                                        satuan_bayar=obj.satuan_bayar,
                                        group=bidang_obj.group,
                                        pemilik_name=bidang_obj.pemilik_name,
                                        alashak=bidang_obj.alashak,
                                        desa_name=bidang_obj.desa_name,
                                        project_name=bidang_obj.project_name,
                                        luas_surat=bidang_obj.luas_surat,
                                        luas_ukur=bidang_obj.luas_ukur,
                                        luas_nett=bidang_obj.luas_nett,
                                        luas_gu_perorangan=bidang_obj.luas_gu_perorangan,
                                        luas_gu_pt=bidang_obj.luas_gu_pt,
                                        luas_pbt_perorangan=bidang_obj.luas_pbt_perorangan,
                                        luas_pbt_pt=bidang_obj.luas_pbt_pt,
                                        manager_name=bidang_obj.manager_name,
                                        no_peta=bidang_obj.no_peta,
                                        notaris_name=bidang_obj.notaris_name,
                                        ptsk_name=bidang_obj.ptsk_name,
                                        status_sk=bidang_obj.status_sk,
                                        bundle_hd_id=bidang_obj.bundle_hd_id,
                                        ktp=ktp_value,
                                        npwp=npwp_value,
                                        sppt_pbb_nop=sppt_pbb_nop_value,
                                        termins=termins,
                                        percentage_lunas=percentage_lunas.percentage_lunas if percentage_lunas else 0)
        
        # GET REKENING FROM PEMILIK BIDANG
        if bidang_obj.pemilik:
            rekenings:list[RekeningSch] = []
            for rk in bidang_obj.pemilik.rekenings:
                rekening = RekeningSch(**rk.dict())
                rekenings.append(rekening)
            
            bidang_sch.rekenings = rekenings
        
        obj_return = SpkByIdSch(**obj.dict())
        obj_return.bidang = bidang_sch

        workflow = await crud.workflow.get_by_reference_id(reference_id=obj.id)
        if workflow:
            obj_return.status_workflow = workflow.last_status
            obj_return.step_name_workflow = workflow.step_name

        pengembalian = False
        if obj.jenis_bayar == JenisBayarEnum.PENGEMBALIAN_BEBAN_PENJUAL:
            pengembalian = True
        
        pajak = False
        if obj.jenis_bayar == JenisBayarEnum.PAJAK:
            pajak = True

        komponen_biayas = await crud.bidang_komponen_biaya.get_multi_by_bidang_id(bidang_id=obj.bidang_id, pengembalian=pengembalian, pajak=pajak)

        list_komponen_biaya = []
        for kb in komponen_biayas:
            komponen_biaya_sch = BidangKomponenBiayaSch(**kb.dict())
            komponen_biaya_sch.beban_biaya_name = kb.beban_biaya_name
            komponen_biaya_sch.is_tax = kb.is_tax
            komponen_biaya_sch.order_number = kb.order_number
            list_komponen_biaya.append(komponen_biaya_sch)
        
        list_kelengkapan_dokumen = []
        for kd in obj.spk_kelengkapan_dokumens:
            kelengkapan_dokumen_sch = SpkKelengkapanDokumenSch(**kd.dict())
            kelengkapan_dokumen_sch.dokumen_name = kd.dokumen_name
            kelengkapan_dokumen_sch.has_meta_data = kd.has_meta_data
            kelengkapan_dokumen_sch.file_path = kd.file_path
            kelengkapan_dokumen_sch.order_number = kd.order_number
            kelengkapan_dokumen_sch.is_exclude_printout = kd.is_exclude_printout
            list_kelengkapan_dokumen.append(kelengkapan_dokumen_sch)

        obj_return.spk_beban_biayas = list_komponen_biaya
        obj_return.spk_kelengkapan_dokumens = list_kelengkapan_dokumen
        obj_return.created_name = obj.created_name
        obj_return.updated_name = obj.updated_name

        return obj_return

    # INIT CHECKLIST KELENGKAPAN DETAIL, UNTUK HANDLE DOKUMEN YANG MEMILIKI RIWAYAT
    async def init_checklist_kelengkapan_dt(self, checklist_kelengkapan_dts:list[ChecklistKelengkapanDokumenDt], riwayat_alashak) -> list[ChecklistKelengkapanDokumenDtSch]:
        result:list[ChecklistKelengkapanDokumenDtSch] = []
        for ch in checklist_kelengkapan_dts:
            idx = 0
            dokumen = await crud.dokumen.get(id=ch.bundle_dt.dokumen_id)
            if dokumen.is_riwayat and ch.bundle_dt.riwayat_data:
                riwayat_data = json.loads(ch.bundle_dt.riwayat_data)
                if len(riwayat_data["riwayat"]) == 0:
                    data = ChecklistKelengkapanDokumenDtSch.from_orm(ch)
                    result.append(data)
                else:
                    for riwayat in riwayat_data["riwayat"]:
                        meta_data = riwayat["meta_data"]
                        data = ChecklistKelengkapanDokumenDtSch.from_orm(ch)
                        if dokumen.name in ["VALIDASI RIWAYAT", "PPH RIWAYAT", "BPHTB RIWAYAT"]:
                            if len(riwayat_alashak) == 0:
                                data.field_value = ''
                            else:
                                if idx > (len(riwayat_alashak) - 1):
                                    data.field_value = ''
                                else:
                                    data.field_value = riwayat_alashak[idx]
                            idx += 1
                        else:
                            data.field_value = meta_data[dokumen.key_field]
                            data.key_value = meta_data[dokumen.key_field]

                        data.key_value = meta_data[dokumen.key_field]
                        data.file_path = riwayat["file_path"]
                        data.is_default = riwayat["is_default"]
                        result.append(data)
            else:
                data = ChecklistKelengkapanDokumenDtSch.from_orm(ch)
                result.append(data)

        return result

    # INIT RIWAYAT ALASHAK
    async def init_riwayat_alashak(self, bundle_hd_id:UUID):
        result = []
        try:
            dokumen = await crud.dokumen.get_by_name(name='ALAS HAK')
            bundle_dt_alashak = await crud.bundledt.get_by_bundle_hd_id_and_dokumen_id(bundle_hd_id=bundle_hd_id, dokumen_id=dokumen.id)

            if bundle_dt_alashak.riwayat_data:
                riwayat_data = json.loads(bundle_dt_alashak.riwayat_data.replace("'", '"'))
                if len(riwayat_data["riwayat"]) == 0:
                    return []
                else:
                    for riwayat in riwayat_data["riwayat"]:
                        meta_data = riwayat["meta_data"]
                        data =  meta_data[dokumen.key_field]
                        result.append(data)
            return result
        except :
            raise HTTPException(status_code=422, detail="Failed initialize alashak riwayat!")

    # GET BY ID BIDANG YANG DIPILIH UNTUK DIBUATKAN SPK
    async def search_bidang_by_id(self, id:UUID) -> BidangForSPKByIdExtSch:

        obj = await crud.bidang.get_by_id(id=id)

        if obj is None:
            raise HTTPException(status_code=404, detail="Bidang not found!")

        hasil_peta_lokasi_current = await crud.hasil_peta_lokasi.get_by_bidang_id(bidang_id=obj.id)
        kjb_dt_current = await crud.kjb_dt.get_by_id(id=hasil_peta_lokasi_current.kjb_dt_id)
        spk_exists_on_bidangs = await crud.spk.get_multi_by_bidang_id(bidang_id=id)
        # harga = await crud.kjb_harga.get_by_kjb_hd_id_and_jenis_alashak(kjb_hd_id=kjb_dt_current.kjb_hd_id, jenis_alashak=obj.jenis_alashak if (obj.is_ptsl or False) is False else JenisAlashakEnum.Girik)
        harga = await crud.kjb_harga.get_by_kjb_hd_id_and_jenis_alashak(kjb_hd_id=kjb_dt_current.kjb_hd_id, jenis_alashak=obj.jenis_alashak)
        
        if harga is None:
            raise HTTPException(status_code=404, detail="KJB Harga not found")
        
        termins = []
        if harga:
            for tr in harga.termins:
                spk_exists_on_bidang = next((spk_exists for spk_exists in spk_exists_on_bidangs if spk_exists.kjb_termin_id == tr.id), None)
                if spk_exists_on_bidang:
                    termin = KjbTerminInSpkSch(**tr.dict(), spk_id=spk_exists_on_bidang.id, spk_code=spk_exists_on_bidang.code)
                    termins.append(termin)
                else:
                    termin = KjbTerminInSpkSch(**tr.dict())
                    termins.append(termin)

        beban = []

        beban = await crud.bidang_komponen_biaya.get_multi_beban_by_bidang_id_for_spk(bidang_id=id)
        if len(beban) == 0:
            beban = await crud.kjb_bebanbiaya.get_kjb_beban_by_kjb_hd_id(kjb_hd_id=kjb_dt_current.kjb_hd_id, jenis_alashak=obj.jenis_alashak)
        
        # GET VALUE in BUNDLE
        ktp_value:str | None = await BundleHelper().get_key_value(dokumen_name='KTP PENJUAL', bidang_id=obj.id)
        npwp_value:str | None = await BundleHelper().get_key_value(dokumen_name='NPWP', bidang_id=obj.id)
        sppt_pbb_nop_value:str | None = await BundleHelper().get_key_value(dokumen_name='SPPT PBB NOP', bidang_id=obj.id)
        
        riwayat_alashak = await self.init_riwayat_alashak(bundle_hd_id=obj.bundle_hd_id)
        checklist_kelengkapan_dokumen_dts = await crud.checklist_kelengkapan_dokumen_dt.get_all_for_spk(bidang_id=obj.id)
        kelengkapan_dokumen = await SpkService().init_checklist_kelengkapan_dt(checklist_kelengkapan_dts=checklist_kelengkapan_dokumen_dts, riwayat_alashak=riwayat_alashak)

        percentage_lunas = next((termin.nilai for termin in harga.termins if termin.jenis_bayar == JenisBayarEnum.PELUNASAN), None)

        obj_return = BidangForSPKByIdExtSch(id=obj.id,
                                        jenis_alashak=obj.jenis_alashak,
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
                                        luas_nett=obj.luas_nett,
                                        luas_gu_perorangan=obj.luas_gu_perorangan,
                                        luas_gu_pt=obj.luas_gu_pt,
                                        luas_pbt_perorangan=obj.luas_pbt_perorangan,
                                        luas_pbt_pt=obj.luas_pbt_pt,
                                        manager_name=obj.manager_name,
                                        no_peta=obj.no_peta,
                                        notaris_name=obj.notaris_name,
                                        ptsk_name=obj.ptsk_name,
                                        status_sk=obj.status_sk,
                                        bundle_hd_id=obj.bundle_hd_id,
                                        beban_biayas=beban,
                                        kelengkapan_dokumens=kelengkapan_dokumen,
                                        ktp=ktp_value,
                                        npwp=npwp_value,
                                        sppt_pbb_nop=sppt_pbb_nop_value,
                                        sisa_pelunasan=obj.sisa_pelunasan,
                                        termins=termins,
                                        percentage_lunas=percentage_lunas if percentage_lunas else 100)
        
         # GET REKENING FROM PEMILIK BIDANG
        if obj.pemilik:
            rekenings:list[RekeningSch] = []
            for rk in obj.pemilik.rekenings:
                rekening = RekeningSch(**rk.dict())
                rekenings.append(rekening)
            
            obj_return.rekenings = rekenings

        
        return obj_return
    
    # MEMASANGKAN DOKUMEN ALASHAK DENGAN DOKUMEN VALIDASI RIWAYAT, PPH RIWAYAT, BPHTB RIWAYAT UNTUK KEPERLUAN PRINTOUT
    async def get_riwayat_bundle_dt(self, bundle_dt_id: UUID) -> list[BundleDtRiwayatSch]:
        datas = []
        bundle_dt = await crud.bundledt.get_by_id(id=bundle_dt_id)
        if bundle_dt is None:
            return datas
        
        if bundle_dt.dokumen.is_riwayat == False:
            return datas
        
        if bundle_dt.riwayat_data is None:
            return datas
        
        riwayat_data = json.loads(bundle_dt.riwayat_data)

        riwayat_alashak = await self.init_riwayat_alashak(bundle_hd_id=bundle_dt.bundle_hd_id)
        idx = 0
        
        for riwayat in riwayat_data["riwayat"]:
            meta_data = riwayat["meta_data"]
            data = BundleDtRiwayatSch.from_orm(bundle_dt)
            if bundle_dt.dokumen.name in ["VALIDASI RIWAYAT", "PPH RIWAYAT", "BPHTB RIWAYAT"]:
                if len(riwayat_alashak) == 0:
                    data.field_value = ''
                else:
                    if idx > (len(riwayat_alashak) - 1):
                        data.field_value = ''
                    else:
                        data.field_value = riwayat_alashak[idx]
                idx += 1
            else:
                data.field_value = meta_data[bundle_dt.dokumen.key_field]
                

            file_path = riwayat.get('file_path', None)
            data.file_exists = True if file_path and file_path != "" else False
            data.key_value = meta_data[bundle_dt.dokumen.key_field]
            data.file_path = file_path
            datas.append(data)
        
        return datas

    # TASK WORKFLOW
    async def task_workflow(self, obj: Spk, additional_info: str, request):

        wf_current = await crud.workflow.get_by_reference_id(reference_id=obj.id)
        if not wf_current:
            raise HTTPException(status_code=404, detail="Workflow not found")

        public_url = await encrypt_id(id=str(obj.id), request=request)
        wf_system_attachment = WorkflowSystemAttachmentSch(name=obj.code, url=f"{public_url}?en={WorkflowEntityEnum.SPK.value}")
        wf_system_sch = WorkflowSystemCreateSch(client_ref_no=str(obj.id), 
                                                flow_id=wf_current.flow_id, 
                                                descs=f"""Dokumen SPK {obj.code} ini membutuhkan Approval dari Anda:<br><br>
                                                        Tanggal: {obj.created_at.date()}<br>
                                                        Dokumen: {obj.code}<br><br>
                                                        KJB: {obj.kjb_hd_code or ""}<br><br>
                                                        Berikut lampiran dokumen terkait : """, 
                                                additional_info={"jenis_bayar" : str(additional_info)}, 
                                                attachments=[vars(wf_system_attachment)],
                                                version=wf_current.version)
        
        body = vars(wf_system_sch)
        response, msg = await WorkflowService().create_workflow(body=body)

        if response is None:
            logging.error(msg=f"Spk {obj.code} Failed to connect workflow system. Detail : {msg}")
            raise HTTPException(status_code=422, detail=f"Failed to connect workflow system. Detail : {msg}")
        
        wf_updated = WorkflowUpdateSch(**wf_current.dict(exclude={"last_status"}), last_status=response.last_status)
        await crud.workflow.update(obj_current=wf_current, obj_new=wf_updated, updated_by_id=obj.updated_by_id)

        return True

    # TASK GENERATE PRINTOUT FOR UPLOAD TO STORAGE & MERGE TO BUNDLE DOKUMEN SPK
    async def task_generate_printout_and_merge_to_bundle(self, obj: Spk):
        
        try:
            db_session = db.session
            file_path: str | None = obj.file_path

            if file_path is None:
                file_path = await SpkService().generate_printout(id=obj.id)

            if obj.jenis_bayar in [JenisBayarEnum.DP, JenisBayarEnum.PELUNASAN, JenisBayarEnum.LUNAS]:
                bidang = await crud.bidang.get(id=obj.bidang_id)
                bundle = await crud.bundlehd.get(id=bidang.bundle_hd_id)
                if bundle:
                    await BundleHelper().merge_spk(bundle=bundle, code=f"{obj.code}-{str(obj.updated_at.date())}", tanggal=obj.updated_at.date(), file_path=obj.file_path, worker_id=obj.updated_by_id, db_session=db_session)
                    await db_session.commit()

        except Exception as e:
            logging.error(msg=f"Spk {obj.code} error generate printout. Detail: {str(e.args)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.args))

    async def filter_biaya_lain(self, beban_biaya_ids:list[UUID], bidang_id:UUID):

        beban_biaya_add_pays = await crud.bebanbiaya.get_beban_biaya_add_pay(list_id=beban_biaya_ids)
        add_pay_from_master = False
        if len(beban_biaya_add_pays) > 0:
            add_pay_from_master = True 
        
        komponen_biaya_add_pays = await crud.bidang_komponen_biaya.get_komponen_biaya_add_pay(list_id=beban_biaya_ids, bidang_id=bidang_id)
        add_pay_from_komponen = False
        if len(komponen_biaya_add_pays) > 0:
            add_pay_from_komponen = True
        
        if add_pay_from_master == False and add_pay_from_komponen == False:
            raise HTTPException(status_code=422, detail="Bidang tidak memiliki beban biaya lain diluar dari biaya tanah")

    async def filter_sisa_pelunasan(self, bidang_id:UUID):
        bidang = await crud.bidang.get_by_id_for_spk(id=bidang_id)

        if bidang.has_invoice_lunas != True:
            raise HTTPException(status_code=422, detail="Bidang tidak memiliki pembayaran pelunasan")
        
        if bidang.sisa_pelunasan == 0:
            raise HTTPException(status_code=422, detail="Bidang tidak memiliki sisa pelunasan")

    async def filter_kelengkapan_dokumen(self, bundle_dt_ids:list[UUID]):
        bundle_dts = await crud.bundledt.get_by_ids(list_ids=bundle_dt_ids)

        bundle_dt_no_have_metadata = any(bundledt.file_exists == False for bundledt in bundle_dts)
        if bundle_dt_no_have_metadata:
            raise HTTPException(status_code=422, detail="Failed create SPK. Detail : Data bundle untuk kelengkapan spk belum diinput")
        
    async def filter_have_input_peta_lokasi(self, bidang_id:UUID):
        hasil_peta_lokasi = await crud.hasil_peta_lokasi.get_by_bidang_id(bidang_id=bidang_id)

        if not hasil_peta_lokasi:
            raise HTTPException(status_code=422, detail="Failed create SPK. Detail : Bidang belum memiliki input hasil peta lokasi")

    async def filter_with_same_kjb_termin(self, bidang_id:UUID, kjb_termin_id:UUID, spk_id:UUID | None = None):
        exists = await crud.spk.get_by_bidang_id_kjb_termin_id(bidang_id=bidang_id, kjb_termin_id=kjb_termin_id)
        if exists:
            if exists.id != spk_id:
                raise HTTPException(status_code=422, detail="Failed create SPK. Detail : Termin yang pembayaran yang dimaksud sudah pernah dibuat")
        
    # GENERATE PRINTOUT AND SAVE TO GCLOUD STORAGE
    async def generate_printout(self, id:UUID|str) -> str:

        obj = await crud.spk.get_by_id_for_printout(id=id)
        if obj is None:
            raise HTTPException(status_code=404, detail="SPK not found")
        
        bidang = await crud.bidang.get_by_id(id=obj.bidang_id)
        
        filename:str = "spk_clear.html" if obj.jenis_bayar != JenisBayarEnum.PAJAK else "spk_pajak_clear.html"
        
        spk_header = SpkPrintOut(**dict(obj))
        remarks = spk_header.remark.splitlines() if spk_header.remark else ''
        percentage_value:str = ""
        if spk_header.satuan_bayar == SatuanBayarEnum.Percentage and spk_header.jenis_bayar in [JenisBayarEnum.DP, JenisBayarEnum.LUNAS, JenisBayarEnum.PELUNASAN, JenisBayarEnum.TAMBAHAN_DP]:
            percentage_value = f" {spk_header.amount}%"
        
        ktp_value:str | None = await BundleHelper().get_key_value(dokumen_name='KTP PENJUAL', bidang_id=spk_header.bidang_id)
        npwp_value:str | None = await BundleHelper().get_key_value(dokumen_name='NPWP', bidang_id=spk_header.bidang_id)
        kk_value:str | None = await BundleHelper().get_key_value(dokumen_name='KARTU KELUARGA', bidang_id=spk_header.bidang_id)
        nop_value:str | None = await BundleHelper().get_key_value(dokumen_name='SPPT PBB NOP', bidang_id=spk_header.bidang_id)
        
        spk_details = []
        no = 1

        obj_kelengkapans = await crud.spk.get_kelengkapan_by_id_for_printout(id=id)

        for k in obj_kelengkapans:
            kelengkapan = SpkDetailPrintOut(**dict(k))
            kelengkapan.no = no
            spk_details.append(kelengkapan)
            no += 1

        obj_beban_biayas = []
        obj_beban_biayas = await crud.spk.get_beban_biaya_for_printout(id=id, jenis_bayar=spk_header.jenis_bayar)

        for bb in obj_beban_biayas:
            beban_biaya = SpkDetailPrintOut(bundle_dt_id=None, field_value='', tanggapan=bb.tanggapan, name=bb.name)
            if beban_biaya.name == 'PBB 10 Tahun Terakhir s/d Tahun ini' and spk_header.jenis_bayar != JenisBayarEnum.PAJAK:
                continue

            beban_biaya.no = no
            spk_details.append(beban_biaya)
            no += 1
        

        pm_1 = await crud.spk.get_pm1(id=id, check_meta_data_exists=False)
        if pm_1["jumlah"] > 0:
            pm_1_lengkap = await crud.spk.get_pm1(id=id, check_meta_data_exists=True)
            if pm_1_lengkap["jumlah"] == 0:
                pm1 = SpkDetailPrintOut(no=no, name="PM1", tanggapan="PM1 Lengkap", field_value="")
                spk_details.append(pm1)

        overlap_details = []
        if obj.jenis_bidang == JenisBidangEnum.Overlap:
            filename:str = "spk_overlap.html" if obj.jenis_bayar != JenisBayarEnum.PAJAK else "spk_pajak_overlap.html"
            obj_overlaps = await crud.spk.get_overlap_by_id_for_printout(id=id)
            for ov in obj_overlaps:
                overlap = SpkOverlapPrintOutExt(**dict(ov))
                overlap.luas_overlapExt = "{:,.0f}".format(overlap.luas_overlap)
                overlap.luas_suratExt = "{:,.0f}".format(overlap.luas_surat)
                overlap.tipe_overlapExt = overlap.tipe_overlap.value.replace('_', ' ')
                overlap.tahap = overlap.tahap if overlap.tahap != "0" else "-"
                overlap_details.append(overlap)

        rekening:str = ""
        rekenings = await crud.spk.get_rekening_by_id_for_printout(id=id)
        for r in rekenings:
            rek = SpkRekeningPrintOut(**dict(r))
            rekening += f"{rek.rekening}, "
        
        rekening = rekening[0:-2]

        
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template(filename)

        akta_peralihan:str = ""
        if bidang.jenis_alashak == JenisAlashakEnum.Girik:
            akta_peralihan = "PPJB" if spk_header.status_il == StatusSKEnum.Belum_IL else "SPH"
        else:
            akta_peralihan = "PPJB"

        render_template = template.render(kjb_hd_code=spk_header.kjb_hd_code,
                                        jenisbayar=f'{spk_header.jenis_bayar.value if spk_header.jenis_bayar != JenisBayarEnum.SISA_PELUNASAN else "KURANG BAYAR"}{percentage_value}'.replace("_", " "),
                                        jenis_bayar=spk_header.jenis_bayar,
                                        group=spk_header.group, 
                                        pemilik_name=spk_header.pemilik_name,
                                        alashak=spk_header.alashak,
                                        desa_name=spk_header.desa_name,
                                        luas_surat="{:,.2f}".format(spk_header.luas_surat or 0),
                                        luas_ukur="{:,.2f}".format(spk_header.luas_ukur or 0),
                                        luas_nett="{:,.2f}".format(spk_header.luas_nett or 0),
                                        luas_gu_perorangan="{:,.2f}".format(spk_header.luas_gu_perorangan or 0),
                                        luas_pbt_perorangan="{:,.2f}".format(spk_header.luas_pbt_perorangan or 0),
                                        luas_gu_pt="{:,.2f}".format(spk_header.luas_gu_pt or 0),
                                        luas_pbt_pt="{:,.2f}".format(spk_header.luas_pbt_pt or 0),
                                        proses_bpn=bidang.proses_bpn_order_gu,
                                        id_bidang=spk_header.id_bidang,
                                        no_peta=spk_header.no_peta,
                                        notaris_name=spk_header.notaris_name,
                                        project_name=spk_header.project_name, 
                                        ptsk=spk_header.ptsk_name,
                                        status_il=spk_header.status_il.replace("_"," ") if spk_header.status_il is not None else "",
                                        hasil_analisa_peta_lokasi=spk_header.analisa.value if spk_header.analisa else '',
                                        data=spk_details,
                                        data_overlap=overlap_details,
                                        worker_name=spk_header.worker_name, 
                                        manager_name=spk_header.manager_name,
                                        sales_name=spk_header.sales_name,
                                        akta_peralihan=akta_peralihan,
                                        no_rekening=rekening,
                                        nop=nop_value,
                                        npwp=npwp_value,
                                        ktp=ktp_value,
                                        kk=kk_value,
                                        remarks=remarks)
        
        try:
            doc = await PdfService().get_pdf(render_template)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed generate document")
        
        obj_current = await crud.spk.get(id=id)

        binary_io_data = BytesIO(doc)
        file = UploadFile(file=binary_io_data, filename=f"{obj_current.code.replace('/', '_')}.pdf")

        try:
            file_path = await GCStorageService().upload_file_dokumen(file=file, file_name=f"{obj_current.code.replace('/', '_')}-{str(obj_current.id)}", is_public=True)

            obj_updated = SpkUpdateSch(**obj_current.dict())
            obj_updated.file_path = file_path
            await crud.spk.update(obj_current=obj_current, obj_new=obj_updated)

        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed generate document")
        
        return file_path