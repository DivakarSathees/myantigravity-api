import platform
import os

print("123")


def get_total_ram():
    """Return total physical RAM in bytes or None if it can't be determined."""
    # Prefer psutil if available
    try:
        import psutil

        return psutil.virtual_memory().total
    except Exception:
        pass

    # Linux: read /proc/meminfo
    try:
        if platform.system() == "Linux":
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        parts = line.split()
                        # value is in kB
                        return int(parts[1]) * 1024
    except Exception:
        pass

    # POSIX: sysconf
    try:
        if hasattr(os, "sysconf"):
            pages = os.sysconf("SC_PHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
            return pages * page_size
    except Exception:
        pass

    # Windows fallback using ctypes
    try:
        if platform.system() == "Windows":
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            return stat.ullTotalPhys
    except Exception:
        pass

    return None


def sizeof_fmt(num, suffix="B"):
    if num is None:
        return "Unknown"
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Pi{suffix}"


if __name__ == "__main__":
    total = get_total_ram()
    print("Total RAM:", sizeof_fmt(total))
