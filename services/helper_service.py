from models.dokumen_model import Dokumen
from datetime import date,datetime
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
                                            is_default:bool|None = False) -> str:
            
        riwayat_data:str = ""
        metadata_dict = json.loads(meta_data.replace("'", '"'))
        key_value = metadata_dict[f'{key_riwayat}']

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
            riwayat_data = str(new_riwayat_data).replace('None', 'null')
        else:
            current_riwayat_obj = eval(current_riwayat.replace('null', 'None'))
            new_riwayat_obj = {
                                'tanggal':str(datetime.now()), 
                                'key_value':key_value, 
                                'file_path':file_path, 
                                'is_default':False, 
                                'meta_data': metadata_dict }
            
            current_riwayat_obj['riwayat'].append(new_riwayat_obj)
            riwayat_data = str(current_riwayat_obj).replace('null', 'None')

        return riwayat_data