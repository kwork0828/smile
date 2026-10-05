"""script.json → 16:9 강의 영상 (mp4 + srt + thumbnail + upload.txt).

사용:
    python render.py video/ep01/script.json            # edge-tts 음성
    python render.py video/ep01/script.json --tts none # 음성 없이 타이밍만 (TTS가 막힌 환경 테스트용)

필요: pip install edge-tts pillow / ffmpeg (PATH)
산출물은 script.json이 있는 폴더에 만든다. 중간 파일은 그 안의 _build/.
"""

import argparse
import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from mask import mask_text  # noqa: E402

W, H = 1920, 1080
FPS = 30
GAP = 0.3          # 문장 사이 쉼
TAIL = 0.5         # 장면 끝 여유
SUB_LINE = 25      # 자막 한 줄 최대 글자
SAFE_BOTTOM = 860  # 이 아래는 자막 영역 → 슬라이드 내용 금지

BG = (15, 26, 46)
CARD = (24, 38, 64)
WHITE = (240, 243, 248)
MUTED = (150, 163, 184)
GOLD = (245, 197, 66)
HILITE = (245, 197, 66, 70)

FONT_CANDIDATES = {
    "title": ["C:/Windows/Fonts/malgunbd.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc",
              "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"],
    "body": ["C:/Windows/Fonts/malgun.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc",
             "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"],
    "code": ["C:/Windows/Fonts/consola.ttf", "/System/Library/Fonts/Menlo.ttc",
             "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"],
}
_TTC_INDEX = {"NotoSansCJK": 1}  # Noto CJK ttc: 1 = KR
_font_cache: dict = {}
warnings: list[str] = []


# ---------- 공통 ----------

def run(cmd: list[str], cwd: Path | None = None) -> None:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        raise RuntimeError(f"명령 실패: {' '.join(cmd[:6])}...\n{p.stderr[-1500:]}")


