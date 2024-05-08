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
            with subquery as (select
            b.id,
            b.id_bidang,
            b.alashak,
            tr.id as kjb_termin_id,
            hd.satuan_bayar,
            hd.satuan_harga,
            tr.nilai,
            'DP' as jenis_bayar
            from hasil_peta_lokasi hpl
			inner join bidang b ON b.id = hpl.bidang_id
            inner join kjb_dt dt ON dt.id = hpl.kjb_dt_id
            inner join kjb_harga hg ON hg.kjb_hd_id = dt.kjb_hd_id and hg.jenis_alashak = dt.jenis_alashak
            inner join kjb_termin tr ON hg.id = tr.kjb_harga_id and tr.jenis_bayar = 'DP' and tr.nilai > 0
            inner join kjb_hd hd ON hd.id = hg.kjb_hd_id
            Where 
				  NOT EXISTS (select 1 from checklist_kelengkapan_dokumen_dt c_dt
							inner join checklist_kelengkapan_dokumen_hd c_hd ON c_hd.id = c_dt.checklist_kelengkapan_dokumen_hd_id
							inner join bundle_dt b_dt ON b_dt.id = c_dt.bundle_dt_id and b_dt.meta_data is NULL
							Where c_hd.bidang_id = b.id
							and c_dt.jenis_bayar IN ('DP', 'UTJ'))
				  AND NOT EXISTS (select 1 from spk s
							 where s.bidang_id = b.id AND s.jenis_bayar = 'DP' and s.is_void is FALSE)
				  AND NOT EXISTS (select 1 from spk ss
							 where ss.bidang_id = b.id and ss.jenis_bayar = 'LUNAS' and ss.is_void is FALSE)
				  AND hpl.status_hasil_peta_lokasi = 'Lanjut'
            UNION
            select 
            b.id,
            b.id_bidang,
            b.alashak,
            tr.id as kjb_termin_id,
            hd.satuan_bayar,
            hd.satuan_harga,
            tr.nilai,
            'PELUNASAN' as jenis_bayar
            from hasil_peta_lokasi hpl
            inner join kjb_dt dt ON dt.id = hpl.kjb_dt_id
            inner join kjb_harga hg ON hg.kjb_hd_id = dt.kjb_hd_id and hg.jenis_alashak = dt.jenis_alashak
            inner join kjb_termin tr ON hg.id = tr.kjb_harga_id and tr.jenis_bayar = 'PELUNASAN' and tr.nilai > 0
            inner join kjb_hd hd ON hd.id = hg.kjb_hd_id
            inner join bidang b ON b.id = hpl.bidang_id
            Where 
				NOT EXISTS (select 1 from checklist_kelengkapan_dokumen_dt c_dt
							inner join checklist_kelengkapan_dokumen_hd c_hd ON c_hd.id = c_dt.checklist_kelengkapan_dokumen_hd_id
							inner join bundle_dt b_dt ON b_dt.id = c_dt.bundle_dt_id
							Where c_hd.bidang_id = b.id
							and c_dt.jenis_bayar IN ('PELUNASAN', 'DP', 'UTJ')
							and b_dt.meta_data is null)
				AND NOT EXISTS (select 1 from spk s
							 where s.bidang_id = b.id AND s.jenis_bayar = 'PELUNASAN' and s.is_void is FALSE)
				AND NOT EXISTS (select 1 from spk ss
							 where ss.bidang_id = b.id and ss.jenis_bayar = 'LUNAS' and ss.is_void is FALSE)
				AND hpl.status_hasil_peta_lokasi = 'Lanjut'
            UNION
            select 
            b.id,
            b.id_bidang,
            b.alashak,
            null as kjb_termin_id,
            null as satuan_bayar,
            null as satuan_harga,
            null as nilai,
            'PENGEMBALIAN_BEBAN_PENJUAL' as jenis_bayar 
            from hasil_peta_lokasi hpl
            inner join bidang b ON b.id = hpl.bidang_id
            Where 
				EXISTS (select 1 
						from bidang_komponen_biaya kb
						left outer join invoice_detail inv_dt ON inv_dt.bidang_komponen_biaya_id = kb.id
						left outer join invoice inv ON inv.id = inv_dt.invoice_id
						left outer join termin tr ON tr.id = inv.termin_id
						where kb.is_void != true and kb.is_retur = true
						and tr.id is null and tr.jenis_bayar = 'PENGEMBALIAN_BEBAN_PENJUAL')
				AND NOT EXISTS (select 1 from checklist_kelengkapan_dokumen_hd c_hd
								inner join checklist_kelengkapan_dokumen_dt c_dt ON c_hd.id = c_dt.checklist_kelengkapan_dokumen_hd_id 
								and c_dt.jenis_bayar = 'BIAYA_LAIN'
								inner join bundle_dt b_dt ON b_dt.id = c_dt.bundle_dt_id
								Where c_hd.bidang_id = hpl.bidang_id
								and b_dt.meta_data is null)
				AND NOT EXISTS (select 1 from spk s
							 where s.bidang_id = b.id AND s.jenis_bayar = 'PENGEMBALIAN_BEBAN_PENJUAL' and s.is_void is FALSE)
				AND hpl.status_hasil_peta_lokasi = 'Lanjut'
            UNION
            select 
            b.id,
            b.id_bidang,
            b.alashak,
            null as kjb_termin_id,
            null as satuan_bayar,
            null as satuan_harga,
            null as nilai,
            'PAJAK' as jenis_bayar
            from hasil_peta_lokasi hpl
            inner join kjb_dt dt ON dt.id = hpl.kjb_dt_id
            inner join bidang b ON b.id = hpl.bidang_id
			Where NOT EXISTS (select 1 from spk s
							 where s.bidang_id = b.id AND s.jenis_bayar = 'PAJAK' and s.is_void is FALSE)
				  AND hpl.status_hasil_peta_lokasi = 'Lanjut'
            Order by id_bidang),

