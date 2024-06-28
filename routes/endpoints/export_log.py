from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from fastapi_pagination import Params
from sqlmodel import select
from models import Worker, ExportLog
from common.exceptions import IdNotFoundException
from schemas.response_sch import create_response, GetResponsePaginatedSch
from schemas.export_log_sch import ExportLogSch
from services.gcloud_storage_service import GCStorageService
from services.helper_service import HelperService
from uuid import UUID
import crud
import json


router = APIRouter()

@router.get("", response_model=GetResponsePaginatedSch[ExportLogSch])
async def get_list(
        params: Params=Depends(), 
        order_by:str = None, 
        keyword:str = None, 
        filter_query:str = None,
        current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(ExportLog).join(ExportLog.worker)

    if current_worker.is_super_admin is False:
        query = query.filter(ExportLog.created_by_id == current_worker.id)

    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
            query = query.where(getattr(ExportLog, key) == value)

    objs = await crud.export_log.get_multi_paginated(params=params, query=query)
    return create_response(data=objs)

@router.get("/download/file/{id}")
async def get_document_or_file(id: UUID, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Get a file"""
    
    obj = await crud.export_log.get(id=id)

    if not obj:
        raise IdNotFoundException(model=ExportLog, id=id)
    
    if obj.file_path is None:
        raise HTTPException(status_code=404, detail=f"File not found!")
    
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