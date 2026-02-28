#!/system/bin/sh

OUT="/data/local/tmp/psi_data.csv"

echo "ts,some_delta,full_delta,mem_available,pgscan_direct,pgsteal_direct,pgmajfault,workingset_refault,allocstall,pswpin,pswpout" > $OUT

PREV_SOME=0
PREV_FULL=0
PREV_PGSCAN=0
PREV_PGSTEAL=0
PREV_PGMAJ=0
PREV_REFAULT=0
PREV_ALLOCSTALL=0
PREV_PSWPIN=0
PREV_PSWPOUT=0

while true
do
    TS=$(date +%s%3N)

    PSI=$(cat /proc/pressure/memory)
    SOME=$(echo "$PSI" | grep some | sed -n 's/.*total=\([0-9]*\).*/\1/p')
    FULL=$(echo "$PSI" | grep full | sed -n 's/.*total=\([0-9]*\).*/\1/p')

    MEM_AVAIL=$(grep MemAvailable /proc/meminfo | awk '{print $2}')

    PGSCAN=$(grep "^pgscan_direct " /proc/vmstat | awk '{print $2}')
    PGSTEAL=$(grep "^pgsteal_direct " /proc/vmstat | awk '{print $2}')
    PGMAJ=$(grep "^pgmajfault " /proc/vmstat | awk '{print $2}')
    REFAULT=$(grep "^workingset_refault " /proc/vmstat | awk '{print $2}')
    ALLOCSTALL=$(grep "^allocstall " /proc/vmstat | awk '{print $2}')
    PSWPIN=$(grep "^pswpin " /proc/vmstat | awk '{print $2}')
    PSWPOUT=$(grep "^pswpout " /proc/vmstat | awk '{print $2}')

    # 计算 delta
    SOME_D=$((SOME - PREV_SOME))
    FULL_D=$((FULL - PREV_FULL))
    PGSCAN_D=$((PGSCAN - PREV_PGSCAN))
    PGSTEAL_D=$((PGSTEAL - PREV_PGSTEAL))
    PGMAJ_D=$((PGMAJ - PREV_PGMAJ))
    REFAULT_D=$((REFAULT - PREV_REFAULT))
    ALLOCSTALL_D=$((ALLOCSTALL - PREV_ALLOCSTALL))
    PSWPIN_D=$((PSWPIN - PREV_PSWPIN))
    PSWPOUT_D=$((PSWPOUT - PREV_PSWPOUT))

    echo "$TS,$SOME_D,$FULL_D,$MEM_AVAIL,$PGSCAN_D,$PGSTEAL_D,$PGMAJ_D,$REFAULT_D,$ALLOCSTALL_D,$PSWPIN_D,$PSWPOUT_D" >> $OUT

    PREV_SOME=$SOME
    PREV_FULL=$FULL
    PREV_PGSCAN=$PGSCAN
    PREV_PGSTEAL=$PGSTEAL
    PREV_PGMAJ=$PGMAJ
    PREV_REFAULT=$REFAULT
    PREV_ALLOCSTALL=$ALLOCSTALL
    PREV_PSWPIN=$PSWPIN
    PREV_PSWPOUT=$PSWPOUT

    usleep 500000   # 500ms 精准采样
done
