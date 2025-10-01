<#
build.ps1 - Compila la tesis dentro de la carpeta build/

Uso:
  .\build.ps1       # compila usando latexmk si está; si no, usa pdflatex+bibtex

Qué hace:
  - crea/limpia la carpeta build/
  - copia los fuentes relevantes (Tesis.tex, chapters/, sty/, bibliography/) a build/
  - ejecuta la compilación dentro de build/ y deja los artefactos ahí
#>

param()

set -e

$root = Split-Path -Path $PSScriptRoot -Parent
Push-Location $PSScriptRoot

Write-Host "Preparando carpeta build/..."
if (Test-Path build) { Remove-Item -Recurse -Force build }
New-Item -ItemType Directory -Path build | Out-Null

Write-Host "Copiando archivos fuente a build/"
Copy-Item -Recurse -Force Tesis.tex build\Tesis.tex
if (Test-Path chapters) { Copy-Item -Recurse -Force chapters build\chapters }
if (Test-Path sty) { Copy-Item -Recurse -Force sty build\sty }
if (Test-Path bibliography) { Copy-Item -Recurse -Force bibliography build\bibliography }

Push-Location build

function Run-Command($cmd, $desc) {
    Write-Host "==> $desc: $cmd"
    $proc = Start-Process -FilePath cmd -ArgumentList "/c", $cmd -NoNewWindow -Wait -PassThru
    if ($proc.ExitCode -ne 0) { throw "Comando falló: $cmd (exit $($proc.ExitCode))" }
}

if (Get-Command latexmk -ErrorAction SilentlyContinue) {
    Run-Command "latexmk -pdf -interaction=nonstopmode -file-line-error Tesis.tex" "Compilando con latexmk"
} else {
    Run-Command "pdflatex -interaction=nonstopmode -file-line-error Tesis.tex" "pdflatex (1)"
    if (Test-Path "Tesis.aux") {
        Run-Command "bibtex Tesis" "bibtex"
    }
    Run-Command "pdflatex -interaction=nonstopmode -file-line-error Tesis.tex" "pdflatex (2)"
    Run-Command "pdflatex -interaction=nonstopmode -file-line-error Tesis.tex" "pdflatex (3)"
}

Write-Host "Compilación completada. Artefactos en: $(Resolve-Path .)"

Pop-Location
Pop-Location
