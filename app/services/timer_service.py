import time
from typing import Callable, Any, Tuple

class TimerService:
    @staticmethod
    def measure_execution_time(func: Callable, *args, **kwargs) -> Tuple[Any, float]:
        """
        Mengukur waktu eksekusi fungsi menggunakan Persamaan (3.5):
        t_komputasi = t_selesai - t_mulai
        Mengembalikan: (hasil_fungsi, durasi_milidetik)
        """
        t_mulai = time.perf_counter()
        result = func(*args, **kwargs)
        t_selesai = time.perf_counter()
        
        t_komputasi_detik = t_selesai - t_mulai
        t_komputasi_ms = round(t_komputasi_detik * 1000, 3)
        return result, t_komputasi_ms
