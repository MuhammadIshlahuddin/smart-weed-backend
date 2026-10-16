# Smart Weed Management - Backend Engine & API

Backend RESTful API untuk penelitian Proyek Akhir:  
**“Segmentasi Zona Penyemprotan Gulma Berbasis Clustering pada Sistem Smart weed management”**  
*Penulis:* Muhammad Ishlahuddin Albaihaqi (NRP 2223612222)  
*Program Studi:* STr-PJJ Teknik Telekomunikasi, PENS.

---

## Fitur Utama

1. **Dual-Engine K-Means Clustering ($K=3$):**
   - **Scratch Engine:** Implementasi murni rumus matematika Persamaan (3.1) - (3.4) pada Bab 3 proposal (Jarak Euclidean, Pembaruan Mean Centroid, Pengecekan Konvergensi $\epsilon$, dan Coverage).
   - **Scikit-learn Engine:** Implementasi pustaka standar untuk pembanding benchmarking waktu komputasi.
2. **Kalkulasi Coverage & Klasifikasi Zona SSWM:**
   - **Zona Rendah:** Coverage $< 20\%$ (Hijau) $\to$ *Routine Monitoring*.
   - **Zona Sedang:** Coverage $20\% - 40\%$ (Kuning) $\to$ *Targeted Control*.
   - **Zona Tinggi:** Coverage $> 40\%$ (Merah) $\to$ *Immediate Treatment*.
3. **Spatial & GIS Ready:**
   - Menghasilkan payload GeoJSON standar dengan Point layers, Poligon batas zona (Convex Hull), dan titik centroid.
4. **Benchmark Waktu Komputasi:**
   - Endpoint pengujian waktu komputasi ($t_{\text{komputasi}} = t_{\text{selesai}} - t_{\text{mulai}}$) untuk membuktikan performa rata-rata pada dataset 225 titik.
5. **RESTful Architecture & OpenAPI Docs:**
   - Dokumentasi Swagger UI interaktif otomatis di `/docs`.

---

## Struktur Folder

```text
├── app/
│   ├── api/v1/          # Endpoints (auth, weeds, clustering, spatial)
│   ├── core/            # Konfigurasi & security JWT
│   ├── db/              # SQLAlchemy session & base
│   ├── models/          # 4 Tabel Database (users, data_gulma, hasil_cluster, zona_gulma)
│   ├── schemas/         # Pydantic schema validation
│   ├── services/        # K-Means Scratch, Sklearn, Spatial GeoJSON, Timer
│   └── main.py          # FastAPI Entry Point
├── data/
│   └── sample_weeds_225.csv  # Dataset uji 225 titik sesuai proposal Bab 3
├── tests/               # Unit testing & API test
├── requirements.txt
└── README.md
```

---

## Panduan Menjalankan

### 1. Masuk ke Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Jalankan Server FastAPI (Uvicorn)
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 3. Akses Dokumentasi Swagger API
Buka peramban (browser) di alamat:  
👉 **http://127.0.0.1:8000/docs**
# smart-weed-backend
