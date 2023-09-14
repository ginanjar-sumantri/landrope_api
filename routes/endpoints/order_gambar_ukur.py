from uuid import UUID
from fastapi import APIRouter, status, Depends, HTTPException, Response
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_, or_
from models.order_gambar_ukur_model import OrderGambarUkur, OrderGambarUkurBidang, OrderGambarUkurTembusan
from models.kjb_model import KjbDt
from models.hasil_peta_lokasi_model import HasilPetaLokasi
from models.bidang_model import Bidang
from models.worker_model import Worker
from models.code_counter_model import CodeCounterEnum
from schemas.order_gambar_ukur_sch import (OrderGambarUkurSch, OrderGambarUkurCreateSch, OrderGambarUkurUpdateSch, OrderGambarUkurByIdSch, OrderGambarUkurUpdateExtSch)
from schemas.order_gambar_ukur_bidang_sch import OrderGambarUkurBidangPdfSch, OrderGambarUkurBidangCreateSch
from schemas.order_gambar_ukur_tembusan_sch import OrderGambarUkurTembusanCreateSch
from schemas.kjb_dt_sch import KjbDtSrcForGUSch, KjbDtForOrderGUById
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ContentNoChangeException)
from common.generator import generate_code_month
from common.enum import TipeSuratGambarUkurEnum, HasilAnalisaPetaLokasiEnum, StatusHasilPetaLokasiEnum
from services.helper_service import HelperService
from services.pdf_service import PdfService
from datetime import datetime, date
from jinja2 import Environment, FileSystemLoader
import crud
import string
import secrets
import roman


router = APIRouter()

