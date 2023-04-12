import random
import string
from enum import Enum

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