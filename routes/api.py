from fastapi import APIRouter
from routes.endpoints import (bidang, desa, planing, project, ptsk, section, jenis_lahan, 
                              draft, gps, skpt, worker, role, dokumen, bundle_hd, bundle_dt,
                              checklist_dokumen, marketing, pemilik, kjb_hd)

api_router = APIRouter()
api_router.include_router(bidang.router, prefix="/bidang", tags=["bidang"])
# api_router.include_router(bidangoverlap.router, prefix="/bidangoverlap", tags=["bidangoverlap"])
api_router.include_router(desa.router, prefix="/desa", tags=["desa"])
api_router.include_router(planing.router, prefix="/planing", tags=["planing"])
api_router.include_router(project.router, prefix="/project", tags=["project"])
api_router.include_router(ptsk.router, prefix="/ptsk", tags=["ptsk"])
api_router.include_router(skpt.router, prefix="/skpt", tags=["skpt"])
api_router.include_router(section.router, prefix="/section", tags=["section"])
api_router.include_router(worker.router, prefix="/worker", tags=["worker"])
api_router.include_router(role.router, prefix="/role", tags=["role"])
api_router.include_router(dokumen.router, prefix="/dokumen", tags=["dokumen"])
api_router.include_router(checklist_dokumen.router, prefix="/cheklistdokumen", tags=["checklistdokumen"])
api_router.include_router(bundle_hd.router, prefix="/bundlehd", tags=["bundlehd"])
api_router.include_router(bundle_dt.router, prefix="/bundledt", tags=["bundledt"])
api_router.include_router(kjb_hd.router, prefix="/kjbhd", tags=["kjbhd"])


api_router.include_router(jenis_lahan.router, prefix="/jenislahan", tags=["jenislahan"])
api_router.include_router(draft.router, prefix="/draft", tags=["draft"])
api_router.include_router(gps.router, prefix="/gps", tags=["gps"])
api_router.include_router(pemilik.router_pemilik, prefix="/pemilik", tags=["pemilik"])
api_router.include_router(pemilik.router_kontak, prefix="/kontak", tags=["kontak"])
api_router.include_router(pemilik.router_rekening, prefix="/rekening", tags=["rekening"])
api_router.include_router(marketing.manager, prefix="/manager", tags=["manager"])
api_router.include_router(marketing.sales, prefix="/sales", tags=["sales"])
