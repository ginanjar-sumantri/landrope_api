from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, File, HTTPException
from fastapi_pagination import Params
from sqlmodel import select
from sqlalchemy.orm import selectinload
import crud
from models import SubProject, Worker
from schemas.sub_project_sch import (SubProjectSch, SubProjectCreateSch, SubProjectUpdateSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException)
from services.geom_service import GeomService

router = APIRouter()

@router.post("", response_model=PostResponseBaseSch[SubProjectSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: SubProjectCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    
    obj_current = await crud.sub_project.get_by_name(name=sch.name)
    if obj_current:
        raise NameExistException(SubProject, name=sch.name)
    
    new_obj = await crud.sub_project.create(obj_in=sch, created_by_id=current_worker.id)
    new_obj = await crud.sub_project.get_by_id(id=new_obj.id)

    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[SubProjectSch])
async def get_list(
                params:Params = Depends(), 
                order_by:str = None, 
                keyword:str = None, 
                filter_query:str = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.sub_project.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query, join=True)
    
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[SubProjectSch])
async def get_by_id(id:UUID):

    """Get an object by id"""
    
    obj = await crud.sub_project.get_by_id(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(SubProject, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[SubProjectSch])
async def update(
            id:UUID, 
            sch:SubProjectUpdateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.sub_project.get(id=id)
    if not obj_current:
        raise IdNotFoundException(SubProject, id)
    
    obj_updated = await crud.sub_project.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    obj_updated = await crud.sub_project.get_by_id(id=obj_updated.id)

    return create_response(data=obj_updated)