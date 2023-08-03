from fastapi import UploadFile
from sqlmodel.ext.asyncio.session import AsyncSession
from models.dokumen_model import Dokumen
from schemas.dokumen_sch import RiwayatSch
from datetime import date,datetime
from common.exceptions import ContentNoChangeException
from services.gcloud_storage_service import GCStorageService
from uuid import UUID
from typing import Tuple
import crud
import json

class HelperService:

    def extract_metadata_for_history(self, meta_data:str | None = None,
                                current_history:str | None = None) -> str:

    ## Memeriksa apakah ada key "Nomor" dalam metadata
        o_json = json.loads(meta_data.replace("'", '"'))
        Nomor = ""
        if "Nomor" in o_json:
            Nomor = o_json['Nomor']

        if current_history is None:
            history_data = {'history':
                            [{'tanggal': str(datetime.now()),
                            'nomor': Nomor,
                            'meta_data': json.loads(meta_data.replace("'", '"'))}]
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
                    raise ContentNoChangeException(detail=f"{key_value} sudah ada dalam riwayat!")
                #kalau dari tanda terima notaris, buang dulu yg current karena akan direplace dari tanda terima notaris
                elif item.get("key_value") == key_value and from_notaris == True:
                    current_riwayat_obj["riwayat"] = [item for item in riwayat_data["riwayat"] if item["key_value"] != key_value]

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
            file_path = await GCStorageService().upload_file_dokumen(file=file, file_name=f'{id}-{dokumen.name}-{key_value}')
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