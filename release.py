"""Build, smoke-test and archive the two portable programs on the native OS."""
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from PIL import Image

from smoke_test import sample_pdf


ROOT = Path(__file__).resolve().parent
SUFFIX = '.exe' if sys.platform == 'win32' else ''


def build(name: str, stage: Path) -> Path:
    gui = name == 'PDF2MD'
    mac_app = gui and sys.platform == 'darwin'
    args = [
        sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
        '--name', name, '--distpath', str(stage),
        '--onedir' if mac_app else '--onefile',
        '--windowed' if gui else '--console',
        '--collect-all', 'magika', '--collect-all', 'onnxruntime', '--collect-all', 'markitdown',
    ]
    if gui:
        args.extend(['--collect-all', 'customtkinter', '--collect-all', 'tkinterdnd2'])
        for asset in ('app.ico', 'app.png', 'logo.png'):
            args.extend(['--add-data', f'assets/{asset}:assets'])
    if sys.platform == 'win32':
        args.extend(['--icon', 'assets/app.ico'])
    if mac_app:
        icon = stage.parent / 'app.icns'
        with Image.open(ROOT / 'assets/app.png') as image:
            image.save(icon)
        args.extend(['--icon', str(icon), '--osx-bundle-identifier', 'io.github.nson22.pdf2md'])
    subprocess.run([*args, 'app.py' if gui else 'cli.py'], cwd=ROOT, check=True)
    return stage / (f'{name}.app' if mac_app else f'{name}{SUFFIX}')


def smoke_test(product: Path, work: Path) -> None:
    if product.name in ('PDF2MD.app', f'PDF2MD{SUFFIX}'):
        executable = product / 'Contents/MacOS/PDF2MD' if product.suffix == '.app' else product
        report = work / 'gui-smoke.txt'
        result = subprocess.run([str(executable), '--smoke-test', str(report)], cwd=work, timeout=180)
        if report.exists():
            print(report.read_text(encoding='utf-8'), flush=True)
        result.check_returncode()
        if not report.read_text(encoding='utf-8').startswith('PASS:'):
            raise RuntimeError('GUI smoke test did not pass.')
        return

    pdf = work / 'document with spaces.pdf'
    bad_pdf = work / 'invalid.pdf'
    sample_pdf(pdf)
    bad_pdf.write_bytes(b'invalid')
    subprocess.run([str(product), '--help'], cwd=work, check=True, timeout=120)
    output = work / 'markdown'
    result = subprocess.run([str(product), '-o', str(output), str(bad_pdf), str(pdf)], cwd=work, timeout=120)
    if result.returncode != 1 or 'Portable conversion test' not in (output / 'document with spaces.md').read_text(encoding='utf-8'):
        raise RuntimeError('CLI did not convert the valid PDF and report the invalid one.')


def archive(product: Path, platform_name: str, release: Path, notices: Path) -> Path:
    name = product.stem if product.suffix else product.name
    inputs = [product, ROOT / 'README.md', ROOT / 'LICENSE', notices]
    if sys.platform == 'win32':
        destination = release / f'{name}-{platform_name}.zip'
        with ZipFile(destination, 'w', compression=ZIP_DEFLATED) as bundle:
            for path in inputs:
                for file in path.rglob('*') if path.is_dir() else (path,):
                    if file.is_file():
                        bundle.write(file, Path(path.name) / file.relative_to(path) if path.is_dir() else path.name)
    else:
        destination = release / f'{name}-{platform_name}.tar.gz'
        with tarfile.open(destination, 'w:gz', compresslevel=5) as bundle:
            for path in inputs:
                bundle.add(path, arcname=path.name)
    return destination


def main() -> None:
    os_name = {'Windows': 'Windows', 'Linux': 'Linux', 'Darwin': 'macOS'}[platform.system()]
    arch = {'AMD64': 'x64', 'x86_64': 'x64', 'arm64': 'arm64', 'aarch64': 'arm64'}[platform.machine()]
    platform_name = f'{os_name}-{arch}'
    if sys.argv[1:] != [platform_name]:
        raise SystemExit(f'Usage: python release.py {platform_name}')
    release = ROOT / 'dist/release'
    release.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='pdf2md-release-') as folder:
        work = Path(folder).resolve()
        subprocess.run([sys.executable, str(ROOT / 'notices.py'), str(work)], check=True)
        packages = []
        for name in ('PDF2MD', 'PDF2MD-CLI'):
            product = build(name, work / name)
            smoke_test(product, work)
            packages.append(archive(product, platform_name, work, work / 'THIRD-PARTY-LICENSES'))
        for package in packages:
            shutil.move(str(package), str(release / package.name))
            print(release / package.name, flush=True)


if __name__ == '__main__':
    main()
