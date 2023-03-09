from uuid import UUID
from fastapi import APIRouter, Depends, status
from fastapi_pagination import Params
import crud
from models.project_model import Project
from schemas.project_sch import (ProjectSch, ProjectCreateSch, ProjectUpdateSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException)

router = APIRouter()

@router.post("", response_model=PostResponseBaseSch[ProjectSch], status_code=status.HTTP_201_CREATED)
async def create(sch: ProjectCreateSch):
    
    """Create a new object"""
    
    obj_current = await crud.project.get_by_name(name=sch.name)
    if obj_current:
        raise NameExistException(Project, name=sch.name)
    
    new_obj = await crud.project.create(obj_in=sch)
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[ProjectSch])
async def get_list(params:Params = Depends()):
    
    """Gets a paginated list objects"""

    objs = await crud.project.get_multi_paginated(params=params)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[ProjectSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.project.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Project, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[ProjectCreateSch])
async def update(id:UUID, sch:ProjectUpdateSch):
    
    """Update a obj by its id"""

    obj_current = await crud.project.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Project, id)
    
    obj_updated = await crud.project.update(obj_current=obj_current, obj_new=sch)
    return create_response(data=obj_updated)

