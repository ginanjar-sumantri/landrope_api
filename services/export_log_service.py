from fastapi import HTTPException
from fastapi.responses import Response
from models import ExportLog
from schemas.export_log_sch import ExportLogUpdateSch
from services.gcloud_storage_service import GCStorageService
from services.helper_service import HelperService
from common.enum import TaskStatusEnum
import crud

class ExportLogService:

    async def get_file_export(self, obj:ExportLog):
        try:
            file_bytes = await GCStorageService().download_dokumen(file_path=obj.file_path)

            ext = obj.file_path.split('.')[-1]
            media_type = HelperService.get_media_type(ext=ext)
            if media_type is None:
                raise HTTPException(status_code=422, detail="File extentions of file not support")
            
            response = Response(content=file_bytes, media_type=media_type)
            response.headers["Content-Disposition"] = f"attachment; filename={obj.name}-{obj.id}.{ext}"
            return response
            
        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e.args))
        
    async def deleted_file_expired():

        try:
            export_logs = await crud.export_log.get_export_expired()

            for export_log in export_logs:

                await GCStorageService().delete_blob(blob_name=export_log.file_path)

                export_log_updated = ExportLogUpdateSch.from_orm(export_log)
                export_log_updated.status = TaskStatusEnum.Expired
                export_log_updated.file_path = None

                await crud.export_log.update(obj_current=export_log, obj_new=export_log_updated)

        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e.args))