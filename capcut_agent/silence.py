"""ffmpeg silencedetect로 무음 구간을 찾고, 남길 구간(keep ranges)을 계산한다."""

import re
import subprocess
from dataclasses import dataclass

_START = re.compile(r"silence_start:\s*(-?[\d.]+)")
_END = re.compile(r"silence_end:\s*(-?[\d.]+)")


@dataclass(frozen=True)
class SilenceParams:
    noise_db: float = -35.0   # 이보다 작으면 무음
    min_silence: float = 0.5  # 이 길이(초) 이상 무음만 자른다
    pad: float = 0.12         # 말 앞뒤로 남겨둘 여유(초). 너무 작으면 발음이 잘린다
    min_keep: float = 0.25    # 이보다 짧은 발화 조각은 버린다


def probe_duration(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def parse_silences(stderr: str, duration: float) -> list[tuple[float, float]]:
    """silencedetect 로그 → [(start, end)]. 파일 끝까지 무음이면 end가 없으므로 duration으로 닫는다."""
    silences: list[tuple[float, float]] = []
    start: float | None = None
    for line in stderr.splitlines():
        if (m := _START.search(line)):
            start = max(0.0, float(m.group(1)))
        elif (m := _END.search(line)) and start is not None:
            silences.append((start, min(float(m.group(1)), duration)))
            start = None
    if start is not None:
        silences.append((start, duration))
    return silences


def detect_silences(path: str, params: SilenceParams, duration: float) -> list[tuple[float, float]]:
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn",
         "-af", f"silencedetect=noise={params.noise_db}dB:d={params.min_silence}",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg silencedetect 실패: {proc.stderr[-500:]}")
    return parse_silences(proc.stderr, duration)


def keep_ranges(silences: list[tuple[float, float]], duration: float,
                params: SilenceParams) -> list[tuple[float, float]]:
    """무음의 여집합에 pad를 붙이고, 겹치면 합치고, 너무 짧은 조각은 버린다."""
    raw: list[tuple[float, float]] = []
    cursor = 0.0
    for s, e in sorted(silences):
        if s > cursor:
            raw.append((cursor, s))
        cursor = max(cursor, e)
    if cursor < duration:
        raw.append((cursor, duration))

    padded = [(max(0.0, s - params.pad), min(duration, e + params.pad)) for s, e in raw]
    merged: list[tuple[float, float]] = []
    for s, e in padded:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return [(s, e) for s, e in merged if e - s >= params.min_keep]
