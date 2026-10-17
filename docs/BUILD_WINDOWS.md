# HR-OTO Windows 11 Build Guide

## Required tools

1. Install Flutter stable for Windows and add its `bin` directory to PATH.
2. Install Visual Studio 2022 Community or Build Tools with **Desktop development with C++**, MSVC, Windows 10/11 SDK and CMake/Ninja.
3. Run `flutter doctor` and resolve all Windows toolchain errors.
4. For Android builds install Android Studio, Android SDK Platform/Build Tools, Android SDK Command-line Tools, and accept licenses with `flutter doctor --android-licenses`.
5. For setup installers install Inno Setup 6 or WiX Toolset after the Flutter Windows builds are verified.

## Generate platform folders

From `D:\HR-OTO`:

```powershell
flutter create --platforms=windows apps\admin_flutter
flutter create --platforms=windows apps\owner_flutter
flutter create --platforms=android,ios apps\employee_flutter
flutter create --platforms=android,ios apps\admin_flutter
flutter create --platforms=android,ios apps\owner_flutter
```

Review generated files before building; do not overwrite the existing `lib/` or `pubspec.yaml` changes.

## Analyze and test

```powershell
foreach ($app in 'employee_flutter','admin_flutter','owner_flutter') {
  Push-Location "apps\$app"
  flutter pub get
  flutter analyze
  flutter test
  Pop-Location
}
```

## Windows release builds

```powershell
Push-Location apps\admin_flutter
flutter build windows --release --target-platform windows-x64
Pop-Location
Push-Location apps\owner_flutter
flutter build windows --release --target-platform windows-x64
Pop-Location
```

Verify the generated `build\windows\x64\runner\Release` directories by launching the executables before creating installers. Package only verified directories with Inno Setup/WiX. Never rename an unbuilt file to `.exe` or `.msi`.

## Android APK/AAB

```powershell
foreach ($app in 'employee_flutter','admin_flutter','owner_flutter') {
  Push-Location "apps\$app"
  flutter build apk --release
  flutter build appbundle --release
  Pop-Location
}
```

Configure real Android signing keys before distributing release artifacts.