subquery_hasil_petlok as (
                    select 
                        hpl.id,
                        dk.name,
                        dt.meta_data
                    from 
                        hasil_peta_lokasi hpl
                    INNER JOIN 
                        bidang b ON b.id = hpl.bidang_id
                    INNER JOIN 
                        bundle_hd hd ON hd.id = b.bundle_hd_id
                    INNER JOIN
                        bundle_dt dt ON hd.id = dt.bundle_hd_id
                    INNER JOIN
                        dokumen dk ON dk.id = dt.dokumen_id 
                        and dk.name IN ('GAMBAR UKUR PBT', 'GAMBAR UKUR PERORANGAN', 'PBT PERORANGAN', 'PBT PT')
						and dk.is_active is TRUE
                    )
SELECT 
	'outstanding_gu_pbt' as tipe_worklist,
	count(hpl.id) as total
FROM hasil_peta_lokasi hpl
LEFT OUTER JOIN 
	subquery_hasil_petlok gu_pt ON gu_pt.id = hpl.id AND gu_pt.name = 'GAMBAR UKUR PBT'
LEFT OUTER JOIN 
	subquery_hasil_petlok gu_perorangan ON gu_perorangan.id = hpl.id AND gu_perorangan.name = 'GAMBAR UKUR PERORANGAN'
LEFT OUTER JOIN 
	subquery_hasil_petlok pbt_pt ON pbt_pt.id = hpl.id AND pbt_pt.name = 'PBT PT'
LEFT OUTER JOIN 
	subquery_hasil_petlok pbt_perorangan ON pbt_perorangan.id = hpl.id AND pbt_perorangan.name = 'PBT PERORANGAN'
WHERE
	(gu_pt.meta_data IS NOT NULL AND hpl.luas_gu_pt = 0)
	OR (gu_perorangan.meta_data IS NOT NULL AND hpl.luas_gu_perorangan = 0)
	OR (pbt_pt.meta_data IS NOT NULL AND hpl.luas_pbt_pt = 0)
	OR (pbt_perorangan.meta_data IS NOT NULL AND hpl.luas_pbt_perorangan = 0)
union
select 'outstanding_spk' as tipe_worklist, Count(*) as total from subquery
union
select 'outstanding_hasil_peta_lokasi' as tipe_worklist, count(*) as total 
from request_peta_lokasi
where kjb_dt_id not in (select kjb_dt_id from hasil_peta_lokasi)
union
select 'outstanding_invoice' as tipe_worklist, count(*) as total 
from spk
inner join workflow ON spk.id = workflow.reference_id
where spk.id not in (select spk_id 
				from invoice i
				join termin t on t.id = i.termin_id
				where i.is_void != true 
				and t.jenis_bayar not in ('UTJ', 'UTJ_KHUSUS', 'BEGINNING_BALANCE'))
and jenis_bayar not in ('PAJAK', 'BEGINNING_BALANCE')
and is_void != True
and workflow.last_status = 'COMPLETED'
union
SELECT 'outstanding_payment' as tipe_worklist, count(*)
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
			Coalesce(SUM(idt.amount), 0)
			from invoice_detail idt
			inner join bidang_komponen_biaya kb on kb.id = idt.bidang_komponen_biaya_id
			inner join beban_biaya bb on bb.id = kb.beban_biaya_id
			inner join bidang b on b.id = kb.bidang_id
			where idt.invoice_id = i.id
			and kb.beban_pembeli = false)
				) != 0 and i.is_void != TRUE
        """)

    result = await db_session.execute(query)
    data = result.fetchall()
    return create_response(data=data)