from fastapi import HTTPException
from fastapi_async_sqlalchemy import db

class ImportPraTransactionService:

    async def filter_pemilik(self):

        db_session = db.session

        query = """SELECT 
                        STRING_AGG(t.pemilik,', ') as nama
                    FROM (SELECT DISTINCT * FROM (SELECT pemilik FROM import_temp_ttn UNION ALL SELECT penjual FROM import_temp_kjb_detail)t)t 
                    LEFT JOIN pemilik p on lower(t.pemilik) = lower(p.name) 
                    where p.id IS NULL;"""
        
        response = await db_session.execute(query)
        data = response.fetchone()

        if data.nama is not None:
            raise HTTPException(status_code=404, detail=f"Pemilik Tidak ditemukan : {data.nama}")
        
    async def filter_jenis_surat(self):

        db_session = db.session

        query = """SELECT 
                        STRING_AGG(kd.jenis_surat,', ') as jenis_surat
                    FROM import_temp_kjb_detail kd 
                    LEFT JOIN jenis_surat js on lower(kd.jenis_surat) = lower(js.name) 
                    where js.id IS NULL;"""
        
        response = await db_session.execute(query)
        data = response.fetchone()

        if data.jenis_surat is not None:
            raise HTTPException(status_code=404, detail=f"Jenis Surat Tidak ditemukan : {data.jenis_surat}")
        
    async def filter_kjb_termin(self):

        db_session = db.session

        query = """SELECT 
                        STRING_AGG(kjb_no || '-' || jenis_alashak,', ') as kjb
                    FROM (SELECT kjb_no, jenis_alashak, SUM(nilai) AS jumlah 
                    FROM import_temp_kjb_termin GROUP BY kjb_no,jenis_alashak)a 
                    WHERE jumlah <> 100;"""
        
        response = await db_session.execute(query)
        data = response.fetchone()

        if data.kjb is not None:
            raise HTTPException(status_code=404, detail=f"KJB Termin persentase tidak lengkap : {data.kjb}")
        
    # async def filter_bidang(self):

    #     db_session = db.session

    #     query = """SELECT 
    #                     kd.id_bidang_lama 
    #                 FROM import_temp_kjb_detail kd 
    #                 INNER JOIN bidang b ON kd.id_bidang_lama = b.id_bidang_lama 
    #                 INNER JOIN kjb_dt dt ON b.bundle_hd_id = dt.bundle_hd_id 
    #                 WHERE b.id IS NULL OR (b.id IS NOT NULL AND dt.id IS NOT NULL);"""
        
    #     response = await db_session.execute(query)
    #     data = response.fetchone()

    #     if data.kjb is not None:
    #         raise HTTPException(status_code=404, detail=f"KJB Termin persentase tidak lengkap : {data.kjb}")

    async def execute_import(self):

        await self.filter_pemilik()
        await self.filter_jenis_surat()