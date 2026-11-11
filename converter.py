"""Local PDF conversion, with exclusive output creation to preserve existing files."""
from pathlib import Path


def convert_pdf(source: Path, destination: Path, engine=None) -> Path:
    source = Path(source).resolve(strict=True)
    if source.suffix.lower() != '.pdf' or not source.is_file():
        raise ValueError('Selecione um arquivo PDF válido.')
    with source.open('rb') as stream:
        if b'%PDF-' not in stream.read(1024):
            raise ValueError('O arquivo não possui um cabeçalho PDF válido.')
    if engine is None:
        from markitdown import MarkItDown
        engine = MarkItDown(enable_plugins=False)
    result = engine.convert_local(str(source))
    content = result.text_content
    if not content.strip():
        raise ValueError('PDF sem texto extraível. Pode precisar de OCR.')
    destination.mkdir(parents=True, exist_ok=True)
    index = 0
    while True:
        suffix = f' ({index})' if index else ''
        target = destination / f'{source.stem}{suffix}.md'
        try:
            stream = target.open('x', encoding='utf-8', newline='\n')
        except FileExistsError:
            index += 1
            continue
        try:
            with stream:
                stream.write(content)
        except Exception:
            target.unlink(missing_ok=True)
            raise
        return target
