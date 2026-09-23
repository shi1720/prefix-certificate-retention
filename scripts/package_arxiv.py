"""Build a minimal source archive without local environments or private files."""
from pathlib import Path
import tarfile,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'output/prefix-certificate-retention-arxiv.tar.gz'
files=[(ROOT/'paper/main.tex','main.tex'),(ROOT/'paper/references.bib','references.bib'),
       (ROOT/'output/pdf/main.bbl','main.bbl')]
for path in sorted((ROOT/'paper/figures').glob('*.pdf')):
    files.append((path,'figures/'+path.name))
for path in sorted((ROOT/'paper/tables').glob('*.tex')):
    files.append((path,'tables/'+path.name))
for path,_ in files:
    if not path.is_file():raise FileNotFoundError(path)
with tarfile.open(out,'w:gz') as tar:
    for path,name in files:
        info=tar.gettarinfo(str(path),arcname=name)
        info.uid=info.gid=0;info.uname=info.gname='';info.mtime=1790121600
        with path.open('rb') as f:tar.addfile(info,f)
manifest={name:hashlib.sha256(path.read_bytes()).hexdigest() for path,name in files}
(ROOT/'output/arxiv_source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(out)
