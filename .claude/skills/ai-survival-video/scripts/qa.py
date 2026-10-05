"""STEP 5 자동 점검 준비: 10초 간격 프레임 추출 + 기계적으로 잡을 수 있는 문제 목록.

python qa.py video/ep01/script.json

- <ep>/qa_frames/fNNN.png 생성 → Claude가 이미지를 직접 열어 글자 잘림·겹침·오타를 눈으로 확인
- 자동 검사: 문장 40자 초과, prompt 장면 3초 미만, 비밀정보 후보, 자막 25자 초과 줄, 렌더 경고
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mask import find_secrets  # noqa: E402


def main() -> int:
    script = Path(sys.argv[1]).resolve()
    root = script.parent
    meta = json.loads(script.read_text(encoding="utf-8"))
    stem = meta["episode"].lower()
    video, srt = root / f"{stem}.mp4", root / f"{stem}.srt"
    issues: list[str] = []

    frames = root / "qa_frames"
    frames.mkdir(exist_ok=True)
    for f in frames.glob("*.png"):
        f.unlink()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-vf", "fps=1/10,scale=960:-1",
                    str(frames / "f%03d.png")], check=True)
    n_frames = len(list(frames.glob("*.png")))

    for i, s in enumerate(meta["scenes"]):
        for sent in s.get("narration", []):
            if len(sent) > 40:
                issues.append(f"장면{i}({s['type']}) 문장 {len(sent)}자 > 40: {sent}")
        if s["type"] == "prompt" and float(s.get("min_sec", 3)) < 3:
            issues.append(f"장면{i} prompt min_sec < 3")
    if meta["scenes"][-1]["type"] != "recap" or not meta["scenes"][-1].get("next"):
        issues.append("마지막 장면에 다음 편 예고(recap.next)가 없음")

    text = script.read_text(encoding="utf-8") + (srt.read_text(encoding="utf-8") if srt.exists() else "")
    for name, val in find_secrets(text):
        issues.append(f"비밀정보 후보 [{name}] {val[:6]}… → script.json에서 직접 **** 처리 권장")
    if srt.exists():
        for line in srt.read_text(encoding="utf-8").splitlines():
            if len(line) > 25 and "-->" not in line:
                issues.append(f"자막 줄 25자 초과: {line}")

    rep = root / "render_report.json"
    if rep.exists():
        issues += [f"렌더 경고: {w}" for w in json.loads(rep.read_text(encoding="utf-8")).get("warnings", [])]

    print(json.dumps({"frames_dir": str(frames), "frames": n_frames, "auto_issues": issues},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
