"""Build a reproducible source ZIP with a strict allowlist; never include local secrets."""
from pathlib import Path
import hashlib
import json
import zipfile
import shutil

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ('agent', 'apps', 'data', 'docs', 'evals', 'infra', 'mcp_servers', 'rag', 'tests', 'scripts', '.github')
FILES = ('README.md', 'START_HERE.md', 'Makefile', 'pyproject.toml', '.env.example', '.gitignore', '.dockerignore', 'render.yaml', 'requirements-lock.txt', 'submission.json')
SKIP = {'node_modules', '__pycache__', 'dist', 'processed', '.pytest_cache', 'playwright-report', 'test-results'}


def allowed(path):
    relative = path.relative_to(ROOT)
    return (not any(part in SKIP or part.startswith('.venv') for part in relative.parts)
            and '.env' not in relative.parts and not path.name.startswith('.env.')
            and path.name != 'traces.jsonl'
            and path.name != 'GigBid_Engineering_Review.pdf'
            and not any(suffix in path.name for suffix in ('.sqlite', '.pyc', '.tsbuildinfo')))


def package():
    output = ROOT / 'output/submission'
    output.mkdir(parents=True, exist_ok=True)
    paths = [ROOT / name for name in FILES if (ROOT / name).is_file()]
    for name in DIRECTORIES:
        paths.extend(path for path in (ROOT / name).rglob('*') if path.is_file() and allowed(path))
    paths = sorted(set(paths))
    target = output / 'GigBid_Source.zip'
    hashes = {}
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            relative = 'GigBid/' + path.relative_to(ROOT).as_posix()
            content = path.read_bytes()
            hashes[relative] = hashlib.sha256(content).hexdigest()
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content)
        archive.writestr('GigBid/SOURCE_MANIFEST.json', json.dumps(hashes, indent=2))
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    (output / 'SHA256SUMS.txt').write_text(f'{digest}  {target.name}\n', encoding='utf-8')
    print(f'{target} ({len(paths)} files); SHA256 {digest}')
    deliverables=[
        (ROOT/'output/pdf/GigBid_RnD_Report.pdf','GigBid_RnD_Report.pdf'),
        (ROOT/'output/demo/GigBid_3min_Demo.webm','GigBid_3min_Demo.webm'),
        (ROOT/'docs/TECHNICAL_WRITEUP.md','Technical_Writeup_Draft.md'),
        (ROOT/'docs/SUBMISSION_CHECKLIST.md','Submission_Checklist.md'),
        (ROOT/'submission.json','submission.json'),
    ]
    for source,name in deliverables:
        if not source.is_file():raise FileNotFoundError(f'Required local deliverable missing: {source}')
        shutil.copyfile(source,output/name)
    bundle=output/'GigBid_Final.zip'
    with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as archive:
        with zipfile.ZipFile(target) as source_archive:
            for entry in source_archive.infolist():
                archive.writestr(entry,source_archive.read(entry.filename))
        for path in [output/name for _,name in deliverables]:
            info=zipfile.ZipInfo('GigBid/deliverables/'+path.name,date_time=(1980,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,path.read_bytes())
    (output/'SHA256SUMS.txt').write_text('\n'.join(
        f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}'
        for path in [target,bundle]+[output/name for _,name in deliverables])+'\n',encoding='utf-8')
    print(f'{bundle}; read START_HERE.md and the explicit verification status in submission.json.')


if __name__ == '__main__':
    package()
