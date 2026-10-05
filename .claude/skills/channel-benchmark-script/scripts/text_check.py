"""대본 기계 점검: 글자 수 계산 + 원본 표절 구간 검출.

python text_check.py stats  <파일...>                 → 파일별 글자 수(공백 포함/제외)와 평균
python text_check.py overlap <대본> <원본...> [--n 6]  → 대본과 원본이 연속 n어절 이상 겹치는 구간

목표 글자 수를 눈대중으로 잡지 않고, 베끼기 여부를 감으로 판단하지 않으려고 쓴다.
"""

import re
import sys
from pathlib import Path


def read(p: str) -> str:
    return Path(p).read_text(encoding="utf-8", errors="replace")


def clean(text: str) -> str:
    # 유튜브 자막 타임스탬프(0:12, 1:02:03)와 [음악] 같은 표시 제거
    text = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", " ", text)
    text = re.sub(r"\[[^\]]{1,10}\]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def stats(paths: list[str]) -> None:
    rows = []
    for p in paths:
        t = clean(read(p))
        rows.append((p, len(t), len(t.replace(" ", ""))))
        print(f"{p}: {len(t)}자 (공백 제외 {rows[-1][2]}자)")
    if len(rows) > 1:
        avg = sum(r[1] for r in rows) / len(rows)
        print(f"평균 {avg:.0f}자 → 목표(+10%) {avg * 1.1:.0f}자")


def words(text: str) -> list[str]:
    return re.findall(r"[\w가-힣]+", clean(text))


def overlap(draft: str, sources: list[str], n: int) -> None:
    dw = words(read(draft))
    grams = set()
    for s in sources:
        sw = words(read(s))
        grams |= {tuple(sw[i:i + n]) for i in range(len(sw) - n + 1)}
    hits, i = [], 0
    while i <= len(dw) - n:
        if tuple(dw[i:i + n]) in grams:
            j = i + n
            while j < len(dw) and tuple(dw[j - n + 1:j + 1]) in grams:
                j += 1
            hits.append(" ".join(dw[i:j]))
            i = j
        else:
            i += 1
    for h in hits:
        print(f"- 겹침: {h}")
    print(f"연속 {n}어절 이상 겹치는 구간 {len(hits)}개" + (" → 해당 문장을 새 표현으로 다시 쓰세요" if hits else ""))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(1)
    cmd, args = sys.argv[1], sys.argv[2:]
    n = 6
    if "--n" in args:
        k = args.index("--n")
        n = int(args[k + 1])
        args = args[:k] + args[k + 2:]
    if cmd == "stats":
        stats(args)
    elif cmd == "overlap":
        overlap(args[0], args[1:], n)
    else:
        print(__doc__)
        raise SystemExit(1)
