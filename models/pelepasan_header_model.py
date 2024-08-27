# from sqlmodel import SQLModel, Field, Relationship
# from models.base_model import BaseUUIDModel
# from uuid import UUID
# from typing import TYPE_CHECKING
# from datetime import datetime 

# if TYPE_CHECKING:
#     from models import (Planing, Ptsk, PelepasanBidang, PelepasanPenggarap)

# class PelepasanHeaderBase(SQLModel):
#     nomor_perjanjian: str | None = Field(nullable=True)
#     tanggal_perjanjian: datetime | None = Field(nullable=True)
#     planing_id: UUID = Field(nullable=False, foreign_key="planing.id")
#     ptsk_id: UUID = Field(nullable=False, foreign_key="ptsk.id")
#     tanda_tangan_lurah: bool | None = Field(nullable=True)
#     tanda_tangan_saksi: bool | None = Field(nullable=True)
#     file_path: str | None = Field(nullable=True)
    
# class PelepasanHeaderFullBase(PelepasanHeaderBase, BaseUUIDModel):
#     pass

# class PelepasanHeader(PelepasanHeaderFullBase, table=True):
#      planing:"Planing" = Relationship(sa_relationship_kwargs = {'lazy':'select'})
#      ptsk:"Ptsk"= Relationship(sa_relationship_kwargs = {'lazy':'select'})
#      pelepasan_bidangs:list["PelepasanBidang"] = Relationship(sa_relationship_kwargs = {'lazy':'select'})
#      pelepasan_penggaraps:list["PelepasanPenggarap"] = Relationship(sa_relationship_kwargs = {'lazy':'select'})




    