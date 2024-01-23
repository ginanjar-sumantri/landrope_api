from uuid import UUID
from fastapi import APIRouter, Depends
from sqlmodel import text, select
from models.bidang_model import Bidang
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from fastapi_async_sqlalchemy import db
from schemas.report_map_sch import (SearchMapObj, SummaryProject, SummaryStatus, SummaryKategori,
                                    FishboneProject, FishboneStatus, FishboneKategori,
                                    ParamProject) 
from schemas.bidang_sch import (ReportBidangBintang)
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, create_response)
from common.rounder import RoundTwo
from decimal import Decimal
import crud

router = APIRouter()

@router.get("/search", response_model=GetResponseBaseSch[list[SearchMapObj]])
async def search_for_map(keyword:str | None,
                         size:int | None = 10):

    """Get for search"""

    db_session = db.session

    keyword = f"'%{keyword.lower().replace(' ', '')}%'"

    query = text(f"""
            (SELECT
                'P' as type,
                project.id as project_id,
                project.name as project_name,
                NULL as desa_id,
                NULL as desa_name,
                NULL as ptsk_id,
                NULL as ptsk_name,
                NULL as bidang_id,
                NULL as id_bidang,
                NULL as alashak,
                NULL as id_bidang_lama,
                NULL as pemilik_name,
                NULL as group,
                NULL as mediator,
                NULL as luas
            FROM
                project
            WHERE
                LOWER(TRIM(project.name)) LIKE {keyword})
            UNION
            (SELECT
                'D' as type,
                project.id as project_id,
                project.name as project_name,
                desa.id as desa_id,
                desa.name as desa_name,
                NULL as ptsk_id,
                NULL as ptsk_name,
                NULL as bidang_id,
                NULL as id_bidang,
                NULL as alashak,
                NULL as id_bidang_lama,
                NULL as pemilik_name,
                NULL as group,
                NULL as mediator,
                NULL as luas
            FROM
                desa
            INNER JOIN planing ON desa.id = planing.desa_id
            INNER JOIN project ON project.id = planing.project_id
            WHERE
                LOWER(TRIM(desa.name)) LIKE {keyword})
            UNION
            (SELECT DISTINCT
                'S' as type,
                project.id as project_id,
                project.name as project_name,
                desa.id as desa_id,
                desa.name as desa_name,
                ptsk.id::text as ptsk_id,
                ptsk.name as ptsk_name,
                NULL as bidang_id,
                NULL as id_bidang,
                NULL as alashak,
                NULL as id_bidang_lama,
                NULL as pemilik_name,
                NULL as group,
                NULL as mediator,
                NULL as luas
            FROM
                ptsk
            INNER JOIN skpt ON ptsk.id = skpt.ptsk_id
            INNER JOIN skpt_dt ON skpt.id = skpt_dt.skpt_id
            INNER JOIN planing ON planing.id = skpt_dt.planing_id
            INNER JOIN desa ON desa.id = planing.desa_id
            INNER JOIN project ON project.id = planing.project_id
            WHERE
                LOWER(TRIM(ptsk.name)) LIKE {keyword})
            UNION
            (SELECT
                'B' as type,
                project.id as project_id,
                project.name as project_name,
                desa.id as desa_id,
                desa.name as desa_name,
                ptsk.id::text as ptsk_id,
                ptsk.name as ptsk_name,
                bidang.id::text as bidang_id,
                bidang.id_bidang as id_bidang,
                bidang.alashak as alashak,
                bidang.id_bidang_lama as id_bidang_lama,
                pemilik.name as pemilik_name,
                bidang.group as group,
                bidang.mediator as mediator,
                bidang.luas_surat::text as luas
            FROM
                Bidang
            LEFT OUTER JOIN Skpt ON Bidang.skpt_id = Skpt.id
            LEFT OUTER JOIN Ptsk ON Skpt.ptsk_id = Ptsk.id
            INNER JOIN Planing ON Bidang.planing_id = Planing.id
            INNER JOIN Desa ON Planing.desa_id = Desa.id
            INNER JOIN Project ON Planing.project_id = Project.id
            LEFT OUTER JOIN Pemilik ON Bidang.pemilik_id = Pemilik.id
            WHERE
                LOWER(TRIM(REPLACE(bidang.id_bidang, ' ', ''))) LIKE {keyword} 
                OR LOWER(TRIM(REPLACE(bidang.alashak, ' ', ''))) LIKE {keyword}
                OR LOWER(TRIM(REPLACE(bidang.id_bidang_lama, ' ', ''))) LIKE {keyword}
                OR LOWER(TRIM(REPLACE(bidang.group, ' ', ''))) LIKE {keyword}
                OR LOWER(TRIM(REPLACE(bidang.mediator, ' ', ''))) LIKE {keyword}
                OR LOWER(TRIM(REPLACE(pemilik.name, ' ', ''))) LIKE {keyword}
                OR LOWER(TRIM(REPLACE(bidang.luas_surat::text, ' ', ''))) LIKE {keyword})
            ORDER BY
                project_id, project_name, desa_id, desa_name, ptsk_id, ptsk_name, bidang_id, id_bidang, alashak
            LIMIT {size}
        """)

    result = await db_session.execute(query)
    data = result.fetchall()
    return create_response(data=data)

