# smile

> **상태: 진행 중 (main 브랜치 비어 있음)**
> 실제 작업물은 `claude/pycapcut-1bdnrc` 브랜치에 있고, 아직 main에 병합되지 않았습니다.

## 이 저장소는 무엇인가

`claude/pycapcut-1bdnrc` 브랜치에서 **edit-auto(캡컷 에이전트)** 를 개발 중입니다.
한국어 토킹 영상(mp4/mov)을 받아 무음·NG 구간을 잘라낸 캡컷(CapCut) 드래프트를 자동으로 만드는 도구입니다.
드래프트 생성에는 [pyCapCut](https://github.com/GuanYixuan/pyCapCut)을 사용합니다.

## 진행 현황

| 단계 | 내용 | 상태 |
|---|---|---|
| 1단 | 무음 구간 점프컷 → 캡컷 드래프트 생성 | 구현됨 (캡컷에서 재생 검증 필요) |
| 2단 이후 | 잔말·NG 컷, 단어별 자막(Whisper ASR) | 미착수 |
| 부가 | `ai-survival-video` 스킬 (저장소 이력 → 강의 영상) | 초안 |

## 브랜치 구조

| 브랜치 | 내용 |
|---|---|
| `main` | 초기 커밋과 이 README만 있음 |
| `claude/pycapcut-1bdnrc` | `capcut_agent/` 패키지, 테스트, Claude Code 스킬 |

## 다음 할 일

1. 브랜치의 1단 결과를 캡컷에서 직접 재생해 검증
2. 검증되면 main에 병합하고, 저장소 이름을 `edit-auto` 등 내용에 맞는 이름으로 변경 검토
