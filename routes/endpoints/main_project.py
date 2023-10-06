from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, File, HTTPException
from fastapi_pagination import Params
from sqlmodel import select
from sqlalchemy.orm import selectinload
import crud
from models import MainProject, Worker
from schemas.main_project_sch import (MainProjectSch, MainProjectCreateSch, MainProjectUpdateSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException, CodeExistException)
from services.geom_service import GeomService

router = APIRouter()

@router.post("", response_model=PostResponseBaseSch[MainProjectSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: MainProjectCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    
    obj_current = await crud.main_project.get_by_code(code=sch.code)
    if obj_current:
        raise CodeExistException(MainProject, name=sch.code)
    
    new_obj = await crud.main_project.create(obj_in=sch, created_by_id=current_worker.id)

    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[MainProjectSch])
async def get_list(
                params:Params = Depends(), 
                order_by:str = None, 
                keyword:str = None, 
                filter_query:str = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.main_project.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query, join=True)
    
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[MainProjectSch])
async def get_by_id(id:UUID):

    """Get an object by id"""
    
    obj = await crud.main_project.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(MainProject, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[MainProjectSch])
async def update(
            id:UUID, 
            sch:MainProjectUpdateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.main_project.get(id=id)
    if not obj_current:
        raise IdNotFoundException(MainProject, id)
    
    obj_updated = await crud.main_project.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)

    return create_response(data=obj_updated)