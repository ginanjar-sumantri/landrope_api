from fastapi_async_sqlalchemy import db
import sqlalchemy

from common.enum import StatusReportPembebasanEnum

from datetime import date
from uuid import UUID
import calendar


class ReportPembebasanService:

    async def summary_project(self, period_date:date):

        db_session = db.session

        today = date.today()
        is_current_period: bool = True if today.month == period_date.month and today.year == period_date.year else False

        last_day = calendar.monthrange(period_date.year, period_date.month)[1]
        period_date = date(day=last_day, month=period_date.month, year=period_date.year)

        query = f"SELECT * FROM _b_report_lili_summary_pembebasan('{period_date}', {is_current_period})"
        response = await db_session.execute(query)
        rows = response.fetchall()

        result = []
        for row in rows:
            result.append(dict(row))

        return result
    
    async def detail_project(self, period_date:date, status_pembebasan:StatusReportPembebasanEnum, project_id:UUID | None = None, keyword:str | None = None):

        objs = []
        db_session = db.session

        today = date.today()
        is_current_period: bool = True if today.month == period_date.month and today.year == period_date.year else False

        last_day = calendar.monthrange(period_date.year, period_date.month)[1]
        period_date = date(day=last_day, month=period_date.month, year=period_date.year)

        params = {
            "cut_off" : period_date,
            "is_current_period" : is_current_period,
            "project_ids": None if project_id is None else [project_id]
        }

        if status_pembebasan == StatusReportPembebasanEnum.BELUM_BEBAS:
            query = sqlalchemy.text(f"""SELECT * FROM public._b_report_lili_bidang_belum_bebas(:cut_off, :is_current_period, :project_ids)""")
        elif status_pembebasan == StatusReportPembebasanEnum.BEBAS:
            query = sqlalchemy.text(f"""SELECT * FROM public._b_report_lili_bidang_bebas(:cut_off, :is_current_period, :project_ids)""")
        elif status_pembebasan == StatusReportPembebasanEnum.BELUM_PETLOK:
            query = sqlalchemy.text(f"""SELECT * FROM public._b_report_lili_bidang_belum_petlok(:project_ids)""")
        elif status_pembebasan == StatusReportPembebasanEnum.DEAL:
            query = sqlalchemy.text(f"""SELECT * FROM public._b_report_lili_bidang_deal(:cut_off, :is_current_period, :project_ids)""")
        elif status_pembebasan == StatusReportPembebasanEnum.DEAL_REKLAMASI:
            query = sqlalchemy.text(f"""SELECT * FROM public._b_report_lili_bidang_deal_reklamasi(:cut_off, :is_current_period, :project_ids)""")
        elif status_pembebasan == StatusReportPembebasanEnum.KJB:
            query = sqlalchemy.text(f"""SELECT * FROM public._b_report_lili_bidang_kjb(:project_ids)""")
        else:
            query = sqlalchemy.text(f"""SELECT * FROM public._b_report_lili_bidang_relokasi(:cut_off, :is_current_period, :project_ids)""")

        if keyword:
            query = sqlalchemy.text(f"""{query} WHERE 
                                REPLACE(lower(id_bidang), ' ', '') like '%{keyword.lower().replace(' ', '')}%' 
                                OR REPLACE(lower(alashak), ' ', '') like '%{keyword.lower().replace(' ', '')}%'
                                OR REPLACE(lower(notaris_name), ' ', '') like '%{keyword.lower().replace(' ', '')}%'
                                OR REPLACE(lower(project_name), ' ', '') like '%{keyword.lower().replace(' ', '')}%'
                                OR REPLACE(lower(desa_name), ' ', '') like '%{keyword.lower().replace(' ', '')}%'
                                OR REPLACE(lower('group'), ' ', '') like '%{keyword.lower().replace(' ', '')}%'
                                OR REPLACE(lower(manager_name), ' ', '') like '%{keyword.lower().replace(' ', '')}%'
                                OR REPLACE(lower(sales_name), ' ', '') like '%{keyword.lower().replace(' ', '')}%'
                                OR REPLACE(lower(pemilik_name), ' ', '') like '%{keyword.lower().replace(' ', '')}%'
                                OR REPLACE(lower(mediator), ' ', '') like '%{keyword.lower().replace(' ', '')}%'
                                OR REPLACE(lower(jenis_alashak), ' ', '') like '%{keyword.lower().replace(' ', '')}%'
                                OR REPLACE(lower(kategori_name), ' ', '') like '%{keyword.lower().replace(' ', '')}%'
                    """)

        query = query.params(**params)

        response = await db_session.execute(query)
        rows = response.fetchall()

        result = []
        for row in rows:
            result.append(dict(row))

        return result