from fastapi import Depends
from fastapi_async_sqlalchemy import db
from sqlmodel.ext.asyncio.session import AsyncSession
from models import Worker, Bidang
from schemas.bidang_sch import BidangSch
from schemas.bidang_history_sch import BidangHistoryCreateSch, MetaDataSch
from schemas.spk_history_sch import SpkHistoryCreateSch
from schemas.spk_sch import SpkByIdSch
from services.helper_service import HelperService
from shapely import wkt, wkb
from uuid import UUID
import crud


class HistoryService:

    async def create_history_bidang(self, obj_current:Bidang,
                                worker_id:UUID|None = None,
                                db_session:AsyncSession | None = None):

        meta_data_current = MetaDataSch(**dict(obj_current), created_by_name=obj_current.created_by_name, updated_by_name=obj_current.updated_by_name,
                                        pemilik_name=obj_current.pemilik_name, project_name=obj_current.project_name, desa_name=obj_current.desa_name,
                                        sub_project_name=obj_current.sub_project_name, planing_name=obj_current.planing_name, jenis_surat_name=obj_current.jenis_surat_name,
                                        kategori_name=obj_current.kategori_name, kategori_sub_name=obj_current.kategori_sub_name, kategori_proyek_name=obj_current.kategori_proyek_name,
                                        ptsk_name=obj_current.ptsk_name, no_sk=obj_current.no_sk, status_sk=obj_current.status_sk, penampung_name=obj_current.penampung_name,
                                        manager_name=obj_current.manager_name, sales_name=obj_current.sales_name, notaris_name=obj_current.notaris_name)

        
        sch = BidangHistoryCreateSch(meta_data=meta_data_current.json(),
                                     bidang_id=meta_data_current.id,
                                     trans_worker_id=obj_current.updated_by_id,
                                     trans_at=HelperService().no_timezone(obj_current.updated_at)
                                    )
        
        await crud.bidang_history.create(obj_in=sch, created_by_id=worker_id, db_session=db_session, with_commit=False)

    
    async def create_history_spk(self, spk:SpkByIdSch,
                                worker_id:UUID|None = None,
                                db_session:AsyncSession | None = None,):

        sch = SpkHistoryCreateSch(spk_id=spk.id, 
                                    meta_data=spk.json(), 
                                    trans_at=HelperService().no_timezone(spk.updated_at), 
                                    trans_worker_id=spk.updated_by_id)
        

        await crud.spk_history.create(obj_in=sch, created_by_id=worker_id, db_session=db_session, with_commit=False)
        

