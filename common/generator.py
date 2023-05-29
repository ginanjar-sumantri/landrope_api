import random
import string
from enum import Enum
import crud
from schemas.desa_sch import DesaSch
from geoalchemy2.shape import to_shape
from models.code_counter_model import CodeCounter, CodeCounterEnum


async def generate_id_bidang(planing_id:str):
    planing = await crud.planing.get(id=planing_id)
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
    await crud.desa.update(obj_current=desa, obj_new=sch)

    number = str(code_counter).zfill(max_digit)

    id_bidang = f"{code_section}{code_project}{code_desa}{number}"
    return id_bidang
   
async def generate_code(entity:CodeCounterEnum):

    obj_current = await crud.codecounter.get_by_entity(entity=entity)

    code_counter = 1
    max_digit = 3

    if obj_current is None:
        obj_in = CodeCounter(entity=entity, code_counter=code_counter, digit=max_digit)
        await crud.codecounter.create(obj_in=obj_in)

        code = str(code_counter).zfill(max_digit)
        return code
    
    else:
        code_counter = (obj_current.last + 1)
        max_digit = obj_current.digit or max_digit
        max_value = 10 ** max_digit - 1 

        if code_counter > max_value:
            max_digit += 1

        obj_new = CodeCounter(entity=obj_current.entity, last=code_counter, digit=max_digit)
        await crud.codecounter.update(obj_current=obj_current, obj_new=obj_new)

        code = str(code_counter).zfill(max_digit)
        return code
    




    



