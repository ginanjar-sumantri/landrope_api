from fastapi import UploadFile, BackgroundTasks
from schemas.export_log_sch import ExportLogCreateSch, ExportLogUpdateSch
from services.geom_service import GeomService
from services.gcloud_storage_service import GCStorageService
from common.enum import TaskStatusEnum
from datetime import date, timedelta, datetime
from uuid import uuid4
from io import BytesIO
import crud


class BidangService:

    # FUNGSI UNTUK CREATE EXPORT LOG, SEKALIGUS GENERATE FILE ZIP (SHP) DAN DIUPLOAD KE CLOUD STORAGE
    async def create_export_log_with_generate_file_shp(self, param, created_by_id, bg_task:BackgroundTasks):

        # CREATE EXPORT LOG DATA
        export_log_new = ExportLogCreateSch(name="BIDANG SHP", status=TaskStatusEnum.OnProgress, 
                                            media_type=".zip", expired_date=self.add_days(n=14).date())
        
        export_log = await crud.export_log.create(obj_in=export_log_new, created_by_id=created_by_id)

        # bg_task.add_task(self.generate_file_shp, param, export_log.id)
        await self.generate_file_shp(param=param, export_log_id=export_log.id)

        return export_log

    async def generate_file_shp(self, param, export_log_id):

        export_log = await crud.export_log.get(id=export_log_id)

        try:
            # # QUERY DATA BIDANG YANG INGIN DIEXPORT 
            # results = await crud.bidang.get_multi_export_shape_file(param=param)

            # # FUNGSI UNTUK MERUBAH DATA KE DALAM ZIP STREAM
            # bytes_io_zip = GeomService.export_shp_bytes(data=results, obj_name="bidang")
            # file_name = f"{str(export_log_id)}"

            bytes_io_zip = self.export_shp_with_postgis(param=param)
            file_name = f"{str(export_log_id)}"

            file = UploadFile(file=bytes_io_zip, filename=f"{file_name}.zip")

            # UPLOAD TO CLOUD STORAGE
            file_path = await GCStorageService().upload_export_file(file=file, file_name=file_name)

            # UPDATE EXPORT STATUS 
            export_log_update = ExportLogUpdateSch.from_orm(export_log)
            export_log_update.file_path = file_path
            export_log_update.status = TaskStatusEnum.Done

            await crud.export_log.update(obj_current=export_log, obj_new=export_log_update)

        except Exception as e:

            export_log_update = ExportLogUpdateSch.from_orm(export_log)
            export_log_update.error_msg = str(e.args)
            export_log_update.status = TaskStatusEnum.Failed

            await crud.export_log.update(obj_current=export_log, obj_new=export_log_update)
    
    def add_days(self, n, d:date | None = datetime.today()):
        return d + timedelta(n)

    def export_shp_with_postgis(self, param):
        import os
        import subprocess
        import tempfile
        import zipfile

        # Koneksi ke database PostgreSQL
        db_host = "34.101.44.6"
        db_port = "5432"
        db_name = "landrope_staging"
        db_user = "landrope-app"
        db_password = "<Fl/8L&N;H4=n,}V"
        
        filter:str|None = None

        if len(param.projects) > 0:
            pj = [f"'{pr}'" for pr in param.projects]
            projects = ",".join(pj)

            if filter is None:
                filter = f" where pl.project_id in ({projects})"

        if len(param.desas) > 0:
            ds = [f"'{da}'" for da in param.desas]
            desas = ",".join(ds)

            if filter is None:
                filter = f" where pl.desa_id in ({desas})"
            else:
                filter += f" and pl.desa_id in ({desas})"
        
        if len(param.jenis_bidangs) > 0:
            jns = [f"'{jn}'" for jn in param.jenis_bidangs]
            jenis_bidangs = ",".join(jns)

            if filter is None:
                filter = f" where b.jenis_bidang in ({jenis_bidangs})"
            else:
                filter += f" and b.jenis_bidang in ({jenis_bidangs})"
                

        query = f"""
                    select
                        b.id_bidang as n_idbidang,
                        b.id_bidang_lama as o_idbidang,
                        COALESCE(pm.name, '') as pemilik,
                        COALESCE(ds.code, '') as code_desa,
                        b.jenis_alashak as dokumen,
                        COALESCE(js.name, '') as sub_surat,
                        b.alashak,
                        b.luas_surat as luassurat,
                        COALESCE(kt.name, '') as kat,
                        COALESCE(kts.name, '') as kat_bidang,
                        COALESCE(ktp.name, '') as kat_proyek,
                        COALESCE(pt.name, '') as ptsk,
                        COALESCE(pn.name, '') as penampung,
                        COALESCE(sk.nomor_sk, '') as no_sk,
                        COALESCE(sk.status, '') as status_sk,
                        COALESCE(mng.name, '') as manager,
                        COALESCE(sls.name, '') as sales,
                        b.mediator,
                        b.jenis_bidang as proses,
                        b.status,
                        b.group,
                        b.no_peta,
                        COALESCE(ds.name, '') as desa,
                        COALESCE(pr.name, '') as project,
                        COALESCE(ds.kecamatan, '') as kecamatan,
                        COALESCE(ds.kota, '') as kota,
                        ST_ASTEXT(b.geom) as geom
                    from bidang b
                        left join pemilik pm on pm.id = b.pemilik_id
                        left join planing pl on pl.id = b.planing_id
                        left join project pr on pr.id = pl.project_id
                        left join desa ds on ds.id = pl.desa_id
                        left join jenis_surat js on js.id = b.jenis_surat_id
                        left join kategori kt on kt.id = b.kategori_id
                        left join kategori_sub kts on kts.id = b.kategori_sub_id
                        left join kategori_proyek ktp on ktp.id = b.kategori_proyek_id
                        left join skpt sk on sk.id = b.skpt_id
                        left join ptsk pt on pt.id = sk.ptsk_id
                        left join ptsk pn on pn.id = b.penampung_id
                        left join manager mng on mng.id = b.manager_id
                        left join sales sls on sls.id = b.sales_id
                     {filter}
                    """

        # Tempat sementara untuk menyimpan file
        temp_dir = tempfile.mkdtemp()
        shp_file_path = os.path.join(temp_dir, 'output')

        # Perintah untuk menjalankan pgsql2shp
        pgsql2shp_cmd = f"pgsql2shp -f {shp_file_path} -h {db_host} -p {db_port} -u {db_user} {db_name} \"{query}\""

        # Menjalankan pgsql2shp
        subprocess.run(pgsql2shp_cmd, shell=True, check=True, env={"PGPASSWORD": db_password})

        # Membuat file zip dalam memori
        bytes_io = BytesIO()
        with zipfile.ZipFile(bytes_io, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for ext in ['shp', 'shx', 'dbf']:
                zipf.write(f"{shp_file_path}.{ext}", f"output.{ext}")

        # Mengatur posisi ke awal dari buffer
        bytes_io.seek(0)

        # Membersihkan direktori sementara
        for ext in ['shp', 'shx', 'dbf']:
            os.remove(f"{shp_file_path}.{ext}")
        os.rmdir(temp_dir)

        # Membaca file zip sebagai bytes
        return bytes_io

        
