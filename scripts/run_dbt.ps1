# Loads .env from repo root, then runs `dbt build` with local profiles.
# Usage: powershell -File scripts\run_dbt.ps1   (from anywhere)

$repoRoot = Split-Path -Parent $PSScriptRoot

Get-Content "$repoRoot\.env" | ForEach-Object {
    if ($_ -match '^([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
        [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], "Process")
    }
}

& "$repoRoot\.venv\Scripts\dbt.exe" build `
    --project-dir "$repoRoot\dbt\lifebase" `
    --profiles-dir "$repoRoot\dbt\lifebase"
