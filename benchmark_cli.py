import pandas as pd
from app.services.kmeans_scratch import KMeansScratch
from app.services.kmeans_sklearn import KMeansSklearn
from app.services.timer_service import TimerService

def main():
    df = pd.read_csv('data/sample_weeds_225.csv')
    points = list(zip(df['latitude'], df['longitude']))

    print(f"Dataset berhasil dimuat: {len(points)} titik pengamatan.")

    scratch_times = []
    for i in range(5):
        model = KMeansScratch(k=3, random_state=42 + i)
        res_scratch, t_ms = TimerService.measure_execution_time(model.fit, points)
        scratch_times.append(t_ms)

    sklearn_times = []
    for i in range(5):
        model = KMeansSklearn(k=3, random_state=42 + i)
        res_sklearn, t_ms = TimerService.measure_execution_time(model.fit, points)
        sklearn_times.append(t_ms)

    print("\n================ HASIL PENGUJIAN WAKTU KOMPUTASI (BAB 3.3.6) ================")
    for i in range(5):
        print(f"Pengujian ke-{i+1} : Scratch = {scratch_times[i]:.2f} ms  |  Sklearn = {sklearn_times[i]:.2f} ms")
    
    avg_scratch = sum(scratch_times) / 5
    avg_sklearn = sum(sklearn_times) / 5
    print("-----------------------------------------------------------------------------")
    print(f"Rata-rata Scratch Engine : {avg_scratch:.2f} ms")
    print(f"Rata-rata Sklearn Engine : {avg_sklearn:.2f} ms")
    print("=============================================================================")

    print("\n================ HASIL SEGMENTASI ZONA (SESUAI TABEL 3.8 & 3.9) =============")
    for s in res_scratch['summaries']:
        print(f"Cluster {s['cluster']} [{s['zone'].upper()}]: {s['points_count']} Titik | Coverage: {s['coverage']}%")
        print(f"  Rekomendasi: {s['recommendation']}")

if __name__ == "__main__":
    main()