@router.post("/fishbone", response_model=GetResponseBaseSch[list[FishboneProject]])
async def fishbone(project_ids:ParamProject):
    
    """Get For Fishbone"""

    if len(project_ids.project_ids) == 0:
        fishbone = []
        return fishbone

    projects = ""
    for project_id in project_ids.project_ids:
        projects += f"'{project_id}',"
    
    projects = projects[0:-1]

    summary_project = await fishbone_get_project_data(projects=projects)
    summary_status = await fishbone_get_status_data(projects=projects)
    summary_kategori = await fishbone_get_kategori_data(projects=projects)

    fishbone = []
    total_luas_project:Decimal = 0

    for project in summary_project:

        total_luas_project = project.luas
        project_fishbone_sch = FishboneProject(**project.dict())
        planings = await crud.planing.get_by_project_id(project_id=project_fishbone_sch.project_id)
        project_fishbone_sch.luas_planning = RoundTwo(angka=sum([pl.luas for pl in planings])/10000)

        status_fishbones = []
        for status in summary_status:
            if status.project_id != project.project_id:
                continue

            total_luas_status = status.luas
            percentage_luas_status = RoundTwo((status.luas/total_luas_project) * 100)
            status_fishbone_sch = FishboneStatus(**status.dict(), percentage=percentage_luas_status)

            kategori_fishbones = []
            for kategori in summary_kategori:

                if kategori.project_id != project.project_id or kategori.status != status.status:
                    continue

                percentage_luas_kategori = RoundTwo((kategori.luas/total_luas_status) * 100)
                kategori_fishbone_sch = FishboneKategori(**kategori.dict(),
                                                         total=kategori.luas,
                                                         percentage=percentage_luas_kategori)
                
                kategori_fishbones.append(kategori_fishbone_sch)
            
            status_fishbone_sch.categories = kategori_fishbones
            status_fishbones.append(status_fishbone_sch)
        
        project_fishbone_sch.status = status_fishbones
        fishbone.append(project_fishbone_sch)

    return create_response(data=fishbone)
        
