import random
import string
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from fastapi_pagination import Params

import crud
from models.worker_model import Worker
from schemas.response_sch import (DeleteResponseBaseSch, GetResponseBaseSch,
                                  GetResponsePaginatedSch, PostResponseBaseSch,
                                  PutResponseBaseSch, create_response)
from schemas.worker_sch import (WorkerByIdSch, WorkerCreateSch, WorkerSch,
                                WorkerUpdateSch)
from services.oauth_service import OauthService
from common.exceptions import (EmailExistException, IdNotFoundException)

router = APIRouter()


@router.get("", response_model=GetResponsePaginatedSch[WorkerByIdSch])
async def get(
    params: Params = Depends(),
    order_by:str = None, 
    keyword:str=None, 
    filter_query:str=None
):
    """
    Gets a paginated list objects
    """

    objs = await crud.worker.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)


@router.get("/{id}", response_model=GetResponseBaseSch[WorkerByIdSch])
async def get_by_id(
    id: UUID
):
    """
    Gets an object by its id
    """
    obj = await crud.worker.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(Worker, id)


@router.post(
    "",
    response_model=PostResponseBaseSch[WorkerSch],
    status_code=status.HTTP_201_CREATED,
)
async def create(
    sch: WorkerCreateSch,
    current_worker: Worker = Depends(crud.worker.get_current_user)

):
    """
    Creates a new obj

    """
    if current_worker.is_super_admin:
        already_exist_email = await crud.worker.get_by_email(email=sch.email)
        if already_exist_email:
            raise EmailExistException(Worker, email=sch.email)

        # already_exist_phone = await crud.worker.get_by_phone(phone=sch.phone)

        # if already_exist_phone:
        #     raise PhoneExistException(Worker, phone=sch.phone)

        response_exist = await OauthService().check_user_by_email_or_phone(email=sch.email)

        letters = string.ascii_letters
        password = ''.join(random.choice(letters) for _ in range(8))
        role = 'LANDROPE'

        oauth_response = None

        if 'detail' in response_exist:
            first_name, *last_name = str(sch.name).split(' ', 1)
            data = {
                'email': sch.email,
                'mobile_no': "",
                'first_name': first_name,
                'last_name': ''.join(last_name),
                'email_verified': False,
                'mobile_verified': False,
                'password': password,
                'roles': [role]
            }
            oauth_response, _ = await OauthService().register_user_oauth(body=data)
        elif (response_exist['mobile'] == response_exist['email'] and response_exist['email'] is not None) or (response_exist['email'] is not None and response_exist['mobile'] is None and response_exist['email']['mobile_no'] is None):
            data = response_exist['email']
            data['mobile_no'] = ""
            id = data.pop('id')
            data['password'] = password
            [data.pop(e) for e in ['avatar', 'full_name']]
            data['roles'].append(role) if role not in data['roles'] else data['roles']

            oauth_response, _ = await OauthService().update_user_oauth(body=data, id=id)

        else:
            # if response_exist['mobile'] is not None and response_exist['mobile']['email'] != sch.email:
            #     raise HTTPException(status_code=409,
            #                         detail='Mobile Number already register in our subsystem with another email address')
            # elif response_exist['email'] is not None and change_phone_format(response_exist['email']['mobile_no']) != sch.phone:
            #     raise HTTPException(status_code=409, detail='Email already registered with other mobile number')

            if response_exist['email'] is not None :
                raise HTTPException(status_code=409, detail='Email already registered')

            raise HTTPException(status_code=400, detail='Something wrong. Please contact developer.')

        new_obj = await crud.worker.create(obj_in=sch, oauth_user=oauth_response, worker_id=current_worker.id)
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return create_response(data=new_obj)


