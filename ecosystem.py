"""
ecosystem.py — Business Matchmaking Ecosystem Mapper (gaya OCBC)
================================================================
Pilih satu industri (tema) -> tarik peran UPSTREAM & DOWNSTREAM konkret
langsung dari Tabel Input-Output BPS 185 sektor, diurutkan dari nilai
transaksi nyata. Peran "Pendukung" (keuangan, hukum, sewa alat, dll)
dipisah ke kotak Supporting Industries.

Sumber peran = 185 sektor asli (bukan dikarang). Sumber urutan = data I-O.
Dependensi: numpy, pandas, openpyxl
"""
from __future__ import annotations
import numpy as np, pandas as pd, openpyxl


class EcosystemMapper:
    def __init__(self, io_path, roles_path,
                 io_sheet="BCD 185",
                 theme_sheet="12 Tema Fokus",
                 role_sheet="Kamus Peran (185)"):
        self._load_io(io_path, io_sheet)
        self._load_roles(roles_path, theme_sheet, role_sheet)

    # ---- 185x185 matrix + margins ----
    def _load_io(self, path, sheet):
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        g = list(wb[sheet].iter_rows(values_only=True)); wb.close()
        def val(r,c):
            v=g[r-1][c-1]; return 0.0 if v is None else float(v)
        def as_int(v):
            if isinstance(v,(int,np.integer)): return int(v)
            if isinstance(v,float) and v.is_integer(): return int(v)
            if isinstance(v,str) and v.strip().isdigit(): return int(v.strip())
            return None
        rows=[]; e=1
        for i in range(len(g)):
            if as_int(g[i][1])==e and g[i][2] is not None: rows.append(i+1); e+=1
        hdr=g[3]; cols=[]; e=1
        for c in range(len(hdr)):
            if as_int(hdr[c])==e: cols.append(c+1); e+=1
        N=len(rows); self.N=N
        self.Z=np.array([[val(rows[i],cols[j]) for j in range(N)] for i in range(N)])
        def frow(code):
            for i in range(len(g)):
                if as_int(g[i][1])==code: return i+1
        def fcol(code):
            for c in range(len(hdr)):
                if as_int(hdr[c])==code: return c+1
        rt=frow(2100); cfd=fcol(3090)
        self.x=np.array([val(rt,cols[j]) for j in range(N)])
        self.fd=np.array([val(rows[i],cfd) for i in range(N)])

    # ---- themes + role dictionary ----
    def _load_roles(self, path, tsheet, rsheet):
        wb=openpyxl.load_workbook(path, read_only=True, data_only=True)
        # themes
        self.theme_codes={}
        for r in list(wb[tsheet].iter_rows(min_row=2, values_only=True)):
            if r[0] is None: continue
            codes=[int(x) for x in str(r[1]).replace(" ","").split(",") if x]
            self.theme_codes[str(r[0]).strip()]=codes
        # roles
        self.role_name={}; self.role_type={}
        for r in list(wb[rsheet].iter_rows(min_row=2, values_only=True)):
            if r[0] is None: continue
            code=int(r[0]); self.role_name[code]=str(r[2]); self.role_type[code]=str(r[3])
        wb.close()

    def themes(self):
        return list(self.theme_codes)

    # ---- core: build ecosystem map for a theme ----
    def map(self, theme, top=8, min_share=0.01):
        if theme not in self.theme_codes:
            raise ValueError(f"tema '{theme}' tak ada. Pilihan: {self.themes()}")
        T=[c-1 for c in self.theme_codes[theme]]         # 0-based indices
        inT=set(T)
        Z=self.Z

        # --- UPSTREAM: pemasok ke tema (kolom) ---
        supply=Z[:, T].sum(1)                            # per sektor i
        out_idx=[i for i in range(self.N) if i not in inT]
        tot_up=sum(supply[i] for i in out_idx) or 1
        up=[(supply[i]/tot_up, supply[i], i) for i in out_idx if supply[i]/tot_up>=min_share]
        up.sort(reverse=True)

        # --- DOWNSTREAM: pembeli output tema (baris) ---
        buy=Z[T, :].sum(0)                               # per sektor j
        tot_out=self.x[T].sum() or 1
        fd_share=self.fd[T].sum()/tot_out
        dn=[(buy[j]/tot_out, buy[j], j) for j in out_idx if buy[j]/tot_out>=min_share]
        dn.sort(reverse=True)

        # --- MIDSTREAM: jenis usaha di industri ini, dibobot ukuran output ---
        tot_theme = self.x[list(inT)].sum() or 1
        mids = sorted(((self.x[i]/tot_theme, self.x[i], i) for i in inT), reverse=True)
        mid_list = [(self.role_name[i+1], s, v) for s, v, i in mids if s >= min_share]
        if not mid_list and mids:                    # jamin minimal 1 muncul
            s, v, i = mids[0]; mid_list = [(self.role_name[i+1], s, v)]
        mid_list = mid_list[:top]

        def split(items):
            inti=[(self.role_name[i+1],s,v) for s,v,i in items if self.role_type[i+1]=="Inti"]
            pend=[(self.role_name[i+1],s,v) for s,v,i in items if self.role_type[i+1]=="Pendukung"]
            return inti[:top], pend
        up_inti,up_pend=split(up)
        dn_inti,dn_pend=split(dn)
        # supporting = gabungan pendukung upstream+downstream (unik, terkuat)
        supp={}
        for nm,s,v in up_pend+dn_pend: supp[nm]=max(supp.get(nm,0),s)
        supporting=sorted(supp.items(), key=lambda x:-x[1])

        return dict(
            tema=theme,
            anggota=[self.role_name[c] for c in self.theme_codes[theme]],
            midstream=[{"peran":n,"share":round(s*100,1),"rp":round(v)} for n,s,v in mid_list],
            upstream=[{"peran":n,"share":round(s*100,1),"rp":round(v)} for n,s,v in up_inti],
            downstream=[{"peran":n,"share":round(s*100,1),"rp":round(v)} for n,s,v in dn_inti],
            ke_konsumen_akhir=round(fd_share*100,1),
            supporting=[n for n,_ in supporting],
        )


if __name__ == "__main__":
    em=EcosystemMapper("idn_IO_185_table_2020_BPS.xlsx","tema_dan_kamus_peran.xlsx")
    for tema in ["Construction","F&B"]:
        m=em.map(tema)
        print("="*66)
        print(f"ECOSYSTEM MAP — {m['tema']}   (ke konsumen akhir: {m['ke_konsumen_akhir']}%)")
        print("\n  UPSTREAM (pemasok):")
        for r in m["upstream"]: print(f"     {r['share']:5.1f}%  {r['peran']}")
        print("\n  DOWNSTREAM (pembeli):")
        for r in m["downstream"]: print(f"     {r['share']:5.1f}%  {r['peran']}")
        print("\n  SUPPORTING INDUSTRIES:")
        print("     " + " · ".join(m["supporting"]))
        print()
