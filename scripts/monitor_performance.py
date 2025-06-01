#!/usr/bin/env python3
"""
Скрипт для мониторинга производительности приложения.
"""

import time
import psutil
import requests
import json
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import argparse


class PerformanceMonitor:
    """Класс для мониторинга производительности."""
    
    def __init__(self, base_url: str = "http://localhost:8000", interval: int = 5):
        self.base_url = base_url
        self.interval = interval
        self.metrics = []
        self.running = False
        self.start_time = None
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Получить системные метрики."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_mb": memory.used / 1024 / 1024,
            "memory_available_mb": memory.available / 1024 / 1024,
            "disk_percent": disk.percent,
            "disk_used_gb": disk.used / 1024 / 1024 / 1024,
            "disk_free_gb": disk.free / 1024 / 1024 / 1024
        }
    
    def get_app_metrics(self) -> Dict[str, Any]:
        """Получить метрики приложения."""
        try:
            # Health check
            start_time = time.time()
            health_response = requests.get(f"{self.base_url}/health", timeout=5)
            health_time = time.time() - start_time
            
            # Status check
            start_time = time.time()
            status_response = requests.get(f"{self.base_url}/api/status", timeout=5)
            status_time = time.time() - start_time
            
            return {
                "health_status": health_response.status_code,
                "health_response_time": health_time,
                "status_status": status_response.status_code,
                "status_response_time": status_time,
                "app_available": True
            }
        except Exception as e:
            return {
                "health_status": None,
                "health_response_time": None,
                "status_status": None,
                "status_response_time": None,
                "app_available": False,
                "error": str(e)
            }
    
    def get_process_metrics(self, pid: int = None) -> Dict[str, Any]:
        """Получить метрики процесса приложения."""
        try:
            if pid:
                process = psutil.Process(pid)
            else:
                # Ищем процесс Python с main.py
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if 'python' in proc.info['name'].lower():
                            cmdline = proc.info['cmdline']
                            if cmdline and any('main.py' in arg for arg in cmdline):
                                processes.append(proc)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if not processes:
                    return {"error": "Application process not found"}
                
                process = processes[0]  # Берем первый найденный
            
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent()
            
            return {
                "pid": process.pid,
                "cpu_percent": cpu_percent,
                "memory_rss_mb": memory_info.rss / 1024 / 1024,
                "memory_vms_mb": memory_info.vms / 1024 / 1024,
                "num_threads": process.num_threads(),
                "num_fds": process.num_fds() if hasattr(process, 'num_fds') else None,
                "create_time": process.create_time()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def collect_metrics(self):
        """Собрать все метрики."""
        system_metrics = self.get_system_metrics()
        app_metrics = self.get_app_metrics()
        process_metrics = self.get_process_metrics()
        
        combined_metrics = {
            **system_metrics,
            "app": app_metrics,
            "process": process_metrics
        }
        
        self.metrics.append(combined_metrics)
        return combined_metrics
    
    def print_metrics(self, metrics: Dict[str, Any]):
        """Вывести метрики в консоль."""
        timestamp = metrics["timestamp"]
        cpu = metrics["cpu_percent"]
        memory = metrics["memory_percent"]
        
        app_status = "🟢" if metrics["app"]["app_available"] else "🔴"
        health_time = metrics["app"].get("health_response_time", 0)
        
        process_info = ""
        if "error" not in metrics["process"]:
            process_cpu = metrics["process"]["cpu_percent"]
            process_memory = metrics["process"]["memory_rss_mb"]
            process_info = f"Process: CPU {process_cpu:.1f}%, Memory {process_memory:.1f}MB"
        
        print(f"[{timestamp}] {app_status} System: CPU {cpu:.1f}%, Memory {memory:.1f}% | "
              f"Health: {health_time:.3f}s | {process_info}")
    
    def run_load_test(self, duration: int = 60, requests_per_second: int = 10):
        """Запустить нагрузочный тест."""
        print(f"🚀 Starting load test: {requests_per_second} RPS for {duration} seconds")
        
        def make_requests():
            """Функция для отправки запросов."""
            end_time = time.time() + duration
            request_count = 0
            
            while time.time() < end_time:
                try:
                    start = time.time()
                    response = requests.get(f"{self.base_url}/health", timeout=5)
                    response_time = time.time() - start
                    
                    request_count += 1
                    if request_count % 100 == 0:
                        print(f"Sent {request_count} requests, last response: {response_time:.3f}s")
                    
                    # Контролируем частоту запросов
                    sleep_time = (1.0 / requests_per_second) - response_time
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                        
                except Exception as e:
                    print(f"Request failed: {e}")
        
        # Запускаем нагрузочный тест в отдельном потоке
        load_thread = threading.Thread(target=make_requests)
        load_thread.daemon = True
        load_thread.start()
        
        return load_thread
    
    def start_monitoring(self, duration: int = None, load_test: bool = False):
        """Начать мониторинг."""
        self.running = True
        self.start_time = time.time()
        
        print(f"📊 Starting performance monitoring (interval: {self.interval}s)")
        if duration:
            print(f"Duration: {duration} seconds")
        
        load_thread = None
        if load_test:
            load_thread = self.run_load_test()
        
        try:
            while self.running:
                metrics = self.collect_metrics()
                self.print_metrics(metrics)
                
                if duration and (time.time() - self.start_time) >= duration:
                    break
                
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
        finally:
            self.running = False
            if load_thread and load_thread.is_alive():
                print("Waiting for load test to complete...")
                load_thread.join(timeout=5)
    
    def save_report(self, filename: str = None):
        """Сохранить отчет о производительности."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_report_{timestamp}.json"
        
        report = {
            "monitoring_start": self.start_time,
            "monitoring_duration": time.time() - self.start_time if self.start_time else 0,
            "total_measurements": len(self.metrics),
            "metrics": self.metrics
        }
        
        # Добавляем статистику
        if self.metrics:
            cpu_values = [m["cpu_percent"] for m in self.metrics]
            memory_values = [m["memory_percent"] for m in self.metrics]
            response_times = [m["app"]["health_response_time"] 
                            for m in self.metrics 
                            if m["app"]["health_response_time"] is not None]
            
            report["statistics"] = {
                "cpu": {
                    "min": min(cpu_values),
                    "max": max(cpu_values),
                    "avg": sum(cpu_values) / len(cpu_values)
                },
                "memory": {
                    "min": min(memory_values),
                    "max": max(memory_values),
                    "avg": sum(memory_values) / len(memory_values)
                },
                "response_time": {
                    "min": min(response_times) if response_times else None,
                    "max": max(response_times) if response_times else None,
                    "avg": sum(response_times) / len(response_times) if response_times else None
                }
            }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📄 Performance report saved to {filename}")
        return filename
    
    def generate_summary(self):
        """Сгенерировать краткий отчет."""
        if not self.metrics:
            print("No metrics collected")
            return
        
        print("\n📈 Performance Summary")
        print("=" * 50)
        
        # Системные метрики
        cpu_values = [m["cpu_percent"] for m in self.metrics]
        memory_values = [m["memory_percent"] for m in self.metrics]
        
        print(f"System CPU: min={min(cpu_values):.1f}%, max={max(cpu_values):.1f}%, "
              f"avg={sum(cpu_values)/len(cpu_values):.1f}%")
        print(f"System Memory: min={min(memory_values):.1f}%, max={max(memory_values):.1f}%, "
              f"avg={sum(memory_values)/len(memory_values):.1f}%")
        
        # Метрики приложения
        available_count = sum(1 for m in self.metrics if m["app"]["app_available"])
        availability = (available_count / len(self.metrics)) * 100
        print(f"Application Availability: {availability:.1f}% ({available_count}/{len(self.metrics)})")
        
        response_times = [m["app"]["health_response_time"] 
                         for m in self.metrics 
                         if m["app"]["health_response_time"] is not None]
        
        if response_times:
            print(f"Response Time: min={min(response_times):.3f}s, max={max(response_times):.3f}s, "
                  f"avg={sum(response_times)/len(response_times):.3f}s")


def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(description="Performance monitoring tool")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="Base URL of the application")
    parser.add_argument("--interval", type=int, default=5, 
                       help="Monitoring interval in seconds")
    parser.add_argument("--duration", type=int, 
                       help="Monitoring duration in seconds")
    parser.add_argument("--load-test", action="store_true", 
                       help="Run load test during monitoring")
    parser.add_argument("--output", help="Output file for the report")
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor(base_url=args.url, interval=args.interval)
    
    try:
        monitor.start_monitoring(duration=args.duration, load_test=args.load_test)
    finally:
        monitor.generate_summary()
        if args.output:
            monitor.save_report(args.output)
        else:
            monitor.save_report()


if __name__ == "__main__":
    main()