@router.put("/{id}", response_model=PutResponseBaseSch[WorkerSch])
async def update(
    id: UUID,
    sch: WorkerUpdateSch,
    current_worker: Worker = Depends(crud.worker.get_current_user)

):
    """
    Updates a obj by its id
    """
    obj_current = await crud.worker.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Worker, id=id)

    if current_worker.is_admin:
        # alrady_exist_mobile = await crud.worker.get_phone_exclude_me(phone=sch.phone, worker_id=current_worker.id)
        # if len(alrady_exist_mobile) != 0:
        #     raise HTTPException(status_code=409, detail='Mobile Number already used.')

        already_exist_email = await crud.worker.get_email_exclude_me(email=sch.email, worker_id=obj_current.id)
        if len(already_exist_email) != 0:
            raise HTTPException(status_code=409, detail='Email already used.')

        response_exist = await OauthService().check_user_by_email_or_phone(email=sch.email)

        letters = string.ascii_letters
        password = ''.join(random.choice(letters) for _ in range(8))
        role = 'LANDROPE'

        oauth_response = None
        if obj_current.oauth_id is not None:
            response_exist = await OauthService().get_user_by_id(oauth_id=str(obj_current.oauth_id))

            if 'detail' in response_exist:
                raise HTTPException(status_code=409, detail='Something wrong, please contact developer')

            response_exist = await OauthService().check_user_by_email_or_phone(email=obj_current.email)

            if (response_exist['mobile'] == response_exist['email'] 
                and response_exist['email'] is not None) or (response_exist['email'] is not None and response_exist['mobile'] is None and (response_exist['email']['mobile_no'] is None or response_exist['email']['id'] == str(obj_current.oauth_id))) or (obj_current.phone is not None and response_exist['mobile'] is not None and response_exist['email'] is None and response_exist['mobile']['id'] == str(obj_current.oauth_id)):
                data = response_exist['email'] if response_exist['email'] is not None else response_exist['mobile']
                data['mobile_no'] = None
                id = data.pop('id')
                data['password'] = password
                [data.pop(e) for e in ['avatar', 'full_name']]
                data['roles'].append(role) if role not in data['roles'] else data['roles']

                oauth_response = await OauthService().update_user_oauth(body=data, id=id)
            else:
                # if response_exist['mobile'] is not None and response_exist['mobile']['email'] != sch.email:
                #     raise HTTPException(
                #         status_code=409, detail='Mobile Number already register in our subsystem with another email address')
                # elif response_exist['email'] is not None and change_phone_format(response_exist['email']['mobile_no']) != sch.phone:
                #     raise HTTPException(
                #         status_code=409, detail='Email already registered with other mobile number')
                
                if response_exist['email'] is not None:
                    raise HTTPException(
                        status_code=409, detail='Email already registered')

                raise HTTPException(status_code=409, detail='Something wrong, please contact developer')
        else:
            response_exist = await OauthService().check_user_by_email_or_phone(email=obj_current.email, phone="")
            if 'detail' in response_exist:
                first_name, *last_name = str(obj_current.name).split(' ', 1)
                data = {
                    'email': obj_current.email,
                    'mobile_no': "",
                    'first_name': first_name,
                    'last_name': ''.join(last_name),
                    'email_verified': False,
                    'mobile_verified': False,
                    'password': password,
                    'roles': [role]
                }

                oauth_response = await OauthService().register_user_oauth(body=data)
            elif (response_exist['mobile'] == response_exist['email'] and response_exist['email'] is not None) or (response_exist['email'] is not None and response_exist['mobile'] is None and (response_exist['email']['mobile_no'] is None or response_exist['email']['id'] == str(obj_current.id))):
                data = response_exist['email']
                data['mobile_no'] = None
                id = data.pop('id')
                data['password'] = password
                [data.pop(e) for e in ['avatar', 'full_name']]
                data['roles'].append(role) if role not in data['roles'] else data['roles']

                oauth_response = await OauthService().update_user_oauth(data=data, id=id)
            else:
                # if response_exist['mobile'] is not None and response_exist['mobile']['email'] != sch.email:
                #     raise HTTPException(status_code=409,
                #                         detail='Mobile Number already register in our subsystem with another email address')
                # elif response_exist['email'] is not None and change_phone_format(response_exist['email']['mobile_no']) != sch.phone:
                #     raise HTTPException(status_code=409, detail='Email already registered with other mobile number')
                
                if response_exist['email'] is not None:
                    raise HTTPException(status_code=409, detail='Email already registered')

                raise HTTPException({'detail': 'Something wrong. Please contact developer.'})

        sch.oauth_id = oauth_response[0].id

        obj_updated = await crud.worker.update(obj_current=obj_current, obj_new=sch)
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return create_response(data=obj_updated)


@router.delete("/{id}", response_model=DeleteResponseBaseSch[WorkerSch])
async def delete(
    id: UUID,
    current_worker: Worker = Depends(crud.worker_crud.worker.get_current_user)
):
    obj_current = await crud.worker.get(id=id)
    if not obj_current:
        raise IdNotFoundException(Worker, id)

    else:
        obj_current = await crud.worker.remove(id=id, worker_id=current_worker.id)
    return create_response(data=obj_current)
