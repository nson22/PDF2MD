"""Include installed dependency license texts alongside the portable distribution."""
from importlib.metadata import distributions
from pathlib import Path
import sys

root = Path(sys.argv[1]) / 'THIRD-PARTY-LICENSES'
root.mkdir(parents=True, exist_ok=True)
index = []
for dist in distributions():
    name = dist.metadata['Name']
    index.append(f'{name} {dist.version} — {dist.metadata.get("License-Expression") or dist.metadata.get("License") or "See included license files"}')
    for item in dist.files or []:
        if any(word in item.name.lower() for word in ('license', 'copying', 'notice')):
            path = Path(dist.locate_file(item))
            if path.is_file():
                output = root / name / str(item).replace('../', '').replace('..\\', '')
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(path.read_bytes())
(root / 'INDEX.txt').write_text('\n'.join(index), encoding='utf-8')
