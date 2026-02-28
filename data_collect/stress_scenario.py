import subprocess
import time
import random

APPS = [
    "com.tencent.mm",
    "com.taobao.taobao",
    "com.ss.android.ugc.aweme",
    "com.jingdong.app.mall",
    "com.autonavi.minimap",
    "tv.danmaku.bili",
    "com.eg.android.AlipayGphone",
    "com.xingin.xhs"
]


def adb(cmd, timeout=10, retries=3):
    """执行 adb shell 命令，支持超时和重试"""
    for attempt in range(retries):
        try:
            return subprocess.run(
                ["adb", "shell"] + cmd.split(),
                timeout=timeout,
                check=False
            )
        except subprocess.TimeoutExpired:
            print(f"[!] Timeout ({timeout}s), retry {attempt + 1}/{retries}...")
    # 最后一次尝试
    return subprocess.run(["adb", "shell"] + cmd.split(), timeout=timeout, check=False)


def launch_app(pkg):
    print(f"Launching {pkg}")
    adb(f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1")


def swipe_up():
    """上滑屏幕（刷抖音）"""
    adb("input swipe 540 1500 540 500 300")


def switch_to(pkg):
    adb(f"am start -n $(cmd package resolve-activity --brief {pkg} | tail -n 1)")


def phase1():
    print("=== Phase 1: Cold Start Accumulation ===")
    for pkg in APPS:
        launch_app(pkg)
        time.sleep(15)


def phase2():
    print("=== Phase 2: Rapid Switching ===")
    for _ in range(180):  # 15 minutes
        pkg = random.choice(APPS)
        launch_app(pkg)
        time.sleep(5)


def phase3():
    print("=== Phase 3: Video + Background Switching ===")
    launch_app("com.ss.android.ugc.aweme")
    for i in range(120):  # 20 minutes
        # 每隔几次切换 APP，其余时间刷抖音
        if i % 4 == 0:
            pkg = random.choice(APPS)
            launch_app(pkg)
            time.sleep(5)
            # 切回抖音
            launch_app("com.ss.android.ugc.aweme")
            time.sleep(5)
        else:
            # 刷抖音，上滑切换视频
            swipe_up()
            time.sleep(8)


if __name__ == "__main__":
    phase1()
    phase2()
    phase3()
