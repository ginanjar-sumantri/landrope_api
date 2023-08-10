from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from models.marketing_model import Manager, Sales
from models.worker_model import Worker
from schemas.marketing_sch import (ManagerSch, ManagerCreateSch, ManagerUpdateSch, SalesSch, SalesCreateSch, SalesUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException)
import crud

#region Manager
manager = APIRouter()

@manager.post("/create", response_model=PostResponseBaseSch[ManagerSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: ManagerCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
        
    new_obj = await crud.manager.create(obj_in=sch, created_by_id=current_worker.id)
    
    return create_response(data=new_obj)

@manager.get("", response_model=GetResponsePaginatedSch[ManagerSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.manager.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@manager.get("/{id}", response_model=GetResponseBaseSch[ManagerSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.manager.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Manager, id)

@manager.put("/{id}", response_model=PutResponseBaseSch[ManagerSch])
async def update(
            id:UUID, 
            sch:ManagerUpdateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.manager.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Manager, id)
    
    obj_updated = await crud.manager.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker)
    return create_response(data=obj_updated)

@manager.delete("/delete", response_model=DeleteResponseBaseSch[ManagerSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Delete a object"""

    obj_current = await crud.manager.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Manager, id)
    
    obj_deleted = await crud.manager.remove(id=id)

    return obj_deleted
#endregion


#region Sales
sales = APIRouter()

@sales.post("/create", response_model=PostResponseBaseSch[SalesSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: SalesCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
        
    new_obj = await crud.sales.create(obj_in=sch, created_by_id=current_worker.id)
    
    return create_response(data=new_obj)

@sales.get("", response_model=GetResponsePaginatedSch[SalesSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.sales.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@sales.get("/{id}", response_model=GetResponseBaseSch[SalesSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.sales.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Sales, id)

@sales.put("/{id}", response_model=PutResponseBaseSch[SalesSch])
async def update(
            id:UUID, 
            sch:SalesUpdateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.sales.get(id=id)

    if not obj_current:
        raise IdNotFoundException(Sales, id)
    
    obj_updated = await crud.sales.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)

@sales.delete("/delete", response_model=DeleteResponseBaseSch[SalesSch], status_code=status.HTTP_200_OK)
async def delete(id:UUID, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Delete a object"""

    obj_current = await crud.sales.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Sales, id)
    
    obj_deleted = await crud.sales.remove(id=id)

    return obj_deleted

   
#endregion