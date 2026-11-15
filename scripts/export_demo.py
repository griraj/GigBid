"""Export the actual browser recording as a narration-ready H.264 MP4.

Install the optional encoder with: python -m pip install imageio-ffmpeg
Run from the repository root: python scripts/export_demo.py
The original WebM is preserved. No footage is retimed or fabricated.
"""
from pathlib import Path
import json
import re
import subprocess
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/demo/GigBid_Silent_Demo.webm'
OUTPUT = ROOT / 'docs/demo/GigBid_Silent_Demo.mp4'
# Inspected source ranges for this take: exclude blank browser initialization
# and the redundant settled closing hold. Application actions stay at 1x speed.
SOURCE_IN_SECONDS = 2.5
SOURCE_OUT_SECONDS = 182.5


def main():
    if not SOURCE.is_file():
        raise SystemExit('Record first: cd apps/web && npm run record:demo')
    if OUTPUT.exists():
        raise SystemExit(f'Preserving existing export: {OUTPUT}')
    encoder = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([
        encoder, '-nostdin', '-hide_banner', '-n', '-i', str(SOURCE),
        '-map', '0:v:0', '-an', '-vf',
        f'trim=start={SOURCE_IN_SECONDS}:end={SOURCE_OUT_SECONDS},setpts=PTS-STARTPTS',
        '-c:v', 'libx264', '-preset', 'medium',
        '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
        str(OUTPUT),
    ], check=True)
    # Decode every frame to detect truncated or corrupt exports.
    subprocess.run([
        encoder, '-nostdin', '-v', 'error', '-xerror', '-i', str(OUTPUT),
        '-map', '0:v:0', '-f', 'null', '-',
    ], check=True)
    metadata = subprocess.run([encoder, '-hide_banner', '-i', str(OUTPUT)],
                              capture_output=True, text=True).stderr
    duration = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', metadata)
    seconds = (sum(float(v) * factor for v, factor in zip(duration.groups(),
               [3600, 60, 1])) if duration else None)
    (OUTPUT.parent / 'GigBid_Video_Info.json').write_text(json.dumps({
        'file': OUTPUT.name, 'duration_seconds': seconds,
        'bytes': OUTPUT.stat().st_size, 'video': 'H.264 / yuv420p',
        'audio': 'No audio stream; waiting for user narration',
        'verification': 'Entire exported video decoded successfully with -xerror',
        'provenance': 'Original Playwright capture; real application; synthetic data',
        'edit': {'source_in_seconds': SOURCE_IN_SECONDS,
                 'source_out_seconds': SOURCE_OUT_SECONDS, 'speed': 1,
                 'reason': 'Remove blank initialization and redundant closing hold'},
    }, indent=2) + '\n', encoding='utf-8')
    print(f'Exported and fully decoded: {OUTPUT}')


if __name__ == '__main__':
    main()
