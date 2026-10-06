"""Helper sisi-driver (TIDAK dikirim ke worker Spark)."""
import os
import platform
import sys

STOPWORDS = {
    "yang", "dan", "di", "ke", "dari", "untuk", "dengan", "pada", "ini", "itu",
    "adalah", "dalam", "tidak", "akan", "juga", "atau", "oleh", "sebagai",
    "karena", "dapat",
}


def set_partitions(rdd, n):
    """Paksa RDD punya tepat n partition (coalesce = tanpa shuffle bila mengecil)."""
    cur = rdd.getNumPartitions()
    if cur > n:
        return rdd.coalesce(n)
    if cur < n:
        return rdd.repartition(n)
    return rdd


def job_stage_task(sc, group):
    """Ambil info Job -> Stage -> Task dari StatusTracker untuk job group tertentu."""
    st = sc.statusTracker()
    jobs = []
    for jid in sorted(st.getJobIdsForGroup(group)):
        ji = st.getJobInfo(jid)
        if ji is None:
            continue
        stages = []
        for sid in ji.stageIds:
            si = st.getStageInfo(sid)
            if si is not None:
                stages.append({
                    "stage_id": sid,
                    "name": si.name,
                    "num_tasks": si.numTasks,
                    "completed_tasks": si.numCompletedTasks,
                })
        jobs.append({"job_id": jid, "status": str(ji.status), "stages": stages})
    return jobs


def _ram_gb():
    try:
        return round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024 ** 3, 1)
    except (ValueError, OSError, AttributeError):
        pass
    try:  # Windows
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        s = MEMORYSTATUSEX()
        s.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s))
        return round(s.ullTotalPhys / 1024 ** 3, 1)
    except Exception:
        return None


def machine_info(spark_version=None):
    return {
        "os": f"{platform.system()} {platform.release()}",
        "cpu_cores": os.cpu_count(),
        "ram_gb": _ram_gb(),
        "python": sys.version.split()[0],
        "spark": spark_version,
    }
