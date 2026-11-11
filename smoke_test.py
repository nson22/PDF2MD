"""Exercise real conversion and the GUI without external test dependencies."""
from pathlib import Path
import tempfile
from time import monotonic, sleep
from converter import convert_pdf


def sample_pdf(path):
    content = b'BT /F1 18 Tf 72 720 Td (Portable conversion test) Tj ET'
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>',
               b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
               b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
               b'<< /Length ' + str(len(content)).encode() + b' >>\nstream\n' + content + b'\nendstream']
    data = bytearray(b'%PDF-1.4\n')
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data.extend(f'{number} 0 obj\n'.encode() + obj + b'\nendobj\n')
    start = len(data)
    data.extend(b'xref\n0 6\n0000000000 65535 f \n')
    for offset in offsets[1:]:
        data.extend(f'{offset:010d} 00000 n \n'.encode())
    data.extend(f'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{start}\n%%EOF'.encode())
    path.write_bytes(data)


def run(report):
    from app import App
    with tempfile.TemporaryDirectory(prefix='pdf2md-test-') as temp:
        root = Path(temp).resolve()
        source = root / 'documento com espaços.pdf'
        sample_pdf(source)
        target = convert_pdf(source, root)
        assert 'Portable conversion test' in target.read_text(encoding='utf-8')
        assert convert_pdf(source, root).name == 'documento com espaços (1).md'
        broken = root / 'broken.pdf'
        broken.write_bytes(b'not a PDF')
        try:
            convert_pdf(broken, root)
        except Exception:
            pass
        else:
            raise AssertionError('Invalid PDF accepted')
        app = App()
        app.withdraw()
        assert app.title() == 'PDF2MD'
        app.help_button.invoke()
        assert app.help_window.title() == 'Ajuda do PDF2MD'
        app.help_window.destroy()
        manual = root / 'manual.pdf'
        second = root / 'segundo.pdf'
        sample_pdf(manual)
        sample_pdf(second)
        app.add_files([manual])
        app.destination = root / 'automatico'
        app.on_drop(type('Drop', (), {'data': app.tk.call('list', str(source), str(source), str(second))})())
        assert app.busy and len(app.files) == 3
        deadline = monotonic() + 15
        while app.busy and monotonic() < deadline:
            app.update()
            sleep(0.02)
        assert not app.busy
        assert {p.name for p in app.destination.glob('*.md')} == {source.with_suffix('.md').name, 'segundo.md'}
        app.add_files([broken])
        app.worker([broken, source], root / 'batch')
        app.poll()
        assert (root / 'batch' / 'documento com espaços.md').exists()
        assert 'cabeçalho' in app.files[broken].detail
        assert app.files[broken].state == 'Erro'
        app.query.set('com espaços')
        assert app.tree.get_children() == (str(source),)
        app.toggle_all()
        assert app.checked == {source}
        app.query.set('')
        app.filter.set('Com erro')
        app.refresh_queue()
        assert app.tree.get_children() == (str(broken),)
        app.stop.set()
        app.worker([source], root / 'cancelled')
        assert not (root / 'cancelled').exists()
        app.clear_files()
        assert not app.files
        app.destroy()
    Path(report).write_text('PASS: real PDF conversion, collision preservation, invalid PDF, GUI, automatic batch drop, deduplication, batch error isolation, cancellation.\n', encoding='utf-8')


if __name__ == '__main__':
    run('smoke-result.txt')
