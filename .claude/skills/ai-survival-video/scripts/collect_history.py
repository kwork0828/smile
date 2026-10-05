"""STEP 1 원자료 수집 (읽기 전용). 대상 저장소의 작업 흔적을 한 파일로 모은다.

python collect_history.py <repo_path> <out.md>

모으는 것: 커밋 타임라인(--reverse --stat), 모든 .md 문서, package.json/pyproject 등 스택 파일,
배포·플랫폼 설정 파일 목록, 이미지 후보(캡처로 쓸 수 있는 png/jpg/gif).
비밀정보는 mask.py로 가린 뒤 기록한다.
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mask import find_secrets, mask_text  # noqa: E402

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", ".next", "__pycache__", "video"}
STACK_FILES = ["package.json", "pyproject.toml", "requirements.txt", "granite.config.ts", "granite.config.js",
               "app.json", "vercel.json", "render.yaml", "netlify.toml", "firebase.json", "Dockerfile",
               "vite.config.ts", "next.config.js", "tsconfig.json"]
DEPLOY_HINTS = ("granite", "apps-in-toss", "appsintoss", "vercel", "render", "firebase", "netlify", "deploy",
                "github/workflows")
MAX_DOC = 12_000  # 문서 하나당 최대 글자


def walk(root: Path):
    for p in root.rglob("*"):
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        if p.is_file():
            yield p


def git(root: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.stdout if p.returncode == 0 else f"[git 실패] {p.stderr.strip()}"


def main() -> int:
    root, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
    files = list(walk(root))
    parts: list[str] = [f"# 원자료: {root.name}\n"]

    count = git(root, "rev-list", "--count", "HEAD").strip()
    shallow = git(root, "rev-parse", "--is-shallow-repository").strip()
    parts.append(f"- 커밋 수: {count} (shallow: {shallow})")
    if shallow == "true":
        parts.append("- 경고: 얕은 클론이라 과거 기록이 빠졌을 수 있음 → `git fetch --unshallow` 권장")
    parts.append(f"- 브랜치: {git(root, 'branch', '-a', '--format=%(refname:short)').split()}\n")

    parts.append("## 커밋 타임라인 (오래된 순)\n```")
    parts.append(git(root, "log", "--reverse", "--stat", "--date=format:%Y-%m-%d %H:%M",
                     "--format=---%n%ad | %h | %s%n%b"))
    parts.append("```\n")

    parts.append("## 스택·설정 파일")
    for p in files:
        rel = p.relative_to(root).as_posix()
        if p.name in STACK_FILES or any(h in rel.lower() for h in DEPLOY_HINTS):
            text = p.read_text(encoding="utf-8", errors="replace")[:4000]
            parts.append(f"\n### {rel}\n```\n{text}\n```")

    parts.append("\n## 문서 (.md)")
    for p in sorted(f for f in files if f.suffix.lower() == ".md"):
        text = p.read_text(encoding="utf-8", errors="replace")
        cut = " (잘림)" if len(text) > MAX_DOC else ""
        parts.append(f"\n### {p.relative_to(root).as_posix()}{cut}\n{text[:MAX_DOC]}")

    imgs = [p.relative_to(root).as_posix() for p in files if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp")]
    parts.append("\n## 이미지 후보 (screen 장면용)\n" + ("\n".join(f"- {i}" for i in imgs) or "- 없음"))

    raw = "\n".join(parts)
    hits = find_secrets(raw)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(mask_text(raw), encoding="utf-8")
    print(json.dumps({"out": str(out), "commits": count, "md_files": sum(f.suffix == ".md" for f in files),
                      "images": len(imgs), "masked": len(hits)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
