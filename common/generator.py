import random
import string
from enum import Enum
import crud
from schemas.desa_sch import DesaSch
from geoalchemy2.shape import to_shape

class EntityEnum(str, Enum):
    desa = "VILL"

def generate_code(EntityEnum:EntityEnum | None = EntityEnum.desa, length:int = 5):
    head:str = EntityEnum
    num = string.digits
    length:int = length
    all = num

    temp = random.sample(all, length)
    code = head + "".join(temp)

    return code

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
   
