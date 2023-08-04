from uuid import UUID
from fastapi import APIRouter, status, Depends, UploadFile, File
from fastapi_pagination import Params
import crud
from services.geom_service import GeomService
from models.draft_model import Draft
from models.worker_model import Worker
from schemas.draft_sch import (DraftSch, DraftCreateSch, DraftRawSch)
from schemas.response_sch import (PostResponseBaseSch, DeleteResponseBaseSch,  create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from shapely.geometry import shape

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[DraftRawSch], status_code=status.HTTP_201_CREATED)
async def create(sch: DraftCreateSch = Depends(DraftCreateSch.as_form), file:UploadFile = File(),
                 current_worker:Worker = Depends(crud.worker.get_current_user)):
    
    """Create a new object"""

    if file is not None:

        geo_dataframe = GeomService.file_to_geodataframe(file=file.file)

        if geo_dataframe.geometry[0].geom_type == "LineString":
            polygon = GeomService.linestring_to_polygon(shape(geo_dataframe.geometry[0]))
            geo_dataframe['geometry'] = polygon.geometry
        
        sch = DraftSch(rincik_id=sch.rincik_id, skpt_id=sch.skpt_id, planing_id=sch.planing_id, geom=GeomService.single_geometry_to_wkt(geo_dataframe.geometry))
    else:
        raise ImportFailedException()
        
    new_obj = await crud.draft.create(obj_in=sch, created_by_id=current_worker.id)
    
    return create_response(data=new_obj)

@router.delete("/delete", response_model=DeleteResponseBaseSch[DraftRawSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID):
    
    """Delete a object"""

    obj_current = await crud.draft.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Draft, id)
    
    obj_deleted = await crud.draft.remove(id=id)

    return obj_deleted

   