"""快速冒烟测试：验证 collector 能正常采集数据"""
import subprocess
import time


def run(cmd):
    print(f"> {cmd}")
    return subprocess.run(cmd, shell=True, check=False, timeout=15)


# 1. 清理
run("adb shell rm -f /data/local/tmp/psi_data.csv /data/local/tmp/collector.pid /data/local/tmp/current_phase.txt")

# 2. 推送 + 去 \r + chmod
run("adb push psi_collector_with_phase.sh /data/local/tmp/psi_collector.sh")
run("""adb shell "sed -i 's/\\r$//' /data/local/tmp/psi_collector.sh" """)
run("adb shell chmod +x /data/local/tmp/psi_collector.sh")

# 3. 验证 shebang
print("\n=== Shebang check ===")
run("""adb shell "head -1 /data/local/tmp/psi_collector.sh | od -c | head -1" """)

# 4. 启动 collector
run("""adb shell "nohup /data/local/tmp/psi_collector.sh > /dev/null 2>&1 & echo $! > /data/local/tmp/collector.pid" """)
time.sleep(1)

# 5. 检查 PID 和进程
print("\n=== PID ===")
run("adb shell cat /data/local/tmp/collector.pid")
run("""adb shell "ps -p $(cat /data/local/tmp/collector.pid) 2>/dev/null || echo PROCESS NOT RUNNING" """)

# 6. 等 5 秒
print("\nWaiting 5s for samples...")
time.sleep(5)

# 7. 检查 CSV
print("\n=== CSV check ===")
run("adb shell wc -l /data/local/tmp/psi_data.csv")
run("adb shell head -3 /data/local/tmp/psi_data.csv")

# 8. 停止
run("""adb shell "kill $(cat /data/local/tmp/collector.pid) 2>/dev/null" """)
print("\nDone! If you see ~10 lines and valid CSV above, collector is working.")
