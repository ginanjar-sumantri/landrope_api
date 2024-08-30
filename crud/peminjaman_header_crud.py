import random
import string

from fastapi import HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from fastapi.security import HTTPBearer
from sqlmodel import and_, select
from sqlmodel.ext.asyncio.session import AsyncSession
from crud.base_crud import CRUDBase
from fastapi.encoders import jsonable_encoder
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
    async def get_by_id(
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
    

    async def edit(self, 
                     *, 
                     obj_current : PeminjamanHeader, 
                     obj_new : PeminjamanHeaderUpdateSch | PeminjamanHeader,
                     updated_by_id: UUID | str | None = None,
                     db_session : AsyncSession | None = None,
                     with_commit: bool | None = True
                     ) -> PeminjamanHeader | None:
        
        db_session = db_session or db.session
    
        obj_data = jsonable_encoder(obj_current)
    
        if isinstance(obj_new, dict):
            update_data = obj_new
        else:
            update_data = obj_new.dict(exclude_unset=True)
    
        for field in obj_data:
            if field in update_data:
                setattr(obj_current, field, update_data[field])
            if field == "updated_at":
                setattr(obj_current, field, datetime.utcnow())
    
        if updated_by_id:
            obj_current.updated_by_id = updated_by_id
        
        if 'peminjaman_bidangs' in update_data:
            bidangs_data = update_data['peminjaman_bidangs']
    
            current_bidang_query = select(PeminjamanBidang).where(
                PeminjamanBidang.peminjaman_header_id == obj_current.id
            )
            result_bidang = await db_session.execute(current_bidang_query)
            existing_bidangs = result_bidang.scalars().all()
    
            existing_bidang_ids = {bidang.bidang_id for bidang in existing_bidangs}
            #id dari peminjaman bidangnya
    
            for bidang_data in bidangs_data:
                bidang_id = bidang_data['bidang_id']
    
                if bidang_id in existing_bidang_ids:
                    existing_bidang = next(b for b in existing_bidangs if b.bidang_id == bidang_id)
                    for key, value in bidang_data.items():
                        setattr(existing_bidang, key, value)
                else:
                    filtered_bidang_data = {k: v for k, v in bidang_data.items() if k not in ['peminjaman_header_id']}
                    new_bidang = PeminjamanBidang(
                        peminjaman_header_id=obj_current.id,
                        updated_by_id=obj_current.updated_by_id,
                        created_by_id=obj_current.created_by_id,
                        **filtered_bidang_data
                    )
                    db_session.add(new_bidang)
    
        db_session.add(obj_current)
        if with_commit:
            await db_session.commit()
            await db_session.refresh(obj_current)
        
        return obj_current
    
    
    # async def edit_pinjam(
    #     self,
    #     id: str | None, 
    #     sch: PeminjamanHeaderUpdateSch, 
    #     db_session: AsyncSession | None = None
    # ):
    #     db_session = db_session or db.session

    #     current_header_query = await crud.peminjaman_header.get_by_id(id=id)
    #     result_header = await db_session.execute(current_header_query)
    #     header = result_header.scalar_one_or_none()

    #     if header:
    #         # Update the PeminjamanHeader fields with the provided schema values
    #         for key, value in sch.dict(exclude={'bidangs'}).items():
    #             setattr(header, key, value)

    #         # Update or add PeminjamanBidang entries
    #         if 'bidangs' in sch.dict():
    #             bidangs_data = sch.dict()['bidangs']

    #             # Retrieve existing PeminjamanBidang for the current header
    #             current_bidang_query = select(PeminjamanBidang).where(
    #                 PeminjamanBidang.peminjaman_header_id == id
    #             )
    #             result_bidang = await db_session.execute(current_bidang_query)
    #             existing_bidangs = result_bidang.scalars().all()

    #             existing_bidang_ids = {bidang.bidang_id for bidang in existing_bidangs}

    #             # Update or create new PeminjamanBidang entries
    #             for bidang_data in bidangs_data:
    #                 bidang_id = bidang_data['bidang_id']

    #                 if bidang_id in existing_bidang_ids:
    #                     # Update existing PeminjamanBidang
    #                     existing_bidang = next(b for b in existing_bidangs if b.bidang_id == bidang_id)
    #                     for key, value in bidang_data.items():
    #                         setattr(existing_bidang, key, value)
    #                 else:
    #                     # Create new PeminjamanBidang
    #                     new_bidang = PeminjamanBidang(
    #                         peminjaman_header_id=id,
    #                         **bidang_data
    #                     )
    #                     db_session.add(new_bidang)

    #     else:
    #         # If no header found, you can either raise an exception or handle it as needed
    #         raise ValueError("PeminjamanHeader not found")

    #     await db_session.commit()

    #     # Refresh header to get updated state
    #     await db_session.refresh(header)

    #     return header

    async def update_islock(
                                self, id: UUID | None = None, 
                                db_session: AsyncSession | None = None
                            ) -> PeminjamanHeader | None:
        
        db_session = db_session or db.session

        query = select(PeminjamanHeader).where(PeminjamanHeader.id == id)

        result = await db_session.execute(query)

        peminjaman_header = result.scalars().first()

        if not peminjaman_header:
            return None

        # Set is_lock to False
        peminjaman_header.is_lock = False

        await db_session.commit()
        await db_session.refresh(peminjaman_header)

        return peminjaman_header
    
    
peminjaman_header = CRUDPeminjamanHeader(PeminjamanHeader)
