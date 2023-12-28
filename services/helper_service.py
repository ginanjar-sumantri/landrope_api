from fastapi import UploadFile
from fastapi_async_sqlalchemy import db
from sqlmodel.ext.asyncio.session import AsyncSession
from models.dokumen_model import Dokumen
from models.bundle_model import BundleDt, BundleHd
from schemas.dokumen_sch import RiwayatSch
from schemas.bidang_sch import BidangUpdateSch
from schemas.bidang_komponen_biaya_sch import BidangKomponenBiayaUpdateSch
from datetime import date,datetime
from common.exceptions import ContentNoChangeException
from common.enum import StatusBidangEnum, JenisBidangEnum, JenisAlashakEnum, SatuanBayarEnum, SatuanHargaEnum
from services.gcloud_storage_service import GCStorageService
from uuid import UUID
from decimal import Decimal
from typing import Tuple
from shapely import wkt, wkb
import crud
import json
import pytz

class HelperService:
    def extract_metadata_for_history(self, meta_data:str | None = None,
                                current_history:str | None = None) -> str:

    ## Memeriksa apakah ada key "Nomor" dalam metadata
        o_json = json.loads(meta_data.replace("'", "\""))
        Nomor = ""
        if "Nomor" in o_json:
            Nomor = o_json['Nomor']

        if current_history is None:
            history_data = {'history':
                            [{'tanggal': str(datetime.now()),
                            'nomor': Nomor,
                            'meta_data': json.loads(meta_data.replace("'", "\""))}]
                            }
        else:
            history_data = eval(current_history.replace('null', 'None'))
            new_metadata = {'tanggal': str(datetime.now()), 'nomor': Nomor, 'meta_data': json.loads(meta_data.replace("'", '"'))}
            history_data['history'].append(new_metadata)

        result = str(history_data).replace('None', 'null')
        return result

    def extract_metadata_for_riwayat(self, current_riwayat:str | None,
                                            meta_data:str | None,
                                            key_riwayat:str | None,
                                            file_path:str|None,
                                            is_default:bool|None = False,
                                            from_notaris:bool = False) -> str:
            
        riwayat_data:str = ""
        metadata_dict = json.loads(meta_data.replace("'", "\""))
        key_value = metadata_dict[f'{key_riwayat}']

        if key_value is None or key_value == "":
            raise ContentNoChangeException(detail=f"{key_riwayat} wajib terisi!")

        if current_riwayat is None:
            new_riwayat_data = {'riwayat':
                                [
                                    {
                                    'tanggal':str(datetime.now()), 
                                    'key_value':key_value, 
                                    'file_path':file_path, 
                                    'is_default':is_default, 
                                    'meta_data': metadata_dict
                                    }
                                ]}
            
            new_riwayat_data = json.dumps(new_riwayat_data)
            riwayat_data = str(new_riwayat_data).replace('None', 'null').replace('"', "'")
        else:
            # current_riwayat_obj = eval(current_riwayat.replace('null', 'None'))
            current_riwayat = current_riwayat.replace("'", "\"")
            current_riwayat_obj = json.loads(current_riwayat)

            for i, item in enumerate(current_riwayat_obj["riwayat"]):
                if item.get("key_value") == key_value and from_notaris == False:
                    # raise ContentNoChangeException(detail=f"{key_value} sudah ada dalam riwayat!")
                    current_riwayat_obj["riwayat"] = [item for item in current_riwayat_obj["riwayat"] if item["key_value"] != key_value]
                #kalau dari tanda terima notaris, buang dulu yg current karena akan direplace dari tanda terima notaris
                elif item.get("key_value") == key_value and from_notaris == True:
                    current_riwayat_obj["riwayat"] = [item for item in current_riwayat_obj["riwayat"] if item["key_value"] != key_value]

            for i, item in enumerate(current_riwayat_obj["riwayat"]):
                item["is_default"] = False

            new_riwayat_obj = {
                                'tanggal':str(datetime.now()), 
                                'key_value':key_value, 
                                'file_path':file_path, 
                                'is_default':is_default, 
                                'meta_data': metadata_dict }
            
            current_riwayat_obj['riwayat'].append(new_riwayat_obj)

            current_riwayat_obj = json.dumps(current_riwayat_obj)
            riwayat_data = str(current_riwayat_obj).replace('None', 'null').replace('"', "'")

        return riwayat_data
    
    async def update_riwayat(self, 
                            current_riwayat_data:str,
                            dokumen:Dokumen,
                            sch:RiwayatSch,
                            codehd:str = None,
                            codedt:str = None,
                            file:UploadFile = None,
                            from_notaris:bool = False
                            ) -> Tuple[str | None, str | None]:
        
    
        metadata_dict = json.loads(sch.meta_data.replace("'", "\""))
        key_value = metadata_dict[f'{dokumen.key_riwayat}']

        if key_value is None or key_value == "":
            raise ContentNoChangeException(detail=f"{dokumen.key_riwayat} wajib terisi!")

        riwayat_data = json.loads(current_riwayat_data.replace("'", "\""))

        current_dict_riwayat = next((x for x in riwayat_data["riwayat"] if x["key_value"] == sch.key_value), None)
        if current_dict_riwayat is None and from_notaris == False:
            raise ContentNoChangeException(detail=f"Riwayat {sch.key_value} tidak ditemukan")
        
        if file:
            if codehd is None and codedt is None:
                file_path = await GCStorageService().upload_file_dokumen(file=file, file_name=f'{dokumen.name}-{key_value}')
            else:
                file_path = await GCStorageService().upload_file_dokumen(file=file, file_name=f'{codehd}-{codedt}-{dokumen.name}-{key_value}')
        else:
            file_path = sch.file_path
        
        if sch.is_default == True:
            for i, item in enumerate(riwayat_data["riwayat"]):
                item["is_default"] = False
        
        new_riwayat_obj = {
                            'tanggal':str(datetime.now()), 
                            'key_value':key_value, 
                            'file_path':file_path, 
                            'is_default':sch.is_default, 
                            'meta_data': metadata_dict
                        }
        
        found = False
        for i, item in enumerate(riwayat_data["riwayat"]):
            if item.get("key_value") == sch.key_value:
                riwayat_data["riwayat"][i] = new_riwayat_obj
                found = True
                break
        
        if from_notaris is True and found is False:
            riwayat_data['riwayat'].append(new_riwayat_obj)
        
        riwayat_data = json.dumps(riwayat_data)
        riwayat_data = str(riwayat_data).replace('None', 'null').replace('"', "'")

        return riwayat_data, file_path
      
    async def update_bundle_keyword(self, meta_data:str|None,
                        bundle_hd_id:UUID|None,
                        key_field:str|None,
                        worker_id:UUID|None,
                        db_session : AsyncSession | None = None):
    
        obj_json = json.loads(meta_data.replace("'", '"'))
        current_bundle_hd = await crud.bundlehd.get(id=bundle_hd_id)

        metadata_keyword = obj_json[f'{key_field}']
        if metadata_keyword:
            # periksa apakah keyword belum eksis di bundle hd
            if metadata_keyword not in current_bundle_hd.keyword:
                edit_keyword_hd = current_bundle_hd
                if current_bundle_hd.keyword is None or current_bundle_hd.keyword == "":
                    edit_keyword_hd.keyword = metadata_keyword
                else:
                    edit_keyword_hd.keyword = f"{current_bundle_hd.keyword},{metadata_keyword}"
                    
                    await crud.bundlehd.update(obj_current=current_bundle_hd, 
                                                obj_new=edit_keyword_hd, 
                                                db_session=db_session, 
                                                with_commit=False,
                                                updated_by_id=worker_id)
                    
    async def merging_to_bundle(self,
                            bundle_hd_obj : BundleHd,
                            dokumen : Dokumen,
                            meta_data : str,
                            db_session : AsyncSession | None,
                            file_path : str | None = None,
                            worker_id : UUID | str = None):

        # Memeriksa apakah dokumen yang dimaksud eksis di bundle detail (bisa jadi dokumen baru di master dan belum tergenerate)
        bundledt_obj_current = next((x for x in bundle_hd_obj.bundledts if x.dokumen_id == dokumen.id and x.bundle_hd_id == bundle_hd_obj.id), None)
        
        if bundledt_obj_current is None:
            code = bundle_hd_obj.code + dokumen.code

            history_data = self.extract_metadata_for_history(meta_data, current_history=None)

            riwayat_data = None
            if dokumen.is_riwayat == True:
                riwayat_data = self.extract_metadata_for_riwayat(meta_data=meta_data, 
                                                                        key_riwayat=dokumen.key_riwayat, 
                                                                        current_riwayat=None, 
                                                                        file_path=file_path, 
                                                                        is_default=True,
                                                                        from_notaris=True)

            new_dokumen = BundleDt(code=code, 
                                dokumen_id=dokumen.id, 
                                meta_data=meta_data, 
                                history_data=history_data,
                                riwayat_data=riwayat_data,
                                bundle_hd_id=bundle_hd_obj.id, 
                                file_path=file_path)

            bundledt_obj_current = await crud.bundledt.create(obj_in=new_dokumen, db_session=db_session, with_commit=False, created_by_id=worker_id)
        else:

            history_data = self.extract_metadata_for_history(str(meta_data), current_history=bundledt_obj_current.history_data)

            riwayat_data = None
            if dokumen.is_riwayat == True:
                riwayat_data = self.extract_metadata_for_riwayat(meta_data=meta_data, 
                                                                        key_riwayat=dokumen.key_riwayat, 
                                                                        current_riwayat=bundledt_obj_current.riwayat_data, 
                                                                        file_path=file_path, 
                                                                        is_default=True,
                                                                        from_notaris=True)
            
            if file_path is None:
                file_path = bundledt_obj_current.file_path

            bundledt_obj_updated = bundledt_obj_current
            bundledt_obj_updated.meta_data = meta_data
            bundledt_obj_updated.history_data = history_data
            bundledt_obj_updated.riwayat_data = riwayat_data
            bundledt_obj_updated.file_path = file_path

            bundledt_obj_current = await crud.bundledt.update(obj_current=bundledt_obj_current, 
                                                            obj_new=bundledt_obj_updated, 
                                                            db_session=db_session, 
                                                            with_commit=False,
                                                            updated_by_id=worker_id)
        
        #updated bundle header keyword when dokumen metadata is_keyword true
        if dokumen.is_keyword == True:
            await self.update_bundle_keyword(meta_data=meta_data,
                                                        bundle_hd_id=bundle_hd_obj.id, 
                                                        worker_id=worker_id, 
                                                        key_field=dokumen.key_field, 
                                                        db_session=db_session)
    
    def ToMonthName(self, month:int = None) -> str | None:
        if month == 1:
            return "Januari"
        elif month == 2:
            return "Februari"
        elif month == 3:
            return "Maret"
        elif month == 4:
            return "April"
        elif month == 5:
            return "Mei"
        elif month == 6:
            return "Juni"
        elif month == 7:
            return "Juli"
        elif month == 8:
            return "Agustus"
        elif month == 9:
            return "September"
        elif month == 10:
            return "Oktober"
        elif month == 11:
            return "November"
        elif month == 12:
            return "Desember"
        else:
            return ""
        
    def ToDayName(self, day:str = None) -> str | None:
        if day == "Monday":
            return "SENIN"
        elif day == "Tuesday":
            return "SELASA"
        elif day == "Wednesday":
            return "RABU"
        elif day == "Thursday":
            return "KAMIS"
        elif day == "Friday":
            return "JUMAT"
        elif day == "Saturday":
            return "SABTU"
        elif day == "Sunday":
            return "MINGGU"
        else:
            return ""
        
    def CheckField(self, gdf, field_values:list) -> str | None:
        for field in field_values:
            if field not in gdf.columns:
                return str(field)
        
        return None

    def no_timezone(self, date_time:datetime) -> datetime:
        trans_at = date_time.astimezone(pytz.utc)
        trans_at = trans_at.replace(tzinfo=None)
        return trans_at

    async def bidang_update_status(self, bidang_ids:list[UUID]):
        for id in bidang_ids:
            payment_details = await crud.payment_detail.get_payment_detail_by_bidang_id(bidang_id=id)
            if len(payment_details) > 0:
                bidang_current = await crud.bidang.get(id=id)
                if bidang_current.geom :
                    bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))
                bidang_updated = BidangUpdateSch(status=StatusBidangEnum.Bebas)
                await crud.bidang.update(obj_current=bidang_current, obj_new=bidang_updated)
            else:
                bidang_current = await crud.bidang.get(id=id)
                if bidang_current.geom :
                    bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))
                bidang_updated = BidangUpdateSch(status=StatusBidangEnum.Deal)
                await crud.bidang.update(obj_current=bidang_current, obj_new=bidang_updated)

    def FindStatusBidang(self, status:str|None = None):
        if status:
            if status.replace(" ", "").lower() == StatusBidangEnum.Bebas.replace("_", "").lower():
                return StatusBidangEnum.Bebas
            elif status.replace(" ", "").lower() == StatusBidangEnum.Belum_Bebas.replace("_", "").lower():
                return StatusBidangEnum.Belum_Bebas
            elif status.replace(" ", "").lower() == StatusBidangEnum.Batal.replace("_", "").lower():
                return StatusBidangEnum.Batal
            elif status.replace(" ", "").lower() == StatusBidangEnum.Lanjut.replace("_", "").lower():
                return StatusBidangEnum.Lanjut
            elif status.replace(" ", "").lower() == StatusBidangEnum.Pending.replace("_", "").lower():
                return StatusBidangEnum.Pending
            else:
                return StatusBidangEnum.Belum_Bebas
        else:
            return StatusBidangEnum.Belum_Bebas

    def FindJenisBidang(self, type:str|None = None):
        if type:
            if type.replace(" ", "").lower() == JenisBidangEnum.Bintang.lower():
                return JenisBidangEnum.Bintang
            elif type.replace(" ", "").lower() == JenisBidangEnum.Standard.lower():
                return JenisBidangEnum.Standard
            elif type.replace(" ", "").lower() == JenisBidangEnum.Overlap.lower():
                return JenisBidangEnum.Overlap
            elif type.replace(" ", "").lower() == JenisBidangEnum.Kulit_Bintang.lower():
                return JenisBidangEnum.Kulit_Bintang
            else:
                return JenisBidangEnum.Standard
        else:
            return JenisBidangEnum.Standard

    def FindJenisAlashak(self, type:str|None = None):
        if type:
            if type.replace(" ", "").lower() == JenisAlashakEnum.Girik.lower():
                return JenisAlashakEnum.Girik
            elif type.replace(" ", "").lower() == JenisAlashakEnum.Sertifikat.lower():
                return JenisAlashakEnum.Sertifikat
            else:
                return None
        else:
            return None
        
    async def update_nilai_njop_bidang(self, bundle_dt:BundleDt, meta_data:str|None = None):
        """Mengupdate Nilai NJOP di Bidang"""

        if meta_data is None:
            return None

        if bundle_dt.bundlehd.bidang:
            bidang_current = await crud.bidang.get_by_id(id=bundle_dt.bundlehd.bidang.id)
            if bidang_current.geom :
                bidang_current.geom = wkt.dumps(wkb.loads(bidang_current.geom.data, hex=True))

            if bidang_current.geom_ori :
                bidang_current.geom_ori = wkt.dumps(wkb.loads(bidang_current.geom_ori.data, hex=True))

            metadata_dict = json.loads(meta_data.replace("'", "\""))
            value = metadata_dict.get('NJOP', None)
            if value:
                value = Decimal(value)
                bidang_updated = BidangUpdateSch(njop=value)

                obj_updated = await crud.bidang.update(obj_current=bidang_current, obj_new=bidang_updated, updated_by_id=bundle_dt.updated_by_id)

                await KomponenBiayaHelper().calculated_all_komponen_biaya(bidang_id=[obj_updated.id])

