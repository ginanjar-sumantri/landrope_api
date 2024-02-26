from fastapi import HTTPException, Request
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from fastapi.encoders import jsonable_encoder
from sqlmodel import select, or_, and_, text, delete
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from common.enum import WorkflowEntityEnum, WorkflowLastStatusEnum
from crud.base_crud import CRUDBase
from models.kjb_model import KjbHd, KjbBebanBiaya, KjbHarga, KjbTermin, KjbRekening, KjbPenjual, KjbDt, Workflow
from models import BundleHd, Rekening
from schemas.beban_biaya_sch import BebanBiayaCreateSch
from schemas.kjb_hd_sch import KjbHdCreateSch, KjbHdUpdateSch, KjbHdForTerminByIdSch, KjbHdForCloud
from schemas.workflow_sch import WorkflowCreateSch, WorkflowSystemCreateSch, WorkflowSystemAttachmentSch
from services.gcloud_task_service import GCloudTaskService
from services.gcloud_storage_service import GCStorageService
from services.history_service import HistoryService
from services.workflow_service import WorkflowService
from typing import Any, Dict, Generic, List, Type, TypeVar
from uuid import UUID
from datetime import datetime
from sqlalchemy import exc
import crud
import json

class CRUDKjbHd(CRUDBase[KjbHd, KjbHdCreateSch, KjbHdUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> KjbHd | None:
        
        db_session = db_session or db.session
        
        query = select(KjbHd).where(KjbHd.id == id).options(selectinload(KjbHd.desa)
                                                ).options(selectinload(KjbHd.manager)
                                                ).options(selectinload(KjbHd.sales)
                                                ).options(selectinload(KjbHd.kjb_dts
                                                                        ).options(selectinload(KjbDt.pemilik)
                                                                        ).options(selectinload(KjbDt.kjb_hd)
                                                                        ).options(selectinload(KjbDt.jenis_surat)
                                                                        ).options(selectinload(KjbDt.request_peta_lokasi)
                                                                        ).options(selectinload(KjbDt.hasil_peta_lokasi)
                                                                        ).options(selectinload(KjbDt.bundlehd
                                                                                        ).options(selectinload(BundleHd.bundledts))
                                                                        )
                                                ).options(selectinload(KjbHd.rekenings)
                                                ).options(selectinload(KjbHd.hargas
                                                                        ).options(selectinload(KjbHarga.termins
                                                                                                ).options(selectinload(KjbTermin.spks)
                                                                                                )
                                                                        )
                                                ).options(selectinload(KjbHd.bebanbiayas
                                                                        ).options(selectinload(KjbBebanBiaya.beban_biaya))
                                                ).options(selectinload(KjbHd.penjuals))

        response = await db_session.execute(query)

        return response.scalar_one_or_none()

    async def get_by_id_cu(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> KjbHd | None:
        
        db_session = db_session or db.session
        
        query = select(KjbHd).where(KjbHd.id == id).options(selectinload(KjbHd.desa)
                                                ).options(selectinload(KjbHd.manager)
                                                ).options(selectinload(KjbHd.sales)
                                                ).options(selectinload(KjbHd.kjb_dts)
                                                ).options(selectinload(KjbHd.penjuals))

        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def create_(self, *, 
                    obj_in: KjbHdCreateSch | KjbHd,
                    request: Request,
                    created_by_id : UUID | str | None = None, 
                    db_session : AsyncSession | None = None,
                    ) -> KjbHd :
        
        db_session = db_session or db.session
        db_obj = self.model.from_orm(obj_in) #type ignore
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()
        if created_by_id:
            db_obj.created_by_id = created_by_id

        for dt in obj_in.details:
            # alashak = await crud.kjb_dt.get_by_alashak(alashak=dt.alashak)
            # if alashak:
            #     raise HTTPException(status_code=409, detail=f"alashak {dt.alashak} ada di KJB lain ({alashak.kjb_code})")
            
            detail = KjbDt(**dt.dict(), created_by_id=created_by_id, updated_by_id=created_by_id)
            
            db_obj.kjb_dts.append(detail)

        
        for i in obj_in.rekenings:
            rekening = KjbRekening(**i.dict(exclude={"pemilik_id"}), created_by_id=created_by_id, updated_by_id=created_by_id)
            db_obj.rekenings.append(rekening)

            if i.pemilik_id:
                #menambahkan rekening dari pemilik
                rekenings = await crud.rekening.get_by_pemilik_id(pemilik_id=i.pemilik_id)
                existing_rekening = next((r for r in rekenings if r.nomor_rekening == i.nomor_rekening), None)
                if existing_rekening is None:
                    new_rekening = Rekening(**i.dict(exclude={"id"}))
                    db_session.add(new_rekening)

        for j in obj_in.hargas:
            obj_harga = next((harga for harga in db_obj.hargas if harga.jenis_alashak == j.jenis_alashak), None)
            if obj_harga:
                raise HTTPException(status_code=409, detail=f"Harga {j.jenis_alashak} double input")
            
            termins = []
            for l in j.termins:
                termin = KjbTermin(**l.dict(), created_by_id=created_by_id, updated_by_id=created_by_id)
                termins.append(termin)
            
            harga = KjbHarga(**j.dict(exclude={"termins"}), created_by_id=created_by_id, updated_by_id=created_by_id)
            
            if len(termins) > 0:
                harga.termins = termins
            
            db_obj.hargas.append(harga)
        
        for k in obj_in.bebanbiayas:
            if k.beban_biaya_id != "":
                obj_bebanbiaya = await crud.bebanbiaya.get(id=k.beban_biaya_id)
            else:
                obj_bebanbiaya = await crud.bebanbiaya.get_by_name(name=k.beban_biaya_name)
                
            if obj_bebanbiaya is None:
                    obj_bebanbiaya_in = BebanBiayaCreateSch(name=k.beban_biaya_name, is_active=True)
                    obj_bebanbiaya = await crud.bebanbiaya.create(obj_in=obj_bebanbiaya_in)
                
            bebanbiaya = KjbBebanBiaya(**k.dict(), created_by_id=created_by_id, updated_by_id=created_by_id)
            
            db_obj.bebanbiayas.append(bebanbiaya)
        
        for p in obj_in.penjuals:
            penjual = KjbPenjual(pemilik_id=p.pemilik_id, created_by_id=created_by_id, updated_by_id=created_by_id)
            db_obj.penjuals.append(penjual)

        if obj_in.file:
            db_obj.file_path = await GCStorageService().base64ToFilePath(base64_str=obj_in.file, file_name=obj_in.code.replace('/', '_'))

        db_session.add(db_obj)

        if db_obj.is_draft == False:
            public_url = await GCStorageService().public_url(file_path=db_obj.file_path)
            flow = await crud.workflow_template.get_by_entity(entity=WorkflowEntityEnum.KJB)
            wf_system_attachment = WorkflowSystemAttachmentSch(name=f"KJB-{db_obj.code}", url=public_url)
            wf_system_sch = WorkflowSystemCreateSch(client_ref_no=str(db_obj.id), flow_id=flow.flow_id, additional_info={"approval_number" : "ONE_APPROVAL"}, attachments=[vars(wf_system_attachment)], version=1,
                                                    descs=f"""Dokumen KJB {db_obj.code} ini membutuhkan Approval dari Anda:<br><br>
                                                            Tanggal: {db_obj.created_at.date()}<br>
                                                            Dokumen: {db_obj.code}<br><br>
                                                            Berikut lampiran dokumen terkait : """)

            response, msg = await WorkflowService().create_workflow(body=vars(wf_system_sch))

            if response is None:
                raise HTTPException(status_code=422, detail=f"Workflow Failed. Detail : {msg}")
            
            new_workflow = Workflow(reference_id=db_obj.id, entity=WorkflowEntityEnum.KJB, flow_id=flow.flow_id, last_status=response.last_status, version=1)
            db_session.add(new_workflow)

        try:
            await db_session.commit()
        except exc.IntegrityError:
            await db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
        
        await db_session.refresh(db_obj)
        return db_obj

    async def update_(self, 
                     *,
                     request: Request,
                     obj_current : KjbHd, 
                     obj_new : KjbHdUpdateSch | Dict[str, Any] | KjbHd,
                     updated_by_id: UUID | str | None = None,
                     db_session : AsyncSession | None = None,
                     with_commit: bool | None = True) -> KjbHd :
        
       
        difference_two_approve:bool = False
        is_draft = obj_current.is_draft or False
        db_session =  db_session or db.session

        if obj_current.is_draft != True:
            #add history
            await HistoryService().create_history_kjb(obj_current=obj_current, worker_id=updated_by_id, db_session=db_session)

        obj_data = jsonable_encoder(obj_current)

        if isinstance(obj_new, dict):
            update_data =  obj_new
        else:
            update_data = obj_new.dict(exclude_unset=True) #This tell pydantic to not include the values that were not sent
        
        for field in obj_data:
            if field in update_data:
                setattr(obj_current, field, update_data[field])
            if field == "updated_at":
                setattr(obj_current, field, datetime.utcnow())
        
        if updated_by_id:
            obj_current.updated_by_id = updated_by_id
        
        if obj_new.file:
            obj_current.file_path = await GCStorageService().base64ToFilePath(base64_str=obj_new.file, file_name=obj_new.code.replace('/', '_'))
        
        db_session.add(obj_current)

        #delete all data detail current when not exists in schema update
        await db_session.execute(delete(KjbRekening).where(and_(KjbRekening.id.notin_(r.id for r in obj_new.rekenings if r.id is not None), 
                                                        KjbRekening.kjb_hd_id == obj_current.id)))
        
        await db_session.execute(delete(KjbHarga).where(and_(KjbHarga.id.notin_(h.id for h in obj_new.hargas if h.id is not None),
                                                            KjbHarga.kjb_hd_id == obj_current.id)))
        
        
        if difference_two_approve is False:
            difference_two_approve = True if len(list(map(lambda item: item, filter(lambda x: x.id not in map(lambda y: y.id, obj_new.bebanbiayas), obj_current.bebanbiayas)))) > 0 and is_draft == False else False
       
        await db_session.execute(delete(KjbBebanBiaya).where(and_(KjbBebanBiaya.id.notin_(b.id for b in obj_new.bebanbiayas if b.id is not None),
                                                            KjbBebanBiaya.kjb_hd_id == obj_current.id)))
        
        await db_session.execute(delete(KjbPenjual).where(and_(KjbPenjual.id.notin_(p.id for p in obj_new.penjuals if p.id is not None),
                                                            KjbPenjual.kjb_hd_id == obj_current.id)))
        
        await db_session.execute(delete(KjbDt).where(and_(KjbDt.id.notin_(dt.id for dt in obj_new.details if dt.id is not None),
                                                            KjbDt.kjb_hd_id == obj_current.id)))
        

        for rekening in obj_new.rekenings:
            existing_rekening = next((r for r in obj_current.rekenings if r.id == rekening.id), None)
            if existing_rekening:
                rek = rekening.dict(exclude={"pemilik_id"}, exclude_unset=True)
                for key, value in rek.items():
                    setattr(existing_rekening, key, value)
                existing_rekening.updated_at = datetime.utcnow()
                existing_rekening.updated_by_id = updated_by_id
                db_session.add(existing_rekening)
            else:
                new_rekening = KjbRekening(**rekening.dict(), kjb_hd_id=obj_current.id, created_by_id=updated_by_id, updated_by_id=updated_by_id)
                db_session.add(new_rekening)
            
            if rekening.pemilik_id:
                rekenings = await crud.rekening.get_by_pemilik_id(pemilik_id=rekening.pemilik_id)
                existing_rekening_ = next((r for r in rekenings if r.nomor_rekening == rekening.nomor_rekening), None)
                if existing_rekening_ is None:
                    new_rekening_ = Rekening(**rekening.dict(exclude={"id"}))
                    db_session.add(new_rekening_)
        
        for harga in obj_new.hargas:
            existing_harga = next((h for h in obj_current.hargas if h.id == harga.id), None)
            if existing_harga:
                har = harga.dict(exclude_unset=True)
                for key, value in har.items():
                    if key == 'termins':
                        continue
                    setattr(existing_harga, key, value)
                existing_harga.updated_at = datetime.utcnow()
                existing_harga.updated_by_id = updated_by_id
                db_session.add(existing_harga)

                await db_session.execute(delete(KjbTermin).where(and_(KjbTermin.id.notin_(b.id for b in harga.termins if b.id is not None),
                                                            KjbTermin.kjb_harga_id == existing_harga.id)))
                
                for termin in harga.termins:
                    existing_termin = next((t for t in existing_harga.termins if t.id == termin.id), None)
                    if existing_termin:
                        ter = termin.dict(exclude_unset=True)
                        for key, value in ter.items():
                            setattr(existing_termin, key, value)
                        existing_termin.updated_at = datetime.utcnow()
                        existing_termin.updated_by_id = updated_by_id
                        db_session.add(existing_termin)

                    else:
                        new_termin = KjbTermin(**termin.dict(), kjb_harga_id=existing_harga.id, created_by_id=updated_by_id, updated_by_id=updated_by_id)
                        db_session.add(new_termin)
                
            else:
                new_harga = KjbHarga(**harga.dict(), kjb_hd_id=obj_current.id, created_by_id=updated_by_id, updated_by_id=updated_by_id)
                db_session.add(new_harga)

                for termin in harga.termins:
                    new_termin = KjbTermin(**termin.dict(), kjb_harga_id=new_harga.id, created_by_id=updated_by_id, updated_by_id=updated_by_id)
                    db_session.add(new_termin)
        
        
        for beban_biaya in obj_new.bebanbiayas:
            existing_bebanbiaya = next((b for b in obj_current.bebanbiayas if b.id == beban_biaya.id), None)
            if existing_bebanbiaya:
                bb = beban_biaya.dict(exclude_unset=True)
                for key, value in bb.items():
                    if key == "beban_biaya_name":
                        continue
                    if difference_two_approve == False:
                        difference_two_approve == True if value != getattr(existing_bebanbiaya, key) and is_draft == False else False

                    setattr(existing_bebanbiaya, key, value)
                existing_bebanbiaya.updated_at = datetime.utcnow()
                existing_bebanbiaya.updated_by_id = updated_by_id
                db_session.add(existing_bebanbiaya)
            else:
                new_bebanbiaya = KjbBebanBiaya(**beban_biaya.dict(), kjb_hd_id=obj_current.id, created_by_id=updated_by_id, updated_by_id=updated_by_id)
                db_session.add(new_bebanbiaya)
                if difference_two_approve == False:
                    difference_two_approve = True if is_draft == False else False
        
        for penjual in obj_new.penjuals:
            existing_penjual = next((p for p in obj_current.penjuals if p.id == penjual.id), None)
            if existing_penjual:
                pj = penjual.dict(exclude_unset=True)
                for key, value in pj.items():
                    setattr(existing_penjual, key, value)
                existing_penjual.updated_at = datetime.utcnow()
                existing_penjual.updated_by_id = updated_by_id
                db_session.add(existing_penjual)
            else:
                new_penjual = KjbPenjual(**penjual.dict(), kjb_hd_id=obj_current.id, created_by_id=updated_by_id, updated_by_id=updated_by_id)
                db_session.add(new_penjual)
        
        for detail in obj_new.details:
            existing_detail = next((dt for dt in obj_current.kjb_dts if dt.id == detail.id), None)
            if existing_detail:
                dtl = detail.dict(exclude_unset=True)
                for key, value in dtl.items():
                    setattr(existing_detail, key, value)
                existing_detail.updated_at = datetime.utcnow()
                existing_detail.updated_by_id = updated_by_id
                db_session.add(existing_detail)

            else:
                new_detail = KjbDt(**detail.dict(), kjb_hd_id=obj_current.id, created_by_id=updated_by_id, updated_by_id=updated_by_id)
                db_session.add(new_detail)
        
        if obj_new.is_draft == False:
            public_url = await GCStorageService().public_url(file_path=obj_current.file_path)
            flow = await crud.workflow_template.get_by_entity(entity=WorkflowEntityEnum.KJB)
            wf_system_attachment = WorkflowSystemAttachmentSch(name=f"KJB-{obj_current.code}", url=public_url)
            wf_system_sch = WorkflowSystemCreateSch(client_ref_no=str(obj_current.id), flow_id=flow.flow_id, additional_info={"approval_number" : "ONE_APPROVAL"}, version=1, attachments=[vars(wf_system_attachment)],
                                                    descs=f"""Dokumen KJB {obj_current.code} ini membutuhkan Approval dari Anda:<br><br>
                                                            Tanggal: {obj_current.created_at.date()}<br>
                                                            Dokumen: {obj_current.code}<br><br>
                                                            Berikut lampiran dokumen terkait : """)
            
            wf_current = await crud.workflow.get_by_reference_id(reference_id=obj_current.id)
            version = 1 if wf_current.version is None else wf_current.version

            if wf_current:
                if wf_current.last_status == WorkflowLastStatusEnum.COMPLETED:
                    wf_system_sch.version = version + 1
                    wf_current.version = version + 1
                else:
                    wf_system_sch.version = wf_current.version
                
                response, msg = await WorkflowService().create_workflow(body=vars(wf_system_sch))

                if response is None:
                    raise HTTPException(status_code=422, detail=f"Workflow Failed. Detail : {msg}")
                
                wf_current.last_status = response.last_status
                db_session.add(wf_current)
            else:
                response, msg = await WorkflowService().create_workflow(body=vars(wf_system_sch))
                if response is None:
                    raise HTTPException(status_code=422, detail=f"Workflow Failed. Detail : {msg}")
                new_workflow = Workflow(reference_id=id, entity=WorkflowEntityEnum.KJB, flow_id=flow.flow_id, last_status=response.last_status, version=1)
                db_session.add(new_workflow)
            
        if with_commit:
            await db_session.commit()
            await db_session.refresh(obj_current)

        # fungsi ini pindah ke dalam workflow notification
        # if obj_new.is_draft == False:
        #     url = f'{request.base_url}landrope/kjbhd/task/update-alashak'
        #     GCloudTaskService().create_task(payload={"id":str(obj_current.id)}, base_url=url)

        return obj_current

    async def get_multi_kjb_not_draft(
        self,
        *,
        keyword:str | None = None,
        filter_query: str | None = None,
        params: Params | None = Params(),
        order_by: str | None = None,
        order: OrderEnumSch | None = OrderEnumSch.ascendent,
        query: KjbHd | Select[KjbHd] | None = None,
        db_session: AsyncSession | None = None,
        join:bool | None = False
    ) -> Page[KjbHd]:
        db_session = db_session or db.session

        columns = self.model.__table__.columns

        find = False
        for c in columns:
            if c.name == order_by:
                find = True
                break
        
        if order_by is None or find == False:
            order_by = "id"
        
        if query is None:
            query = select(self.model)

        if filter_query is not None and filter_query:
            filter_query = json.loads(filter_query)
            
            for key, value in filter_query.items():
                query = query.where(getattr(self.model, key) == value)
        
        filter_clause = None

        if keyword:
            for attr in columns:
                if not "CHAR" in str(attr.type) or attr.name.endswith("_id") or attr.name == "id":
                    continue

                condition = getattr(self.model, attr.name).ilike(f'%{keyword}%')
                if filter_clause is None:
                    filter_clause = condition
                else:
                    filter_clause = or_(filter_clause, condition)
                
        #Filter Column yang berelasi dengan object (untuk case tertentu)
        if join:
            relationships = self.model.__mapper__.relationships

            for r in relationships:
                if r.uselist: #filter object list dilewati
                    continue
                if class_relation.__name__.lower() == "worker":
                    continue

                class_relation = r.mapper.class_
                query = query.join(class_relation)

                if keyword:
                    relation_columns = class_relation.__table__.columns
                            
                    for c in relation_columns:
                        if not "CHAR" in str(c.type) or c.name.endswith("_id") or c.name == "id":
                            continue
                        if "updated" in c.name or "created" in c.name:
                            continue
                        
                        cond = getattr(class_relation, c.name).ilike(f'%{keyword}%')
                        if filter_clause is None:
                            filter_clause = cond
                        else:
                            filter_clause = or_(filter_clause, cond)

        if filter_clause is not None:        
            query = query.filter(filter_clause)

        if order == OrderEnumSch.ascendent:
            query = query.order_by(columns[order_by].asc())
        else:
            query = query.order_by(columns[order_by].desc())

        query.where(self.model.is_draft != True)
            
        return await paginate(db_session, query, params)
    
    async def get_by_id_for_termin(self, *, id: UUID | str, db_session: AsyncSession | None = None) -> KjbHdForTerminByIdSch | None:
        db_session = db_session or db.session
        query = select(KjbHd.id,
                       KjbHd.code,
                       KjbHd.nama_group,
                       KjbHd.utj_amount,
                       ).select_from(KjbHd
                            ).where(KjbHd.id == id)

        response = await db_session.execute(query)

        return response.fetchone()
    
    async def get_by_id_for_cloud(
                    self, 
                    *, 
                    id: UUID | str,
                    db_session: AsyncSession | None = None
                    ) -> KjbHdForCloud | None:
        
        db_session = db_session or db.session
        query = text(f"""
                    select
                    id,
                    nama_group,
                    manager_id,
                    sales_id,
                    mediator,
                    telepon_mediator,
                    kategori_penjual
                    from kjb_hd
                    where id = '{str(id)}'
                    """)

        response = await db_session.execute(query)

        return response.fetchone()

kjb_hd = CRUDKjbHd(KjbHd)

