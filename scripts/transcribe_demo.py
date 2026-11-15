"""Transcribe the supplied narration locally for editable, measured cue timing.

Optional dependencies: pip install faster-whisper
Usage: python scripts/transcribe_demo.py path/to/narration.ogg
The model is downloaded to the ignored tmp directory; voice stays local.
"""
import argparse
import json
import os
import subprocess
from pathlib import Path
import numpy as np
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('HF_HUB_DISABLE_XET', '1')
os.environ.setdefault('HF_HOME', str(ROOT / 'tmp/huggingface'))
from faster_whisper import WhisperModel


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('audio', type=Path)
    args = parser.parse_args()
    model = WhisperModel('base.en', device='cpu', compute_type='int8',
                         download_root=str(ROOT / 'tmp/asr-models'))
    # Decode with FFmpeg to avoid PyAV API differences between releases.
    decoded = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-v', 'error',
        '-i', str(args.audio), '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'],
        check=True, capture_output=True).stdout
    waveform = np.frombuffer(decoded, dtype=np.float32)
    segments, info = model.transcribe(waveform, language='en',
        beam_size=5, word_timestamps=True, vad_filter=True,
        initial_prompt='GigBid freelance marketplace. LangGraph, MCP, portfolio evidence, '
        'Connects cost, idempotency keys, synthetic dataset, counteroffer.')
    result = []
    for item in segments:
        row = {'start': item.start, 'end': item.end, 'text': item.text.strip(),
               'words': [{'start': w.start, 'end': w.end, 'word': w.word,
                          'probability': w.probability} for w in item.words or []]}
        result.append(row)
        print(f'{item.start:.2f}-{item.end:.2f}: {item.text.strip()}', flush=True)
    destination = ROOT / 'tmp/narration-transcript-raw.json'
    destination.parent.mkdir(exist_ok=True, parents=True)
    destination.write_text(json.dumps({'language': info.language,
        'duration': info.duration, 'segments': result}, indent=2), encoding='utf-8')
    print(f'Saved: {destination}')


if __name__ == '__main__':
    main()
