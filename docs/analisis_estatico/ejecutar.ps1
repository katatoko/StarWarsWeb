# Compila las APIs y la WebApp con analizadores y genera el informe de análisis estático.
# Uso (desde cualquier carpeta):  powershell -ExecutionPolicy Bypass -File docs\analisis_estatico\ejecutar.ps1
$ErrorActionPreference = "Stop"
$dir  = $PSScriptRoot
$repo = (Resolve-Path (Join-Path $dir "..\..")).Path
$out  = Join-Path $dir "advertencias-compilador.txt"

$proys = "2.- Backend\2.1- Microservices\StarWars.Api",
         "1.- Frontend\WebApp\StarWarsWeb" | ForEach-Object { Join-Path $repo $_ }

Write-Host "1/3 Limpiando compilaciones anteriores..."
foreach ($p in $proys) { dotnet clean $p -v:q | Out-Null }

Write-Host "2/3 Compilando con analizadores (tarda unos minutos)..."
if (Test-Path $out) { Remove-Item $out }
foreach ($p in $proys) {
    Write-Host "   $(Split-Path $p -Leaf)"
    dotnet build $p -p:AnalysisMode=Recommended -p:RunAnalyzers=true -clp:NoSummary | Out-File $out -Append -Encoding utf8
}

Write-Host "3/3 Generando informe..."
$py = if (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python" }
& $py (Join-Path $dir "analisis_estatico.py") $repo
if ($LASTEXITCODE -ne 0) { throw "El análisis falló. Revisa el mensaje anterior." }

Write-Host "Listo. Abre: $(Join-Path $dir 'Informe-Analisis-Estatico-StarWarsWeb.pdf')"
