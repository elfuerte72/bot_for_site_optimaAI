"""
Тесты для мониторинга использования памяти.
"""

import gc
import psutil
import time
from memory_profiler import profile
import pytest


class MemoryMonitor:
    """Класс для мониторинга использования памяти."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = self.get_memory_usage()
    
    def get_memory_usage(self):
        """Получить текущее использование памяти в MB."""
        return self.process.memory_info().rss / 1024 / 1024
    
    def get_memory_percent(self):
        """Получить процент использования памяти."""
        return self.process.memory_percent()
    
    def memory_diff(self):
        """Получить разницу в использовании памяти с начального момента."""
        return self.get_memory_usage() - self.initial_memory


@profile
def test_basic_memory_usage():
    """Базовый тест использования памяти."""
    monitor = MemoryMonitor()
    
    # Создаем некоторые объекты
    data = []
    for i in range(1000):
        data.append(f"Test string {i}" * 10)
    
    memory_after_creation = monitor.get_memory_usage()
    print(f"Memory after data creation: {memory_after_creation:.2f} MB")
    
    # Очищаем данные
    del data
    gc.collect()
    
    memory_after_cleanup = monitor.get_memory_usage()
    print(f"Memory after cleanup: {memory_after_cleanup:.2f} MB")
    
    # Проверяем, что память освободилась
    memory_diff = memory_after_creation - memory_after_cleanup
    print(f"Memory freed: {memory_diff:.2f} MB")
    
    assert memory_diff > 0, "Memory should be freed after cleanup"


@profile
def test_large_data_processing():
    """Тест обработки больших объемов данных."""
    monitor = MemoryMonitor()
    
    # Создаем большой объем данных
    large_data = []
    for i in range(10000):
        large_data.append({
            "id": i,
            "data": "x" * 1000,
            "metadata": {
                "timestamp": time.time(),
                "processed": False
            }
        })
    
    memory_peak = monitor.get_memory_usage()
    print(f"Peak memory usage: {memory_peak:.2f} MB")
    
    # Обрабатываем данные
    processed_count = 0
    for item in large_data:
        item["metadata"]["processed"] = True
        processed_count += 1
        
        # Проверяем память каждые 1000 элементов
        if processed_count % 1000 == 0:
            current_memory = monitor.get_memory_usage()
            print(f"Memory at {processed_count} items: {current_memory:.2f} MB")
    
    # Очищаем данные
    del large_data
    gc.collect()
    
    final_memory = monitor.get_memory_usage()
    print(f"Final memory usage: {final_memory:.2f} MB")
    
    # Проверяем, что память не выросла критично
    memory_growth = final_memory - monitor.initial_memory
    assert memory_growth < 50, f"Memory growth too high: {memory_growth:.2f} MB"


@profile
def test_memory_leak_simulation():
    """Тест на обнаружение утечек памяти."""
    monitor = MemoryMonitor()
    
    # Симулируем потенциальную утечку памяти
    global_cache = []
    
    for iteration in range(5):
        # Создаем данные в каждой итерации
        iteration_data = []
        for i in range(1000):
            data = {
                "iteration": iteration,
                "index": i,
                "payload": "data" * 100
            }
            iteration_data.append(data)
            
            # Симулируем "случайное" сохранение в глобальном кеше
            if i % 100 == 0:
                global_cache.append(data)
        
        # Очищаем локальные данные
        del iteration_data
        gc.collect()
        
        current_memory = monitor.get_memory_usage()
        print(f"Memory after iteration {iteration}: {current_memory:.2f} MB")
    
    # Очищаем глобальный кеш
    global_cache.clear()
    gc.collect()
    
    final_memory = monitor.get_memory_usage()
    print(f"Memory after cache cleanup: {final_memory:.2f} MB")


@profile
def test_concurrent_memory_usage():
    """Тест использования памяти при конкурентной обработке."""
    import threading
    import queue
    
    monitor = MemoryMonitor()
    result_queue = queue.Queue()
    
    def worker(worker_id, data_size):
        """Рабочая функция для потока."""
        worker_data = []
        for i in range(data_size):
            worker_data.append(f"Worker {worker_id} data {i}")
        
        # Симулируем обработку
        processed = [item.upper() for item in worker_data]
        result_queue.put(len(processed))
        
        del worker_data, processed
    
    # Запускаем несколько потоков
    threads = []
    for i in range(5):
        thread = threading.Thread(target=worker, args=(i, 1000))
        threads.append(thread)
        thread.start()
    
    # Ждем завершения всех потоков
    for thread in threads:
        thread.join()
    
    # Собираем результаты
    results = []
    while not result_queue.empty():
        results.append(result_queue.get())
    
    memory_after_threads = monitor.get_memory_usage()
    print(f"Memory after concurrent processing: {memory_after_threads:.2f} MB")
    print(f"Processed items: {sum(results)}")
    
    gc.collect()
    final_memory = monitor.get_memory_usage()
    print(f"Final memory: {final_memory:.2f} MB")


def test_memory_benchmarks():
    """Бенчмарки производительности памяти."""
    import pytest
    
    monitor = MemoryMonitor()
    
    @pytest.mark.benchmark(group="memory")
    def test_list_creation(benchmark):
        """Бенчмарк создания списков."""
        def create_list():
            return [i for i in range(10000)]
        
        result = benchmark(create_list)
        assert len(result) == 10000
    
    @pytest.mark.benchmark(group="memory")
    def test_dict_creation(benchmark):
        """Бенчмарк создания словарей."""
        def create_dict():
            return {i: f"value_{i}" for i in range(10000)}
        
        result = benchmark(create_dict)
        assert len(result) == 10000
    
    @pytest.mark.benchmark(group="memory")
    def test_string_operations(benchmark):
        """Бенчмарк операций со строками."""
        def string_ops():
            text = "test string"
            for _ in range(1000):
                text = text.upper().lower().strip()
            return text
        
        result = benchmark(string_ops)
        assert result == "test string"


if __name__ == "__main__":
    print("Running memory usage tests...")
    
    print("\n=== Basic Memory Usage ===")
    test_basic_memory_usage()
    
    print("\n=== Large Data Processing ===")
    test_large_data_processing()
    
    print("\n=== Memory Leak Simulation ===")
    test_memory_leak_simulation()
    
    print("\n=== Concurrent Memory Usage ===")
    test_concurrent_memory_usage()
    
    print("\nMemory tests completed!")