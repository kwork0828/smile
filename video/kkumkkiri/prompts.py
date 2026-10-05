"""장면별 화면 유형 + 이미지/영상 프롬프트 → 마크다운 산출물.

kind
  REAL : 실제 화면 녹화/캡처 사용 (생성 금지 — 증명할 수 있는 장면)
  CARD : 텍스트 카드/모션 그래픽 (편집 툴에서 제작)
  GEN  : 이미지 생성 (추상·책상·빛·사물, 얼굴·로고·글자 없음)
GEN 프롬프트 형식: image description / camera angle / lighting / mood / action
"""
import json

STYLE = ("calm warm documentary style, muted dark charcoal tones with soft natural window light, "
         "subtle teal (#52B788) and warm gold (#D4A853) accents, shallow depth of field, "
         "photorealistic, cinematic 16:9, no human faces, no readable text, no logos or brand marks")

P = {
 1: ("GEN", "A quiet dark desk at night with a closed laptop and a phone lying face up",
     "medium shot, eye level", "only the faint cold glow of the phone screen", "uneasy, hushed",
     "the phone screen lights up silently with a notification"),
 2: ("GEN", "Abstract stream of blurred social media cards and notification bubbles flying past, no readable words",
     "close-up, slightly tilted", "cool blue screen glow", "overwhelming, restless", "cards rush past rapidly"),
 3: ("GEN", "A coworking space seen from behind the last row: rows of glowing laptop screens, people out of focus from behind",
     "wide shot, from the back of the room", "bright overhead office light", "distant, intimidating",
     "screens flicker with activity"),
 4: ("GEN", "A lone laptop on a dark wooden desk, an empty document with a blinking cursor",
     "medium close-up, eye level", "single dim desk lamp", "stuck, lonely", "the cursor keeps blinking, nothing is typed"),
 5: ("CARD", "큰 자막 카드 \"나만 뒤쳐지고 있는 건 아닐까?\" — 4번 노트북 화면 위에 정지, 핵심어 '뒤쳐지고' 금색"),
 6: ("GEN", "Rain streaks on a window at night, a desk lamp switched off in the foreground",
     "medium shot through the window", "dark, faint streetlight from outside", "heavy, weighed down",
     "raindrops slide slowly down the glass"),
 7: ("REAL", "프로그램 설치 화면 녹화 (Node.js·Git·Claude Code 등 실제 설치 과정)"),
 8: ("REAL", "터미널 창 + 실제 오류 메시지 화면 (경로·이메일·토큰 **** 마스킹)"),
 9: ("REAL", "디스코드 설치 화면"),
 10: ("REAL", "디스코드 인증 오류 화면 (이메일·전화번호 **** 마스킹)"),
 11: ("GEN", "Two hands resting away from a keyboard while lines of code scroll by themselves on the monitor",
      "over-the-shoulder, hands only", "cool monitor light", "detached, unreal", "code keeps scrolling without the hands moving"),
 12: ("GEN", "A monitor's glow reflected in a dark window, an empty office chair turned away from the desk",
      "wide shot", "low cold light", "a quiet gap between person and work", "the chair rotates slightly to a stop"),
 13: ("CARD", "텍스트 카드 2장: \"한 번 더 질문하기\" → \"한 단계만 하기\" (대본 화면 지시의 오류 장면 뒤 카드)"),
 14: ("GEN", "A stack of tutorial printouts beside a cold cup of coffee, the top page slightly curled",
      "top-down shot", "flat grey afternoon light", "fading interest", "a draft from the window lifts the top page and lets it fall"),
 15: ("REAL", "직접 만든 스탑워치·간단한 웹사이트 화면 (없으면 GEN 대체: 'A minimal stopwatch app on a laptop screen, desk top-down')"),
 16: ("GEN", "A laptop lid slowly closing on a desk, dust floating in a beam of light",
      "low angle, side view", "single shaft of window light", "quiet giving up", "the lid closes gently"),
 17: ("CARD", "제목 카드: \"AI에 익숙해지는 세 가지 방법\""),
 18: ("GEN", "An open notebook with three empty hand-drawn checkboxes and a teal pen beside it",
      "top-down close-up", "soft morning window light", "hopeful, organized", "the pen rolls slightly toward the first box"),
 19: ("CARD", "팁 카드 ① \"내 삶에 필요한 것부터\""),
 20: ("REAL", "직접 만든 취업·이직 서비스 / 양육 챗봇 화면 (있을 때). 없으면 GEN 대체: 'A resume sheet, a child's crayon drawing and a small chat bubble icon card arranged on a wooden desk, top-down, warm light'"),
 21: ("GEN", "An office attendance sheet on a clipboard next to a time card machine, early morning",
      "medium close-up, slight high angle", "pale morning light", "everyday routine", "the clock hand ticks forward"),
 22: ("GEN", "A hand writing a short list in a notebook with a teal pen, words not readable",
      "close-up, hand only", "warm desk lamp", "focused, personal", "the pen moves steadily down the page"),
 23: ("CARD", "팁 카드 ② \"강제성 있는 환경\""),
 24: ("GEN", "A wall calendar where only the first three days are crossed out and the rest are blank",
      "medium shot, straight on", "flat indoor light", "slipping back to old habits", "a slow push-in on the blank fourth day"),
 25: ("REAL", "챌린지 참여·과제 제출 화면 (이름·이메일 **** 마스킹)"),
 26: ("REAL", "젠스파크·바이브코딩 작업 화면"),
 27: ("REAL", "AI 부트캠프 화면 (수강생 이름·얼굴 블러)"),
 28: ("REAL", "부트캠프 화면 이어서 (27과 같은 녹화의 다음 구간)"),
 29: ("CARD", "작은 안내 카드: \"관련 정보 → 다음 영상에서\""),
 30: ("CARD", "팁 카드 ③ \"꾸준히 할 수 있는 시간대\""),
 31: ("GEN", "A child's small toy and a work bag placed side by side at an apartment entrance at dusk",
      "low angle, floor level", "warm hallway light mixed with blue dusk", "busy life, little time", "the hallway light flickers on"),
 32: ("GEN", "A bedside clock showing early dawn next to an open laptop, deep blue pre-dawn window",
      "medium close-up", "blue dawn light and the laptop's soft glow", "quiet determination", "the sky outside lightens slightly"),
 33: ("GEN", "Exterior of a generic 24-hour drive-thru restaurant before dawn, empty lane, no logos or brand names",
      "wide shot from across the street", "warm interior light against dark blue sky", "solitary, calm", "a single car light passes by"),
 34: ("GEN", "A quiet, clean Korean internet cafe at night with rows of empty desks and one lit booth",
      "wide shot, eye level", "dim ambient light, one booth warmly lit", "calm, focused", "a slow dolly along the empty row"),
 35: ("GEN", "Hands typing steadily on a keyboard under a warm lamp",
      "close-up, side angle", "warm lamp light", "steady, growing confidence", "fingers type in an even rhythm"),
 36: ("GEN", "The first step of a wooden staircase lit by a soft beam of light",
      "low angle", "single warm light beam", "a small beginning", "the light gently brightens"),
 37: ("GEN", "A wooden staircase seen from a few steps up, more steps glowing ahead",
      "low angle looking up", "warm light growing toward the top", "confidence building", "slow tilt up the stairs"),
 38: ("GEN", "A subway window in morning light, a phone held in hands with a blurred lecture video playing",
      "over-the-shoulder, hands only", "soft morning sunlight", "making use of spare time", "the train sways gently"),
 39: ("CARD", "전후 비교 카드: \"처음: 설치 화면 앞에서 멈춤\" → \"지금: 연결을 시도하고 기록함\""),
 40: ("REAL", "지금의 터미널 작업 화면 (익숙해진 모습, 토큰·경로 **** 마스킹)"),
 41: ("REAL", "도구 연결 화면 (커넥터·연동 설정 등 실제 화면, 계정 정보 마스킹)"),
 42: ("GEN", "An open notebook with a handwritten quotation mark on a sunlit desk",
      "top-down", "warm side light", "reflective, gentle", "a page turns softly"),
 43: ("CARD", "인용 자막 크게: \"아직 낯설어서 그런 것뿐이다.\" (핵심어 '낯설어서' 청록)"),
 44: ("CARD", "43 인용 카드 유지 → 천천히 페이드"),
 45: ("GEN", "A closed wooden door in a dim hallway",
      "medium shot, straight on", "dim, cool light", "uncertain", "a thin line of light appears under the door"),
 46: ("GEN", "The same kind of wooden door now slightly ajar with warm light spilling out",
      "medium shot, straight on", "warm light from inside", "not unable, just unfamiliar", "the door opens a little wider"),
 47: ("CARD", "카드 '두려움' (회색)"),
 48: ("CARD", "'두려움' 카드가 '도구' 카드(금색)로 부드럽게 전환"),
 49: ("GEN", "An open wooden toolbox on a workbench with a small warm glowing light inside",
      "medium close-up, slight high angle", "warm glow from inside the box", "fear turned into a tool", "the glow softly pulses"),
 50: ("GEN", "Abstract streaks of light racing past in a dark space",
      "wide, centered", "fast cool light streaks", "a race, comparison", "the streaks slow down and fade"),
 51: ("GEN", "A family dining table set for an evening meal with empty chairs and a small notebook, no people",
      "medium wide shot", "warm evening pendant light", "care, responsibility", "steam rises from a teacup"),
 52: ("GEN", "Hands watering a small plant on a windowsill",
      "close-up, hands only", "soft morning window light", "tending, caring", "water pours gently into the soil"),
 53: ("GEN", "An hourglass on a desk with its top half still mostly full",
      "close-up, eye level", "warm side light", "not too late", "sand flows slowly"),
 54: ("GEN", "A door opening onto a bright open field at sunrise, seen from inside a dim room",
      "wide shot from inside", "bright sunrise backlight", "a new opportunity", "the door swings open"),
 55: ("GEN", "Small wooden blocks stacked into a growing tower on a desk, one block being placed on top by a hand",
      "close-up, hand only", "warm desk light", "steady building of expertise", "the block settles into place"),
 56: ("GEN", "A single young sapling standing firm while surrounding tall grass bends in the wind",
      "low angle", "golden late afternoon light", "unshaken", "grass sways while the sapling stays upright"),
 57: ("CARD", "꿈끼리 맵 시작: 중앙에 '꿈끼리' 노드만 등장"),
 58: ("GEN", "An old leather diary with a pressed flower and a fountain pen, no photos of people",
      "top-down close-up", "warm window light", "tender memory", "a page flutters slightly"),
 59: ("REAL", "성경 암송 앱 실제 화면 — 필수 1컷 (계정·이메일 마스킹)"),
 60: ("GEN", "A notebook with a hand-drawn career mind map and colored sticky notes, words not readable",
      "top-down", "soft daylight", "organizing a path", "a sticky note is pressed onto the page"),
 61: ("GEN", "An open Bible next to handwritten sheet music and a children's picture book on a wooden table",
      "slight high angle", "warm window light", "gentle, faithful creativity", "a soft breeze turns a page"),
 62: ("GEN", "A drawing tablet showing rough storyboard panels with simple silhouettes, stylus beside it",
      "over-the-desk, slight high angle", "cool screen light and warm lamp", "creative work in progress", "the stylus draws a line"),
 63: ("CARD", "꿈끼리 맵 애니메이션: '성경 암송 앱 / 찬양 / 웹소설 / 유튜브 / 작은 도구'가 둥글게 연결"),
 64: ("CARD", "맵 확장 — 연결선이 이어지며 조금씩 커짐"),
 65: ("GEN", "A small camera on a tripod facing a desk by a window, recording light on",
      "medium shot from the side", "soft window light", "documenting the journey", "the red recording light blinks"),
 66: ("GEN", "An unfinished wooden model under construction on a workbench with tools around",
      "medium close-up", "warm workshop light", "in progress, not finished", "wood shavings drift down"),
 67: ("GEN", "Crumpled paper drafts on a desk beside a fresh clean sheet",
      "top-down", "warm lamp light", "try, fail, try again", "a hand smooths out the new sheet"),
 68: ("GEN", "A finger pressing the power button of a laptop, a small teal light turning on",
      "extreme close-up", "dim room, teal button glow", "just start", "the light switches on"),
 69: ("CARD", "자막 강조: \"완벽주의 = 가장 큰 병목\" (핵심어 '병목' 금색)"),
 70: ("GEN", "A desk shown at night then the same desk at morning with a slightly fuller notebook",
      "static wide shot", "night lamp fading into morning light", "little by little", "time-lapse from night to morning"),
 71: ("GEN", "A phone and a small notebook on a cafe table during a short break, a half-finished coffee",
      "slight high angle", "soft cafe light", "using spare minutes", "steam curls from the coffee"),
 72: ("GEN", "Inside a subway car in the morning, hands holding a phone with blurred learning content",
      "over-the-shoulder, hands only", "morning light through the windows", "learning on the move", "the train gently sways"),
 73: ("GEN", "Stepping stones across a calm stream, the first stone lit by sunlight",
      "low angle", "warm sunlight", "one easy step first", "water ripples around the first stone"),
 74: ("GEN", "A gardener's hands tending young plants in a well-kept garden bed",
      "close-up, hands only", "soft morning light", "stewardship, responsibility", "hands gently firm the soil"),
 75: ("GEN", "A lantern glowing on a dark path",
      "medium shot, low angle", "warm lantern light in darkness", "goodness, guidance", "the flame flickers softly"),
 76: ("GEN", "A hand placing a pen down on a closed notebook on a tidy desk",
      "close-up", "warm lamp light", "quiet commitment", "the pen is set down"),
 77: ("GEN", "An empty crossroads path at dawn with soft fog",
      "wide shot", "pale dawn light", "uncertain beginnings", "fog slowly lifts"),
 78: ("GEN", "An open Bible and a laptop side by side on a desk in morning light",
      "slight high angle", "warm morning window light", "faith and dreams in daily life", "sunlight slowly spreads across the desk"),
 79: ("GEN", "Two cups of tea on a small table with one empty chair pulled out invitingly",
      "medium shot", "warm afternoon light", "invitation, together", "steam rises from both cups"),
 80: ("CARD", "CTA 자막: \"구독하고, 이번 주 낯선 도구 하나만 함께 켜 봐요.\" (배경음 살짝 고조 시작)"),
 81: ("GEN", "A quiet, tidy work desk by a window at dusk, empty chair, space left in the center for a channel title",
      "static wide shot", "warm low sunlight", "peaceful closing", "light slowly dims; channel name '꿈끼리' is added in editing"),
}

