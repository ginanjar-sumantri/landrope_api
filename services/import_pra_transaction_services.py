from fastapi import HTTPException
from fastapi_async_sqlalchemy import db

from models import KjbHd, KjbHarga, KjbTermin, KjbBebanBiaya, KjbPenjual
from uuid import UUID, uuid4
import crud

class ImportPraTransactionService:

    async def execute_import(self):

        db_session = db.session

        await self.filter_pemilik()
        await self.filter_jenis_surat()
        await self.filter_kjb_termin()
        await self.filter_bidang()
        await self.filter_beban_biaya()

        import_worker = await crud.worker.get_by_name(name="IMPORTER")

        #GET KJB HD IMPORT
        kjb_hd_imports = await self.get_import_temp_kjb()

        # INSERT KJB HD
        for kjb_hd_import in kjb_hd_imports:
            kjb_hd = await crud.kjb_hd.create(obj_in=kjb_hd_import, created_by_id=import_worker.id, db_session=db_session, with_commit=False)

            # INSERT KJB HARGA
            kjb_harga_imports = await self.get_import_temp_kjb_harga(kjb_hd_id=kjb_hd.id, kjb_hd_code=kjb_hd.code)
            for kjb_harga_import in kjb_harga_imports:
                kjb_harga = await crud.kjb_harga.create(obj_in=kjb_harga_import, created_by_id=import_worker.id, db_session=db_session, with_commit=False)

                # INSERT KJB TERMIN
                kjb_termin_imports = await self.get_import_temp_kjb_termin(kjb_harga_id=kjb_harga.id, kjb_hd_code=kjb_hd.code, jenis_alashak=kjb_harga.jenis_alashak)
                for kjb_termin_import in kjb_termin_imports:
                    await crud.kjb_termin.create(obj_in=kjb_termin_import, created_by_id=import_worker.id, db_session=db_session, with_commit=False)
            
            # INSERT KJB BEBAN BIAYA
            kjb_beban_biaya_imports = await self.get_import_temp_kjb_beban_biaya(kjb_hd_code=kjb_hd.code, kjb_hd_id=kjb_hd.id)
            for kjb_beban_biaya_import in kjb_beban_biaya_imports:
                await crud.kjb_bebanbiaya.create(obj_in=kjb_beban_biaya_import, created_by_id=import_worker.id, db_session=db_session, with_commit=False)

            # INSERT KJB PENJUAL
            kjb_penjual_imports = await self.get_import_temp_kjb_penjual(kjb_hd_code=kjb_hd.code, kjb_hd_id=kjb_hd.id)
            for kjb_penjual_import in kjb_penjual_imports:
                await crud.kjb_penjual.create(obj_in=kjb_penjual_import, created_by_id=import_worker.id, db_session=db_session, with_commit=False)

            # INSERT KJB REKENING
            # kjb_rekening_imports = await



    async def get_import_temp_kjb(self) -> list[KjbHd]:

        db_session = db.session

        query = """
                SELECT
                    k.kjb_no as code, 
                    k.tanggal_kjb, 
                    k.kategori_penjual, 
                    k.category, 
                    group_name as nama_group, 
                    d.id as desa_id, 
                    k.luas_kjb, 
                    m.id as manager_id, 
                    s.id as sales_id, 
                    k.mediator, 
                    k.telepon_mediator, 
                    k.remark, 
                    COALESCE(k.utj_amount,0) as utj_amount, 
                    CASE WHEN COALESCE(k.utj_amount,0)=0 THEN false ELSE true END as ada_utj,
                    'Percentage' as satuan_bayar,
                    'Per_Meter2' as satuan_harga, 
                    FALSE as is_draft, 
                    uuid_generate_v4() as id, 
                    NOW() as created_at, 
                    NOW() as updated_at
                FROM import_temp_kjb k 
                LEFT JOIN desa d ON k.desa = d.name
                LEFT JOIN manager m ON k.manager = m.name
                LEFT JOIN sales s ON k.sales = s.name AND m.id = s.manager_id
                LEFT JOIN kjb_hd kh ON k.kjb_no = kh.code
                WHERE kh.id IS NULL
                """
        response = await db_session.execute(query)
        rows = response.fetchall()

        datas:list[KjbHd] = []
        for row in rows:
            data = KjbHd(code=row.code, tanggal_kjb=row.tanggal_kjb, kategori_penjual=row.kategori_penjual,
                        category=row.category, nama_group=row.nama_group, desa_id=row.desa_id, luas_kjb=row.luas_kjb,
                        manager_id=row.manager_id, sales_id=row.sales_id, mediator=row.mediator, telepon_mediator=row.telepon_mediator,
                        remark=row.remark, utj_amount=row.utj_amount, ada_utj=row.ada_utj, satuan_bayar=row.satuan_bayar, satuan_harga=row.satuan_harga,
                        is_draft=row.is_draft, id=row.id, created_at=row.created_at, updated_at=row.updated_at)
            datas.append(data)

        return datas

    async def get_import_temp_kjb_harga(self, kjb_hd_id:UUID, kjb_hd_code:str) -> list[KjbHarga]:
        
        db_session = db.session

        query = f"""SELECT DISTINCT ON (kjb_no,jenis_alashak) 
                        kjb_no,
                        jenis_alashak,
                        harga_akta,
                        harga_transaksi 
                        FROM import_temp_kjb_harga 
                    where kjb_no = '{kjb_hd_code}'
                    ORDER BY kjb_no, jenis_alashak, harga_akta, harga_transaksi"""
        
        response = await db_session.execute(query)
        rows = response.fetchall()

        datas:list[KjbHarga] = []
        for row in rows:
            data = KjbHarga(id=uuid4().hex, jenis_alashak=row.jenis_alashak, harga_akta=row.harga_akta,
                            harga_transaksi=row.harga_transaksi, kjb_hd_id=kjb_hd_id)
            datas.append(data)

        return datas

    async def get_import_temp_kjb_termin(self, kjb_harga_id:UUID, kjb_hd_code:str, jenis_alashak:str) -> list[KjbTermin]:
        
        db_session = db.session

        query = f"""
                with termin as (SELECT 
                                    kjb_no,
                                    jenis_alashak,
                                    jenis_bayar,
                                    nilai 
                                FROM import_temp_kjb_termin 
                                WHERE jenis_bayar NOT IN ('PELUNASAN','LUNAS')
                                UNION ALL
                                SELECT DISTINCT ON (kjb_no,jenis_alashak,jenis_bayar) 
                                    kjb_no,
                                    jenis_alashak,
                                    jenis_bayar,
                                    nilai 
                                FROM import_temp_kjb_termin 
                                WHERE jenis_bayar IN ('PELUNASAN','LUNAS') 
                                ORDER BY kjb_no,jenis_alashak,jenis_bayar,nilai)
                                    SELECT * FROM termin WHERE kjb_no = '{kjb_hd_code}' and jenis_alashak = '{jenis_alashak}'
                """
        
        response = await db_session.execute(query)
        rows = response.fetchall()

        datas:list[KjbTermin] = []
        for row in rows:
            data = KjbTermin(id=uuid4().hex, jenis_bayar=row.jenis_bayar, nilai=row.nilai, kjb_harga_id=kjb_harga_id)
            datas.append(data)

        return datas
    
    async def get_import_temp_kjb_beban_biaya(self, kjb_hd_code:str, kjb_hd_id:UUID) -> list[KjbBebanBiaya]:
        
        db_session = db.session

        query = f"""
                SELECT 
                    bb.id as beban_biaya_id,
                    kb.beban_pembeli,
                    uuid_generate_v4() as id,
                    NOW() as created_at, 
                    NOW() as updated_at
                FROM import_temp_kjb_beban kb
                    LEFT JOIN beban_biaya bb ON kb.beban_biaya = bb.name
                WHERE kb.kjb_no = '{kjb_hd_code}';
                """
        
        response = await db_session.execute(query)
        rows = response.fetchall()

        datas:list[KjbBebanBiaya] = []
        for row in rows:
            data = KjbBebanBiaya(id=row.id, beban_biaya_id=row.beban_biaya_id, beban_pembeli=row.beban_pembeli, kjb_hd_id=kjb_hd_id)
            datas.append(data)

        return datas
    
    async def get_import_temp_kjb_penjual(self, kjb_hd_code:str, kjb_hd_id:UUID) -> list[KjbPenjual]:
        
        db_session = db.session

        query = f"""
                SELECT 
                    p.id as pemilik_id,
                    uuid_generate_v4() as id,
                    NOW() as created_at, 
                    NOW() as updated_at
                FROM import_temp_kjb kb
                    LEFT JOIN pemilik p ON kb.penjual = p.name
                WHERE kb.kjb_no = '{kjb_hd_code}';
                """
        
        response = await db_session.execute(query)
        rows = response.fetchall()

        datas:list[KjbPenjual] = []
        for row in rows:
            data = KjbPenjual(id=row.id, pemilik_id=row.pemilik_id, kjb_hd_id=kjb_hd_id)
            datas.append(data)

        return datas


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
        
    async def filter_bidang(self):

        db_session = db.session

        query = """SELECT 
                        kd.id_bidang_lama as bidang
                    FROM import_temp_kjb_detail kd 
                    INNER JOIN bidang b ON kd.id_bidang_lama = b.id_bidang_lama 
                    INNER JOIN kjb_dt dt ON b.bundle_hd_id = dt.bundle_hd_id 
                    WHERE b.id IS NULL OR (b.id IS NOT NULL AND dt.id IS NOT NULL);"""
        
        response = await db_session.execute(query)
        data = response.fetchone()

        if data.bidang is not None:
            raise HTTPException(status_code=404, detail=f"Bidang tidak ditemukan atau Bundle_HD_ID sudah terpakai : {data.bidang}")
        
    async def filter_beban_biaya(self):

        db_session = db.session

        query = """SELECT 
                        STRING_AGG(kb.beban_biaya,', ') as beban_biaya
                    FROM import_temp_kjb_beban kb 
                    LEFT JOIN beban_biaya bb on lower(kb.beban_biaya) = lower(bb.name) 
                    where bb.id IS NULL;"""
        
        response = await db_session.execute(query)
        data = response.fetchone()

        if data.beban_biaya is not None:
            raise HTTPException(status_code=404, detail=f"Beban Biaya Tidak ditemukan : {data.beban_biaya}")


