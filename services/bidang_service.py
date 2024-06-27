from fastapi import UploadFile, BackgroundTasks
from schemas.export_log_sch import ExportLogCreateSch, ExportLogUpdateSch
from services.geom_service import GeomService
from services.gcloud_storage_service import GCStorageService
from common.enum import TaskStatusEnum
from datetime import date, timedelta, datetime
from uuid import uuid4
import crud


class BidangService:

    # FUNGSI UNTUK CREATE EXPORT LOG, SEKALIGUS GENERATE FILE ZIP (SHP) DAN DIUPLOAD KE CLOUD STORAGE
    async def create_export_log_with_generate_file_shp(self, param, created_by_id, bg_task:BackgroundTasks):

        # CREATE EXPORT LOG DATA
        export_log_new = ExportLogCreateSch(name="BIDANG SHP", status=TaskStatusEnum.OnProgress, 
                                            media_type=".zip", expired_date=self.add_days(n=14).date())
        
        export_log = await crud.export_log.create(obj_in=export_log_new, created_by_id=created_by_id)

        bg_task.add_task(self.generate_file_shp, param, export_log.id)

        return export_log

    
    async def generate_file_shp(self, param, export_log_id):

        export_log = await crud.export_log.get(id=export_log_id)

        try:
            # QUERY DATA BIDANG YANG INGIN DIEXPORT 
            results = await crud.bidang.get_multi_export_shape_file(param=param)

            # FUNGSI UNTUK MERUBAH DATA KE DALAM ZIP STREAM
            bytes_io_zip = GeomService.export_shp_bytes(data=results, obj_name="bidang")
            file_name = f"{str(export_log_id)}"

            file = UploadFile(file=bytes_io_zip, filename=f"{file_name}.zip")

            # UPLOAD TO CLOUD STORAGE
            file_path = await GCStorageService().upload_export_file(file=file, file_name=file_name)

            # UPDATE EXPORT STATUS 
            export_log_update = ExportLogUpdateSch.from_orm(export_log)
            export_log_update.file_path = file_path
            export_log_update.status = TaskStatusEnum.Done

            await crud.export_log.update(obj_current=export_log, obj_new=export_log_update)

        except Exception as e:

            export_log_update = ExportLogUpdateSch.from_orm(export_log)
            export_log_update.error_msg = str(e.args)
            export_log_update.status = TaskStatusEnum.Failed

            await crud.export_log.update(obj_current=export_log, obj_new=export_log_update)

        




    
    def add_days(self, n, d:date | None = datetime.today()):
        return d + timedelta(n)