class KomponenBiayaHelper:

    async def get_estimated_amount(self, bidang_id:UUID, bidang_komponen_biaya_id:UUID, formula:str | None = None) -> Decimal | None:

        """Calculate estimated amount from formula"""

        db_session = db.session

        if formula is None:
            return 0

        query = f"""select  
                coalesce(round({formula}, 2), 0) As estimated_amount
                from bidang
                inner join bidang_komponen_biaya ON bidang.id = bidang_komponen_biaya.bidang_id
                where bidang.id = '{bidang_id}'
                and bidang_komponen_biaya.id = '{bidang_komponen_biaya_id}'"""
    
        response = await db_session.execute(query)
        result = response.fetchone()
 
        return result.estimated_amount
    
    async def calculated_all_komponen_biaya(self, bidang_ids:list[UUID]):
        """Calculated all komponen bidang when created or updated spk"""

        komponen_biayas = await crud.bidang_komponen_biaya.get_multi_by_bidang_ids(list_bidang_id=bidang_ids)

        for komponen_biaya in komponen_biayas:
            sch_updated = BidangKomponenBiayaUpdateSch.from_orm(komponen_biaya)
            if komponen_biaya.satuan_bayar == SatuanBayarEnum.Amount and komponen_biaya.satuan_harga == SatuanHargaEnum.Lumpsum:
                sch_updated.estimated_amount = sch_updated.amount
            else:
                sch_updated.estimated_amount = await KomponenBiayaHelper().get_estimated_amount(formula=komponen_biaya.formula, bidang_id=komponen_biaya.bidang_id, bidang_komponen_biaya_id=komponen_biaya.id)

            await crud.bidang_komponen_biaya.update(obj_current=komponen_biaya, obj_new=sch_updated, updated_by_id=komponen_biaya.updated_by_id)

class BundleHelper:

    async def get_key_value(self, dokumen_name:str, bidang_id:UUID) -> str | None:
        value = None
        bundle_dt_meta_data = await crud.bundledt.get_meta_data_by_dokumen_name_and_bidang_id(dokumen_name=dokumen_name, bidang_id=bidang_id)
        if bundle_dt_meta_data:
            if bundle_dt_meta_data.meta_data is not None and bundle_dt_meta_data.meta_data != "":
                metadata_dict = json.loads(bundle_dt_meta_data.meta_data.replace("'", "\""))
                value = metadata_dict[f'{bundle_dt_meta_data.key_field}']

        return value