d = json.load(open("chunks.json", encoding="utf-8"))
chunks = d["chunks"]
assert set(P) == {c["id"] for c in chunks}, "장면 번호 불일치"


def tc(x):
    return f"{int(x // 60)}:{int(x % 60):02d}"


img = ["# 이미지 프롬프트 (전 구간)\n",
       f"화면 문체 키워드: `{STYLE}`\n",
       "- GEN: 구글 플로우에 그대로 붙여넣기 (본문 영어, 라벨만 한국어)",
       "- REAL: 생성하지 말고 실제 화면 녹화 사용 → `capture_list.md`",
       "- CARD: 편집 툴에서 텍스트 카드로 제작\n"]
sec = None
for c in chunks:
    if c["sec"] != sec:
        sec = c["sec"]
        img.append(f"\n## {sec}\n")
    p = P[c["id"]]
    head = f"**#{c['id']:02d} [{tc(c['start'])}–{tc(c['end'])}] {p[0]}** [{c['text']}]"
    if p[0] == "GEN":
        img.append(f"{head}\n```\n{p[1]} / {p[2]} / {p[3]} / {p[4]} / {p[5]}. {STYLE}\n```")
    else:
        img.append(f"{head}\n→ {p[1]}\n")
open("04_image_prompts.md", "w", encoding="utf-8").write("\n".join(img) + "\n")

