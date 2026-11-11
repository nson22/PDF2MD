# PDF2MD

![Logo PDF2MD](assets/logo.png)

O PDF2MD converte PDFs em arquivos Markdown localmente. Use a interface gráfica para arrastar documentos ou o CLI para converter lotes pelo terminal. Os PDFs são processados no seu computador.

## Downloads

Baixe o aplicativo ou o CLI na [release mais recente](https://github.com/nson22/PDF2MD/releases/latest). Os pacotes incluem as dependências Python e as licenças dos componentes.

| Sistema | Arquitetura | Pacote | Como abrir |
| --- | --- | --- | --- |
| Windows | x64 | `*-Windows-x64.zip` | Extraia o ZIP e abra `PDF2MD.exe`. |
| Linux | x64 | `*-Linux-x64.tar.gz` | Extraia com `tar -xzf` e execute `./PDF2MD` em uma sessão gráfica. |
| macOS | Apple Silicon ou Intel | `*-macOS-arm64.tar.gz` ou `*-macOS-x64.tar.gz` | Extraia e abra `PDF2MD.app`. |

Os pacotes não são assinados para distribuição comercial. No Linux, os binários são compilados no Ubuntu 22.04 e a interface requer uma sessão gráfica com suporte a X11 ou XWayland.

## Aplicativo gráfico

1. Escolha a pasta de destino ou use a mesma pasta de cada PDF.
2. Arraste um ou mais PDFs para converter na hora. Para montar a fila antes da conversão, use **Adicionar PDFs** e depois **Converter para Markdown**.
3. Use busca, ordenação, filtros e caixas de seleção para organizar a fila. Um duplo clique no item mostra a saída ou o erro. O botão **?** (ou **F1**) abre a ajuda.

O aplicativo salva um arquivo `.md` em UTF-8 por PDF e preserva arquivos existentes com nomes como `relatório (1).md`. Cancelar interrompe a fila após o arquivo em andamento.

## CLI

Windows (PowerShell):

```powershell
.\PDF2MD-CLI.exe --help
.\PDF2MD-CLI.exe -o "markdown" "relatório.pdf" "outro arquivo.pdf"
```

Linux e macOS:

```sh
./PDF2MD-CLI --help
./PDF2MD-CLI -o "markdown" "relatório.pdf" "outro arquivo.pdf"
```

Sem `-o`, o Markdown fica ao lado do PDF de origem. O CLI imprime os caminhos gerados na saída padrão, registra erros na saída de erro e continua com os demais PDFs. Se alguma conversão falhar, retorna código `1`.

## Limites da conversão

A estrutura do Markdown depende do texto e do layout do PDF. PDFs digitalizados sem camada de texto precisam passar por OCR antes da conversão. Arquivos protegidos ou corrompidos podem falhar.

## Desenvolvimento

Requer Python 3.12 com Tcl/Tk. Em Linux, instale o pacote de Tkinter da sua distribuição para o Python usado no ambiente. No Windows, ative o ambiente com `.venv\Scripts\Activate.ps1`.

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
python cli.py --help
python smoke_test.py
```

O [workflow de release](.github/workflows/release.yml) compila e testa o aplicativo e o CLI em cada sistema antes de publicar. Para compilar localmente, execute `python release.py <plataforma>` em um sistema correspondente, por exemplo `python release.py Linux-x64`. Os pacotes são escritos em `dist/release/`. No Windows, `build.ps1` também gera as distribuições locais em `dist/` e substitui os artefatos da versão anterior.

## Licença e créditos

O código do PDF2MD está sob a [licença MIT](LICENSE). As distribuições incluem os avisos das dependências em `THIRD-PARTY-LICENSES/`.

- [MarkItDown](https://github.com/microsoft/markitdown) para conversão de PDF.
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) e [TkinterDnD2](https://pypi.org/project/tkinterdnd2/) para a interface.
- [Typer](https://github.com/fastapi/typer) para o CLI.
- [PyInstaller](https://github.com/pyinstaller/pyinstaller) para empacotamento.