async def fishbone_get_project_data(projects:str) -> list[SummaryProject]:

    query = text(f"""
                    with subquery as (
                    SELECT
                    project.id AS project_id,
                    project.name AS project_name,
                    desa.name As desa_name,
                    bidang.id_bidang,
                    bidang.jenis_bidang,
                    bidang.jenis_alashak,
                    kategori.name as kategori_name,
                    kategori_sub.name as kategori_sub_name,
                    CASE
                        WHEN bidang.jenis_bidang = 'Bintang' THEN 
                            CASE
                                WHEN kategori.name = 'Asset' AND kategori_sub.name IN ('Bolong', 'Saluran') THEN 'Bebas'
                                ELSE 'Belum_Bebas'
                            END
                        ELSE bidang.status
                    END AS report_status,
                    bidang.status AS current_status,
                    COALESCE(bidang.luas_surat, 0) AS luas_surat,
                    COALESCE(bidang.luas_ukur, 0) AS luas_ukur,
                    COALESCE(bidang.luas_gu_perorangan, 0) AS luas_gu_perorangan,
                    COALESCE(bidang.luas_gu_pt, 0) AS luas_gu_pt,
                    COALESCE(bidang.luas_nett, 0) AS luas_nett,
                    COALESCE(bidang.luas_clear, 0) AS luas_clear,
                    COALESCE(bidang.luas_pbt_perorangan, 0) AS luas_pbt_perorangan,
                    COALESCE(bidang.luas_pbt_pt, 0) AS luas_pbt_pt,
                    COALESCE(bidang.luas_bayar, 0) AS luas_bayar,
                    CASE 
                        WHEN bidang.jenis_bidang = 'Bintang' THEN COALESCE((select sum(bidang_overlap.luas) 
                                                                            from bidang_overlap
                                                                            inner join bidang bd on bd.id = bidang_overlap.parent_bidang_id
                                                                            where bidang_overlap.parent_bidang_intersect_id = bidang.id
                                                                            and bd.status = 'Bebas'
                                                                            ), 0) 
                        ELSE 0
                    END AS luas_damai,
                    CASE
                        WHEN bidang.jenis_bidang = 'Overlap' THEN COALESCE((select sum(bidang_overlap.luas) 
                                                                            from bidang_overlap
                                                                            inner join bidang bd on bd.id = bidang_overlap.parent_bidang_intersect_id
                                                                            where bidang_overlap.parent_bidang_id = bidang.id
                                                                            ), 0) 
                        ELSE 0
                    END AS luas_overlap,
                    CASE
                        WHEN bidang.jenis_bidang IN ('Standard', 'Overlap')
                        THEN
                            ROUND((CASE
                                WHEN bidang.status IN ('Deal', 'Belum_Bebas') THEN bidang.luas_surat
                                WHEN bidang.status IN ('Bebas') THEN COALESCE(bidang.luas_bayar, bidang.luas_surat)
                                ELSE 0
                            END) - COALESCE((SELECT SUM(COALESCE(luas, 0)) 
                                            FROM bidang_overlap bo
                                            WHERE bo.parent_bidang_id = bidang.id), 0), 2)
                        WHEN bidang.jenis_bidang IN ('Bintang')
                        THEN ROUND(COALESCE(bidang.luas_surat, 0) - COALESCE((SELECT SUM(COALESCE(luas, 0))
                                                                    FROM bidang_overlap bo
                                                                    INNER JOIN bidang bd ON bd.id = bo.parent_bidang_id
                                                                    WHERE bo.parent_bidang_intersect_id = bidang.id
                                                                    AND bd.status = 'Bebas'), 0), 2)
                        ELSE 0
                    END AS luas_product
                    FROM bidang
                    INNER JOIN planing ON planing.id = bidang.planing_id
                    INNER JOIN project ON project.id = planing.project_id
                    INNER JOIN desa ON desa.id = planing.desa_id
                    LEFT OUTER JOIN kategori ON kategori.id = bidang.kategori_id
                    LEFT OUTER JOIN kategori_sub ON kategori_sub.id = bidang.kategori_sub_id
                    WHERE ((status = 'Lanjut' AND bidang.jenis_bidang = 'Bintang')
                    OR (status != 'Batal' AND bidang.jenis_bidang IN ('Overlap', 'Standard')))
                    AND project.id IN ({projects})
                    )
                    select project_id, 
                    project_name, 
                    ROUND(sum(luas_product)/10000::numeric, 2) as luas, 
                    COUNT(id_bidang) as jumlah_bidang
                    from subquery
                    group by project_id, project_name
                """)
    
    db_session = db.session
    result = await db_session.execute(query)
    datas = result.all()

    list_data = [SummaryProject(project_id=data["project_id"], 
                                project_name=data["project_name"], 
                                luas=data["luas"],
                                jumlah_bidang=data["jumlah_bidang"]
                                ) for data in datas]
    
    return list_data

