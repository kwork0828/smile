import json
import shutil
import subprocess

import pytest

from capcut_agent.silence import SilenceParams, keep_ranges, parse_silences

P = SilenceParams(pad=0.1, min_keep=0.25)


def test_parse_silences_closes_trailing_silence():
    log = "\n".join([
        "[silencedetect @ 0x1] silence_start: 1.5",
        "[silencedetect @ 0x1] silence_end: 3.0 | silence_duration: 1.5",
        "[silencedetect @ 0x1] silence_start: 8.2",
    ])
    assert parse_silences(log, 10.0) == [(1.5, 3.0), (8.2, 10.0)]


def test_keep_ranges_pads_and_merges():
    # 0~1.5 말, 1.5~1.7 무음(pad로 합쳐짐), 1.7~4 말, 4~6 무음, 6~10 말
    keeps = keep_ranges([(1.5, 1.7), (4.0, 6.0)], 10.0, P)
    assert keeps == [(0.0, 4.1), (5.9, 10.0)]


def test_keep_ranges_drops_tiny_fragments():
    keeps = keep_ranges([(0.0, 5.0), (5.02, 10.0)], 10.0, P)
    assert keeps == []


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg 필요")
def test_end_to_end_draft(tmp_path):
    from capcut_agent.cli import main

    # 2s 톤 + 2s 무음 + 2s 톤 테스트 영상
    video = tmp_path / "talk.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", "color=c=gray:s=640x360:r=30:d=6",
        "-f", "lavfi", "-i", "sine=f=440:d=6",
        "-filter_complex", "[1:a]volume='if(between(t,2,4),0,1)':eval=frame[a]",
        "-map", "0:v", "-map", "[a]", "-shortest", "-pix_fmt", "yuv420p", str(video),
    ], check=True)
    root = tmp_path / "drafts"
    root.mkdir()

    assert main([str(video), "--draft-root", str(root), "--name", "t"]) == 0

    d = root / "t"
    content = json.loads((d / "draft_content.json").read_text())
    assert (d / "draft_info.json").read_text() == (d / "draft_content.json").read_text()
    segs = content["tracks"][0]["segments"]
    assert len(segs) == 2
    assert segs[0]["target_timerange"]["start"] == 0
    # 이음새: 다음 세그먼트는 직전 끝에서 정확히 시작
    first = segs[0]["target_timerange"]
    assert segs[1]["target_timerange"]["start"] == first["start"] + first["duration"]
    # 무음 2s 중 pad 여유를 뺀 만큼 줄었는지
    assert 4.1e6 < content["duration"] < 4.6e6

    meta = json.loads((d / "draft_meta_info.json").read_text())
    assert meta["tm_duration"] == content["duration"]
    assert meta["draft_fold_path"] == str(d)
    # 샌드박스 대응: 소재가 드래프트 폴더 안을 가리킴
    assert content["materials"]["videos"][0]["path"].startswith(str(d))
