# script.json 형식

경로는 `video/epNN/script.json`. 이미지 경로는 **script.json 기준 상대경로**.

```json
{
  "episode": "EP01",
  "series": "AI 생존기",
  "title": "비개발자가 Claude Code로 첫 앱 뼈대 만들기",
  "thumb_title": "코딩 몰라도\n앱 뼈대 30분",
  "voice": "ko-KR-InJoonNeural",
  "upload": {
    "title": "[AI 생존기 EP01] 비개발자가 Claude Code로 첫 앱 뼈대 만들기",
    "description": "이 편에서는 ...\n\n사용한 프롬프트는 영상 속 화면 그대로입니다.",
    "tags": ["AI생존기", "ClaudeCode", "바이브코딩", "비개발자"]
  },
  "scenes": [
    {"type": "title", "title": "첫 앱 뼈대 만들기", "sub": "성경암송 앱 제작기 1편",
     "narration": ["안녕하세요, AI 생존기입니다.", "오늘은 코딩 없이 앱 뼈대를 만듭니다."]},

    {"type": "explain", "heading": "이 편이 끝나면", "chapter": "오늘의 결과물",
     "bullets": ["내 컴퓨터에서 돌아가는 앱 화면", "다음 편에 쓸 작업 기록 파일"],
     "narration": ["이 편이 끝나면 두 가지가 생겨요.", "..."]},

    {"type": "prompt", "heading": "따라 쳐 보세요", "chapter": "첫 프롬프트", "min_sec": 5,
     "prompt": "PRD.md를 읽고 1단계 작업만 해줘. 끝나면 멈추고 보고해.",
     "narration": ["화면의 문장을 그대로 입력해 보세요.", "..."]},

    {"type": "code", "heading": "AI가 만든 저장 로직", "file": "src/db.ts",
     "code": "export const db = new Dexie('bible');\ndb.version(1).stores({\n  verses: 'id, book'\n});",
     "start_line": 12, "highlight": [13, 14],
     "narration": ["노란 줄이 핵심이에요.", "..."]},

    {"type": "screen", "heading": "첫 실행 화면", "image": "../../docs/screenshot.png",
     "capture_hint": "npm run dev 후 브라우저 첫 화면",
     "narration": ["실행하면 이렇게 보여요."]},

    {"type": "explain", "heading": "AI 자동 vs 사람 손",
     "bullets": ["AI: 파일 구조와 코드 작성", "사람: 1단계에서 멈추라고 범위 지정"],
     "narration": ["여기가 오늘의 핵심이에요.", "..."]},

    {"type": "recap", "heading": "오늘 정리", "chapter": "정리",
     "bullets": ["PRD부터 쓰고 시킨다", "단계마다 멈추게 한다"],
     "next": "EP02 — 막혔을 때 AI에게 되묻는 법",
     "narration": ["오늘 두 가지를 기억하세요.", "다음 편에서는 막혔을 때 대처법을 봅니다."]}
  ]
}
```

## 필드

| 필드 | 장면 | 설명 |
|---|---|---|
| `type` | 공통 | title / explain / prompt / code / screen / recap |
| `narration` | 공통 | 문장 배열. 한 문장 40자 이내 |
| `chapter` | 공통(선택) | 있으면 upload.txt 챕터로 들어감 |
| `min_sec` | 공통(선택) | 최소 노출 초. prompt 기본 3 |
| `heading` | explain/prompt/code/screen/recap | 장면 제목 |
| `bullets` | explain/recap | 4개 이하 권장 (하단 자막 영역 침범 방지) |
| `body` | explain | bullets 대신 문단 |
| `prompt` | prompt | 따라 칠 문장 (\n 줄바꿈 가능) |
| `code`, `file`, `start_line`, `highlight` | code | 15줄 이하, highlight는 원본 줄 번호 |
| `image`, `capture_hint` | screen | 이미지 없으면 설명 슬라이드로 대체 + need_capture.md |
| `next` | recap | 다음 편 예고 (마지막 장면 필수) |

분량 감각: 문장 1개 ≈ 4~5초. 5~8분 = 약 60~90문장, 장면 12~20개.
