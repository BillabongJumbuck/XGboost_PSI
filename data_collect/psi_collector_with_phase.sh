#!/system/bin/sh

OUT="/data/local/tmp/psi_data.csv"
PHASE_FILE="/data/local/tmp/current_phase.txt"

echo "idle" > "$PHASE_FILE"
echo "ts,phase,some_delta,full_delta,mem_available,pgscan_direct,pgsteal_direct,pgmajfault,workingset_refault,allocstall,pswpin,pswpout" > "$OUT"

# 引入一个标记，用于跳过第一轮的差异计算，仅作为基准
FIRST_RUN=1

while true
do
    TS=$(date +%s%3N)

    # 读取 phase
    if [ -f "$PHASE_FILE" ]; then
        PHASE=$(cat "$PHASE_FILE" | tr -d '\n\r ')
    else
        PHASE="unknown"
    fi

    # 优化 1: 纯 Shell 字符串截取解析 PSI，避免多余的 grep/sed 开销
    PSI_MEM=$(cat /proc/pressure/memory)
    # 取 some 那一行的 total 值
    SOME=${PSI_MEM#*some*total=}
    SOME=${SOME%% *}
    # 取 full 那一行的 total 值
    FULL=${PSI_MEM#*full*total=}
    FULL=${FULL%% *}

    # 优化 2: awk 单次扫描解析所有 vmstat 和 meminfo 指标
    # 使用 eval 将 awk 的输出直接化为 Shell 变量
    eval $(awk '
        FILENAME == "/proc/meminfo" && /^MemAvailable:/ { mem=$2 }
        FILENAME == "/proc/vmstat" {
            if ($1 == "pgscan_direct") scan=$2
            else if ($1 == "pgsteal_direct") steal=$2
            else if ($1 == "pgmajfault") maj=$2
            else if ($1 == "workingset_refault_anon") ref_a=$2
            else if ($1 == "workingset_refault_file") ref_f=$2
            else if ($1 == "allocstall_dma32") al_d=$2
            else if ($1 == "allocstall_normal") al_n=$2
            else if ($1 == "allocstall_movable") al_m=$2
            else if ($1 == "pswpin") pin=$2
            else if ($1 == "pswpout") pout=$2
        }
        END {
            printf "MEM_AVAIL=%d; PGSCAN=%d; PGSTEAL=%d; PGMAJ=%d; REFAULT=%d; ALLOCSTALL=%d; PSWPIN=%d; PSWPOUT=%d", 
                   mem, scan, steal, maj, ref_a+ref_f, al_d+al_n+al_m, pin, pout
        }
    ' /proc/meminfo /proc/vmstat)

    # 修复核心 Bug：跳过第一轮，只赋初值不写入
    if [ "$FIRST_RUN" -eq 1 ]; then
        FIRST_RUN=0
    else
        SOME_D=$((SOME - PREV_SOME))
        FULL_D=$((FULL - PREV_FULL))
        PGSCAN_D=$((PGSCAN - PREV_PGSCAN))
        PGSTEAL_D=$((PGSTEAL - PREV_PGSTEAL))
        PGMAJ_D=$((PGMAJ - PREV_PGMAJ))
        REFAULT_D=$((REFAULT - PREV_REFAULT))
        ALLOCSTALL_D=$((ALLOCSTALL - PREV_ALLOCSTALL))
        PSWPIN_D=$((PSWPIN - PREV_PSWPIN))
        PSWPOUT_D=$((PSWPOUT - PREV_PSWPOUT))

        echo "$TS,$PHASE,$SOME_D,$FULL_D,$MEM_AVAIL,$PGSCAN_D,$PGSTEAL_D,$PGMAJ_D,$REFAULT_D,$ALLOCSTALL_D,$PSWPIN_D,$PSWPOUT_D" >> "$OUT"
    fi

    # 更新上一轮的基准值
    PREV_SOME=$SOME
    PREV_FULL=$FULL
    PREV_PGSCAN=$PGSCAN
    PREV_PGSTEAL=$PGSTEAL
    PREV_PGMAJ=$PGMAJ
    PREV_REFAULT=$REFAULT
    PREV_ALLOCSTALL=$ALLOCSTALL
    PREV_PSWPIN=$PSWPIN
    PREV_PSWPOUT=$PSWPOUT

    usleep 500000
done