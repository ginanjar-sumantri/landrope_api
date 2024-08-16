from fastapi import UploadFile, BackgroundTasks, HTTPException
from schemas.export_log_sch import ExportLogUpdateSch
from services.export_log_service import ExportLogService
from services.gcloud_task_service import GCloudTaskService
from configs.config import settings
from common.enum import TaskStatusEnum
from datetime import date, timedelta, datetime
from uuid import uuid4
from io import BytesIO
import crud
import requests


class BidangService:

    OAUTH2_TOKEN = settings.OAUTH2_TOKEN
    INSTANCE = settings.INSTANCE

    # FUNGSI UNTUK CREATE EXPORT LOG, SEKALIGUS GENERATE FILE ZIP (SHP) DAN DIUPLOAD KE CLOUD STORAGE
    async def create_export_log_with_generate_file_shp(self, param, created_by_id, request):

        export_log = await ExportLogService().create_export_log(name="BIDANG SHP", media_type=".zip", created_by_id=created_by_id)

        GCloudTaskService().create_task(payload={  
                                                "projects": [str(pr) for pr in param.projects],
                                                "desas": [str(ds) for ds in param.desas],
                                                "jenis_bidangs": param.jenis_bidangs,
                                                "export_log_id" : str(export_log.id)
                                            }, 
                                        base_url=f'{request.base_url}landrope/bidang/task/generate/shp')

        return export_log
    
    # FUNGSI UNTUK CREATE EXPORT LOG, SEKALIGUS GENERATE FILE EXCEL DAN DIUPLOAD KE CLOUD STORAGE
    async def create_export_log_with_generate_file_excel(self, param, created_by_id, is_analyst, request):

        export_log = await ExportLogService().create_export_log(name="BIDANG EXCEL", media_type=".xlsx", created_by_id=created_by_id)

        GCloudTaskService().create_task(payload={  
                                                "projects": [str(pr) for pr in param.projects],
                                                "desas": [str(ds) for ds in param.desas],
                                                "jenis_bidangs": param.jenis_bidangs,
                                                "export_log_id": str(export_log.id),
                                                "is_analyst": is_analyst
                                            }, 
                                        base_url=f'{request.base_url}landrope/bidang/task/generate/excel')

        return export_log

    async def call_generate_shp_file_functions(self, payload, request):

        export_log_id = payload.get("export_log_id", None)

        export_log = await crud.export_log.get(id=export_log_id)
        if export_log is None:
            raise HTTPException(status_code=404, detail=f"Export Log not found!")
        
        try:
            
            url_functions = "https://asia-southeast2-sedayuone.cloudfunctions.net/landrope_generate_shp_bidang"

            headers = {
                'Authorization': 'Bearer ' + self.OAUTH2_TOKEN,
                'Content-Type': 'Application/Json'
            }

            is_staging = True if self.INSTANCE == "STAGING" else False

            body = {  
                    "projects": payload.get("projects", []),
                    "desas": payload.get("desas", []),
                    "jenis_bidangs": payload.get("jenis_bidangs", []),
                    "export_log_id" : str(export_log.id),
                    "is_staging" : is_staging
                }

            response = requests.post(url_functions, json=body, headers=headers)
            if response.status_code == 200:
                export_log_update = ExportLogUpdateSch.from_orm(export_log)

                if response.json()['status'] == 'OK':
                    file_path = response.json()['data']['file_path']

                    # UPDATE EXPORT STATUS OK
                    export_log_update.file_path = file_path
                    export_log_update.status = TaskStatusEnum.Done
                else:

                    err_detail = response.json()['detail']
                    # UPDATE EXPORT STATUS FAILED
                    export_log_update.error_msg = err_detail
                    export_log_update.status = TaskStatusEnum.Done_With_Error

                await crud.export_log.update(obj_current=export_log, obj_new=export_log_update)
                
            else:
                # print(f'{response.status_code}:{response.reason}')
                export_log_update = ExportLogUpdateSch.from_orm(export_log)
                export_log_update.error_msg = str(response.reason)
                export_log_update.status = TaskStatusEnum.Failed

                await crud.export_log.update(obj_current=export_log, obj_new=export_log_update)
                
                raise HTTPException(status_code=response.status_code, detail=response.reason)
            
        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e.args))
        
    async def call_generate_excel_file_functions(self, payload):

        export_log_id = payload.get("export_log_id", None)

        export_log = await crud.export_log.get(id=export_log_id)
        if export_log is None:
            raise HTTPException(status_code=404, detail=f"Export Log not found!")
        
        try:
            
            url_functions = "https://asia-southeast2-sedayuone.cloudfunctions.net/landrope_generate_excel_bidang"

            headers = {
                'Authorization': 'Bearer ' + self.OAUTH2_TOKEN,
                'Content-Type': 'Application/Json'
            }

            is_staging = True if self.INSTANCE == "STAGING" else False

            body = {  
                    "projects": payload.get("projects", []),
                    "desas": payload.get("desas", []),
                    "jenis_bidangs": payload.get("jenis_bidangs", []),
                    "export_log_id" : str(export_log.id),
                    "is_staging" : is_staging,
                    "is_analyst" : payload.get("is_analyst", False)
                }

            response = requests.post(url_functions, json=body, headers=headers)
            if response.status_code == 200:
                export_log_update = ExportLogUpdateSch.from_orm(export_log)

                if response.json()['status'] == 'OK':
                    file_path = response.json()['data']['file_path']

                    # UPDATE EXPORT STATUS OK
                    export_log_update.file_path = file_path
                    export_log_update.status = TaskStatusEnum.Done
                else:

                    err_detail = response.json()['detail']
                    # UPDATE EXPORT STATUS FAILED
                    export_log_update.error_msg = err_detail
                    export_log_update.status = TaskStatusEnum.Done_With_Error

                await crud.export_log.update(obj_current=export_log, obj_new=export_log_update)
                
            else:
                # print(f'{response.status_code}:{response.reason}')
                export_log_update = ExportLogUpdateSch.from_orm(export_log)
                export_log_update.error_msg = str(response.reason)
                export_log_update.status = TaskStatusEnum.Failed

                await crud.export_log.update(obj_current=export_log, obj_new=export_log_update)
                
                raise HTTPException(status_code=response.status_code, detail=response.reason)
            
        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e.args))
        
    


        
