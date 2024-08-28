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
    
    async def detail_project(self, period_date:date, project_id:UUID, status_pembebasan:StatusReportPembebasanEnum):

        objs = []
        db_session = db.session

        today = date.today()
        is_current_period: bool = True if today.month == period_date.month and today.year == period_date.year else False

        last_day = calendar.monthrange(period_date.year, period_date.month)[1]
        period_date = date(day=last_day, month=period_date.month, year=period_date.year)

        params = {
            "cut_off" : period_date,
            "is_current_period" : is_current_period,
            "project_ids": [project_id]
        }

        if status_pembebasan == StatusReportPembebasanEnum.BELUM_BEBAS:
            query = sqlalchemy.text(f"""SELECT * FROM public._b_report_lili_bidang_belum_bebas(:cut_off, :is_current_period, :project_ids)""").params(**params)
        elif status_pembebasan == StatusReportPembebasanEnum.BEBAS:
            query = sqlalchemy.text(f"""SELECT * FROM public._b_report_lili_bidang_bebas(:cut_off, :is_current_period, :project_ids)""").params(**params)
        elif status_pembebasan == StatusReportPembebasanEnum.BELUM_PETLOK:
            query = sqlalchemy.text(f"""SELECT * FROM public._b_report_lili_bidang_belum_petlok(:cut_off, :is_current_period, :project_ids)""").params(**params)
        elif status_pembebasan == StatusReportPembebasanEnum.DEAL:
            query = sqlalchemy.text(f"""SELECT * FROM public._b_report_lili_bidang_deal(:cut_off, :is_current_period, :project_ids)""").params(**params)
        elif status_pembebasan == StatusReportPembebasanEnum.DEAL_REKLAMASI:
            query = sqlalchemy.text(f"""SELECT * FROM public._b_report_lili_bidang_deal_reklamasi(:cut_off, :is_current_period, :project_ids)""").params(**params)
        elif status_pembebasan == StatusReportPembebasanEnum.KJB:
            query = sqlalchemy.text(f"""SELECT * FROM public._b_report_lili_bidang_kjb(:cut_off, :is_current_period, :project_ids)""").params(**params)
        else:
            query = sqlalchemy.text(f"""SELECT * FROM public._b_report_lili_bidang_relokasi(:cut_off, :is_current_period, :project_ids)""").params(**params)

        response = await db_session.execute(query)
        rows = response.fetchall()

        result = []
        for row in rows:
            result.append(dict(row))

        return result