from fastapi_async_sqlalchemy import db

from datetime import date
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

        