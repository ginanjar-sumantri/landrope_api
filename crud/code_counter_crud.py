from crud.base_crud import CRUDBase
from models.code_counter_model import CodeCounter, CodeCounterEnum
from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

class CRUDCodeCounter(CRUDBase[CodeCounter, CodeCounter, CodeCounter]):    
    async def get_by_entity(self, *, entity: CodeCounterEnum | str, db_session: AsyncSession | None = None) -> CodeCounter | None:
        db_session = db_session or db.session
        query = select(self.model).where(self.model.entity == entity)
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
   

codecounter = CRUDCodeCounter(CodeCounter)