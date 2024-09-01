from fastapi_async_sqlalchemy import db
from datetime import date
import crud
import calendar

class ClosingService:

    async def closing_bidang(self):
        
        today = date.today()
        month = today.month
        year = today.year

        period_date: date = date.today()

        if month == 1:
            year = year - 1
            last_day = calendar.monthrange(year, 12)[1]
            period_date = date(day=last_day, month=12, year=year)
        else:
            month = month - 1
            last_day = calendar.monthrange(year, month)[1]
            period_date = date(day=last_day, month=month, year=year)

        await crud.bidang.closing_bidang(period_date=period_date)

    async def closing_kulit_planing(self):

        today = date.today()
        month = today.month
        year = today.year

        period_date: date = date.today()

        if month == 1:
            year = year - 1
            last_day = calendar.monthrange(year, 12)[1]
            period_date = date(day=last_day, month=12, year=year)
        else:
            month = month - 1
            last_day = calendar.monthrange(year, month)[1]
            period_date = date(day=last_day, month=month, year=year)

        await crud.planing.closing_planing(period_date=period_date)

    async def closing_kjb_dt(self):

        today = date.today()
        month = today.month
        year = today.year

        period_date: date = date.today()

        if month == 1:
            year = year - 1
            last_day = calendar.monthrange(year, 12)[1]
            period_date = date(day=last_day, month=12, year=year)
        else:
            month = month - 1
            last_day = calendar.monthrange(year, month)[1]
            period_date = date(day=last_day, month=month, year=year)

        await crud.kjb_dt.closing_kjb_dt_by_kjb(period_date=period_date)
        await crud.kjb_dt.closing_kjb_dt_by_ttn(period_date=period_date)

