from fastapi_pagination import Page
from schemas.hasil_peta_lokasi_sch import HasilPetaLokasiReadySpkExtSch, JenisBayarOnReady
import crud
import math

class HasilPetaLokasiService:

    # LIST BIDANG YANG SUDAH SIAP UNTUK DIBUAT SPKNYA BERDASARKAN JENIS BAYAR & KELENGKAPAN DOKUMENNYA
    # 
    async def get_ready_spk(self, keyword, params):

        spks = await crud.hasil_peta_lokasi.get_ready_spk(keyword=keyword)

        # AMBIL SEMUA ID
        ids = [data.id for data in spks]

        # DISTINCT ID YANG SAMA
        ids = list(set(ids))

        # SETUP UNTUK PAGINATION
        start = (params.page - 1) * params.size
        end = params.page * params.size
        total_items = len(ids)
        pages = math.ceil(total_items / params.size)

        # AMBIL ID YANG AKAN DILOOPING DAN DIMAPING SCHEMA SEJUMLAH SIZE DAN PAGE YANG DIINGINKAN
        ids = ids[start:end]

        objs:list[HasilPetaLokasiReadySpkExtSch] = []

        # INISIALISASI SEMUA OBJECT SESUAI JUMLAH ID YANG TERPILIH PADA PAGINATION
        for id in ids:
            datas = list(filter(lambda obj: obj.id == id, spks))

            # GET FIRST DATA FOR DEFAULT
            data = datas[0]

            # SETUP DATA BIDANG
            data_ready_spk = HasilPetaLokasiReadySpkExtSch(id=data.id, id_bidang=data.id_bidang, alashak=data.alashak,
                                                        satuan_bayar=data.satuan_bayar, satuan_harga=data.satuan_harga, 
                                                        planing_id=data.planing_id, kjb_hd_code=data.kjb_hd_code, group=data.group, 
                                                        manager_id=data.manager_id, pemilik_id=data.pemilik_id, kjb_hd_id=data.kjb_hd_id,
                                                        hasil_petlok_id=data.hasil_petlok_id, req_petlok_id=data.req_petlok_id, 
                                                        kjb_dt_id=data.kjb_dt_id, project_name=data.project_name, desa_name=data.desa_name, 
                                                        manager_name=data.manager_name)
                
            

            # CEK APAKAH PEMILIK BIDANG MEMILIKI REKENING
            rekenings = await crud.rekening.get_by_pemilik_id(pemilik_id=data.pemilik_id)
            data_ready_spk.rekening_on_ready = False if not rekenings else True

            # CEK APAKAH KJB HARGA SUDAH DITENTUKAN
            data_ready_spk.kjb_harga_on_ready = False if data.kjb_harga_id is None else True

            # CEK APAKAH SK PADA BIDANG SUDAH DITENTUKAN
            data_ready_spk.sk_on_ready = False if data.skpt_id is None else True

            # SETUP JENIS BAYAR ON READY SESUAI DOKUMEN KELENGKAPAN
            jenis_bayar_on_ready = []
            for jns in datas:
                j = JenisBayarOnReady(kjb_termin_id=jns.kjb_termin_id, nilai=jns.nilai, jenis_bayar=jns.jenis_bayar)
                jenis_bayar_on_ready.append(j)

            data_ready_spk.jenis_bayar_on_ready = jenis_bayar_on_ready

            objs.append(data_ready_spk)
        

        result = Page(items=objs, size=params.size, page=params.page, pages=pages, total=total_items)

        return result