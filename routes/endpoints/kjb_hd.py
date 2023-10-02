from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, or_
from models.kjb_model import KjbHd, KjbDt, KjbPenjual
from models.worker_model import Worker
from models.marketing_model import Manager, Sales
from models.pemilik_model import Pemilik
from models.code_counter_model import CodeCounterEnum
from schemas.kjb_hd_sch import (KjbHdSch, KjbHdCreateSch, KjbHdUpdateSch, KjbHdByIdSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.generator import generate_code
import crud
import json


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[KjbHdSch], status_code=status.HTTP_201_CREATED)
async def create(sch: KjbHdCreateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""

    db_session = db.session
    sch.code = await generate_code(CodeCounterEnum.Kjb, db_session=db_session, with_commit=False)

    new_obj = await crud.kjb_hd.create_kjb_hd(obj_in=sch, created_by_id=current_worker.id, db_session=db_session)
    new_obj = await crud.kjb_hd.get_by_id_cu(id=new_obj.id)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[KjbHdSch])
async def get_list(
        params: Params=Depends(), 
        order_by: str = None, 
        keyword: str = None, 
        filter_query: str= None,
        current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    query = select(KjbHd).select_from(KjbHd
                        ).outerjoin(Manager, KjbHd.manager_id == Manager.id
                        ).outerjoin(Sales, KjbHd.sales_id == Sales.id
                        ).outerjoin(KjbPenjual, KjbHd.id == KjbPenjual.kjb_hd_id
                        ).outerjoin(Pemilik, KjbPenjual.pemilik_id == Pemilik.id
                        ).outerjoin(KjbDt, KjbHd.id == KjbDt.kjb_hd_id)
    
    if keyword:
        query = query.filter(
            or_(
                KjbHd.code.ilike(f'%{keyword}%'),
                KjbHd.nama_group.ilike(f'%{keyword}%'),
                Pemilik.name.ilike(f'%{keyword}%'),
                Manager.name.ilike(f'%{keyword}%'),
                Sales.name.ilike(f'%{keyword}%'),
                KjbDt.alashak.ilike(f'%{keyword}%')
            )
        )
    
    if filter_query:
        filter_query = json.loads(filter_query)
        for key, value in filter_query.items():
                query = query.where(getattr(KjbHd, key) == value)


    objs = await crud.kjb_hd.get_multi_paginated(params=params, query=query)
    return create_response(data=objs)

@router.get("/not-draft", response_model=GetResponsePaginatedSch[KjbHdSch])
async def get_list_not_draft(params: Params=Depends(), order_by:str = None, keyword:str = None, filter_query:str=None):
    
    """Gets a paginated list objects"""

    objs = await crud.kjb_hd.get_multi_kjb_not_draft(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[KjbHdByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.kjb_hd.get_by_id(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(KjbHd, id)

@router.put("/{id}", response_model=PutResponseBaseSch[KjbHdSch])
async def update(id:UUID, sch:KjbHdUpdateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    obj_current = await crud.kjb_hd.get(id=id)

    if not obj_current:
        raise IdNotFoundException(KjbHd, id)
    
    obj_updated = await crud.kjb_hd.update(obj_current=obj_current, obj_new=sch, updated_by_id=current_worker.id)
    obj_updated = await crud.kjb_hd.get_by_id_cu(id=obj_updated.id)
    return create_response(data=obj_updated)


   