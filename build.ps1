param([switch]$CliOnly)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (!(Test-Path '.venv/Scripts/python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE) { throw 'Falha ao criar ambiente Python.' }
}
& ./.venv/Scripts/python -m pip install -r requirements.txt
if ($LASTEXITCODE) { throw 'Falha ao instalar dependências.' }
& ./.venv/Scripts/python -m pip freeze | Set-Content -Encoding utf8 requirements.lock.txt
& ./.venv/Scripts/python create_icon.py
if ($LASTEXITCODE) { throw 'Falha ao gerar ícone.' }
function New-PortableArchive($Name, $Stage) {
    & ./.venv/Scripts/python notices.py $Stage
    if ($LASTEXITCODE) { throw 'Falha ao reunir licenças.' }
    Copy-Item README.md "$Stage/LEIA-ME.md"
    Copy-Item LICENSE "$Stage/LICENSE"
    Compress-Archive -Path "$Stage/*" -DestinationPath "build/$Name-Windows-x64.zip" -Force
}

if (!$CliOnly) {
    & ./.venv/Scripts/python -m PyInstaller --noconfirm --clean --windowed --onefile --name PDF2MD --distpath build/pdf2md-package --icon assets/app.ico --add-data 'assets/app.ico;assets' --add-data 'assets/logo.png;assets' --collect-all customtkinter --collect-all tkinterdnd2 --collect-all magika --collect-all onnxruntime --collect-all markitdown app.py
    if ($LASTEXITCODE) { throw 'Falha ao gerar aplicativo gráfico.' }
    New-PortableArchive PDF2MD build/pdf2md-package
}

& ./.venv/Scripts/python -m PyInstaller --noconfirm --clean --console --onefile --name PDF2MD-CLI --distpath build/pdf2md-cli-package --icon assets/app.ico --collect-all magika --collect-all onnxruntime --collect-all markitdown cli.py
if ($LASTEXITCODE) { throw 'Falha ao gerar CLI.' }
New-PortableArchive PDF2MD-CLI build/pdf2md-cli-package

New-Item -ItemType Directory -Force -Path dist | Out-Null
$releaseNames = if ($CliOnly) { @('PDF2MD-CLI') } else { @('PDF2MD', 'PDF2MD-CLI') }
foreach ($name in $releaseNames) {
    $stage = 'build/' + $name.ToLowerInvariant() + '-package'
    Move-Item -LiteralPath "$stage/$name.exe" -Destination "dist/$name.exe" -Force
    Move-Item -LiteralPath "build/$name-Windows-x64.zip" -Destination "dist/$name-Windows-x64.zip" -Force
    Write-Host "Pronto: dist/$name-Windows-x64.zip"
}

# Remove only former release names and copies from the previous root layout.
$legacy = '^(MarkItDownPortable(?:-Windows-x64)?|PDF2MD(?:-CLI)?-v?\d+(?:\.\d+)+(?:-Windows-x64)?)\.(exe|zip)$'
$rootCopies = '^PDF2MD(?:-CLI)?(?:-Windows-x64)?\.(exe|zip)$'
Get-ChildItem -LiteralPath '.', 'dist' -File | Where-Object {
    $_.Name -match $legacy -or ($_.DirectoryName -eq $PSScriptRoot -and $_.Name -match $rootCopies)
} | Remove-Item
