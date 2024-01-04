from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, File, HTTPException
from fastapi_pagination import Params
from sqlmodel import select, or_
from sqlalchemy.orm import selectinload
import crud
from models import Project, Section, Planing, Desa
from models.worker_model import Worker
from schemas.project_sch import (ProjectSch, ProjectCreateSch, ProjectUpdateSch, ProjectForTreeReportSch)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException)
from services.geom_service import GeomService
import json

router = APIRouter()

@router.post("", response_model=PostResponseBaseSch[ProjectSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: ProjectCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    
    obj_current = await crud.project.get_by_name(name=sch.name)
    if obj_current:
        raise NameExistException(Project, name=sch.name)
    
    new_obj = await crud.project.create(obj_in=sch, created_by_id=current_worker.id)
    
    new_obj = await crud.project.get_by_id(id=new_obj.id)

    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[ProjectSch])
async def get_list(
                desa_id:str|None = None,
                params:Params = Depends(), 
                order_by:str = None, 
                keyword:str = None, 
                filter_query:str = None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(Project)
    
    if desa_id:
        desa_ids = desa_id.split(',')

        query = query.join(Planing, Planing.project_id == Project.id
                    ).join(Desa, Desa.id == Planing.desa_id
                    ).where(Desa.id.in_(desa_ids))
    
    if keyword:
        query = query.filter(
            or_(
                Project.code.ilike(f'%{keyword}%'),
                Project.name.ilike(f'%{keyword}%')
            )
        )
    
    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
                query = query.where(getattr(Project, key) == value)
    
    query = query.distinct()

    objs = await crud.project.get_multi_paginated_ordered(params=params, query=query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[ProjectSch])
async def get_by_id(id:UUID):

    """Get an object by id"""
    
    obj = await crud.project.get_by_id(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Project, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[ProjectSch])
async def update(
            id:UUID, 
            sch:ProjectUpdateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.project.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Project, id)
    
    obj_updated = await crud.project.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    obj_updated = await crud.project.get_by_id(id=id)

    return create_response(data=obj_updated)

@router.post("/bulk")
async def bulk_create(file:UploadFile=File()):

    """Create bulk or import data"""

    try:
        file = await file.read()
        geo_dataframe = GeomService.file_to_geo_dataframe(file)
        
        for i, geo_data in geo_dataframe.iterrows():
            
            name:str = geo_data['project']

            sch = ProjectSch(name=name, code=name.replace(" ", ""))
            
            obj_current = await crud.project.get_by_name(name=sch.name)
            if not obj_current:
                new_obj = await crud.project.create(obj_in=sch)

    except:
        raise HTTPException(status_code=13, detail="Failed import data")
    
    return {"result" : status.HTTP_200_OK, "message" : "Successfully upload"}


@router.get("/report/map", response_model=GetResponseBaseSch[list[ProjectForTreeReportSch]])
async def get_list_for_report_map(current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Get for tree report map"""
    
    objs = await crud.project.get_all_project_tree_report_map()

    return create_response(data=objs)