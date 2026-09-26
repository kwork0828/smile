"""Step 0: OS 감지 + 환경 점검.

빠진 도구가 있으면 설치 명령만 출력한다 (자동 설치하지 않음).
"""

import os
import platform
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

MIN_FREE_GB = 5


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    fix: str = ""


def detect_track() -> tuple[str, str]:
    """(트랙, ASR 엔진)을 돌려준다."""
    system, machine = platform.system(), platform.machine()
    if system == "Darwin" and machine == "arm64":
        return "A", "mlx-whisper"
    if system == "Windows" and machine.upper() in ("AMD64", "X86_64"):
        return "C", "faster-whisper"
    return "fallback", "faster-whisper"


def find_draft_root() -> Path | None:
    """CapCut 드래프트 루트 폴더. 환경변수 CAPCUT_DRAFT_ROOT가 있으면 우선."""
    override = os.environ.get("CAPCUT_DRAFT_ROOT")
    if override:
        return Path(override).expanduser()
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Movies/CapCut/User Data/Projects/com.lveditor.draft"
    if system == "Windows":
        local = os.environ.get("LOCALAPPDATA", "")
        return Path(local) / "CapCut/User Data/Projects/com.lveditor.draft"
    return None


def run_checks() -> list[Check]:
    system = platform.system()
    is_mac, is_win = system == "Darwin", system == "Windows"
    checks: list[Check] = []

    py_ok = sys.version_info >= (3, 10)
    checks.append(Check(
        "python>=3.10", py_ok, platform.python_version(),
        "brew install python@3.11" if is_mac else
        "https://www.python.org/downloads/ 에서 3.11 설치" if is_win else "apt install python3.11",
    ))

    ff = shutil.which("ffmpeg")
    checks.append(Check(
        "ffmpeg", ff is not None, ff or "없음",
        "brew install ffmpeg" if is_mac else
        "winget install ffmpeg" if is_win else "apt install ffmpeg",
    ))

    try:
        import pymediainfo
        mi_ok = pymediainfo.MediaInfo.can_parse()
    except ImportError:
        mi_ok = False
    checks.append(Check(
        "mediainfo", mi_ok, "ok" if mi_ok else "pycapcut 소재 길이 읽기 불가",
        "brew install mediainfo" if is_mac else
        "pip install pymediainfo (Windows는 DLL 포함)" if is_win else "apt install libmediainfo0v5",
    ))

    try:
        import pycapcut  # noqa: F401
        pc_ok = True
    except ImportError:
        pc_ok = False
    checks.append(Check("pycapcut", pc_ok, "ok" if pc_ok else "없음", "pip install -r requirements.txt"))

    root = find_draft_root()
    root_ok = root is not None and root.is_dir()
    checks.append(Check(
        "CapCut 드래프트 폴더", root_ok, str(root) if root else "이 OS에는 CapCut 데스크톱 없음",
        "CapCut 설치 후 1회 실행 + 빈 프로젝트 1개 생성 (또는 CAPCUT_DRAFT_ROOT 지정)",
    ))

    probe = root if root_ok else Path.home()
    free_gb = shutil.disk_usage(probe).free / 1024**3
    checks.append(Check(f"디스크 {MIN_FREE_GB}GB+", free_gb >= MIN_FREE_GB, f"{free_gb:.1f}GB 여유",
                        "불필요한 파일 정리"))
    return checks


def main() -> int:
    track, asr = detect_track()
    print(f"OS: {platform.system()} {platform.machine()} → 트랙 {track} (ASR: {asr})")
    checks = run_checks()
    for c in checks:
        print(f"  [{'OK' if c.ok else '--'}] {c.name}: {c.detail}")
    missing = [c for c in checks if not c.ok]
    if missing:
        print("\n설치/조치 필요:")
        for c in missing:
            print(f"  - {c.name}: {c.fix}")
        return 1
    print("\n환경 점검 통과.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
