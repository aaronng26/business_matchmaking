"""
Business Matchmaking — Ecosystem Mapping (OCBC)
==============================================
Pilih satu industri -> peta ekosistem Upstream / Middle Stream / Downstream
dengan PERAN KONKRET yang ditarik langsung dari Tabel Input-Output BPS 185
sektor, diurutkan dari nilai transaksi nyata. Jasa lintas-industri
(keuangan, hukum, sewa alat, dll) dipisah ke "Supporting Industries".

Jalankan:
    pip install -r requirements.txt
    streamlit run app.py
"""
from pathlib import Path
import streamlit as st
from ecosystem import EcosystemMapper

DATA = Path(__file__).parent
IO_FILE = DATA / "idn_IO_185_table_2020_BPS.xlsx"
ROLES_FILE = DATA / "tema_dan_kamus_peran.xlsx"

st.set_page_config(page_title="Business Matchmaking — Ecosystem Mapping",
                   page_icon="🔗", layout="wide")

# ---- warna 3 aliran ----
UP, MID, DOWN = "#B5D4F4", "#85B7EB", "#185FA5"
UP_T, MID_T, DOWN_T = "#0C447C", "#042C53", "#FFFFFF"

st.markdown("""
<style>
.stream-head{padding:9px;border-radius:8px;text-align:center;font-weight:600;margin-bottom:8px;}
.eco-card{background:#ffffff;border:1px solid #e6e6e6;border-radius:12px;padding:14px 16px;min-height:230px;}
.role{padding:6px 0;border-bottom:1px solid #f0f0f0;font-size:15px;}
.role:last-child{border-bottom:none;}
.share{color:#888;font-size:12px;display:inline-block;min-width:38px;}
.mid-box{background:#eef4fb;border:1px solid #B5D4F4;border-radius:12px;padding:22px 16px;text-align:center;min-height:230px;
         display:flex;flex-direction:column;align-items:center;justify-content:center;}
.supp{display:inline-block;background:#fff;border:1px solid #ddd;border-radius:16px;padding:5px 14px;margin:4px 4px 0 0;font-size:14px;}
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Memuat data ekosistem…")
def load():
    return EcosystemMapper(str(IO_FILE), str(ROLES_FILE))

em = load()

# ---------------- sidebar ----------------
st.sidebar.title("🔗 Business Matchmaking")
st.sidebar.caption("Ecosystem Mapping — berbasis Tabel Input-Output BPS 2020")
themes = em.themes()
default_i = themes.index("Construction") if "Construction" in themes else 0
theme = st.sidebar.selectbox("Pilih industri", themes, index=default_i)
top = st.sidebar.slider("Peran maksimal per kolom", 3, 12, 8)
min_share = st.sidebar.slider("Ambang minimal (%)", 0.0, 5.0, 1.0, 0.5) / 100
st.sidebar.markdown("---")
st.sidebar.caption("Upstream = pemasok · Downstream = pembeli · "
                   "Supporting = jasa lintas-industri (keuangan, hukum, sewa alat). "
                   "Peran & urutan berasal dari data transaksi antar-sektor, bukan disusun manual.")

m = em.map(theme, top=top, min_share=min_share)

# ---------------- header ----------------
st.title(f"Ekosistem industri: {m['tema']}")
st.caption(f"Sektor inti: {', '.join(m['anggota'][:6])}"
           + (" …" if len(m['anggota']) > 6 else ""))

# ---------------- 3 aliran ----------------
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f'<div class="stream-head" style="background:{UP};color:{UP_T};">UPSTREAM — pemasok</div>',
                unsafe_allow_html=True)
    rows = "".join(
        f'<div class="role"><span class="share">{r["share"]}%</span> {r["peran"]}</div>'
        for r in m["upstream"]) or '<div class="role" style="color:#999;">— tidak ada pemasok signifikan —</div>'
    st.markdown(f'<div class="eco-card">{rows}</div>', unsafe_allow_html=True)

with c2:
    st.markdown(f'<div class="stream-head" style="background:{MID};color:{MID_T};">MIDDLE STREAM — {m["tema"]}</div>',
                unsafe_allow_html=True)
    rows = "".join(
        f'<div class="role"><span class="share">{r["share"]}%</span> {r["peran"]}</div>'
        for r in m["midstream"]) or '<div class="role" style="color:#999;">— tidak ada sub-usaha di atas ambang —</div>'
    st.markdown(f'<div class="eco-card" style="background:#eef4fb;border-color:#B5D4F4;">{rows}</div>',
                unsafe_allow_html=True)

with c3:
    st.markdown(f'<div class="stream-head" style="background:{DOWN};color:{DOWN_T};">DOWNSTREAM — pembeli</div>',
                unsafe_allow_html=True)
    rows = "".join(
        f'<div class="role"><span class="share">{r["share"]}%</span> {r["peran"]}</div>'
        for r in m["downstream"])
    fd = m["ke_konsumen_akhir"]
    rows += (f'<div class="role" style="color:#185FA5;"><span class="share">{fd}%</span> '
             f'Pembeli / konsumen akhir</div>')
    st.markdown(f'<div class="eco-card">{rows}</div>', unsafe_allow_html=True)

# catatan downstream tipis
if len(m["downstream"]) == 0 and m["ke_konsumen_akhir"] > 60:
    st.info(f"ℹ️ {m['ke_konsumen_akhir']}% output {m['tema']} langsung ke pembeli akhir "
            "(investasi/konsumen), jadi pembeli antar-sektornya sedikit. "
            "Untuk industri seperti ini, sisi pembeli sebaiknya dilengkapi data nasabah manual.")

# ---------------- supporting ----------------
st.markdown("---")
st.subheader("Supporting industries")
st.caption("Jasa pendukung yang melintasi hampir semua industri.")
if m["supporting"]:
    chips = "".join(f'<span class="supp">{s}</span>' for s in m["supporting"])
    st.markdown(chips, unsafe_allow_html=True)
else:
    st.write("—")

st.markdown("---")
st.caption("Sumber: Tabel Input-Output Indonesia 2020 (BPS), 185 sektor. "
           "Peran konkret = penerjemahan sektor BPS; kekuatan = share nilai transaksi.")