async def fishbone_get_status_data(projects:str) -> list[SummaryStatus]:

    query = text(f"""
                    with subquery as (
                    SELECT
                    project.id AS project_id,
                    project.name AS project_name,
                    desa.name As desa_name,
                    bidang.id_bidang,
                    bidang.jenis_bidang,
                    bidang.jenis_alashak,
                    kategori.name as kategori_name,
                    kategori_sub.name as kategori_sub_name,
                    CASE
                        WHEN bidang.jenis_bidang = 'Bintang' THEN 
                            CASE
                                WHEN kategori.name = 'Asset' AND kategori_sub.name IN ('Bolong', 'Saluran') THEN 'Bebas'
                                ELSE 'Belum_Bebas'
                            END
                        ELSE bidang.status
                    END AS report_status,
                    bidang.status AS current_status,
                    COALESCE(bidang.luas_surat, 0) AS luas_surat,
                    COALESCE(bidang.luas_ukur, 0) AS luas_ukur,
                    COALESCE(bidang.luas_gu_perorangan, 0) AS luas_gu_perorangan,
                    COALESCE(bidang.luas_gu_pt, 0) AS luas_gu_pt,
                    COALESCE(bidang.luas_nett, 0) AS luas_nett,
                    COALESCE(bidang.luas_clear, 0) AS luas_clear,
                    COALESCE(bidang.luas_pbt_perorangan, 0) AS luas_pbt_perorangan,
                    COALESCE(bidang.luas_pbt_pt, 0) AS luas_pbt_pt,
                    COALESCE(bidang.luas_bayar, 0) AS luas_bayar,
                    CASE 
                        WHEN bidang.jenis_bidang = 'Bintang' THEN COALESCE((select sum(bidang_overlap.luas) 
                                                                            from bidang_overlap
                                                                            inner join bidang bd on bd.id = bidang_overlap.parent_bidang_id
                                                                            where bidang_overlap.parent_bidang_intersect_id = bidang.id
                                                                            and bd.status = 'Bebas'
                                                                            ), 0) 
                        ELSE 0
                    END AS luas_damai,
                    CASE
                        WHEN bidang.jenis_bidang = 'Overlap' THEN COALESCE((select sum(bidang_overlap.luas) 
                                                                            from bidang_overlap
                                                                            inner join bidang bd on bd.id = bidang_overlap.parent_bidang_intersect_id
                                                                            where bidang_overlap.parent_bidang_id = bidang.id
                                                                            ), 0) 
                        ELSE 0
                    END AS luas_overlap,
                    CASE
                        WHEN bidang.jenis_bidang IN ('Standard', 'Overlap')
                        THEN
                            ROUND((CASE
                                WHEN bidang.status IN ('Deal', 'Belum_Bebas') THEN bidang.luas_surat
                                WHEN bidang.status IN ('Bebas') THEN COALESCE(bidang.luas_bayar, bidang.luas_surat)
                                ELSE 0
                            END) - COALESCE((SELECT SUM(COALESCE(luas, 0)) 
                                            FROM bidang_overlap bo
                                            WHERE bo.parent_bidang_id = bidang.id), 0), 2)
                        WHEN bidang.jenis_bidang IN ('Bintang')
                        THEN ROUND(COALESCE(bidang.luas_surat, 0) - COALESCE((SELECT SUM(COALESCE(luas, 0))
                                                                    FROM bidang_overlap bo
                                                                    INNER JOIN bidang bd ON bd.id = bo.parent_bidang_id
                                                                    WHERE bo.parent_bidang_intersect_id = bidang.id
                                                                    AND bd.status = 'Bebas'), 0), 2)
                        ELSE 0
                    END AS luas_product
                    FROM bidang
                    INNER JOIN planing ON planing.id = bidang.planing_id
                    INNER JOIN project ON project.id = planing.project_id
                    INNER JOIN desa ON desa.id = planing.desa_id
                    LEFT OUTER JOIN kategori ON kategori.id = bidang.kategori_id
                    LEFT OUTER JOIN kategori_sub ON kategori_sub.id = bidang.kategori_sub_id
                    WHERE ((status = 'Lanjut' AND bidang.jenis_bidang = 'Bintang')
                    OR (status != 'Batal' AND bidang.jenis_bidang IN ('Overlap', 'Standard')))
                    AND project.id IN ({projects})
                    ),
                    subs as (select 
                    project_id,
                    project_name,
                    report_status as status,
                    sum(luas_product) AS luas,
                    (SELECT sum(luas_damai) from subquery s WHERE s.project_id = subquery.project_id) as luas_damai
                    from subquery
                    group by project_id, project_name, report_status)
                    select
                    project_id,
                    project_name,
                    status,
                    CASE
                        WHEN status = 'Bebas' THEN ROUND((luas + luas_damai)/10000::numeric, 2)
                        ELSE ROUND(luas/10000::numeric, 2)
                    END AS luas
                    from subs
                    Order by project_id, status

                """)
    
    db_session = db.session
    result = await db_session.execute(query)
    datas = result.all()

    list_data = [SummaryStatus(project_id=data["project_id"], 
                               project_name=data["project_name"], 
                               luas=data["luas"], 
                               status=data["status"]
                               ) for data in datas]
    
    return list_data

