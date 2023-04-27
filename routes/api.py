from fastapi import APIRouter
from routes.endpoints import (bidang, bidangoverlap, desa, planing, project, 
                              ptsk, rincik, section, jenis_lahan, draft, gps, skpt)

api_router = APIRouter()
api_router.include_router(bidang.router, prefix="/bidang", tags=["bidang"])
api_router.include_router(bidangoverlap.router, prefix="/bidangoverlap", tags=["bidangoverlap"])
api_router.include_router(desa.router, prefix="/desa", tags=["desa"])
api_router.include_router(planing.router, prefix="/planing", tags=["planing"])
api_router.include_router(project.router, prefix="/project", tags=["project"])
api_router.include_router(ptsk.router, prefix="/ptsk", tags=["ptsk"])
api_router.include_router(skpt.router, prefix="/skpt", tags=["skpt"])
api_router.include_router(rincik.router, prefix="/rincik", tags=["rincik"])
api_router.include_router(section.router, prefix="/section", tags=["section"])
api_router.include_router(jenis_lahan.router, prefix="/jenislahan", tags=["jenislahan"])
api_router.include_router(draft.router, prefix="/draft", tags=["draft"])
api_router.include_router(gps.router, prefix="/gps", tags=["gps"])