def probe(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout
    return float(out.strip())


def font(role: str, size: int) -> ImageFont.FreeTypeFont:
    key = (role, size)
    if key not in _font_cache:
        for path in FONT_CANDIDATES[role]:
            if os.path.exists(path):
                idx = next((i for k, i in _TTC_INDEX.items() if k in path), 0)
                _font_cache[key] = ImageFont.truetype(path, size, index=idx)
                break
        else:
            raise FileNotFoundError(f"{role} 폰트를 찾을 수 없음: {FONT_CANDIDATES[role]}")
    return _font_cache[key]


def has_hangul(s: str) -> bool:
    return any("\uac00" <= c <= "\ud7a3" or "\u3131" <= c <= "\u318e" for c in s)


def wrap(text: str, f: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    """픽셀 폭 기준 줄바꿈. 공백에서 우선 끊고, 긴 단어는 글자 단위로 끊는다."""
    lines: list[str] = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            cand = f"{cur} {word}" if cur else word
            if f.getlength(cand) <= max_w:
                cur = cand
                continue
            if cur:
                lines.append(cur)
            cur = ""
            for ch in word:
                if f.getlength(cur + ch) > max_w:
                    lines.append(cur)
                    cur = ch
                else:
                    cur += ch
        lines.append(cur)
    return lines


# ---------- 슬라이드 ----------

def badge(d: ImageDraw.ImageDraw, ep: str) -> None:
    bf = font("title", 30)
    bw = int(bf.getlength(ep)) + 36
    d.rounded_rectangle((60, 50, 60 + bw, 100), radius=10, fill=GOLD)
    d.text((60 + 18, 75), ep, font=bf, fill=BG, anchor="lm")


def base(ep: str, heading: str | None = None) -> tuple[Image.Image, ImageDraw.ImageDraw, int]:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    badge(d, ep)
    y = 150
    if heading:
        hf = font("title", 64)
        for line in wrap(mask_text(heading), hf, W - 200):
            d.text((100, y), line, font=hf, fill=WHITE)
            y += 84
        d.line((100, y + 10, 220, y + 10), fill=GOLD, width=6)
        y += 60
    return img, d, y


def draw_bullets(d, items: list[str], y: int, size: int = 48) -> int:
    bf = font("body", size)
    for item in items:
        lines = wrap(mask_text(item), bf, W - 320)
        cy = y + int(size * 0.62)
        d.ellipse((110, cy - 8, 126, cy + 8), fill=GOLD)
        for line in lines:
            if y + size > SAFE_BOTTOM:
                warnings.append(f"글자 넘침: '{item[:20]}…' 가 자막 영역을 침범 → 항목을 줄이세요")
                return y
            d.text((150, y), line, font=bf, fill=WHITE)
            y += int(size * 1.45)
        y += int(size * 0.5)
    return y


def slide_title(s, ep, series):
    img, d, _ = base(ep)
    tf = font("title", 96)
    lines = wrap(mask_text(s.get("title", "")), tf, W - 300)
    y = 380 - len(lines) * 55
    if series:
        d.text((W // 2, y - 70), series, font=font("title", 40), fill=GOLD, anchor="mm")
    for line in lines:
        d.text((W // 2, y + 55), line, font=tf, fill=WHITE, anchor="mm")
        y += 120
    if s.get("sub"):
        d.text((W // 2, y + 60), mask_text(s["sub"]), font=font("body", 44), fill=MUTED, anchor="mm")
    return img


def slide_explain(s, ep, series):
    img, d, y = base(ep, s.get("heading"))
    if s.get("bullets"):
        draw_bullets(d, s["bullets"], y)
    elif s.get("body"):
        bf = font("body", 50)
        for line in wrap(mask_text(s["body"]), bf, W - 240):
            d.text((110, y), line, font=bf, fill=WHITE)
            y += 72
    return img


def slide_prompt(s, ep, series):
    img, d, y = base(ep, s.get("heading", "따라 쳐 보세요"))
    text = mask_text(s.get("prompt", ""))
    size = 56
    while True:
        pf = font("body" if has_hangul(text) else "code", size)
        lines = wrap(text, pf, W - 200 - 140)
        if y + 80 + len(lines) * size * 1.4 < SAFE_BOTTOM - 40 or size <= 30:
            break
        size -= 4
    if size <= 30:
        warnings.append("prompt: 문장이 너무 길어 글씨가 최소 크기 → 프롬프트를 나눠 두 장면으로")
    box_bottom = min(SAFE_BOTTOM - 20, max(y + 300, int(y + 110 + len(lines) * size * 1.4)))
    d.rounded_rectangle((100, y, W - 100, box_bottom), radius=18, fill=(8, 12, 20), outline=(60, 72, 96), width=2)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse((130 + i * 36, y + 24, 150 + i * 36, y + 44), fill=c)
    ty = y + 80
    d.text((140, ty), ">", font=font("code", size), fill=GOLD)
    for line in lines:
        d.text((190, ty), line, font=pf, fill=WHITE)
        ty += int(size * 1.4)
    return img


def slide_code(s, ep, series):
    img, d, y = base(ep, s.get("heading"))
    code_lines = mask_text(s.get("code", "")).rstrip("\n").split("\n")
    start = int(s.get("start_line", 1))
    hl = set(s.get("highlight", []))
    avail = SAFE_BOTTOM - y - 40
    size = max(22, min(40, int(avail / max(1, len(code_lines)) / 1.45)))
    max_w = W - 100 - 230 - 30
    widest = lambda sz: max(code_width(l, sz) for l in code_lines)  # noqa: E731
    while size > 18 and widest(size) > max_w:
        size -= 2
    if widest(size) > max_w:
        warnings.append("code: 줄이 너무 길어 잘림 → 긴 줄을 발췌에서 줄이세요")
    lh = int(size * 1.45)
    if len(code_lines) * lh > avail:
        warnings.append(f"코드 {len(code_lines)}줄이 너무 김 → 15줄 이하로 잘라주세요")
        code_lines = code_lines[: avail // lh]
    d.rounded_rectangle((100, y, W - 100, y + len(code_lines) * lh + 40), radius=14, fill=(8, 12, 20))
    if s.get("file"):
        d.text((W - 120, y - 40), s["file"], font=font("code", 26), fill=MUTED, anchor="ra")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    ty = y + 20
    for i, line in enumerate(code_lines):
        n = start + i
        if n in hl:
            od.rectangle((104, ty - 4, W - 104, ty + lh - 8), fill=HILITE)
        ty += lh
    img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"))
    d = ImageDraw.Draw(img)
    ty = y + 20
    for i, line in enumerate(code_lines):
        n = start + i
        d.text((130, ty), f"{n:>3}", font=font("code", size), fill=MUTED)
        draw_code_line(d, 230, ty, line, size, GOLD if n in hl else WHITE)
        ty += lh
    return img


def code_width(line: str, size: int) -> float:
    line = line.replace("\t", "    ")
    indent = len(line) - len(line.lstrip(" "))
    rest = line.lstrip(" ")
    f = font("body" if has_hangul(rest) else "code", size)
    return font("code", size).getlength(" " * indent) + f.getlength(rest)


def draw_code_line(d, x: int, y: int, line: str, size: int, fill) -> None:
    """들여쓰기는 고정폭 폰트 기준으로 맞추고, 한글이 섞인 본문만 본문 폰트로."""
    line = line.replace("\t", "    ")
    indent = len(line) - len(line.lstrip(" "))
    rest = line.lstrip(" ")
    x += font("code", size).getlength(" " * indent)
    d.text((x, y), rest, font=font("body" if has_hangul(rest) else "code", size), fill=fill)


def slide_screen(s, ep, series, root: Path, need: list):
    path = (root / s["image"]).resolve() if s.get("image") else None
    if not path or not path.exists():
        need.append(f"- {s.get('heading', '(제목 없음)')}: {s.get('image', '이미지 경로 없음')} — {s.get('capture_hint', '')}")
        hint = s.get("capture_hint")
        fallback = dict(s, bullets=s.get("bullets") or
                        ["[캡처 필요] 이 장면은 설명 슬라이드로 대체했습니다"] + ([f"필요한 화면: {hint}"] if hint else []))
        return slide_explain(fallback, ep, series)
    shot = Image.open(path).convert("RGB")
    bg = shot.resize((W, H)).filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB", (W, H), BG), 0.55)
    top = 130 if s.get("heading") else 60
    box_w, box_h = W - 240, SAFE_BOTTOM - top - 30
    shot.thumbnail((box_w, box_h))
    x, y = (W - shot.width) // 2, top + (box_h - shot.height) // 2 + 10
    bg.paste(shot, (x, y))
    d = ImageDraw.Draw(bg)
    badge(d, ep)
    if s.get("heading"):
        d.text((W // 2, 100), mask_text(s["heading"]), font=font("title", 44), fill=WHITE, anchor="mm")
    return bg


def slide_recap(s, ep, series):
    img, d, y = base(ep, s.get("heading", "오늘 정리"))
    y = draw_bullets(d, s.get("bullets", []), y, 46)
    if s.get("next"):
        nf = font("title", 42)
        text = "다음 편 ▶ " + mask_text(s["next"])
        lines = wrap(text, nf, W - 300)
        top = SAFE_BOTTOM - 40 - len(lines) * 60
        if top < y:
            warnings.append("recap: 다음 편 예고가 정리 항목과 겹침 → 항목 수를 줄이세요")
        d.rounded_rectangle((100, top - 20, W - 100, SAFE_BOTTOM - 20), radius=14, fill=CARD)
        for line in lines:
            d.text((140, top), line, font=nf, fill=GOLD)
            top += 60
    return img


def thumbnail(meta: dict, out: Path) -> None:
    img = Image.new("RGB", (1280, 720), BG)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 1280, 16), fill=GOLD)
    d.text((60, 70), f"{meta.get('series', '')}  {meta['episode']}", font=font("title", 44), fill=GOLD)
    tf = font("title", 92)
    text = meta.get("thumb_title") or meta["title"]
    lines = wrap(text, tf, 1160)
    while len(lines) > 3 and tf.size > 56:
        tf = font("title", tf.size - 8)
        lines = wrap(text, tf, 1160)
    y = 360 - len(lines) * tf.size * 0.62
    for line in lines:
        d.text((60, y), line, font=tf, fill=WHITE)
        y += tf.size * 1.25
    img.save(out)


# ---------- 음성 ----------

async def _edge(text: str, voice: str, out: Path) -> None:
    import edge_tts
    await edge_tts.Communicate(text, voice).save(str(out))


def tts(text: str, voice: str, out: Path, mode: str) -> float:
    if mode == "none":
        dur = max(1.2, len(text) / 7.0)  # 한국어 낭독 약 7자/초
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", f"{dur:.2f}",
             "-c:a", "libmp3lame", str(out)])
        return dur
    last = None
    for _ in range(3):
        try:
            asyncio.run(_edge(text, voice, out))
            if out.exists() and out.stat().st_size > 0:
                return probe(out)
        except Exception as e:  # 네트워크 일시 오류 재시도
            last = e
    raise RuntimeError(f"edge-tts 실패 (3회): {last}\n막힌 환경이면 --tts none 으로 타이밍만 확인하세요.")


# ---------- 자막 ----------

def split_sub(text: str) -> list[str]:
    """한 줄 SUB_LINE자 이내, 최대 2줄씩 묶어 자막 cue 목록으로."""
    words, lines, cur = text.split(" "), [], ""
    for w in words:
        cand = f"{cur} {w}" if cur else w
        if len(cand) <= SUB_LINE:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            while len(w) > SUB_LINE:
                lines.append(w[:SUB_LINE])
                w = w[SUB_LINE:]
            cur = w
    if cur:
        lines.append(cur)
    return ["\n".join(lines[i:i + 2]) for i in range(0, len(lines), 2)]


def ts(t: float, sep: str = ",") -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02}{sep}{ms:03}"


# ---------- 메인 ----------

def render(script_path: Path, tts_mode: str) -> dict:
    meta = json.loads(script_path.read_text(encoding="utf-8"))
    root = script_path.parent
    ep = meta["episode"]
    stem = ep.lower()
    series = meta.get("series", "")
    voice = meta.get("voice", "ko-KR-InJoonNeural")
    build = root / "_build"
    shutil.rmtree(build, ignore_errors=True)
    build.mkdir()
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            raise SystemExit("ffmpeg 없음 → Windows: winget install Gyan.FFmpeg / Mac: brew install ffmpeg")

    need: list[str] = []
    cues: list[tuple[float, float, str]] = []
    chapters: list[tuple[float, str]] = []
    clips: list[Path] = []
    t = 0.0
    gap = build / "gap.mp3"
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(GAP), "-c:a", "libmp3lame", str(gap)])

    for i, s in enumerate(meta["scenes"]):
        kind = s["type"]
        maker = {"title": slide_title, "explain": slide_explain, "prompt": slide_prompt,
                 "code": slide_code, "recap": slide_recap}.get(kind)
        img = slide_screen(s, ep, series, root, need) if kind == "screen" else maker(s, ep, series)
        png = build / f"s{i:02}.png"
        img.save(png)

        if s.get("chapter"):
            chapters.append((t, s["chapter"]))
        parts, local = [], 0.0
        for j, sent in enumerate(s.get("narration", [])):
            sent = mask_text(sent)
            if len(sent) > 40:
                warnings.append(f"장면{i} 문장 40자 초과: '{sent[:20]}…'")
            mp3 = build / f"s{i:02}_{j:02}.mp3"
            dur = tts(sent, voice, mp3, tts_mode)
            for k, chunk in enumerate(pieces := split_sub(sent)):
                share = dur / len(pieces)
                cues.append((t + local + k * share, t + local + (k + 1) * share, chunk))
            parts += [mp3, gap]
            local += dur + GAP
        min_sec = float(s.get("min_sec", 3.0 if kind == "prompt" else 0))
        scene_dur = max(local, min_sec) + TAIL

        lst = build / f"s{i:02}_a.txt"
        lst.write_text("".join(f"file '{p.name}'\n" for p in parts) or "", encoding="utf-8")
        audio = build / f"s{i:02}.m4a"
        if parts:
            run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst.name, "-af", "apad",
                 "-t", f"{scene_dur:.3f}", "-ar", "48000", "-ac", "2", "-c:a", "aac", audio.name], cwd=build)
        else:
            run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", f"{scene_dur:.3f}",
                 "-c:a", "aac", audio.name], cwd=build)

        frames = int(round(scene_dur * FPS))
        clip = build / f"s{i:02}.mp4"
        zoom = (f"scale=3840:-1,zoompan=z='1+0.04*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                f":d=1:s={W}x{H}:fps={FPS},format=yuv420p")
        run(["ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-i", png.name, "-i", audio.name,
             "-vf", zoom, "-frames:v", str(frames), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
             "-c:a", "copy", "-shortest", clip.name], cwd=build)
        clips.append(clip)
        t += frames / FPS

    # 자막
    srt = root / f"{stem}.srt"
    srt.write_text("\n".join(f"{n}\n{ts(a)} --> {ts(b)}\n{txt}\n" for n, (a, b, txt) in enumerate(cues, 1)),
                   encoding="utf-8")

    # 이어붙이기 → 자막 번인 → -14 LUFS
    (build / "clips.txt").write_text("".join(f"file '{c.name}'\n" for c in clips), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "clips.txt", "-c", "copy", "joined.mp4"], cwd=build)
    shutil.copy(srt, build / "sub.srt")
    fam = font("body", 40).getname()[0]
    style = (f"FontName={fam},FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
             "BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginV=40")
    out = root / f"{stem}.mp4"
    run(["ffmpeg", "-y", "-i", "joined.mp4", "-vf", f"subtitles=sub.srt:force_style='{style}'",
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", "final.mp4"], cwd=build)
    shutil.move(str(build / "final.mp4"), out)

    thumbnail(meta, root / "thumbnail.png")

    up = meta.get("upload", {})
    if not chapters or chapters[0][0] > 0:
        chapters.insert(0, (0.0, "인트로"))
    chap_txt = "\n".join(f"{ts(a, '.')[3:8]} {name}" for a, name in chapters)
    (root / "upload.txt").write_text(
        f"[제목]\n{up.get('title', f'{series} {ep} | ' + meta['title'])}\n\n"
        f"[설명]\n{up.get('description', '')}\n\n[챕터]\n{chap_txt}\n\n"
        f"[태그]\n{', '.join(up.get('tags', []))}\n", encoding="utf-8")

    if need:
        (root / "need_capture.md").write_text("# 캡처 필요 목록\n\n" + "\n".join(need) + "\n", encoding="utf-8")

    total = probe(out)
    report = {"video": str(out), "duration_sec": round(total, 1), "scenes": len(meta["scenes"]),
              "tts": tts_mode, "need_capture": len(need), "warnings": warnings}
    (root / "render_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--tts", choices=["edge", "none"], default="edge")
    args = ap.parse_args()
    report = render(Path(args.script).resolve(), args.tts)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
