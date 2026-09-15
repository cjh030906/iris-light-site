"""음성 안내 클립 다듬기 — 앞 숨소리를 줄이고, 끊긴 끝을 자연스럽게 맺는다.

Qwen3-TTS 출력은 두 가지 버릇이 있다.
1. 말 시작 전에 낮은 숨소리·잡음이 0.5초 가까이 붙는다.
2. 끝 음절의 여운이 최대 음량에서 뚝 끊긴다. "습니다"가 "습니"처럼 들리고
   파형이 0이 아닌 데서 멈춰 딸깍 소리가 난다.

그래서 새로 합성할 때마다 이 스크립트를 한 번 통과시킨다.

    python tools/polish_voice.py media/voice/*.mp3
    python tools/polish_voice.py --dry-run media/voice/10-team.mp3
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

FRAME_MS = 20.0
ONSET_DB = -35.0  # 피크 대비 이만큼 아래면 아직 말이 아니다 (숨소리·잡음)
LEAD_MS = 120.0   # 말 시작 앞에 남길 여백
FADE_MS = 60.0    # 끊긴 끝을 재우는 길이
TAIL_MS = 350.0   # 뒤에 붙일 무음
SAMPLE_RATE = 24000
BITRATE = "64k"


def _frame_rms(x: np.ndarray, sr: int) -> tuple[np.ndarray, int]:
    frame = max(1, int(sr * FRAME_MS / 1000.0))
    n = x.size // frame
    if n < 2:
        return np.array([]), frame
    blocks = x[: n * frame].reshape(n, frame)
    return np.sqrt(np.mean(np.square(blocks), axis=1) + 1e-12), frame


def polish(x: np.ndarray, sr: int) -> np.ndarray:
    rms, frame = _frame_rms(x, sr)
    if rms.size == 0:
        return x

    voiced = np.nonzero(rms >= rms.max() * (10.0 ** (ONSET_DB / 20.0)))[0]
    if voiced.size == 0:
        return x

    start = max(0, voiced[0] * frame - int(sr * LEAD_MS / 1000.0))
    end = min(x.size, (voiced[-1] + 1) * frame)
    out = x[start:end].copy()

    # 시작부 딸깍 방지 — 첫 음소를 뭉개지 않게 아주 짧게만
    rise = min(int(sr * 0.008), out.size)
    if rise > 1:
        out[:rise] *= np.linspace(0.0, 1.0, rise)

    # 끝이 잘려 있어도 여운처럼 들리게 재운 뒤 무음을 붙인다
    fall = min(int(sr * FADE_MS / 1000.0), out.size)
    if fall > 1:
        out[-fall:] *= np.linspace(1.0, 0.0, fall)

    return np.concatenate([out, np.zeros(int(sr * TAIL_MS / 1000.0), dtype=out.dtype)])


def process(path: Path, *, dry_run: bool) -> None:
    x, sr = sf.read(path, dtype="float32", always_2d=False)
    if x.ndim > 1:
        x = x.mean(axis=1)

    out = polish(x, sr)
    print(f"{path.name:16s} {x.size / sr:5.2f}s -> {out.size / sr:5.2f}s", end="")
    if dry_run:
        print("  (dry-run)")
        return

    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "polished.wav"
        sf.write(wav, out, sr)
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav),
             "-ac", "1", "-ar", str(SAMPLE_RATE), "-b:a", BITRATE,
             "-codec:a", "libmp3lame", str(path)],
            check=True,
        )
    print("  ok")


def main() -> int:
    ap = argparse.ArgumentParser(description="음성 안내 클립 다듬기")
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--dry-run", action="store_true", help="바꾸지 않고 길이만 보여 준다")
    args = ap.parse_args()

    for path in args.files:
        if not path.is_file():
            print(f"건너뜀 (없음): {path}", file=sys.stderr)
            continue
        process(path, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
