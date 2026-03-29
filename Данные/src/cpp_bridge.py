from __future__ import annotations

import ctypes
import platform
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = ROOT / "build"

if platform.system() == "Darwin":
    LIB_PATH = BUILD_DIR / "libfinance.dylib"
else:
    LIB_PATH = BUILD_DIR / "libfinance.so"

BUILD_SCRIPT = ROOT / "build.sh"

CPP_AVAILABLE = False
_lib = None


class CAnalysisResult(ctypes.Structure):
    _fields_ = [
        ("price_today", ctypes.c_double),
        ("change_price_1d", ctypes.c_double),

        ("average_7d", ctypes.c_double),
        ("change_av_7d", ctypes.c_double),
        ("change_ab_7d", ctypes.c_double),
        ("change_7d_per", ctypes.c_double),

        ("average_30d", ctypes.c_double),
        ("change_av_30d", ctypes.c_double),
        ("change_ab_30d", ctypes.c_double),
        ("change_30d_per", ctypes.c_double),

        ("average_nd", ctypes.c_double),
        ("change_av_nd", ctypes.c_double),
        ("change_ab_nd", ctypes.c_double),
        ("change_nd_per", ctypes.c_double),

        ("signal", ctypes.c_int),
    ]


def _try_load_library():
    global _lib, CPP_AVAILABLE

    if not LIB_PATH.exists() and BUILD_SCRIPT.exists():
        try:
            subprocess.run(["bash", str(BUILD_SCRIPT)], check=True, cwd=str(ROOT))
        except Exception:
            pass

    if LIB_PATH.exists():
        try:
            _lib = ctypes.CDLL(str(LIB_PATH))
            _lib.analyze_prices.argtypes = [
                ctypes.POINTER(ctypes.c_double),
                ctypes.c_int,
                ctypes.c_int,
                ctypes.POINTER(CAnalysisResult),
            ]
            _lib.analyze_prices.restype = ctypes.c_int
            CPP_AVAILABLE = True
        except OSError:
            _lib = None
            CPP_AVAILABLE = False


_try_load_library()


def _signal_to_str(x: int) -> str:
    return {0: "Buy", 1: "Hold", 2: "Sell"}.get(x, "Unknown")


def analyze_series(prices: list[float], n: int = 20) -> dict:
    if not prices:
        raise ValueError("prices is empty")

    if not CPP_AVAILABLE or _lib is None:
        raise RuntimeError("C++ library is unavailable")

    arr = (ctypes.c_double * len(prices))(*prices)
    out = CAnalysisResult()

    ok = _lib.analyze_prices(arr, len(prices), n, ctypes.byref(out))
    if ok != 1:
        raise RuntimeError("C++ analyze_prices failed")

    return {
        "price_today": out.price_today,
        "change_price_1d": out.change_price_1d,
        "average_7d": out.average_7d,
        "change_av_7d": out.change_av_7d,
        "change_ab_7d": out.change_ab_7d,
        "change_7d_per": out.change_7d_per,
        "average_30d": out.average_30d,
        "change_av_30d": out.change_av_30d,
        "change_ab_30d": out.change_ab_30d,
        "change_30d_per": out.change_30d_per,
        "average_nd": out.average_nd,
        "change_av_nd": out.change_av_nd,
        "change_ab_nd": out.change_ab_nd,
        "change_nd_per": out.change_nd_per,
        "signal": _signal_to_str(out.signal),
    }
