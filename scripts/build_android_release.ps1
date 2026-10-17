$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not (Get-Command flutter -ErrorAction SilentlyContinue)) { throw 'Flutter is unavailable. Install Flutter stable and Android SDK first.' }
$release = Join-Path $root 'releases'; New-Item -ItemType Directory -Force -Path $release | Out-Null
foreach ($app in @('employee_flutter','admin_flutter','owner_flutter')) {
  $dir = Join-Path $root "apps\$app"
  if (-not (Test-Path (Join-Path $dir 'android'))) { throw "$app has no android platform folder. Generate it with flutter create --platforms=android apps\$app." }
  Push-Location $dir
  flutter pub get; flutter analyze; flutter test; flutter build apk --release; flutter build appbundle --release
  Copy-Item 'build\app\outputs\flutter-apk\app-release.apk' (Join-Path $release "HR-OTO-$($app.Replace('_','-').Replace('flutter','')).apk") -Force
  Copy-Item 'build\app\outputs\bundle\release\app-release.aab' (Join-Path $release "HR-OTO-$($app.Replace('_','-').Replace('flutter','')).aab") -Force
  Pop-Location
}
