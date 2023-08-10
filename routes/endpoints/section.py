from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
import crud
from models.section_model import Section
from models.worker_model import Worker
from schemas.section_sch import (SectionSch, SectionCreateSch, SectionUpdateSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException)

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[SectionSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: SectionCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    obj_current = await crud.section.get_by_name(name=sch.name)
    if obj_current:
        raise NameExistException(Section, name=sch.name)
    
    new_obj = await crud.section.create(obj_in=sch, created_by_id=current_worker.id)
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[SectionSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.section.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[SectionSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.section.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Section, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[SectionSch])
async def update(
            id:UUID, 
            sch:SectionUpdateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.section.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Section, id)
    
    obj_updated = await crud.section.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)
