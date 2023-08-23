from uuid import UUID
from fastapi import APIRouter, status, Depends, HTTPException, Response
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from models.order_gambar_ukur_model import OrderGambarUkur, OrderGambarUkurBidang, OrderGambarUkurTembusan
from models.worker_model import Worker
from models.code_counter_model import CodeCounterEnum
from schemas.order_gambar_ukur_sch import (OrderGambarUkurSch, OrderGambarUkurCreateSch, OrderGambarUkurUpdateSch, OrderGambarUkurByIdSch, OrderGambarUkurUpdateExtSch)
from schemas.order_gambar_ukur_bidang_sch import OrderGambarUkurBidangPdfSch, OrderGambarUkurBidangCreateSch
from schemas.order_gambar_ukur_tembusan_sch import OrderGambarUkurTembusanCreateSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException)
from common.generator import generate_code_month
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
    last_number = await generate_code_month(entity=CodeCounterEnum.OrderGambarUkur, with_commit=False, db_session=db_session)

    today = date.today()
    month = roman.toRoman(today.month)
    year = today.year

    sch.code = f"{last_number}/LA-PRA/GU/{month}/{year}"
        
    new_obj = await crud.order_gambar_ukur.create(obj_in=sch, created_by_id=current_worker.id, db_session=db_session, with_commit=False)

    for bidang in sch.bidangs:
        sch_bidang = OrderGambarUkurBidangCreateSch(order_gambar_ukur_id=new_obj.id, bidang_id=bidang)
        await crud.order_gambar_ukur_bidang.create(obj_in=sch_bidang, created_by_id=current_worker.id, db_session=db_session, with_commit=False)

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
    order_gu_bidang_will_removed = await crud.order_gambar_ukur_bidang.get_not_in_by_bidang_ids(list_ids=bidang_ids, order_ukur_id=id)
    if len(order_gu_bidang_will_removed) > 0 :
        await crud.order_gambar_ukur_bidang.remove_multiple_data(list_obj=order_gu_bidang_will_removed, db_session=db_session)
    
    for order_gu_bidang in sch.bidangs:
        gu_bidang = await crud.order_gambar_ukur_bidang.get_by_bidang_id_and_order_ukur_id(bidang_id=order_gu_bidang, order_ukur_id=id)
        if gu_bidang is None:
            new_order_gu_bidang = OrderGambarUkurBidang(bidang_id=order_gu_bidang, order_gambar_ukur_id=id)
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

    tipesurat = obj.tipe_surat.replace("_", " ")
    code = obj.code
    perihal = obj.perihal
    tujuansurat = obj.tujuan_surat

    tembusans = [tembusan.cc_name for tembusan in obj.tembusans]

    data_list = []
    no = 1
    nomor = ""
    for bidang in obj.bidangs:
        data = OrderGambarUkurBidangPdfSch(no=no,
                                           id_bidang=bidang.id_bidang,
                                           pemilik_name=bidang.pemilik_name,
                                           group=bidang.group,
                                           ptsk_name=bidang.ptsk_name,
                                           jenis_surat_name=bidang.jenis_surat_name,
                                           alashak=bidang.alashak,
                                           luas_surat="{:,.2f}".format(bidang.luas_surat)
                                           )
        no = no + 1
        data_list.append(data)

    
    # template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("order_gambar_ukur.html")

    render_template = template.render(tipesurat=tipesurat, 
                                      code=code,
                                      perihal=perihal,
                                      tujuansurat=tujuansurat,
                                      tembusans=tembusans,
                                      data=data_list, 
                                      tanggal=str(obj.created_at.date))

    try:
        doc = await PdfService().get_pdf(render_template)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed generate document")
    
    response = Response(doc, media_type='application/pdf')
    response.headers["Content-Disposition"] = f"attachment; filename={code}.pdf"
    return response

   