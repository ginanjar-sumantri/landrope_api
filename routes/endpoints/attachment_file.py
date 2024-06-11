from uuid import UUID
from fastapi import APIRouter, Query, Depends, HTTPException, UploadFile, Request, Response
from fastapi.responses import FileResponse
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)

from common.exceptions import (IdNotFoundException, ImportFailedException, DocumentFileNotFoundException)
from common.enum import WorkflowEntityEnum, WorkflowLastStatusEnum


from services.gcloud_storage_service import GCStorageService
from services.encrypt_service import encrypt, decrypt
import crud
from configs.config import settings
from urllib.parse import urljoin

router = APIRouter()


@router.get("/encrypt/{id}")
async def encrypt_id(id: str, request: Request):
    """Encrypt a UUID"""
    try:
        kjbhd_id = UUID(id)
        encrypted_id = encrypt(str(kjbhd_id))
        url = f'{request.base_url}landrope/kjbhd/document/{encrypted_id}'
        return url
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")


@router.get("/document/{id}")
async def get_document_or_file(id: str, en: WorkflowEntityEnum | str):
    """Get a document"""
    try:
        decrypted_id = decrypt(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

    try:
        entity_id = UUID(decrypted_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    if en == WorkflowEntityEnum.SPK:
        obj = await crud.spk.get(id=entity_id)
    elif en == WorkflowEntityEnum.TERMIN:
        obj = await crud.termin.get(id=entity_id)
    elif en == WorkflowEntityEnum.KJB:
        obj = await crud.kjb_hd.get(id=entity_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid entity type")

    if not obj:
        raise HTTPException(status_code=404, detail=f"Document with ID {entity_id} not found")

    if obj.file_path:  
        try:
            file_bytes = await GCStorageService().download_dokumen(file_path=obj.file_path)
        except Exception:
            raise HTTPException(status_code=404, detail=f"File for document {obj.code} not found")

        ext = obj.file_path.split('.')[-1]
        return FileResponse(file_bytes, media_type="application/octet-stream", headers={"Content-Disposition": f"attachment; filename={obj.id}.{ext}"})
        # response = Response(content=file_bytes, media_type="application/octet-stream")
        # response.headers["Content-Disposition"] = f"inline; filename={obj.code}-{entity_id}.{ext}"
        
    else:
        raise HTTPException(status_code=404, detail=f"File for document {obj.code} not found")

    # return response
