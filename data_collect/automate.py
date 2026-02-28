import subprocess
import time
import signal
import sys
import os
from datetime import datetime

DEVICE_COLLECTOR_PATH = "/data/local/tmp/psi_collector.sh"
DEVICE_OUTPUT_PATH = "/data/local/tmp/psi_data.csv"

LOCAL_COLLECTOR = "psi_collector.sh"
LOCAL_STRESS_SCRIPT = "stress_scenario.py"


def run(cmd, check=True, timeout=None):
    print(f"[CMD] {cmd}")
    return subprocess.run(cmd, shell=True, check=check, timeout=timeout)


def adb(cmd, check=True, timeout=10, retries=3):
    """执行 adb 命令，支持超时和重试"""
    for attempt in range(retries):
        try:
            return run(f"adb {cmd}", check=check, timeout=timeout)
        except subprocess.TimeoutExpired:
            print(f"[!] Timeout ({timeout}s), retry {attempt + 1}/{retries}...")
        except subprocess.CalledProcessError as e:
            if check and attempt < retries - 1:
                print(f"[!] Command failed, retry {attempt + 1}/{retries}...")
                time.sleep(1)
            else:
                raise
    # 最后一次尝试，不捕获异常
    return run(f"adb {cmd}", check=check, timeout=timeout)


def push_collector():
    adb(f"push {LOCAL_COLLECTOR} {DEVICE_COLLECTOR_PATH}")
    adb(f"shell chmod +x {DEVICE_COLLECTOR_PATH}")


def start_collector():
    print("[*] Starting collector in background...")
    adb(f'shell "nohup {DEVICE_COLLECTOR_PATH} > /dev/null 2>&1 & echo $! > /data/local/tmp/collector.pid"')


def stop_collector():
    print("[*] Stopping collector...")
    adb('shell "if [ -f /data/local/tmp/collector.pid ]; then kill $(cat /data/local/tmp/collector.pid); fi"')


def pull_data():
    print("[*] Pulling data...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    local_output = f"../data/psi_data_{timestamp}.csv"
    result = adb(f"pull {DEVICE_OUTPUT_PATH} {local_output}", check=False)
    if result.returncode != 0:
        print("[!] Warning: Failed to pull data file (may not exist)")
        return None
    return local_output


def clear_previous_data():
    adb(f"shell rm -f {DEVICE_OUTPUT_PATH}")
    adb(f"shell rm -f /data/local/tmp/collector.pid")


def drop_caches():
    print("[*] Dropping caches (optional)...")
    adb('shell su -c "sync"', check=False)
    adb('shell su -c "echo 3 > /proc/sys/vm/drop_caches"', check=False)


def run_stress():
    print("[*] Running stress scenario...")
    subprocess.run(["python", LOCAL_STRESS_SCRIPT])


def main():
    try:
        print("===== PSI Demo Automation =====")

        clear_previous_data()
        push_collector()
        drop_caches()

        start_collector()

        # 等待 2 秒确保采集启动
        time.sleep(2)

        run_stress()

    except KeyboardInterrupt:
        print("Interrupted by user.")

    finally:
        stop_collector()
        time.sleep(1)
        local_output = pull_data()
        print("===== DONE =====")
        if local_output:
            print(f"CSV saved to: {local_output}")
        else:
            print("No data file was generated.")


if __name__ == "__main__":
    main()
