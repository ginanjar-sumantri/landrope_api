from uuid import UUID
from fastapi import APIRouter, status, Depends
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlalchemy import delete, Table
from models.draft_report_map_model import DraftReportMap
from models.worker_model import Worker
from schemas.draft_report_map_sch import (DraftReportMapSch, DraftReportMapCreateSch, DraftReportMapUpdateSch, DraftReportMapHdCreateSch, DraftReportMapHdUpdateSch)
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.generator import generate_code
from models.code_counter_model import CodeCounterEnum
import crud


router = APIRouter()

@router.post("/create", response_model=GetResponseBaseSch[list[DraftReportMapSch]], status_code=status.HTTP_201_CREATED)
async def create(
            sch: DraftReportMapHdCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    db_session = db.session

    drafts = []
    for dt in sch.details:
      draft_sch = DraftReportMapCreateSch(report_id=sch.report_id, type=dt.type, obj_id=dt.obj_id)
      new_obj = await crud.draft_report_map.create(obj_in=draft_sch, created_by_id=current_worker.id, db_session=db_session, with_commit=False)
      drafts.append(new_obj)
    
    await db_session.commit()
    
    return create_response(data=drafts)

@router.get("", response_model=GetResponsePaginatedSch[DraftReportMapSch])
async def get_list(
                params: Params=Depends(), 
                order_by:str = None, 
                keyword:str = None, 
                filter_query:str=None,
                current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.draft_report_map.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[DraftReportMapSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.draft_report_map.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(DraftReportMap, id)

@router.put("/{id}", response_model=GetResponseBaseSch[list[DraftReportMapSch]])
async def update(id:UUID, sch:DraftReportMapHdUpdateSch,
                 current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    db_session = db.session
    obj_currents = await crud.draft_report_map.get_multi_by_report_id(report_id=id)
    if obj_currents is None:
        raise IdNotFoundException(DraftReportMap, id)

    #remove data ketika update 
    list_ids = [draft.id for draft in sch.details if draft.id != None]
    if len(list_ids) > 0:
        draft_will_removed = await crud.draft_report_map.get_not_in_by_ids_and_report_id(list_ids=list_ids, report_id=id)
        if len(draft_will_removed) > 0:
            await crud.draft_report_map.remove_multiple_data(list_obj=draft_will_removed, db_session=db_session)
    elif len(list_ids) == 0 and len(obj_currents) > 0:
        await crud.draft_report_map.remove_multiple_data(list_obj=obj_currents, db_session=db_session)
    
    objs = []
    for draft in sch.details:
        if draft.id is None:
            draft_sch = DraftReportMapCreateSch(report_id=id, type=draft.type, obj_id=draft.obj_id)
            new_obj = await crud.draft_report_map.create(obj_in=draft_sch, created_by_id=current_worker.id, db_session=db_session, with_commit=False)
            objs.append(new_obj)
        else:
            draft_current = await crud.draft_report_map.get(id=draft.id)
            draft_sch = DraftReportMapUpdateSch(report_id=id, type=draft.type, obj_id=draft.obj_id)
            updated_obj = await crud.draft_report_map.update(obj_current=draft_current, obj_new=draft_sch, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)
            objs.append(updated_obj)

    await db_session.commit()
    
    return create_response(data=objs)

@router.delete("/delete", response_model=DeleteResponseBaseSch[DraftReportMap], status_code=status.HTTP_200_OK)
async def delete(id:UUID, current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Delete a object"""
    db_session = db.session

    obj_currents = await crud.draft_report_map.get_multi_by_report_id(report_id=id)
    if obj_currents is None:
        raise IdNotFoundException(DraftReportMap, id)
    
    query = DraftReportMap.__table__.delete().where(DraftReportMap.report_id == id)

    await db_session.execute(query)
    await db_session.commit()

    return {"message": f"Item dengan ID {id} berhasil dihapus"}

   