import random
import string

from fastapi import HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from fastapi.security import HTTPBearer
from sqlmodel import and_, select
from sqlmodel.ext.asyncio.session import AsyncSession
from crud.base_crud import CRUDBase
from models import Role, PeminjamanHeader, Planing, Ptsk, PeminjamanBidang
from schemas.peminjaman_header_sch import PeminjamanHeaderCreateSch, PeminjamanHeaderUpdateSch
from typing import List
from sqlalchemy import text
from fastapi_async_sqlalchemy import db
from uuid import UUID
from sqlalchemy import extract, desc
from datetime import datetime
from sqlalchemy import exc
import crud




from typing import Optional


token_auth_scheme = HTTPBearer()


class CRUDPeminjamanHeader(CRUDBase[PeminjamanHeader, PeminjamanHeaderCreateSch, PeminjamanHeaderUpdateSch]):
    async def get_by_id_bidang(
        self,
        *,
        id: str,
        db_session: AsyncSession | None = None,
    ) -> PeminjamanHeader | None:
                
        db_session = db_session or db.session

        query = select(PeminjamanHeader).where(PeminjamanHeader.id == id)

        response = await db_session.execute(query)
            
        return response.scalar_one_or_none()
    
    async def create_peminjaman_header(
            self, 
            *, 
            obj_in: PeminjamanHeaderCreateSch, 
            created_by_id : UUID | str | None = None, 
            db_session : AsyncSession | None = None,
            with_commit: bool | None = True
            ) -> PeminjamanHeader:
        
        db_session = db_session or self.db_session

        db_obj = self.model.from_orm(obj_in) #type ignore
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()
        if created_by_id:
            db_obj.created_by_id = created_by_id
            db_obj.updated_by_id = created_by_id
        
        if obj_in.planing_id:
            planing = await crud.planing.get(id=obj_in.planing_id)
            if not planing:
                raise HTTPException(status_code=404, detail="Planing not found!")

        if obj_in.ptsk_id:
            ptsk = await crud.ptsk.get(id=obj_in.ptsk_id)
            if not ptsk:
                raise HTTPException(status_code=404, detail="PTSK not found!")
            
        db_session.add(db_obj)

        for pb in obj_in.peminjaman_bidangs:

            bidang = PeminjamanBidang(
                **pb.dict(), 
                created_by_id=created_by_id, 
                updated_by_id=created_by_id
            )
            db_session.add(bidang)  
            db_obj.peminjaman_bidangs.append(bidang)

        
        if with_commit:
            try:
                await db_session.flush()  # Ensure the header ID is generated
                await db_session.commit()
            except Exception as e:
                await db_session.rollback()
                raise e

            return db_obj
    
    
    async def get_latest_by_month_year(self, 
                                        *,
                                       month: int, 
                                       year: int, 
                                       db_session: AsyncSession | None = None
                                       ) -> PeminjamanHeader | None:
        db_session = db_session or db.session

        query = (
            select(PeminjamanHeader)
            .where(
                extract('month', PeminjamanHeader.created_at) == month,
                extract('year', PeminjamanHeader.created_at) == year
            )
            .order_by(desc(PeminjamanHeader.created_at))
            .limit(1)
        )
        result = await db_session.execute(query)
        return result.scalars().first()
    

    async def generate_nomor_perjanjian(self) -> str:

        now = datetime.now()
        current_month = now.month
        current_year = now.year
        
        roman_numerals = [
            "I", "II", "III", "IV", "V", "VI",
            "VII", "VIII", "IX", "X", "XI", "XII"
        ]

        month_roman = roman_numerals[current_month - 1] 

        latest_obj = await self.get_latest_by_month_year(month=current_month, year=current_year)

        if latest_obj:
            latest_sequence = int(latest_obj.nomor_perjanjian.split('/')[0])
            new_sequence = latest_sequence + 1
        else:
            new_sequence = 1

        # Format the sequence number with leading zeros
        sequence_str = f"{new_sequence:03d}"

        obj_nomor = f"{sequence_str}/S/IZIN/LA/{month_roman}/{current_year}"

        return obj_nomor
    
peminjaman_header = CRUDPeminjamanHeader(PeminjamanHeader)
