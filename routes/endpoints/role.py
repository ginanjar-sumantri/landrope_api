from fastapi import APIRouter, Depends
from fastapi_pagination import Params
from sqlalchemy import select, or_

import crud
from crud.worker_crud import worker
from models.worker_model import Role, Worker
from schemas.response_sch import GetResponsePaginatedSch, create_response, GetResponseBaseSch
from schemas.role_sch import RoleSch
from fastapi import exceptions

router = APIRouter()


@router.get("", response_model=GetResponsePaginatedSch[RoleSch])
async def get(

    param: Params = Depends(),
    current_worker: Worker = Depends(worker.get_active_worker)
):
    query = select(Role)
    if current_worker.is_super_admin:
        query = query
    elif current_worker.is_admin:
        query = query.filter(Role.name == 'USER')
    else:
        query = query.filter(Role.id == '')
    objs = await crud.role.get_multi_paginated_ordered(params=param, order_by='created_at', query=query)
    return create_response(data=objs)


@router.get("/no_page", response_model=GetResponseBaseSch[list[RoleSch]])
async def get_no_page(
    current_worker: Worker = Depends(worker.get_active_worker)
):
    query = select(Role)
    if current_worker.is_super_admin:
        query = query
    elif current_worker.is_admin:
        query = query.filter(Role.name == 'USER')
    else:
        # query = query.filter(Role.name == '')
        raise exceptions.HTTPException(status_code=401, detail='Unauthorized')
    objs = await crud.role.get_all_ordered(order_by=['created_at'], query=query)
    return create_response(data=objs)
