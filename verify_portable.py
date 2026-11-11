"""Verify a lone executable from an unrelated directory, including its icon."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import pefile

source = Path('dist/PDF2MD.exe').resolve()
binary = pefile.PE(str(source))
assert any(entry.id == 14 for entry in binary.DIRECTORY_ENTRY_RESOURCE.entries), 'Missing executable icon'
binary.close()
with tempfile.TemporaryDirectory(prefix='PDF2MD portable ') as folder:
    executable = Path(folder) / source.name
    shutil.copy2(source, executable)
    report = Path(folder) / 'result.txt'
    result = subprocess.run([str(executable), '--smoke-test', str(report)], cwd=folder,
                            timeout=120, creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode == 0, result.returncode
    text = report.read_text(encoding='utf-8')
    assert text.startswith('PASS:'), text
    Path('smoke-result-standalone.txt').write_text('Executable icon: PASS\nStandalone executable with no adjacent dependencies: ' + text, encoding='utf-8')
    print(text)
