from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, case, text, and_, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy import exc
from sqlalchemy.orm import selectinload
from crud.base_crud import CRUDBase
from models import (Spk, Bidang, HasilPetaLokasi, KjbDt, SpkKelengkapanDokumen, BundleDt, 
                    TahapDetail, Tahap, Invoice, Termin, BidangKomponenBiaya, Planing)
from schemas.spk_sch import (SpkCreateSch, SpkUpdateSch, SpkInTerminSch, SpkPrintOut, 
                             SpkDetailPrintOut, SpkOverlapPrintOut, SpkRekeningPrintOut)
from common.enum import JenisBayarEnum
from uuid import UUID
from decimal import Decimal
from typing import List
from datetime import datetime
import crud


class CRUDSpk(CRUDBase[Spk, SpkCreateSch, SpkUpdateSch]):

    async def create_(self, *, 
                     obj_in: SpkCreateSch | Spk, 
                     created_by_id : UUID | str | None = None, 
                     db_session : AsyncSession | None = None,
                     with_commit: bool | None = True) -> Spk :
        db_session = db_session or db.session
        db_obj = self.model.from_orm(obj_in) #type ignore
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()
        if created_by_id:
            db_obj.created_by_id = created_by_id
            db_obj.updated_by_id = created_by_id
        
        db_session.add(db_obj)

        bidang = await crud.bidang.get_by_id(id=obj_in.bidang_id)
        beban_biayas = await crud.bebanbiaya.get_by_ids(list_ids=[beban_biaya.beban_biaya_id for beban_biaya in obj_in.spk_beban_biayas])

        for komponen_biaya in obj_in.spk_beban_biayas:
            existing_komponen = next((komponen for komponen in bidang.komponen_biayas if komponen.beban_biaya_id == komponen_biaya.beban_biaya_id), None)
            if existing_komponen:
                komponen = komponen_biaya.dict(exclude={"id"}, exclude_unset=True)
                for key, value in komponen.items():
                    setattr(existing_komponen, key, value)
                existing_komponen.updated_at = datetime.utcnow()
                existing_komponen.updated_by_id = created_by_id
                db_session.add(existing_komponen)
            else:
                beban_biaya = next((bebanbiaya for bebanbiaya in beban_biayas if bebanbiaya.id == komponen_biaya.beban_biaya_id), None)
                new_komponen = BidangKomponenBiaya(**beban_biaya.dict(exclude={"id", "created_at", "updated_at", "created_by_id", "updated_by_id"}),
                                    bidang_id=obj_in.bidang_id,
                                    beban_biaya=beban_biaya.id,
                                    beban_pembeli=komponen_biaya.beban_pembeli,
                                    is_void=False,
                                    is_paid=False,
                                    is_retur=False,
                                    remark=komponen_biaya.remark)
                
                db_session.add(new_komponen)
        
        for kelengkapan in obj_in.spk_kelengkapan_dokumens:
            new_kelengkapan = SpkKelengkapanDokumen(spk_id=db_obj.id, bundle_dt_id=kelengkapan.bundle_dt_id, tanggapan=kelengkapan.tanggapan)
            db_session.add(new_kelengkapan)
        
        try:
            
            if with_commit:
                await db_session.commit()
        except exc.IntegrityError:
            await db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
        
        if with_commit:
            await db_session.refresh(db_obj)
        return db_obj

    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> Spk | None:
        
        db_session = db_session or db.session
        
        query = select(Spk).where(Spk.id == id
                                    ).options(selectinload(Spk.bidang
                                                        ).options(selectinload(Bidang.hasil_peta_lokasi
                                                                            ).options(selectinload(HasilPetaLokasi.kjb_dt
                                                                                                ).options(selectinload(KjbDt.kjb_hd))
                                                                            )
                                                        ).options(selectinload(Bidang.overlaps)
                                                        ).options(selectinload(Bidang.komponen_biayas
                                                                            ).options(selectinload(BidangKomponenBiaya.beban_biaya)
                                                                            )
                                                        ).options(selectinload(Bidang.invoices
                                                                            ).options(selectinload(Invoice.payment_details)
                                                                            ).options(selectinload(Invoice.termin))
                                                        ).options(selectinload(Bidang.planing
                                                                            ).options(selectinload(Planing.project))
                                                        ).options(selectinload(Bidang.sub_project)
                                                        ).options(selectinload(Bidang.tahap_details))
                                    ).options(selectinload(Spk.kjb_termin)
                                    ).options(selectinload(Spk.spk_kelengkapan_dokumens
                                                        ).options(selectinload(SpkKelengkapanDokumen.bundledt
                                                                            ).options(selectinload(BundleDt.dokumen))
                                                        )
                                    ).options(selectinload(Spk.invoices))

        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_by_id_in_termin(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> Spk | None:
        
        db_session = db_session or db.session
        
        query = select(Spk).where(Spk.id == id
                                ).options(selectinload(Spk.bidang
                                            ).options(selectinload(Bidang.invoices
                                                            ).options(selectinload(Invoice.termin)
                                                            ).options(selectinload(Invoice.payment_details)
                                                            )
                                            ).options(selectinload(Bidang.komponen_biayas)
                                            ).options(selectinload(Bidang.planing
                                                            ).options(selectinload(Planing.project)
                                                            )
                                            ).options(selectinload(Bidang.sub_project)
                                            ).options(selectinload(Bidang.tahap_details
                                                                ).options(selectinload(TahapDetail.tahap))
                                            ).options(selectinload(Bidang.manager)
                                            ).options(selectinload(Bidang.sales)
                                            ).options(selectinload(Bidang.notaris)
                                            )
                                )
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_by_bidang_id_kjb_termin_id(self, 
                  *, 
                  bidang_id: UUID | str | None = None,
                  kjb_termin_id:UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> Spk | None:
        
        db_session = db_session or db.session
        
        query = select(Spk).where(and_(
                        Spk.bidang_id == bidang_id, 
                        Spk.kjb_termin_id == kjb_termin_id, 
                        or_(Spk.is_void != True, Spk.is_void == None))
                        )
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
        
    async def get_multi_history_by_bidang_id(self, 
                  *, 
                  bidang_id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> list[Spk] | None:
        
        db_session = db_session or db.session
        
        query = select(Spk)
        query = query.outerjoin(Spk.invoices)
        query = query.filter(Spk.bidang_id == bidang_id)
        query = query.options(selectinload(Spk.invoices
                                        ).options(selectinload(Invoice.termin))
                    ).options(selectinload(Spk.bidang)
                    )
        
        query = query.distinct()
        
        response = await db_session.execute(query)

        return response.scalars().all()

    async def get_multi_by_bidang_id(self, 
                  *, 
                  bidang_id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> list[Spk] | None:
        
        db_session = db_session or db.session
        
        query = select(Spk)
        query = query.where(and_(Spk.bidang_id == bidang_id, or_(Spk.is_void == False, Spk.is_void == None)))
        
        response = await db_session.execute(query)

        return response.scalars().all()

    async def get_by_id_for_termin(self, *, id: UUID | str, db_session: AsyncSession | None = None) -> SpkInTerminSch | None:
        db_session = db_session or db.session
        query = select(Spk.id.label("spk_id"),
                       Spk.code.label("spk_code"),
                       Bidang.id.label("bidang_id"),
                       Bidang.id_bidang,
                       Bidang.alashak,
                       Bidang.group,
                       Bidang.luas_bayar,
                       Bidang.harga_transaksi,
                       Bidang.harga_akta,
                       (Bidang.luas_bayar * Bidang.harga_transaksi).label("total_harga"),
                       Spk.satuan_bayar,
                       Spk.amount.label("spk_amount")
                       ).select_from(Spk
                            ).join(Bidang, Bidang.id == Spk.bidang_id
                            ).where(self.model.id == id)

        response = await db_session.execute(query)

        return response.fetchone()
    
    async def get_multi_by_keyword_tahap_id_and_termin_id(self, 
                                *,
                                keyword:str | None = None,
                                tahap_id:UUID | None = None,
                                termin_id:UUID | None = None,
                                jenis_bayar:JenisBayarEnum | None = None,
                               db_session : AsyncSession | None = None
                        ) -> List[Spk] | None:
        db_session = db_session or db.session
        
        query = select(Spk).outerjoin(Bidang, Bidang.id == Spk.bidang_id
                            ).join(TahapDetail, TahapDetail.bidang_id == Bidang.id
                            ).join(Tahap, Tahap.id == TahapDetail.tahap_id
                            ).outerjoin(Invoice, Invoice.spk_id == Spk.id)
        

        if tahap_id == None and termin_id == None:
             query = query.where(and_(
                                        Spk.jenis_bayar != JenisBayarEnum.PAJAK,
                                        or_(
                                             Invoice.spk_id == None,
                                             Invoice.is_void == True
                                        )
                                    )
                                )
        
        if tahap_id and jenis_bayar == None and termin_id == None:
             query = query.where(and_(
                                        Spk.jenis_bayar != JenisBayarEnum.PAJAK,
                                        Tahap.id == tahap_id,
                                        or_(
                                             Invoice.spk_id == None,
                                             Invoice.is_void == True
                                        )
                                    ))
             

        if tahap_id and jenis_bayar and termin_id == None:
            if jenis_bayar == JenisBayarEnum.DP or jenis_bayar == JenisBayarEnum.TAMBAHAN_DP:
                jenis_bayar = [JenisBayarEnum.DP, JenisBayarEnum.TAMBAHAN_DP]
            else:
                jenis_bayar = [jenis_bayar]
        
            query = query.where(and_(
                                    Spk.jenis_bayar.in_(jenis_bayar),
                                    Tahap.id == tahap_id,
                                    or_(
                                            Invoice.spk_id == None,
                                            Invoice.is_void == True
                                    )
                                ))
            

        if termin_id:
            query = query.outerjoin(Termin, Termin.id == Invoice.termin_id)

            if jenis_bayar == JenisBayarEnum.DP or jenis_bayar == JenisBayarEnum.TAMBAHAN_DP:
                jenis_bayar = [JenisBayarEnum.DP, JenisBayarEnum.TAMBAHAN_DP]
            else:
                jenis_bayar = [jenis_bayar]

            query = query.where(
                                and_(
                                    Spk.jenis_bayar.in_(jenis_bayar),
                                    Tahap.id == tahap_id,
                                    Termin.id == termin_id,
                                    Invoice.is_void != True
                                    ))
        
        if keyword:
            query = query.filter(or_(
                Bidang.id_bidang.ilike(f"%{keyword}%"),
                Bidang.id_bidang_lama.ilike(f"%{keyword}%"),
                Bidang.alashak.ilike(f"%{keyword}%"),
                Spk.code.ilike(f"%{keyword}%")
            ))

        query = query.options(selectinload(Spk.bidang)
                    ).options(selectinload(Spk.invoices))
        query = query.distinct()

        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_multi_by_tahap_id(self, 
                                *,
                                tahap_id:UUID,
                                jenis_bayar:JenisBayarEnum,
                               db_session : AsyncSession | None = None
                        ) -> List[Spk] | None:
        db_session = db_session or db.session
        
        query = select(Spk).outerjoin(Bidang, Bidang.id == Spk.bidang_id
                            ).outerjoin(TahapDetail, TahapDetail.bidang_id == Bidang.id
                            ).outerjoin(Tahap, Tahap.id == TahapDetail.tahap_id
                            ).outerjoin(Invoice, Invoice.spk_id == Spk.id
                            ).where(
                                 and_(
                                        Spk.jenis_bayar == jenis_bayar,
                                        Tahap.id == tahap_id,
                                        or_(
                                             Invoice.spk_id == None,
                                             Invoice.is_void == True
                                        )
                                      )
                            ).options(selectinload(Spk.bidang
                                                ).options(selectinload(Bidang.overlaps)
                                                ).options(selectinload(Bidang.komponen_biayas
                                                                    ).options(selectinload(BidangKomponenBiaya.beban_biaya)
                                                                    )
                                                ).options(selectinload(Bidang.invoices
                                                                    ).options(selectinload(Invoice.payment_details)
                                                                    ).options(selectinload(Invoice.termin))
                                                )
                            )

        response =  await db_session.execute(query)
        return response.scalars().all()
     
    async def get_multi_by_tahap_id_and_termin_id(self, 
                                *,
                                tahap_id:UUID,
                                jenis_bayar:JenisBayarEnum,
                                termin_id:UUID,
                               db_session : AsyncSession | None = None
                        ) -> List[Spk]:
        db_session = db_session or db.session
        
        query = select(Spk).outerjoin(Bidang, Bidang.id == Spk.bidang_id
                            ).outerjoin(TahapDetail, TahapDetail.bidang_id == Bidang.id
                            ).outerjoin(Tahap, Tahap.id == TahapDetail.tahap_id
                            ).outerjoin(Invoice, Invoice.spk_id == Spk.id
                            ).outerjoin(Termin, Termin.id == Invoice.termin_id
                            ).where(
                                 and_(
                                        Spk.jenis_bayar == jenis_bayar,
                                        Tahap.id == tahap_id,
                                        Termin.id == termin_id,
                                        Invoice != True
                                      )
                            ).options(selectinload(Spk.bidang
                                                ).options(selectinload(Bidang.overlaps)
                                                ).options(selectinload(Bidang.komponen_biayas
                                                                    ).options(selectinload(BidangKomponenBiaya.beban_biaya)
                                                                    )
                                                ).options(selectinload(Bidang.invoices
                                                                    ).options(selectinload(Invoice.payment_details)
                                                                    ).options(selectinload(Invoice.termin))
                                                )
                            )

        response =  await db_session.execute(query)
        return response.scalars().all()

    async def get_by_id_for_printout(self, 
                                     *, 
                                     id: UUID | str, 
                                     db_session: AsyncSession | None = None
                                     ) -> SpkPrintOut | None:
        
        db_session = db_session or db.session

        query = text(f"""
                select
                s.bidang_id,
                kh.code As kjb_hd_code,
                b.jenis_bidang,
                b.id_bidang,
                b.alashak,
                b.no_peta,
                b.group,
                b.luas_surat,
                b.luas_ukur,
                b.luas_gu_perorangan,
                b.luas_pbt_perorangan,
                p.name As pemilik_name,
                ds.name As desa_name,
                nt.name As notaris_name,
                pr.name As project_name,
                pt.name As ptsk_name,
                sk.status As status_il,
                hpl.hasil_analisa_peta_lokasi As analisa,
                s.jenis_bayar,
                s.amount,
                s.satuan_bayar,
                mng.name As manager_name,
                sls.name As sales_name,
				w.name as worker_name,
                s.remark
                from spk s
                left join bidang b on s.bidang_id = b.id
                left join hasil_peta_lokasi hpl on b.id = hpl.bidang_id
                left join kjb_dt kd on hpl.kjb_dt_id = kd.id
                left join kjb_hd kh on kd.kjb_hd_id = kh.id
                left join pemilik p on b.pemilik_id = p.id
                left join planing pl on b.planing_id = pl.id
                left join project pr on pl.project_id = pr.id
                left join desa ds on pl.desa_id = ds.id
                left join notaris nt on b.notaris_id = nt.id
                left join skpt sk on b.skpt_id = sk.id
                left join ptsk pt on sk.ptsk_id = pt.id
                left join manager mng on b.manager_id = mng.id
                left join sales sls on b.sales_id = sls.id
				left join worker w on w.id = s.created_by_id
                where s.id = '{str(id)}'
        """)

        response = await db_session.execute(query)

        return response.fetchone()

    async def get_beban_biaya_pajak_by_id_for_printout(self, 
                                                 *, 
                                                 id: UUID | str, 
                                                 db_session: AsyncSession | None = None
                                                 ) -> List[SpkDetailPrintOut] | None:
        db_session = db_session or db.session
        query = text(f"""
                    select 
                    case
                        when bkb.beban_pembeli = true and bkb.is_paid = false Then 'DITANGGUNG PT'
                        when bkb.beban_pembeli = true and bkb.is_paid = true Then 'SUDAH DIBAYAR'
                        when bkb.beban_pembeli = false and bkb.is_paid = true Then 'SUDAH DIBAYAR'
                        else 'DITANGGUNG PENJUAL'
                    end as tanggapan,
                    bb.name
                    from spk s
                    inner join bidang b on b.id = s.bidang_id
                    inner join bidang_komponen_biaya bkb on bkb.bidang_id = b.id
                    inner join beban_biaya bb on bb.id = bkb.beban_biaya_id
                    where s.id = '{str(id)}'
                    and bb.is_tax = true
                    and bkb.is_void != true
                    """)

        response = await db_session.execute(query)

        return response.fetchall()
    
    async def get_beban_biaya_pengembalian_by_id_for_printout(self, 
                                                 *, 
                                                 id: UUID | str, 
                                                 db_session: AsyncSession | None = None
                                                 ) -> List[SpkDetailPrintOut] | None:
        db_session = db_session or db.session
        query = text(f"""
                    select 
                    case
                        when bkb.beban_pembeli = true and bkb.is_paid = false Then 'DITANGGUNG PT'
                        when bkb.beban_pembeli = true and bkb.is_paid = true Then 'SUDAH DIBAYAR'
                        else 'DITANGGUNG PENJUAL (PENGEMBALIAN)'
                    end as tanggapan,
                    bb.name
                    from spk s
                    inner join bidang b on b.id = s.bidang_id
                    inner join bidang_komponen_biaya bkb on bkb.bidang_id = b.id
                    inner join beban_biaya bb on bb.id = bkb.beban_biaya_id
                    where s.id = '{str(id)}'
                    and bkb.is_void != true
                    and bkb.is_retur = true
                    """)

        response = await db_session.execute(query)

        return response.fetchall()
    
    async def get_beban_biaya_lain_by_id_for_printout(self, 
                                                 *, 
                                                 id: UUID | str, 
                                                 db_session: AsyncSession | None = None
                                                 ) -> List[SpkDetailPrintOut] | None:
        db_session = db_session or db.session
        query = text(f"""
                    select 
                    case
                        when bkb.beban_pembeli = true and bkb.is_paid = false Then 'DITANGGUNG PT'
                        when bkb.beban_pembeli = true and bkb.is_paid = true Then 'SUDAH DIBAYAR'
                        else 'DITANGGUNG PENJUAL (PENGEMBALIAN)'
                    end as tanggapan,
                    bb.name
                    from spk s
                    inner join bidang b on b.id = s.bidang_id
                    inner join bidang_komponen_biaya bkb on bkb.bidang_id = b.id
                    inner join beban_biaya bb on bb.id = bkb.beban_biaya_id
                    where s.id = '{str(id)}'
                    and bkb.is_void != true
                    and bkb.is_add_pay = true
                    """)

        response = await db_session.execute(query)

        return response.fetchall()
    
    async def get_beban_biaya_by_id_for_printout(self, 
                                                 *, 
                                                 id: UUID | str, 
                                                 db_session: AsyncSession | None = None
                                                 ) -> List[SpkDetailPrintOut] | None:
        db_session = db_session or db.session
        query = text(f"""
                    select 
                    case
                        when bkb.beban_pembeli = true and bkb.is_paid = false Then 'DITANGGUNG PT'
                        when bkb.beban_pembeli = true and bkb.is_paid = true Then 'SUDAH DIBAYAR'
                        else 'DITANGGUNG PENJUAL'
                    end as tanggapan,
                    bb.name
                    from spk s
                    inner join bidang b on b.id = s.bidang_id
                    inner join bidang_komponen_biaya bkb on bkb.bidang_id = b.id
                    inner join beban_biaya bb on bb.id = bkb.beban_biaya_id
                    where s.id = '{str(id)}'
                    and bkb.is_void != true
                    """)

        response = await db_session.execute(query)

        return response.fetchall()

    async def get_kelengkapan_by_id_for_printout(self,
                                                *, 
                                                id: UUID | str, 
                                                db_session: AsyncSession | None = None
                                                ) -> List[SpkDetailPrintOut] | None:
            
            db_session = db_session or db.session

            query = text(f"""
                    select 
                    d.name,
                    kd.tanggapan
                    from spk s
                    inner join spk_kelengkapan_dokumen kd on kd.spk_id = s.id
                    inner join bundle_dt bdt on bdt.id = kd.bundle_dt_id
                    inner join dokumen d on d.id = bdt.dokumen_id
                    where s.id = '{str(id)}'
                    """)

            response = await db_session.execute(query)

            return response.fetchall()
    
    async def get_rekening_by_id_for_printout(self,
                                                *, 
                                                id: UUID | str, 
                                                db_session: AsyncSession | None = None
                                                ) -> List[SpkRekeningPrintOut] | None:
            
            db_session = db_session or db.session

            query = text(f"""
                    select 
                    (r.bank_rekening || ' (' || r.nomor_rekening || ') ' || ' a/n ' || r.nama_pemilik_rekening) as rekening
                    from spk s
                    inner join bidang b on b.id = s.bidang_id
                    left outer join pemilik p on p.id = b.pemilik_id
                    left outer join rekening r on r.pemilik_id = p.id
                    where s.id = '{str(id)}'
                    """)

            response = await db_session.execute(query)

            return response.fetchall()
    
    async def get_overlap_by_id_for_printout(self,
                                                *, 
                                                id: UUID | str, 
                                                db_session: AsyncSession | None = None
                                                ) -> List[SpkOverlapPrintOut] | None:
            
            db_session = db_session or db.session

            query = text(f"""
                    select
                    Coalesce(p.name, '-') as pemilik_name,
                    bi.alashak,
                    Coalesce(bi.tahap, 0) as tahap,
                    bi.luas_surat,
                    bo.luas as luas_overlap,
                    bi.id_bidang,
                    hpl.tipe_overlap
                    from spk s
                    inner join bidang b on b.id = s.bidang_id
                    inner join bidang_overlap bo on bo.parent_bidang_id = b.id
                    inner join bidang bi on bi.id = bo.parent_bidang_intersect_id
                    inner join hasil_peta_lokasi_detail hpl on hpl.bidang_overlap_id = bo.id
                    left outer join pemilik p on p.id = bi.pemilik_id
                    where s.id = '{str(id)}'
                    """)

            response = await db_session.execute(query)

            return response.fetchall()
    
spk = CRUDSpk(Spk)