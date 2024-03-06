import crud
from geoalchemy2.shape import to_shape
from models.code_counter_model import CodeCounter, CodeCounterEnum
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
from datetime import datetime
import string
import random


async def generate_id_bidang(planing_id:UUID | str,
                             db_session : AsyncSession | None = None,
                             with_commit : bool | None = True) -> str:

    planing = await crud.planing.get_by_id(id=planing_id)

    desa = await crud.desa.get(id=planing.desa_id)
    if desa.geom:
        desa.geom = to_shape(desa.geom).__str__()
    
    code_section = planing.project.section.code
    code_project = planing.project.code
    code_desa = planing.desa.code
    code_counter = desa.last
    max_digit = desa.digit
    max_value = 10 ** max_digit - 1

    if code_counter is None:
        code_counter = 1

    #Update last on desa
    sch = desa
    code_counter += 1
    if code_counter > max_value: #apabila last nilainya sudah melebihi dari max_value dari digit maka digit ditambahkan satu
        max_digit += 1
        sch.digit = max_digit
    
    sch.last = code_counter
    await crud.desa.update(obj_current=desa, obj_new=sch, db_session=db_session, with_commit=with_commit)

    number = str(code_counter).zfill(max_digit)

    id_bidang = f"{code_section}{code_project}{code_desa}{number}"
    return id_bidang

async def generate_code_bundle(planing_id:UUID | None, db_session : AsyncSession | None = None, with_commit: bool | None = True) -> str:
    if planing_id is not None:
        planing = await crud.planing.get_by_id(id=planing_id)
        bundle_code = await generate_code(entity=CodeCounterEnum.Bundle, db_session=db_session, with_commit=with_commit)
        project_code = planing.project.code
        desa_code = planing.desa.code

        codes = [project_code, desa_code, bundle_code]
    else:
        codes = "-GEN" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))

    code = f"D" + "".join(codes)
    return code

   
async def generate_code(entity:CodeCounterEnum,
                        db_session : AsyncSession | None = None,
                        with_commit: bool | None = True) -> str:

    obj_current = await crud.codecounter.get_by_entity(entity=entity)

    code_counter = 1
    max_digit = 3

    if obj_current is None:
        obj_in = CodeCounter(entity=entity, code_counter=code_counter, digit=max_digit)
        await crud.codecounter.create(obj_in=obj_in, db_session=db_session, with_commit=with_commit)

        code = str(code_counter).zfill(max_digit)
        return code
    
    else:
        code_counter = (obj_current.last + 1)
        max_digit = obj_current.digit or max_digit
        max_value = 10 ** max_digit - 1 

        if code_counter > max_value:
            max_digit += 1

        obj_new = CodeCounter(entity=obj_current.entity, last=code_counter, digit=max_digit)
        await crud.codecounter.update(obj_current=obj_current, obj_new=obj_new, db_session=db_session, with_commit=with_commit)
        
        code = str(code_counter).zfill(max_digit)
        return code
    
async def generate_code_month(entity:CodeCounterEnum,
                        db_session : AsyncSession | None = None,
                        with_commit: bool | None = True):

    obj_current = await crud.codecounter.get_by_entity(entity=entity)
    code_counter = 1
    max_digit = 3
    current_month = datetime.now().strftime("%m")
    current_year = datetime.now().strftime("%Y")
    current_date = datetime.now().date()

    if obj_current is None:
        obj_in = CodeCounter(entity=entity, code_counter=code_counter, digit=max_digit)
        await crud.codecounter.create(obj_in=obj_in, db_session=db_session, with_commit=with_commit)

        code = str(code_counter).zfill(max_digit)
        return code
    
    else:
        last_number = obj_current.last
        if obj_current.last is None or obj_current.updated_at.month != current_date.month:
            last_number = 0

        code_counter = (last_number + 1)
        max_digit = obj_current.digit or max_digit
        max_value = 10 ** max_digit - 1 

        if code_counter > max_value:
            max_digit += 1

        obj_new = CodeCounter(entity=obj_current.entity, last=code_counter, digit=max_digit)
        await crud.codecounter.update(obj_current=obj_current, obj_new=obj_new, db_session=db_session, with_commit=with_commit)
        
        code = str(code_counter).zfill(max_digit)
        return code
    




    



