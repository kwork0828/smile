"""narration.txt → 3~5초 장면 단위 + 타임코드 (차분한 다큐 속도 가정)."""
import json
RATE = 5.8      # 공백 제외 글자/초 (차분한 남성 내레이션 가정)
PAUSE = 0.35    # 줄(호흡) 사이 쉼
INTRO = 0.0
def dur(t): return len(t.replace(' ', '')) / RATE + PAUSE
# 자동으로 끊으면 어색한 줄: 끊는 위치만 지정 (문구는 그대로)
MANUAL = {
    "스탑워치 만들고, 간단한 웹사이트 만들고... 신기하지만 지속이 안 됐어요.":
        ["스탑워치 만들고, 간단한 웹사이트 만들고...", "신기하지만 지속이 안 됐어요."],
    "나중엔 직장인도 무료로 들을 수 있는 AI 부트캠프까지 참여했어요.":
        ["나중엔 직장인도 무료로 들을 수 있는", "AI 부트캠프까지 참여했어요."],
    "구독으로 '같이 하나씩 해 보자'는 마음을 전해주시면 감사하겠습니다.":
        ["구독으로 '같이 하나씩 해 보자'는 마음을", "전해주시면 감사하겠습니다."],
}
secs, cur = [], None
for l in open('narration.txt', encoding='utf-8'):
    l = l.rstrip('\n')
    if l.startswith('## '):
        cur = {'name': l[3:], 'lines': []}; secs.append(cur)
    elif l.strip():
        parts = MANUAL.get(l, [l])
        while any(dur(p) > 5.2 for p in parts):
            p = next(p for p in parts if dur(p) > 5.2)
            cuts = [i + 1 for i, ch in enumerate(p) if ch in ',.' and 0 < i < len(p) - 2]
            if not cuts:
                words = p.split(' '); mid = len(words) // 2
                a, b = ' '.join(words[:mid]), ' '.join(words[mid:])
            else:
                k = min(cuts, key=lambda i: abs(i - len(p) / 2))
                a, b = p[:k].strip(), p[k:].strip()
            i = parts.index(p); parts[i:i + 1] = [a, b]
        cur['lines'] += parts
t, out, n = INTRO, [], 0
for s in secs:
    s['start'] = t
    buf = []
    def flush():
        global t, n
        if not buf: return
        text = ' '.join(buf); d = sum(dur(x) for x in buf)
        n += 1
        out.append({'id': n, 'sec': s['name'], 'start': round(t, 1), 'end': round(t + d, 1), 'text': text})
        t += d; buf.clear()
    for line in s['lines']:
        if buf and sum(dur(x) for x in buf) + dur(line) > 5.2:
            flush()
        buf.append(line)
        if sum(dur(x) for x in buf) >= 3.0:
            flush()
    flush()
    if s['name'].startswith('S7'):
        t += 3.0   # 마지막 책상+채널명 여운 (총 8초 중 내레이션 뒤 3초)
    s['end'] = t
json.dump({'sections': [{k: v for k, v in s.items() if k != 'lines'} for s in secs], 'chunks': out},
          open('chunks.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
def tc(x): return f"{int(x//60)}:{x%60:04.1f}"
for s in secs: print(f"[{tc(s['start'])} – {tc(s['end'])}] {s['name']}")
print('총', tc(t), '장면', len(out))
long = [c for c in out if c['end'] - c['start'] > 5.3]
print('5.3초 초과 장면:', [(c['id'], round(c['end']-c['start'],1)) for c in long])
