$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$pythonPaths = @($repositoryRoot)

if ($env:PYTHONPATH) {
    $pythonPaths += $env:PYTHONPATH
}

$env:PYTHONPATH = $pythonPaths -join [IO.Path]::PathSeparator

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 -m unittest discover -s (Join-Path $repositoryRoot 'NGIN') -p 'test*.py' -t $repositoryRoot -v
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    & python3 -m unittest discover -s (Join-Path $repositoryRoot 'NGIN') -p 'test*.py' -t $repositoryRoot -v
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python -m unittest discover -s (Join-Path $repositoryRoot 'NGIN') -p 'test*.py' -t $repositoryRoot -v
} else {
    throw 'Python 3 was not found. Install Python or add it to PATH.'
}

exit $LASTEXITCODE
