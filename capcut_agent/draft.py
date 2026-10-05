"""keep ranges → pycapcut 점프컷 드래프트.

함정 대응은 .claude/skills/pycapcut-mac/SKILL.md 참조 (항목 번호를 주석에 표기).
"""

import json
import shutil
import time
import uuid
from pathlib import Path

import pycapcut as cc

US = 1_000_000


def _us(seconds: float) -> int:
    return int(round(seconds * US))


def save_draft(script: "cc.ScriptFile", draft_dir: Path) -> None:
    """draft_content.json + draft_info.json 둘 다 저장 (SKILL §2)."""
    content = script.dumps()
    for name in ("draft_content.json", "draft_info.json"):
        (draft_dir / name).write_text(content, encoding="utf-8")


def patch_meta(draft_dir: Path, draft_name: str, duration_us: int) -> None:
    """draft_meta_info.json 필수 필드 채우기 (SKILL §3)."""
    meta_path = draft_dir / "draft_meta_info.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    now_us = int(time.time() * US)
    meta.update({
        "draft_id": str(uuid.uuid4()).upper(),
        "draft_name": draft_name,
        "draft_fold_path": str(draft_dir),
        "draft_root_path": str(draft_dir.parent),
        "tm_duration": duration_us,
        "tm_draft_create": now_us,
        "tm_draft_modified": now_us,
    })
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=4), encoding="utf-8")


def build_draft(video_path: str, keeps: list[tuple[float, float]], draft_root: Path,
                draft_name: str, *, replace: bool = False) -> Path:
    """점프컷 드래프트를 만들고 드래프트 폴더 경로를 돌려준다."""
    if not keeps:
        raise ValueError("남길 구간이 없습니다 (전부 무음으로 판정됨). noise_db를 낮춰보세요.")

    folder = cc.DraftFolder(str(draft_root))
    # 소재 크기를 알아야 캔버스를 만들 수 있으므로 원본으로 먼저 읽는다
    probe = cc.VideoMaterial(video_path)
    script = folder.create_draft(draft_name, probe.width, probe.height, allow_replace=replace)
    draft_dir = Path(script.save_path).parent

    # 샌드박스 대응: 원본을 드래프트 폴더 안으로 복사 (SKILL §4)
    mat_dir = draft_dir / "materials"
    mat_dir.mkdir(exist_ok=True)
    local_video = mat_dir / Path(video_path).name
    shutil.copy2(video_path, local_video)
    material = cc.VideoMaterial(str(local_video))

    script.add_track(cc.TrackType.video)
    cursor = 0  # 주 트랙은 0부터, 이음새 겹침 없이 (SKILL §5)
    for start, end in keeps:
        src_start = _us(start)
        src_end = min(_us(end), material.duration)
        dur = src_end - src_start
        if dur <= 0:
            continue
        script.add_segment(cc.VideoSegment(
            material,
            cc.trange(cursor, dur),
            source_timerange=cc.trange(src_start, dur),
        ))
        cursor += dur

    script.duration = cursor
    save_draft(script, draft_dir)
    patch_meta(draft_dir, draft_name, cursor)
    return draft_dir
