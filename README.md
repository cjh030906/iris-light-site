# IRIS Light — 소개 사이트

[Project IRIS Light](https://github.com/kwakminoo/Project-IRIS-Light) 의 소개 페이지입니다.
시연 영상과 음성 안내가 들어 있어 용량이 커서 앱 저장소와 분리했습니다.

**https://cjh030906.github.io/iris-light-site/**

## 구성

| 경로 | 설명 |
|------|------|
| `index.html` | 페이지 전부 — 스타일과 스크립트가 한 파일에 들어 있습니다 |
| `media/iris-demo.mp4` | 시연 영상 (3:31) · `iris-demo-poster.webp` 는 첫 화면 |
| `media/voice/*.mp3` | 섹션마다 재생되는 IRIS 음성 안내 (24kHz mono 64kbps) |
| `shots/` | 실제 화면 캡처 |

## 고칠 때

`index.html` 만 고쳐서 `main` 에 올리면 GitHub Pages 가 바로 반영합니다.
빌드 단계는 없습니다.

음성 안내 문구를 바꾸면 해당 mp3 도 같이 다시 만들어야 합니다. 원문 텍스트는
따로 보관하지 않으므로, 앱 저장소의 `.venv-voice` 에서 이렇게 확인하고 다시 만듭니다.

```powershell
# 지금 뭐라고 읽는지 확인
.\.venv-voice\Scripts\python.exe -c "from faster_whisper import WhisperModel; m=WhisperModel('small',device='cpu',compute_type='int8'); print(''.join(s.text for s in m.transcribe(r'07-install.mp3', language='ko')[0]))"

# 같은 보이스 프로필로 다시 합성
$env:VOICE_RUNTIME_MOCK=0
.\.venv-voice\Scripts\python.exe scripts\preview_voice_profile.py --tone narration --text "새 문구" --out out

# 다른 클립과 같은 포맷으로 인코딩
ffmpeg -y -i out\narration.wav -ac 1 -ar 24000 -b:a 64k -codec:a libmp3lame media\voice\07-install.mp3

# 반드시 마지막에 — 빠뜨리면 숨소리가 길고 끝음절이 잘려 들린다
python tools\polish_voice.py media\voice\07-install.mp3
```

**`tools/polish_voice.py` 를 건너뛰지 말 것.** Qwen3-TTS 출력은 말 시작 전에 낮은
숨소리가 0.5초 가까이 붙고, 끝 음절의 여운이 최대 음량에서 뚝 끊긴다. 그대로 두면
"습니다"가 "습니"처럼 들리고 딸깍 소리가 난다. 스크립트가 앞 여백을 120ms로 맞추고,
끝을 60ms 페이드로 재운 뒤 무음 350ms를 붙인다. 고유명사는 한글로 적으면 발음이
어긋날 수 있으니(`올라마` → "온라마") 합성 입력에 `Ollama` 처럼 원래 표기로 넣는다.

## 다운로드 버튼

설치 프로그램은 앱 저장소의 릴리스에서 받습니다. 주소가 고정이라 에셋 이름이
`IRIS-Setup.exe` 여야 합니다.

```
https://github.com/kwakminoo/Project-IRIS-Light/releases/latest/download/IRIS-Setup.exe
```
