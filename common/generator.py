import random
import string
from enum import Enum
import crud
from schemas.desa_sch import DesaSch
from geoalchemy2.shape import to_shape
from models.code_counter_model import CodeCounterEnum, CodeCounter


async def generate_id_bidang(planing_id:str):
    planing = await crud.planing.get(id=planing_id)
    desa = await crud.desa.get(id=planing.desa_id)
    if desa.geom:
        desa.geom = to_shape(desa.geom).__str__()
    
    code_section = planing.project.section.code
    code_project = planing.project.code
    code_desa = planing.desa.code
    last = desa.last
    if last is None:
        last = 1

    #Update last
    sch = desa
    sch.last = last + 1
    await crud.desa.update(obj_current=desa, obj_new=sch)
    number = '{:04d}'.format(last)
    id_bidang = f"{code_section}{code_project}{code_desa}{number}"
    return id_bidang
   
async def generate_code(entity:CodeCounterEnum):
    code_counter = await crud.codecounter.get_by_entity(entity=entity)

    if code_counter is None:
        obj_in = CodeCounter(entity=entity, last=1)
        obj = await crud.codecounter.create(obj_in=obj_in)

        last = '{:03d}'.format(obj.last)
        return last
    
    else:
        counter = (code_counter.last + 1)
        obj_new = CodeCounter(entity=code_counter.entity, last=counter)
        await crud.codecounter.update(obj_current=code_counter, obj_new=obj_new)
        last = '{:03d}'.format(counter)
        return last



    



