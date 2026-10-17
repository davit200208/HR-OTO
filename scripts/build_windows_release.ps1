$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$release = Join-Path $root 'releases'

function Require-Command($name, $installHint) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) { throw "$name is unavailable. $installHint" }
}

Require-Command flutter 'Install Flutter stable and run flutter doctor.'
Require-Command iscc 'Install Inno Setup 6 before packaging Setup.exe.'
if (-not (Test-Path (Join-Path $root 'assets\branding\oto-hr-logo.ico'))) { throw 'assets\branding\oto-hr-logo.ico is required for signed installer branding. Convert the supplied PNG to ICO before packaging.' }

foreach ($app in @('admin_flutter','owner_flutter')) {
  $dir = Join-Path $root "apps\$app"
  if (-not (Test-Path (Join-Path $dir 'windows'))) { throw "$app has no windows platform folder. Run flutter create --platforms=windows apps\$app after reviewing generated files." }
  Push-Location $dir
  flutter pub get
  flutter analyze
  flutter test
  flutter build windows --release
  Pop-Location
}

New-Item -ItemType Directory -Force -Path $release | Out-Null
$iss = Join-Path $root 'scripts\installer.iss'
& iscc "/DROOT=$root" "/DRELEASE=$release" $iss
$ownerIss = Join-Path $root 'scripts\installer_owner.iss'
& iscc "/DROOT=$root" "/DRELEASE=$release" $ownerIss
Write-Host "Verified installers are in $release"
