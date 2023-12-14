from fastapi import APIRouter, Depends
from fastapi_async_sqlalchemy import db
from sqlmodel import text, select
from schemas.dashboard_sch import OutStandingSch
from schemas.response_sch import (GetResponseBaseSch, GetResponsePaginatedSch, create_response)

router = APIRouter()

@router.get("/search", response_model=GetResponseBaseSch[list[OutStandingSch]])
async def dashboard_outstanding():

    """Get for search"""

    db_session = db.session

    query = text(f"""
            select 'outstanding_hasil_peta_lokasi' as tipe_worklist, count(*) as total 
            from request_peta_lokasi
            where kjb_dt_id not in (select kjb_dt_id from hasil_peta_lokasi)
            union
            select 'outstanding_spk' as tipe_worklist, count(*) as total 
            from spk
            where id not in (select spk_id 
                            from invoice i
                            join termin t on t.id = i.termin_id
                            where i.is_void != true 
                            and t.jenis_bayar not in ('UTJ', 'UTJ_KHUSUS', 'BEGINNING_BALANCE'))
            and jenis_bayar not in ('PAJAK', 'BEGINNING_BALANCE')
            union
            SELECT 'outstanding_invoice' as tipe_worklist, count(*)
            FROM invoice i
            WHERE i.amount - ((
                CASE
                WHEN i.use_utj = True THEN (
                    SELECT COALESCE(SUM(amount), 0)
                    FROM invoice i_utj
                    Inner join termin tr on tr.id = i_utj.termin_id
                    WHERE i.bidang_id = i_utj.bidang_id
                    and tr.jenis_bayar in ('UTJ', 'UTJ_KHUSUS')
                )
                ELSE 0
                END
            ) + (
                select coalesce(sum(amount), 0) 
                from payment_detail py
                where i.id = py.invoice_id
                and py.is_void != true
                ) + (
                    Select 
                        Coalesce(SUM(Case
							When kb.is_retur = FALSE Then idt.amount
							else 0
						end), 0)
                        from invoice_detail idt
                        inner join bidang_komponen_biaya kb on kb.id = idt.bidang_komponen_biaya_id
                        inner join beban_biaya bb on bb.id = kb.beban_biaya_id
                        inner join bidang b on b.id = kb.bidang_id
                        where idt.invoice_id = i.id
                        and kb.beban_pembeli = false)
                            ) != 0 and i.is_void != TRUE;
        """)

    result = await db_session.execute(query)
    data = result.fetchall()
    return create_response(data=data)