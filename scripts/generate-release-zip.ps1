param(
  [string]$Output = "callchat-community-release.zip"
)

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$temp = Join-Path ([System.IO.Path]::GetTempPath()) ("callchat-community-" + [guid]::NewGuid().ToString("N"))

New-Item -ItemType Directory -Path $temp | Out-Null

$exclude = @(
  ".git",
  "zmath-private",
  "shield-private",
  "backups",
  "node_modules",
  "dist",
  "build"
)

Get-ChildItem -Path $root -Force | Where-Object { $exclude -notcontains $_.Name } | ForEach-Object {
  Copy-Item -Path $_.FullName -Destination $temp -Recurse -Force
}

if (Test-Path $Output) {
  Remove-Item -Path $Output -Force
}

Compress-Archive -Path (Join-Path $temp "*") -DestinationPath $Output -Force
Remove-Item -Path $temp -Recurse -Force

Write-Host "Wrote $Output"
