# edit-auto — 캡컷 에이전트

한국어 토킹 영상 자동 편집기. `mp4/mov` → 캡컷 드래프트 (무음·잔말·NG 컷 + 단어별 자막).
드래프트 생성은 [pycapcut](https://github.com/GuanYixuan/pyCapCut)을 사용합니다.

> 현재 **1단(무음 점프컷)** 까지 구현. 캡컷에서 재생 검증 후 2단으로 진행합니다.

## Step 0. 환경 점검

```bash
python3 -c "import platform; print(platform.system(), platform.machine())"
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m capcut_agent.env
```

| OS | 트랙 | ASR (3단부터) | 필요 도구 |
|---|---|---|---|
| Mac M칩 (Darwin arm64) | A | mlx-whisper | `brew install python@3.11 ffmpeg mediainfo` |
| Windows (AMD64) | C | faster-whisper (+MP4 export) | python.org 3.11, `winget install ffmpeg` |
| 그 외 | fallback | faster-whisper | ffmpeg, mediainfo |

CapCut 드래프트 폴더가 없으면 캡컷 설치 → 1회 실행 → 빈 프로젝트 1개 생성.

## 1단 실행: 무음 점프컷

```bash
# 캡컷을 종료한 상태에서 실행
python -m capcut_agent.cli ~/Desktop/talk.mp4
```

옵션: `--noise -35` (무음 기준 dB), `--min-silence 0.5`, `--pad 0.12`, `--name`, `--replace`

### 검증 체크리스트 (캡컷에서 직접)

- [ ] 캡컷 프로젝트 목록에 `talk_jumpcut`이 보인다 (길이가 0:00이 아니다)
- [ ] 열었을 때 미디어 누락(빨간/검은 화면)이 없다
- [ ] 처음부터 끝까지 재생 시 컷 이음새에서 말 끝/첫음절이 잘리지 않는다
- [ ] 무음이 충분히 빠졌다 (덜 빠지면 `--noise -30`, 말이 잘리면 `--pad 0.2`)

결과(스크린샷, 어색한 구간 타임코드)를 알려주면 파라미터/함정을 반영한 뒤 2단으로 갑니다.

## 구조

```
capcut_agent/
  env.py      Step 0 OS 감지, 드래프트 폴더 탐색
  silence.py  ffmpeg silencedetect → keep ranges
  draft.py    pycapcut 드래프트 생성 (Mac 함정 대응)
  cli.py      1단 CLI
.claude/skills/pycapcut-mac/SKILL.md   기술 함정 레퍼런스
```
