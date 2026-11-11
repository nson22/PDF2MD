"""PDF2MD command line interface."""
from pathlib import Path
from typing import Annotated

import typer

from converter import convert_pdf


app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)


@app.command()
def convert(
    pdfs: Annotated[list[Path], typer.Argument(metavar='PDF...', help='Um ou mais arquivos PDF.')],
    output_dir: Annotated[
        Path | None,
        typer.Option('--output-dir', '-o', file_okay=False, help='Pasta de destino. Por padrão, usa a pasta de cada PDF.'),
    ] = None,
) -> None:
    """Converte arquivos PDF em Markdown localmente."""
    failed = False
    for pdf in pdfs:
        try:
            output = convert_pdf(pdf, output_dir if output_dir is not None else pdf.resolve().parent)
        except Exception as error:
            typer.echo(f'Erro em {pdf}: {error}', err=True)
            failed = True
        else:
            typer.echo(str(output))
    if failed:
        raise typer.Exit(code=1)


if __name__ == '__main__':
    app()
