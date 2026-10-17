# HR-OTO Windows Release Build

HR-OTO Admin და HR-OTO Owner Windows installer-ები იგება GitHub Actions-ის `windows-latest` runner-ზე. ლოკალურ კომპიუტერზე Flutter SDK, Visual Studio, CMake, Ninja ან Inno Setup-ის დაყენება ამ workflow-სთვის საჭირო არ არის.

## რას აკეთებს workflow

`.github/workflows/windows-release.yml`:

1. იძახებს Flutter Stable SDK-ს `subosito/flutter-action`-ით.
2. იყენებს GitHub-ის Windows runner-ზე არსებულ Visual Studio C++/Windows toolchain-ს.
3. აყენებს Inno Setup 6-ს და ImageMagick-ს runner-ზე.
4. ამოწმებს `flutter doctor -v`-ს.
5. ქმნის Windows platform folders-ს დროებით runner-ზე, შემდეგ უშვებს `flutter analyze` და `flutter test`-ს Admin და Owner აპებზე.
6. ქმნის ორივე release build-ს და ამოწმებს, რომ რეალური `.exe` არსებობს.
7. supplied PNG ლოგოდან runner-ზე ქმნის ICO-ს და აერთიანებს მას Installer-ში.
8. ქმნის `HR-OTO-Admin-Setup.exe` და `HR-OTO-Owner-Setup.exe`-ს ყველა Flutter DLL/runtime ფაილით.
9. ორივე installer-ს დროებით აყენებს, უშვებს smoke-test-ს, ამოწმებს uninstaller-ს და მხოლოდ ამის შემდეგ ტვირთავს Artifact-ს.

Workflow არ შეიცავს API Keys-ს, provider credentials-ს ან სხვა საიდუმლოებას.

## GitHub Repository-ის მომზადება

ამ სამუშაო გარემოში GitHub remote/repository ჯერ არ იყო დაკავშირებული. შექმენი GitHub-ზე ახალი private repository, სასურველია README-ის ავტომატური ინიციალიზაციის გარეშე. შემდეგ `D:\HR-OTO` საქაღალდეში გაუშვი:

```powershell
git init
git add .
git commit -m "Prepare HR-OTO Windows GitHub Actions build"
git branch -M main
git remote add origin https://github.com/<YOUR_ACCOUNT>/<YOUR_REPOSITORY>.git
git push -u origin main
```

თუ Git ჯერ არ არის დაყენებული, დააყენე Git for Windows ან ატვირთე ეს პროექტი GitHub-ის web upload-ით. GitHub-ზე არ ატვირთო `.env`, API Keys, პაროლები ან token-ები.

## Workflow-ის გაშვება

1. გახსენი repository-ის **Actions** გვერდი.
2. აირჩიე **HR-OTO Windows Release**.
3. დააჭირე **Run workflow**.
4. მიუთითე ვერსია, მაგალითად `1.0.0`.
5. დაელოდე ყველა step-ის მწვანედ დასრულებას.

წარმატებული დასრულება მხოლოდ მაშინ ითვლება, როცა Analyze, Test, ორივე Flutter release build, Inno Setup packaging და installer smoke-test წარმატებულია.

## Installer-ების გადმოწერა

მწვანე workflow run-ში გახსენი **Artifacts** და გადმოწერე `hr-oto-windows-installers-<version>.zip`. ZIP-ში იქნება:

- `HR-OTO-Admin-Setup.exe`
- `HR-OTO-Owner-Setup.exe`

ეს არტიფაქტები იქმნება GitHub Runner-ზე და არა შენს კომპიუტერზე. ამ checkout-ში წინასწარ შექმნილი ცარიელი ან ყალბი Setup ფაილები არ გამოიყენება.

## უსაფრთხოება და შეზღუდვები

- Build workflow-სთვის GitHub Secrets არ არის საჭირო.
- Production API keys უნდა დარჩეს server-side Secret Storage-ში და არ უნდა მოხვდეს Flutter assets-ში ან repository-ში.
- Workflow-ის artifact retention არის 14 დღე; საჭიროების შემთხვევაში ჩამოტვირთე და შეინახე release build.
- Android და iOS build-ები ამ workflow-ში შეგნებულად არ შედის.
- iOS TestFlight build-ს მოგვიანებით დასჭირდება macOS runner, Apple Developer account, certificates და provisioning profiles.
