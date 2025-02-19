from sqlmodel import SQLModel, Relationship, Field
from sqlalchemy.orm import column_property, declared_attr
from models.base_model import BaseUUIDModel, BaseGeoModel
from uuid import UUID
from typing import TYPE_CHECKING
from shapely import wkt, wkb
from decimal import Decimal
import geopandas as gpd
import pandas as pd
import io
import base64

if TYPE_CHECKING:
    from worker_model import Worker
    from bidang_model import Bidang

class DraftBase(SQLModel):
    rincik_id:UUID | None = Field(nullable=True)
    skpt_id:UUID | None = Field(nullable=True)
    planing_id:UUID | None = Field(nullable=True)
    gps_id:UUID | None = Field(nullable=True)

class DraftRawBase(BaseUUIDModel, DraftBase):
    pass

class DraftFullBase(BaseGeoModel, DraftRawBase):
    pass

class Draft(DraftFullBase, table=True):
    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "Draft.updated_by_id==Worker.id",
        }
    )

    details: list["DraftDetail"] = Relationship(
                                            back_populates="draft",
                                            sa_relationship_kwargs={
                                                "lazy" : "selectin",
                                                "cascade" : "delete, all",
                                                "foreign_keys" : "[DraftDetail.draft_id]"
                                            }
    )

    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)
    

class DraftDetailBase(SQLModel):
    bidang_id:UUID | None = Field(foreign_key="bidang.id")
    draft_id:UUID | None = Field(foreign_key="draft.id")
    luas: Decimal | None = Field(nullable=True)

class DraftDetailRawBase(BaseUUIDModel, DraftDetailBase):
    pass

class DraftDetailFullBase(BaseGeoModel, DraftDetailRawBase):
    pass

class DraftDetail(DraftDetailFullBase, table=True):

    draft:"Draft" = Relationship(
                            back_populates="details",
                            sa_relationship_kwargs=
                            {
                                "lazy" : "select"
                            })
    
    bidang:"Bidang" = Relationship(
                            sa_relationship_kwargs=
                            {
                                "lazy" : "select"
                            })
    
    @property
    def id_bidang(self) -> str | None :
        return getattr(getattr(self, "bidang", None), "id_bidang", None)
    
    @property
    def id_bidang_lama(self) -> str | None :
        return getattr(getattr(self, "bidang", None), "id_bidang_lama", None)
    
    @property
    def jenis_bidang(self) -> str | None :
        return getattr(getattr(self, "bidang", None), "jenis_bidang", None)
    
    @property
    def pemilik_name(self) -> str | None :
        return getattr(getattr(getattr(self, "bidang", None), "pemilik", None), "name", None)

    @property
    def alashak(self) -> str | None :
        return getattr(getattr(self, "bidang", None), "alashak", None)
    
    @property
    def image_png(self) -> str | None :

        geometry =  wkt.dumps(wkb.loads(self.geom.data, hex=True))
        bidang_dict = {"id" : self.id, "geometry" : geometry}
        data_bidang = [bidang_dict]

        df_bidang = pd.DataFrame(data_bidang)
        polygon = gpd.GeoSeries.from_wkt(df_bidang['geometry'])

        ax = polygon.plot()
        ax.set_axis_off()
        img_buffer = io.BytesIO()
        ax.figure.savefig(img_buffer, format='png', bbox_inches='tight', pad_inches=0, transparent=True)
        img_buffer.seek(0)
        image_binary = img_buffer.getvalue()
        base64_string = base64.b64encode(image_binary).decode('utf-8')

        return base64_string
    