async def fishbone_get_kategori_data(projects:str) -> list[SummaryKategori]:

    query = text(f"""
                    with subquery as (
                    SELECT
                    project.id AS project_id,
                    project.name AS project_name,
                    desa.name As desa_name,
                    bidang.id_bidang,
                    bidang.jenis_bidang,
                    bidang.jenis_alashak,
                    kategori.name as kategori_name,
                    kategori_sub.name as kategori_sub_name,
                    CASE
                        WHEN bidang.jenis_bidang = 'Bintang' THEN 
                            CASE
                                WHEN kategori.name = 'Asset' AND kategori_sub.name IN ('Bolong', 'Saluran') THEN 'Bebas'
                                ELSE 'Belum_Bebas'
                            END
                        ELSE bidang.status
                    END AS report_status,
                    bidang.status AS current_status,
                    CASE 
                        WHEN bidang.jenis_bidang = 'Bintang' THEN COALESCE((select sum(bidang_overlap.luas) 
                                                                            from bidang_overlap
                                                                            inner join bidang bd on bd.id = bidang_overlap.parent_bidang_id
                                                                            where bidang_overlap.parent_bidang_intersect_id = bidang.id
                                                                            and bd.status = 'Bebas'
                                                                            ), 0) 
                        ELSE 0
                    END AS luas_damai,
                    CASE
                        WHEN bidang.jenis_bidang = 'Overlap' THEN COALESCE((select sum(bidang_overlap.luas) 
                                                                            from bidang_overlap
                                                                            inner join bidang bd on bd.id = bidang_overlap.parent_bidang_intersect_id
                                                                            where bidang_overlap.parent_bidang_id = bidang.id
                                                                            ), 0) 
                        ELSE 0
                    END AS luas_overlap,
                    CASE
                        WHEN bidang.jenis_bidang IN ('Standard', 'Overlap')
                        THEN
                            ROUND((CASE
                                WHEN bidang.status IN ('Deal', 'Belum_Bebas') THEN bidang.luas_surat
                                WHEN bidang.status IN ('Bebas') THEN COALESCE(bidang.luas_bayar, bidang.luas_surat)
                                ELSE 0
                            END) - COALESCE((SELECT SUM(COALESCE(luas, 0)) 
                                            FROM bidang_overlap bo
                                            WHERE bo.parent_bidang_id = bidang.id), 0), 2)
                        WHEN bidang.jenis_bidang IN ('Bintang')
                        THEN ROUND(COALESCE(bidang.luas_surat, 0) - COALESCE((SELECT SUM(COALESCE(luas, 0))
                                                                    FROM bidang_overlap bo
                                                                    INNER JOIN bidang bd ON bd.id = bo.parent_bidang_id
                                                                    WHERE bo.parent_bidang_intersect_id = bidang.id
                                                                    AND bd.status = 'Bebas'), 0), 2)
                        ELSE 0
                    END AS luas_product
                    FROM bidang
                    INNER JOIN planing ON planing.id = bidang.planing_id
                    INNER JOIN project ON project.id = planing.project_id
                    INNER JOIN desa ON desa.id = planing.desa_id
                    LEFT OUTER JOIN kategori ON kategori.id = bidang.kategori_id
                    LEFT OUTER JOIN kategori_sub ON kategori_sub.id = bidang.kategori_sub_id
                    WHERE ((status = 'Lanjut' AND bidang.jenis_bidang = 'Bintang')
                    OR (status != 'Batal' AND bidang.jenis_bidang IN ('Overlap', 'Standard')))
                    AND project.id IN ({projects})
                    ),
                    subs as (SELECT 
                    project_id,
                    project_name,
                    report_status AS status,
                    CASE
                        WHEN jenis_bidang IN ('Standard', 'Overlap') THEN COALESCE(kategori_name, 'Non Category')
                        WHEN jenis_bidang = 'Bintang' THEN 'Hibah'
                    END AS kategori_name,
                    COALESCE(SUM(CASE
                                    WHEN jenis_alashak = 'Sertifikat' THEN luas_product
                                END), 0) AS SHM,
                    COALESCE(SUM(CASE
                                    WHEN jenis_alashak = 'Girik' THEN luas_product
                                END), 0) AS GIRIK,
                    SUM(luas_product) AS luas
                    FROM subquery
                    WHERE report_status = 'Belum_Bebas'
                    GROUP BY project_id, project_name, report_status, jenis_bidang, kategori_name)
                    Select 
                    project_id, 
                    project_name, 
                    status, 
                    kategori_name, 
                    ROUND(sum(shm)/10000::numeric, 2) as shm, 
                    ROUND(sum(girik)/10000::numeric, 2) as girik, 
                    ROUND(sum(luas)/10000::numeric,2) as luas 
                    from subs
                    group by project_id, project_name, status, kategori_name
                """)
    
    db_session = db.session
    result = await db_session.execute(query)
    datas = result.all()

    list_data = [SummaryKategori(project_id=data["project_id"], 
                                 project_name=data["project_name"], 
                                 luas=data["luas"], 
                                 status=data["status"], 
                                 kategori_name=data["kategori_name"], 
                                 shm=data["shm"], 
                                 girik=data["girik"]
                                 ) for data in datas]
    
    return list_data

@router.get("/summary_bintang", response_model=GetResponsePaginatedSch[ReportBidangBintang])
async def search_for_map(project_id:UUID | None,
                        keyword:str | None = None,
                        params:Params = Depends()):

    """Get for search"""

    objs = await crud.bidang.get_report_summary_bintang_by_project_id(project_id=project_id, keyword=keyword, params=params)
    

    return create_response(data=objs)