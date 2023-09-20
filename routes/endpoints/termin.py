from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
import crud
from models.termin_model import Termin
from models.worker_model import Worker
from schemas.termin_sch import (TerminSch, TerminCreateSch, TerminUpdateSch)
from schemas.invoice_sch import InvoiceCreateSch
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, NameExistException)

router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[TerminSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: TerminCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    db_session = db.session

    new_obj = await crud.termin.create(obj_in=sch, db_session=db_session, with_commit=False, created_by_id=current_worker.id)

    #add invoice
    for invoice in sch.invoices:
        invoice_sch = InvoiceCreateSch(**invoice.dict(), termin_id=new_obj.id)
        await crud.invoice.create(obj_in=invoice_sch, db_session=db_session, with_commit=False)



    #return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[TerminSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.termin.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[TerminSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.termin.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Termin, id)
    
@router.put("/{id}", response_model=PutResponseBaseSch[TerminSch])
async def update(
            id:UUID, 
            sch:TerminUpdateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.termin.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Termin, id)
    
    obj_updated = await crud.termin.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    return create_response(data=obj_updated)