gen = [c for c in chunks if P[c["id"]][0] == "GEN"][:10]
vid = ["# 영상(모션) 프롬프트 — 생성 이미지 앞 10개\n",
       "원본 지침의 '맨 앞 10개'를 생성(GEN) 장면 기준으로 적용. REAL·CARD 장면은 생성하지 않으므로 제외.\n"]
for c in gen:
    p = P[c["id"]]
    dur = max(3, min(5, round(c["end"] - c["start"])))
    vid.append(f"**#{c['id']:02d} [{tc(c['start'])}–{tc(c['end'])}]** [{c['text']}]\n```\n"
               f"{dur}-second shot. {p[1]}. Motion: {p[5]}. Camera: {p[2]}, "
               f"{'very slow push-in' if c['id'] % 2 else 'static with subtle handheld drift'}. "
               f"Lighting: {p[3]}. Mood: {p[4]}. No sudden transitions. {STYLE}\n```")
open("04_video_prompts.md", "w", encoding="utf-8").write("\n".join(vid) + "\n")

real = [c for c in chunks if P[c["id"]][0] == "REAL"]
cap = ["# 실제 화면 녹화·캡처 목록\n", "생성 이미지로 대체하면 안 되는 장면입니다 (증명 가능한 실제 경험).\n",
       "| # | 시간 | 내레이션 | 필요한 화면 |", "|---|---|---|---|"]
cap += [f"| {c['id']} | {tc(c['start'])}–{tc(c['end'])} | {c['text']} | {P[c['id']][1]} |" for c in real]
cap.append("\n녹화 전: 이메일·API 키·토큰·실명·타인 얼굴 → **** 또는 블러.")
open("capture_list.md", "w", encoding="utf-8").write("\n".join(cap) + "\n")

kinds = {k: sum(P[c["id"]][0] == k for c in chunks) for k in ("GEN", "REAL", "CARD")}
print(kinds, "영상 프롬프트", len(gen))
