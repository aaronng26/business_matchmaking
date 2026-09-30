# Business Matchmaking — Ecosystem Mapping

Peta ekosistem per industri (upstream / middle stream / downstream + supporting),
berbasis Tabel Input-Output BPS 2020. Untuk keperluan business matchmaking OCBC.

## Struktur
```
business_matchmaking/
├── app.py                        # dashboard Streamlit
├── ecosystem.py                  # mesin: tarik peran dari 185 sektor
├── requirements.txt
├── idn_IO_185_table_2020_BPS.xlsx
└── tema_dan_kamus_peran.xlsx     # definisi 12 tema + kamus peran (bisa diedit)
```

## Menjalankan
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Cara kerja
1. Pilih satu industri (12 tema).
2. `ecosystem.py` membaca 185 sektor BPS, menghitung pemasok (upstream) & pembeli
   (downstream) industri itu dari matriks transaksi, lalu menerjemahkannya jadi
   peran bisnis konkret (mis. "Pabrik semen", "Arsitek & insinyur").
3. Jasa lintas-industri (bank, hukum, sewa alat) dipisah ke Supporting Industries.

Peran & urutannya berasal dari data transaksi nyata, bukan disusun manual.

## Edit
Ubah `tema_dan_kamus_peran.xlsx` (nama peran, tag Inti/Pendukung, atau anggota tema),
lalu jalankan ulang — dashboard otomatis menyesuaikan.
