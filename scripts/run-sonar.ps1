param(
  [string]$HostUrl = "https://sonarcloud.io",
  [string]$ProjectDir
)

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$resolvedProjectDir = if ($ProjectDir) {
  (Resolve-Path $ProjectDir).ProviderPath
} else {
  (Resolve-Path (Join-Path $scriptRoot ".." )).ProviderPath
}
$resolvedProjectDir = [System.IO.Path]::GetFullPath($resolvedProjectDir).TrimEnd('\\')
$dockerProjectDir = if ($resolvedProjectDir -like '\\wsl.localhost\*') {
  ($resolvedProjectDir -replace '^\\\\wsl\.localhost\\', '//wsl.localhost/') -replace '\\', '/'
} else {
  $resolvedProjectDir
}

if (-not $env:SONAR_TOKEN) {
  Write-Error '[sonar] SONAR_TOKEN is not set. Run $env:SONAR_TOKEN="<token>" first.'
  exit 1
}

$scannerImage = if ($env:SONAR_SCANNER_IMAGE) {
  $env:SONAR_SCANNER_IMAGE
} else {
  'sonarsource/sonar-scanner-cli:12.0.0.3214_8.0.1'
}

Write-Host "[sonar] project: $dockerProjectDir"
Write-Host "[sonar] host: $HostUrl"
Write-Host "[sonar] image: $scannerImage"

docker run --rm `
  -w /usr/src `
  -e SONAR_HOST_URL="$HostUrl" `
  -e SONAR_TOKEN="$env:SONAR_TOKEN" `
  -v "${dockerProjectDir}:/usr/src" `
  $scannerImage `
  --define "sonar.projectBaseDir=/usr/src" `
  --define "sonar.projectKey=Nycopaderayon03_March-03-30-2026" `
  --define "sonar.organization=nycopaderayon03" `
  --define "sonar.sources=." `
  --define "sonar.exclusions=.venv/**,venv/**,__pycache__/**,logs/**,media/**,staticfiles/**,db.sqlite3"

exit $LASTEXITCODE
