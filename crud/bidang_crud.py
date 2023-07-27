from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from crud.base_crud import CRUDBase
from models.bidang_model import Bidang
from schemas.bidang_sch import BidangCreateSch, BidangUpdateSch, BidangShpSch, BidangShpExSch
from common.exceptions import (IdNotFoundException, NameNotFoundException, ImportFailedException, FileNotFoundException)
from services.gcloud_storage_service import GCStorageService
from services.geom_service import GeomService
from io import BytesIO
from uuid import UUID
from itertools import islice
import crud
import time


class CRUDBidang(CRUDBase[Bidang, BidangCreateSch, BidangUpdateSch]):
    async def get_by_id_bidang(
        self, *, idbidang: str, db_session: AsyncSession | None = None
    ) -> Bidang:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Bidang).where(Bidang.id_bidang == idbidang))
        return obj.scalar_one_or_none()
    
    async def get_by_id_bidang_lama(
        self, *, idbidang_lama: str, db_session: AsyncSession | None = None
    ) -> Bidang:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Bidang).where(Bidang.id_bidang_lama == idbidang_lama))
        return obj.scalar_one_or_none()
    
    async def get_by_id_bidang_id_bidang_lama(
        self, *, idbidang: str, idbidang_lama: str, db_session: AsyncSession | None = None
    ) -> Bidang:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Bidang).where(and_(Bidang.id_bidang == idbidang, Bidang.id_bidang_lama == idbidang_lama)))
        return obj.scalar_one_or_none()
    
    # async def lets_bulk_bidang(
    #     self,
    #     *,
    #     file:BytesIO | None,
    #     import_log_id:UUID | None,
    #     file_path:str | None,
    #     db_session:AsyncSession | None = None
    #     ) -> bool:

    #     log = await crud.import_log.get(id=import_log_id)
    #     if log is None:
    #         return False

    #     start:int = log.done_count
    #     count:int = log.done_count

    #     if log.done_count > 0:
    #         start = log.done_count

    #     null_values = ["", "None", "nan", None]

    #     file = await GCStorage().download_file(file_path)
    #     if not file:
    #         return False

    #     geo_dataframe = GeomService.file_to_geodataframe(file)

    #     start_time = time.time()
    #     max_duration = 7 * 60

    #     for i, geo_data in islice(geo_dataframe.iterrows(), start, None):
            
    #         shp_data = BidangShpExSch(**geo_data.to_dict())

    #         luas_surat:Decimal = RoundTwo(Decimal(shp_data.luassurat))

    #         pemilik = None
    #         pmlk = await crud.pemilik.get_by_name(name=shp_data.pemilik)
    #         if pmlk:
    #             pemilik = pmlk.id
            
    #         jenis_surat = await crud.jenissurat.get_by_jenis_alashak_and_name(jenis_alashak=shp_data.dokumen, name=shp_data.sub_surat)
    #         if jenis_surat is None:
    #             jenissurat = None
    #         else:
    #             jenissurat = jenis_surat.id

    #         kategori = None
    #         kat = await crud.kategori.get_by_name(name=shp_data.kat)
    #         if kat:
    #             kategori = kat.id
            
    #         kategori_sub = None
    #         kat_sub = await crud.kategori_sub.get_by_name(name=shp_data.kat_bidang)
    #         if kat_sub:
    #             kategori_sub = kat_sub.id
            
    #         kategori_proyek = None
    #         kat_proyek = await crud.kategori_proyek.get_by_name(name=shp_data.kat_proyek)
    #         if kat_proyek:
    #             kategori_proyek = kat_proyek.id
            
    #         pt = None
    #         ptsk = await crud.ptsk.get_by_name(name=shp_data.ptsk)
    #         if ptsk:
    #             pt = ptsk.id
            
    #         skpt = None
    #         no_sk = await crud.skpt.get_by_sk_number(number=shp_data.no_sk)
    #         if no_sk:
    #             skpt = no_sk.id
            
    #         penampung = None
    #         pt_penampung = await crud.ptsk.get_by_name(name=shp_data.penampung)
    #         if pt_penampung:
    #             penampung = pt_penampung.id

    #         manager = None
    #         mng = await crud.manager.get_by_name(name=shp_data.manager)
    #         if mng:
    #             manager = mng.id
            
    #         sales = None
    #         sls = await crud.sales.get_by_name(name=shp_data.sales)
    #         if sls:
    #             sales = sls.id

    #         project = await crud.project.get_by_name(name=shp_data.project)
    #         if project is None:
    #             error_m = f"IdBidang {shp_data.o_idbidang} {shp_data.n_idbidang}, Project {shp_data.project} not exists in table master. "
    #             log_error = ImportLogErrorSch(row=i+1,
    #                                             error_message=error_m,
    #                                             import_log_id=log.id)

    #             log_error = await crud.import_log_error.create(obj_in=log_error)

    #             raise NameNotFoundException(Project, name=shp_data.project)

    #         desa = await crud.desa.get_by_name(name=shp_data.desa)
    #         if desa is None:
    #             error_m = f"IdBidang {shp_data.o_idbidang} {shp_data.n_idbidang}, Desa {shp_data.desa} code {shp_data.code_desa} not exists in table master. "
    #             log_error = ImportLogErrorSch(row=i+1,
    #                                             error_message=error_m,
    #                                             import_log_id=log.id)

    #             log_error = await crud.import_log_error.create(obj_in=log_error)

    #             raise NameNotFoundException(Desa, name=shp_data.desa)

    #         plan = await crud.planing.get_by_project_id_desa_id(project_id=project.id, desa_id=desa.id)
    #         if plan is None:
    #             error_m = f"IdBidang {shp_data.o_idbidang} {shp_data.n_idbidang}, Planing {shp_data.project}-{shp_data.desa} not exists in table master. "
    #             log_error = ImportLogErrorSch(row=i+1,
    #                                             error_message=error_m,
    #                                             import_log_id=log.id)

    #             log_error = await crud.import_log_error.create(obj_in=log_error)

    #             raise NameNotFoundException(Planing, name=f"{shp_data.project}-{shp_data.desa}")
                
    #         if shp_data.n_idbidang in null_values:
    #             bidang_lama = await crud.bidang.get_by_id_bidang_lama(idbidang_lama=shp_data.o_idbidang)
    #             if bidang_lama is None and plan is not None:
    #                 shp_data.n_idbidang = await generate_id_bidang(planing_id=plan.id)
    #             else:
    #                 shp_data.n_idbidang = bidang_lama.id_bidang

    #         sch = BidangSch(id_bidang=shp_data.n_idbidang,
    #                         id_bidang_lama=shp_data.o_idbidang,
    #                         no_peta=shp_data.no_peta,
    #                         pemilik_id=pemilik,
    #                         jenis_bidang=FindJenisBidang(shp_data.proses),
    #                         status=FindStatusBidang(shp_data.status),
    #                         planing_id=plan.id,
    #                         group=shp_data.group,
    #                         jenis_alashak=FindJenisAlashak(shp_data.dokumen),
    #                         jenis_surat_id=jenissurat,
    #                         alashak=shp_data.alashak,
    #                         kategori_id=kategori,
    #                         kategori_sub_id=kategori_sub,
    #                         kategori_proyek_id=kategori_proyek,
    #                         skpt_id=skpt,
    #                         penampung_id=penampung,
    #                         manager_id=manager,
    #                         sales_id=sales,
    #                         mediator=shp_data.mediator,
    #                         luas_surat=luas_surat,
    #                         geom=shp_data.geom)

    #         obj_current = await crud.bidang.get_by_id_bidang_id_bidang_lama(idbidang=sch.id_bidang, idbidang_lama=sch.id_bidang_lama)
    #         # obj_current = await crud.bidang.get_by_id_bidang_lama(idbidang_lama=shp_data.o_idbidang)

    #         if obj_current:
    #             if obj_current.geom :
    #                 obj_current.geom = wkt.dumps(wkb.loads(obj_current.geom.data, hex=True))
    #             obj = await crud.bidang.update(obj_current=obj_current, obj_new=sch)
    #         else:
    #             obj = await crud.bidang.create(obj_in=sch)
            
    #         obj_updated = log
    #         count = count + 1
    #         obj_updated.done_count = count

    #         log = await crud.import_log.update(obj_current=log, obj_new=obj_updated)

    #         # Waktu sekarang
    #         current_time = time.time()

    #         # Cek apakah sudah mencapai 7 menit
    #         elapsed_time = current_time - start_time
    #         if elapsed_time >= max_duration:
    #             url = f'{request.base_url}landrope/bidang/cloud-task-bulk'
    #             GCloudTaskService().create_task_import_data(import_instance=log, base_url=url)
    #             break  # Hentikan looping setelah 7 menit berlalu

    #         time.sleep(0.2)

    # except:
    #     error_m = f"Failed import, please check your data or contact administrator"
    #     log_error = ImportLogErrorSch(row=i+1,
    #                                     error_message=error_m,
    #                                     import_log_id=log.id)

    #     log_error = await crud.import_log_error.create(obj_in=log_error)
    #     raise ImportFailedException(filename=log.file_name)

    # if log.total_row == log.done_count:
    #     obj_updated = log
    #     obj_updated.status = TaskStatusEnum.Done
    #     obj_updated.completed_at = datetime.now()

    #     await crud.import_log.update(obj_current=log, obj_new=obj_updated)
        


bidang = CRUDBidang(Bidang)