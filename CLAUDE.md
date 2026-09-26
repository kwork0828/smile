# edit-auto

한국어 토킹 영상 자동 편집기 "캡컷 에이전트". 입력 mp4/mov → 출력 캡컷 드래프트.

## 작업 규칙

- 영상 편집 결과물은 항상 **pycapcut**으로 캡컷 드래프트를 만든다.
- 드래프트/자막/ASR 관련 코드를 만지기 전에 `.claude/skills/pycapcut-mac/SKILL.md`를 읽는다.
- 새 기술 함정을 발견하면 그 스킬의 "발견 로그"에 추가한다.
- 빌드 성공 ≠ 검증. 각 단계는 사용자가 캡컷에서 직접 재생해 확인한 뒤 다음 단계로 간다.
- 전체 대본(script)을 먼저 추출하고, 그걸로 NG/자막을 결정한다 (단어 단위 즉시 결정 금지).

## 빌드 단계

| 단계 | 내용 | 상태 |
|---|---|---|
| 1 | silence_detect + build_draft → 점프컷 드래프트 (CLI) | 구현, 캡컷 검증 대기 |
| 2 | FastAPI + 정적 HTML (drag/drop + SSE stepper) | 대기 |
| 3 | whisper Transcript + 세그먼트 자막 | 대기 |
| 4 | filler_ng + cuts + transcript 결과 카드 | 대기 |
| 5 | 영상 프리뷰 + 보존 구간 마킹 (`[` `]`) | 대기 |

## 명령

- 환경 점검: `python -m capcut_agent.env`
- 1단 실행: `python -m capcut_agent.cli 영상.mp4`
- 테스트: `python -m pytest -q`

## 스킬

- `pycapcut-mac`: 캡컷 드래프트 함정 레퍼런스
- `ai-survival-video`: Claude Code로 만든 저장소의 작업 기록 → "AI 생존기" 강의 영상 (캡컷 없이 edge-tts + Pillow + ffmpeg)
  - `python .claude/skills/ai-survival-video/scripts/render.py video/ep01/script.json`
