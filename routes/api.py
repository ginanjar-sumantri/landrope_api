from fastapi import APIRouter
from routes.endpoints import (bidang, bidang_overlap, desa, kjb_termin, planing, project, ptsk, section, jenis_lahan, jenis_surat, harga_standard,
                              draft, draft_detail, draft_report_map, gps, skpt, skpt_dt, worker, role, dokumen, kategori_dokumen, bundle_hd, bundle_dt,
                              checklist_dokumen, checklist_kelengkapan_dokumen_hd,checklist_kelengkapan_dokumen_dt, marketing, pemilik, beban_biaya,
                              kategori, kategori_sub, kategori_proyek, giro, spk, tahap, 
                              kjb_hd, kjb_termin, kjb_harga, kjb_dt, kjb_rekening, kjb_beban_biaya, kjb_penjual,
                              tanda_terima_notaris_hd, tanda_terima_notaris_dt, notaris, request_peta_lokasi, hasil_peta_lokasi, 
                              hasil_peta_lokasi_detail, import_log, order_gambar_ukur,
                              report_map)

api_router = APIRouter()
api_router.include_router(bidang.router, prefix="/bidang", tags=["bidang"])
api_router.include_router(bidang_overlap.router, prefix="/bidang_overlap", tags=["bidang_overlap"])
api_router.include_router(desa.router, prefix="/desa", tags=["desa"])
api_router.include_router(planing.router, prefix="/planing", tags=["planing"])
api_router.include_router(project.router, prefix="/project", tags=["project"])
api_router.include_router(draft.router, prefix="/draft", tags=["draft"])
api_router.include_router(draft_detail.router, prefix="/draft_detail", tags=["draft_detail"])
api_router.include_router(draft_report_map.router, prefix="/draft_report_map", tags=["draft_report_map"])
api_router.include_router(gps.router, prefix="/gps", tags=["gps"])
api_router.include_router(ptsk.router, prefix="/ptsk", tags=["ptsk"])
api_router.include_router(skpt.router, prefix="/skpt", tags=["skpt"])
api_router.include_router(skpt_dt.router, prefix="/skptdt", tags=["skptdt"])
api_router.include_router(section.router, prefix="/section", tags=["section"])
api_router.include_router(worker.router, prefix="/worker", tags=["worker"])
api_router.include_router(role.router, prefix="/role", tags=["role"])

api_router.include_router(dokumen.router, prefix="/dokumen", tags=["dokumen"])
api_router.include_router(kategori_dokumen.router, prefix="/kategori_dokumen", tags=["kategori_dokumen"])
api_router.include_router(checklist_dokumen.router, prefix="/cheklistdokumen", tags=["checklistdokumen"])
api_router.include_router(checklist_kelengkapan_dokumen_hd.router, prefix="/checklist_kelengkapan_dokumen_hd", tags=["checklist_kelengkapan_dokumen_hd"])
api_router.include_router(checklist_kelengkapan_dokumen_dt.router, prefix="/checklist_kelengkapan_dokumen_dt", tags=["checklist_kelengkapan_dokumen_dt"])
api_router.include_router(bundle_hd.router, prefix="/bundlehd", tags=["bundlehd"])
api_router.include_router(bundle_dt.router, prefix="/bundledt", tags=["bundledt"])

api_router.include_router(kjb_hd.router, prefix="/kjbhd", tags=["kjbhd"])
api_router.include_router(kjb_dt.router, prefix="/kjbdt", tags=["kjbdt"])
api_router.include_router(kjb_rekening.router, prefix="/kjbrekening", tags=["kjbrekening"])
api_router.include_router(kjb_harga.router, prefix="/kjbharga", tags=["kjbharga"])
api_router.include_router(kjb_termin.router, prefix="/kjbtermin", tags=["kjbtermin"])
api_router.include_router(kjb_beban_biaya.router, prefix="/kjbbebanbiaya", tags=["kjbbebanbiaya"])
api_router.include_router(kjb_penjual.router, prefix="/kjbpenjual", tags=["kjbpenjual"])
api_router.include_router(tanda_terima_notaris_hd.router, prefix="/tandaterimanotaris_hd", tags=["tandaterimanotaris_hd"])
api_router.include_router(tanda_terima_notaris_dt.router, prefix="/tandaterimanotaris_dt", tags=["tandaterimanotaris_dt"])
api_router.include_router(request_peta_lokasi.router, prefix="/requestpetalokasi", tags=["requestpetalokasi"])
api_router.include_router(hasil_peta_lokasi.router, prefix="/hasilpetalokasi", tags=["hasilpetalokasi"])
api_router.include_router(hasil_peta_lokasi_detail.router, prefix="/hasilpetalokasidetail", tags=["hasilpetalokasidetail"])
api_router.include_router(order_gambar_ukur.router, prefix="/ordergambarukur", tags=["ordergambarukur"])
api_router.include_router(spk.router, prefix="/spk", tags=["spk"])
api_router.include_router(tahap.router, prefix="/tahap", tags=["tahap"])

api_router.include_router(notaris.router, prefix="/notaris", tags=["notaris"])
api_router.include_router(jenis_lahan.router, prefix="/jenislahan", tags=["jenislahan"])
api_router.include_router(jenis_surat.router, prefix="/jenissurat", tags=["jenissurat"])
api_router.include_router(pemilik.router_pemilik, prefix="/pemilik", tags=["pemilik"])
api_router.include_router(pemilik.router_kontak, prefix="/kontak", tags=["kontak"])
api_router.include_router(pemilik.router_rekening, prefix="/rekening", tags=["rekening"])
api_router.include_router(marketing.manager, prefix="/manager", tags=["manager"])
api_router.include_router(marketing.sales, prefix="/sales", tags=["sales"])
api_router.include_router(beban_biaya.router, prefix="/bebanbiaya", tags=["bebanbiaya"])
api_router.include_router(harga_standard.router, prefix="/hargastandard", tags=["hargastandard"])
api_router.include_router(kategori.router, prefix="/kategori", tags=["kategori"])
api_router.include_router(kategori_sub.router, prefix="/kategorisub", tags=["kategorisub"])
api_router.include_router(kategori_proyek.router, prefix="/kategoriproyek", tags=["kategoriproyek"])
api_router.include_router(giro.router, prefix="/giro", tags=["giro"])

api_router.include_router(import_log.router, prefix="/importlog", tags=["importlog"])

api_router.include_router(report_map.router, prefix="/report_map", tags=["report_map"])

