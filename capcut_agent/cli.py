"""1단: 무음 컷 점프컷 드래프트 CLI.

    python -m capcut_agent.cli 영상.mp4 [--name 이름] [--noise -35] [--min-silence 0.5]
"""

import argparse
import sys
import time
from pathlib import Path

from .draft import build_draft
from .env import find_draft_root
from .silence import SilenceParams, detect_silences, keep_ranges, probe_duration


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="무음 구간을 잘라 CapCut 점프컷 드래프트 생성")
    ap.add_argument("video", help="입력 mp4/mov")
    ap.add_argument("--name", help="드래프트 이름 (기본: 파일명_jumpcut)")
    ap.add_argument("--noise", type=float, default=SilenceParams.noise_db, help="무음 기준 dB")
    ap.add_argument("--min-silence", type=float, default=SilenceParams.min_silence, help="최소 무음 길이(초)")
    ap.add_argument("--pad", type=float, default=SilenceParams.pad, help="말 앞뒤 여유(초)")
    ap.add_argument("--draft-root", help="CapCut 드래프트 루트 (기본: OS별 자동)")
    ap.add_argument("--replace", action="store_true", help="같은 이름 드래프트 덮어쓰기")
    args = ap.parse_args(argv)

    video = Path(args.video).expanduser().resolve()
    if not video.is_file():
        print(f"입력 파일 없음: {video}", file=sys.stderr)
        return 2

    root = Path(args.draft_root).expanduser() if args.draft_root else find_draft_root()
    if root is None or not root.is_dir():
        print(f"CapCut 드래프트 폴더 없음: {root}\n"
              "CapCut 설치 후 1회 실행하거나 --draft-root 로 지정하세요.", file=sys.stderr)
        return 2

    params = SilenceParams(noise_db=args.noise, min_silence=args.min_silence, pad=args.pad)
    t0 = time.time()
    duration = probe_duration(str(video))
    silences = detect_silences(str(video), params, duration)
    keeps = keep_ranges(silences, duration, params)
    kept = sum(e - s for s, e in keeps)

    name = args.name or f"{video.stem}_jumpcut"
    draft_dir = build_draft(str(video), keeps, root, name, replace=args.replace)

    print(f"원본 {duration:.1f}s → 결과 {kept:.1f}s "
          f"(무음 {duration - kept:.1f}s 제거, 컷 {len(keeps)}개, {time.time() - t0:.1f}s 소요)")
    print(f"드래프트: {draft_dir}")
    print("검증: 캡컷을 (재)실행 → 드래프트 열기 → 처음부터 끝까지 재생")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
