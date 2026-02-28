import subprocess
import time
import random

DOUYIN = "com.ss.android.ugc.aweme"

# 手机上已安装的全部应用（不含抖音）
ALL_APPS = [
    "com.tencent.mm",           # 微信
    "com.tencent.mobileqq",    # QQ
    "com.sina.weibo",           # 微博
    "com.taobao.taobao",        # 淘宝
    "com.jingdong.app.mall",    # 京东
    "com.xunmeng.pinduoduo",   # 拼多多
    "com.smile.gifmaker",       # 快手
    "tv.danmaku.bili",          # B站
    "com.tencent.qqlive",      # 腾讯视频
    "com.youku.phone",         # 优酷
    "com.ss.android.article.news",  # 今日头条
    "com.baidu.searchbox",     # 百度
    "com.xingin.xhs",           # 小红书
    "com.eg.android.AlipayGphone",  # 支付宝
    "com.sankuai.meituan",     # 美团
    "com.autonavi.minimap",     # 高德地图
    "com.baidu.BaiduMap",      # 百度地图
    "com.netease.cloudmusic",   # 网易云音乐
    "com.tencent.qqmusic",     # QQ音乐
]

# 运行时随机挑选 10 个冷启动
COLD_START_COUNT = 10
BACKGROUND_APPS = random.sample(ALL_APPS, COLD_START_COUNT)

TOTAL_BROWSE_TIME = 10 * 60   # 总共刷 10 分钟（秒）
DOUYIN_CYCLE_TIME = 60         # 每轮刷抖音 1 分钟
SWIPE_INTERVAL = (3, 6)        # 随机 3-6 秒刷一次

PHASE_FILE = "/data/local/tmp/current_phase.txt"


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
    return subprocess.run(["adb", "shell"] + cmd.split(), timeout=timeout, check=False)


def set_phase(phase_name):
    """写入当前阶段标签到设备，供 collector 记录"""
    print(f"  [phase] {phase_name}")
    subprocess.run(
        ["adb", "shell", f"echo {phase_name} > {PHASE_FILE}"],
        timeout=5, check=False
    )


def launch_app(pkg):
    print(f"  Launching {pkg}")
    adb(f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1")


def swipe_up():
    """上滑屏幕（模拟刷短视频 / Feed流）"""
    adb("input swipe 540 1500 540 500 300")


def phase_cold_start():
    """Phase 1: 冷启动 10 个非抖音应用"""
    print("=== Phase 1: Cold Start 10 Background Apps ===")
    set_phase("cold_start")
    for pkg in BACKGROUND_APPS:
        launch_app(pkg)
        time.sleep(12)  # 等待应用完成冷启动


def phase_launch_douyin():
    """Phase 2: 启动抖音"""
    print("=== Phase 2: Launch Douyin ===")
    set_phase("launch_douyin")
    launch_app(DOUYIN)
    time.sleep(8)  # 等待抖音完全加载


def browse_douyin(duration):
    """刷抖音指定秒数，返回实际耗时"""
    start = time.time()
    swipe_count = 0
    while time.time() - start < duration:
        swipe_up()
        swipe_count += 1
        wait = random.uniform(*SWIPE_INTERVAL)
        time.sleep(wait)
    elapsed = time.time() - start
    print(f"    Douyin: {swipe_count} swipes in {elapsed:.1f}s")
    return elapsed


def switch_and_back():
    """切到随机已启动应用，刷一次，切回抖音"""
    target = random.choice(BACKGROUND_APPS)
    print(f"  Switch to {target}")
    set_phase(f"switch_{target.split('.')[-1]}")
    launch_app(target)
    time.sleep(4)     # 等待应用恢复
    swipe_up()        # 往下刷一次
    time.sleep(2)
    # 切回抖音
    print(f"  Switch back to Douyin")
    set_phase("douyin_browse")
    launch_app(DOUYIN)
    time.sleep(3)     # 等待抖音恢复


def phase_browse_loop():
    """Phase 3: 循环刷抖音 + 切应用，总共 10 分钟"""
    print("=== Phase 3: Douyin Browse Loop (10 min) ===")
    set_phase("douyin_browse")

    total_elapsed = 0.0
    cycle = 0

    while total_elapsed < TOTAL_BROWSE_TIME:
        cycle += 1
        remaining = TOTAL_BROWSE_TIME - total_elapsed
        browse_time = min(DOUYIN_CYCLE_TIME, remaining)

        print(f"\n--- Cycle {cycle} | Elapsed: {total_elapsed:.0f}s / {TOTAL_BROWSE_TIME}s ---")

        # 刷抖音 1 分钟（或剩余时间）
        set_phase("douyin_browse")
        dt = browse_douyin(browse_time)
        total_elapsed += dt

        if total_elapsed >= TOTAL_BROWSE_TIME:
            break

        # 切到其他应用，刷一次，切回
        switch_and_back()
        switch_and_back()
        switch_and_back()
        # 切换时间不计入刷抖音时间，但计入总流程

    print(f"\n  Total Douyin browse time elapsed: {total_elapsed:.0f}s")


if __name__ == "__main__":
    phase_cold_start()
    phase_launch_douyin()
    phase_browse_loop()
    set_phase("done")
    print("\n=== Scenario Complete ===")
