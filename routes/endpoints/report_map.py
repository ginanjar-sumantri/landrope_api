from uuid import UUID
from fastapi import APIRouter
from sqlmodel import text, select
from fastapi_async_sqlalchemy import db
from schemas.report_map_sch import SearchMapObj
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, 
                                  PostResponseBaseSch, PutResponseBaseSch, ImportResponseBaseSch, create_response)

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
                NULL as alashak
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
                NULL as alashak
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
                NULL as alashak
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
                bidang.alashak as alashak
            FROM
                Bidang
            INNER JOIN Skpt ON Bidang.skpt_id = Skpt.id
            INNER JOIN Ptsk ON Skpt.ptsk_id = Ptsk.id
            INNER JOIN Planing ON Bidang.planing_id = Planing.id
            INNER JOIN Desa ON Planing.desa_id = Desa.id
            INNER JOIN Project ON Planing.project_id = Project.id
            WHERE
                LOWER(TRIM(bidang.id_bidang)) LIKE {keyword} OR LOWER(TRIM(bidang.alashak)) LIKE {keyword})
            ORDER BY
                project_id, project_name, desa_id, desa_name, ptsk_id, ptsk_name, bidang_id, id_bidang, alashak
            LIMIT {size}
            
        """)

    result = await db_session.execute(query)
    data = result.fetchall()
    return create_response(data=data)