# Load environment variables from .env file
# Usage: . .\load-env.ps1

if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]*)\s*=\s*(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, 'Process')
            Write-Host "✓ Loaded: $name" -ForegroundColor Green
        }
    }
    Write-Host "`n✅ Environment variables loaded from .env" -ForegroundColor Cyan
} else {
    Write-Host "⚠️  .env file not found. Create one from .env.example" -ForegroundColor Yellow
    Write-Host "   Copy-Item .env.example .env" -ForegroundColor Gray
}