@router.post("/create", response_model=PostResponseBaseSch[OrderGambarUkurSch], status_code=status.HTTP_201_CREATED)
async def create(
            sch: OrderGambarUkurCreateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Create a new object"""
    db_session = db.session

    if len(sch.tembusans) > 5:
        raise ContentNoChangeException(detail="Tembusan tidak boleh lebih dari 5 orang!")

    last_number = await generate_code_month(entity=CodeCounterEnum.OrderGambarUkur, with_commit=False, db_session=db_session)

    today = date.today()
    month = roman.toRoman(today.month)
    year = today.year

    sch.code = f"{last_number}/LA-PRA/GU/{month}/{year}"
        
    new_obj = await crud.order_gambar_ukur.create(obj_in=sch, created_by_id=current_worker.id, db_session=db_session, with_commit=False)

    for kjb_dt in sch.kjb_dts:
        sch_kjb_dt = OrderGambarUkurBidangCreateSch(order_gambar_ukur_id=new_obj.id, kjb_dt_id=kjb_dt)
        await crud.order_gambar_ukur_bidang.create(obj_in=sch_kjb_dt, created_by_id=current_worker.id, db_session=db_session, with_commit=False)

    for tembusan in sch.tembusans:
        sch_tembusan = OrderGambarUkurTembusanCreateSch(order_gambar_ukur_id=new_obj.id, tembusan_id=tembusan)
        await crud.order_gambar_ukur_tembusan.create(obj_in=sch_tembusan, created_by_id=current_worker.id, db_session=db_session, with_commit=False)

    await db_session.commit()
    await db_session.refresh(new_obj)
    
    return create_response(data=new_obj)

@router.get("", response_model=GetResponsePaginatedSch[OrderGambarUkurSch])
async def get_list(
            params: Params=Depends(), 
            order_by:str = None, 
            keyword:str = None, 
            filter_query:str = None,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Gets a paginated list objects"""

    objs = await crud.order_gambar_ukur.get_multi_paginate_ordered_with_keyword_dict(params=params, order_by=order_by, keyword=keyword, filter_query=filter_query)
    return create_response(data=objs)

@router.get("/{id}", response_model=GetResponseBaseSch[OrderGambarUkurByIdSch])
async def get_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.order_gambar_ukur.get(id=id)
    if obj:
        return create_response(data=obj)
    else:
        raise IdNotFoundException(OrderGambarUkur, id)

@router.put("/{id}", response_model=PutResponseBaseSch[OrderGambarUkurSch])
async def update(
            id:UUID, 
            sch:OrderGambarUkurUpdateSch,
            current_worker:Worker = Depends(crud.worker.get_active_worker)):
    
    """Update a obj by its id"""

    db_session = db.session

    obj_current = await crud.order_gambar_ukur.get(id=id)

    if not obj_current:
        raise IdNotFoundException(OrderGambarUkur, id)
    
    sch_updated = OrderGambarUkurUpdateExtSch(**sch.dict())
    obj_updated = await crud.order_gambar_ukur.update(obj_current=obj_current, obj_new=sch_updated, updated_by_id=current_worker.id, db_session=db_session, with_commit=False)
    
    bidang_ids = [bidang for bidang in sch.bidangs]
    order_gu_bidang_will_removed = await crud.order_gambar_ukur_bidang.get_not_in_by_kjb_dt_ids(list_ids=bidang_ids, order_ukur_id=id)
    if len(order_gu_bidang_will_removed) > 0 :
        await crud.order_gambar_ukur_bidang.remove_multiple_data(list_obj=order_gu_bidang_will_removed, db_session=db_session)
    
    for order_gu_bidang in sch.bidangs:
        gu_bidang = await crud.order_gambar_ukur_bidang.get_by_kjb_dt_id_and_order_ukur_id(kjb_dt_id=order_gu_bidang, order_ukur_id=id)
        if gu_bidang is None:
            new_order_gu_bidang = OrderGambarUkurBidang(kjb_dt_id=order_gu_bidang, order_gambar_ukur_id=id)
            await crud.order_gambar_ukur_bidang.create(obj_in=new_order_gu_bidang, created_by_id=current_worker.id, db_session=db_session, with_commit=False)
    
    tembusan_ids = [tembusan for tembusan in sch.tembusans]
    order_gu_tembusan_will_removed = await crud.order_gambar_ukur_tembusan.get_not_in_by_tembusan_ids(list_ids=tembusan_ids, order_ukur_id=id)
    if len(order_gu_tembusan_will_removed) > 0:
        await crud.order_gambar_ukur_tembusan.remove_multiple_data(list_obj=order_gu_tembusan_will_removed, db_session=db_session)
    
    for order_gu_tembusan in sch.tembusans:
        gu_tembusan = await crud.order_gambar_ukur_tembusan.get_by_tembusan_id_and_order_ukur_id(tembusan_id=order_gu_tembusan, order_ukur_id=id)
        if gu_tembusan is None:
            new_order_gu_tembusan = OrderGambarUkurTembusan(tembusan_id=order_gu_tembusan, order_gambar_ukur_id=id)
            await crud.order_gambar_ukur_tembusan.create(obj_in=new_order_gu_tembusan, created_by_id=current_worker.id, db_session=db_session, with_commit=False)
    
    await db_session.commit()
    await db_session.refresh(obj_updated)
   
    return create_response(data=obj_updated)

@router.get("/print-out/{id}")
async def print_out(id:UUID | str,
                    current_worker:Worker = Depends(crud.worker.get_active_worker)):
    """Print out Order Gambar Ukur"""

    obj = await crud.order_gambar_ukur.get(id=id)
    sla_hari:str = ""
    if obj.tipe_surat == TipeSuratGambarUkurEnum.Surat_Tugas:
        sla_hari = "3 (Tiga)"
    else:
        sla_hari = "4 (Empat)"

    tipesurat = obj.tipe_surat.replace("_", " ")
    code = obj.code
    perihal = obj.perihal or "-"
    tujuansurat = obj.tujuan_surat

    tembusans = [tembusan.cc_name for tembusan in obj.tembusans]

    data_list = []
    no = 1
    nomor = ""
    for bidang in obj.bidangs:
        data = OrderGambarUkurBidangPdfSch(no=no,
                                           id_bidang=bidang.id_bidang or "-",
                                           pemilik_name=bidang.pemilik_name or "-",
                                           group=bidang.group,
                                           ptsk_name=bidang.ptsk_name or "-",
                                           jenis_surat_name=bidang.jenis_surat_name,
                                           alashak=bidang.alashak,
                                           mediator=bidang.mediator,
                                           sales_name=bidang.sales_name,
                                           luas_surat="{:,.2f}".format(bidang.luas_surat or 0)
                                           )
        no = no + 1
        data_list.append(data)

    
    # template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("order_gambar_ukur.html")

    create_date = obj.created_at.date()
    create_at = datetime.strptime(str(create_date), "%Y-%m-%d")
    month = create_date.month
    month_name = HelperService().ToMonthName(month=month)
    formatted_date = create_at.strftime(f"%d {month_name} %Y")

    render_template = template.render(tipesurat=tipesurat, 
                                      code=code,
                                      perihal=perihal,
                                      tujuansurat=tujuansurat,
                                      tembusans=tembusans,
                                      data=data_list, 
                                      sla_hari=sla_hari,
                                      tanggal=formatted_date)

    try:
        doc = await PdfService().get_pdf(render_template)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed generate document")
    
    response = Response(doc, media_type='application/pdf')
    response.headers["Content-Disposition"] = f"attachment; filename={code}.pdf"
    return response

@router.get("/search/kjb_dt", response_model=GetResponseBaseSch[list[KjbDtSrcForGUSch]])
async def search_kjb_dt(
    size:int = 10,
    status_bidang:HasilAnalisaPetaLokasiEnum = None,
    keyword:str = None):

    """Gets a paginated list objects"""

    
    query = select(KjbDt.id.label("kjb_dt_id"),
                    KjbDt.alashak.label("kjb_dt_alashak"),
                    Bidang.id.label("bidang_id"),
                    Bidang.id_bidang.label("id_bidang"))
    
    if status_bidang:
        query = query.select_from(KjbDt
                        ).join(HasilPetaLokasi, HasilPetaLokasi.kjb_dt_id == KjbDt.id
                        ).join(Bidang, HasilPetaLokasi.bidang_id == Bidang.id
                        ).where(
                                and_(
                                        HasilPetaLokasi.hasil_analisa_peta_lokasi == status_bidang,
                                        HasilPetaLokasi.status_hasil_peta_lokasi == StatusHasilPetaLokasiEnum.Lanjut,
                                        KjbDt.hasil_peta_lokasi != None
                                    )
                                )
    else:
        query = query.select_from(KjbDt
                        ).outerjoin(HasilPetaLokasi, HasilPetaLokasi.kjb_dt_id == KjbDt.id
                        ).outerjoin(Bidang, HasilPetaLokasi.bidang_id == Bidang.id
                        ).where(
                            and_(
                                    KjbDt.hasil_peta_lokasi == None,
                                    KjbDt.tanda_terima_notaris_hd != None
                                )
                            )


    if keyword:
        query = query.filter(
                            or_(
                                    Bidang.id_bidang.ilike(f'%{keyword}%'),
                                    KjbDt.alashak.ilike(f'%{keyword}%')
                                )
                            )
        
    query = query.limit(size)
    

    objs = await crud.kjb_dt.get_multi_for_order_gu(query=query)

    return create_response(data=objs) 


@router.get("/search/kjb_dt/{id}", response_model=GetResponseBaseSch[KjbDtForOrderGUById])
async def get_for_order_gu_by_id(id:UUID):

    """Get an object by id"""

    obj = await crud.kjb_dt.get(id=id)
    if obj is None:
        raise IdNotFoundException(KjbDt, id)
    
    obj_bidang = None
    if obj.hasil_peta_lokasi:
        obj_bidang = await crud.bidang.get(id=obj.hasil_peta_lokasi.bidang_id)
        

    obj_return = KjbDtForOrderGUById(id=obj.id,
                                      id_bidang=obj_bidang.id_bidang if obj_bidang is not None else None,
                                      jenis_alashak=obj.jenis_alashak,
                                      alashak=obj.alashak,
                                      status_sk=obj_bidang.status_sk if obj_bidang is not None else None,
                                      ptsk_name=obj_bidang.ptsk_name if obj_bidang is not None else None,
                                      hasil_analisa_peta_lokasi=obj_bidang.hasil_analisa_peta_lokasi if obj_bidang is not None else None,
                                      proses_bpn_order_gu=obj_bidang.proses_bpn_order_gu if obj_bidang is not None else None,
                                      luas_surat=obj.luas_surat_by_ttn)
    
    return create_response(data=obj_return)