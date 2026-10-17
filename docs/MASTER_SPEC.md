# HR-OTO — Master Specification

**სტატუსი:** Draft — Stage 0 approved baseline  
**პროექტი:** HR-OTO  
**მთავარი ენა:** ქართული  
**სამიზნე პროდუქტები:** Android, iOS და Windows native applications; central FastAPI server

## 1. პროდუქტის მიზანი

HR-OTO არის კომერციული, მრავალკომპანიანი HR Management SaaS სისტემა, რომელიც სხვადასხვა კომპანიაზე ქირავდება. სისტემა არ იქნება ვებსაიტი და არ იქნება ბრაუზერში გასაშვები აპლიკაცია. მომხმარებლები გამოიყენებენ Flutter-ით შექმნილ ნამდვილ Android/iOS/Windows აპლიკაციებს, ხოლო მონაცემებს მოემსახურება დაცული ცენტრალური FastAPI backend.

## 2. პროდუქტის კომპონენტები

### 2.1 HR-OTO Employee

- პლატფორმები: Android, iOS.
- თანამშრომლის პირადი სამუშაო სივრცე: პროფილი, დასწრება, სამუშაო საათები, შესვენებები, შვებულებები, დოკუმენტები, განცხადებები, შეტყობინებები, ტრენინგები, KPI/შეფასების შესაბამისი ინფორმაცია.
- Offline Mode: მაქსიმუმ 48 საათი, შემდეგ საჭიროა სერვერთან წარმატებული სინქრონიზაცია/ლიცენზიის შემოწმება.
- ლოკალური მონაცემები ინახება SQLite-ში დაშიფრული სახით.

### 2.2 HR-OTO Admin

- პლატფორმები: Android, iOS, Windows.
- კომპანიის HR/ადმინისტრაციული ოპერაციები: თანამშრომლები, სტრუქტურა, ფილიალები, გრაფიკები, დასწრება, შვებულებები, ხელფასები, დოკუმენტები, KPI, დისციპლინა, რეკრუტინგი, ტრენინგები, გამოკითხვები, განცხადებები, შეტყობინებები და რეპორტები.
- ძირითადი Admin ფუნქციები თანაბრად ხელმისაწვდომი უნდა იყოს მობილურსა და Windows-ზე, responsive/adaptive UX-ით.
- Offline Mode: მაქსიმუმ 48 საათი და ავტომატური სინქრონიზაცია.

### 2.3 HR-OTO Owner

დამოუკიდებელი Super Admin აპლიკაცია, რომელიც არ ეკუთვნის კონკრეტულ tenant-ს და გამოიყენება HR-OTO-ს კომერციული/სისტემური მართვისთვის.

- პლატფორმები: Android, iOS, Windows.
- კომპანიების შექმნა, დაბლოკვა, გააქტიურება.
- პაკეტების შექმნა და არქივირება; წაშლა/ფიზიკური delete არ გამოიყენება.
- ყოველთვიური/წლიური ფასების შეცვლა.
- თანამშრომლების, ფილიალების, ადმინისტრატორებისა და მოწყობილობების ლიმიტები.
- პაკეტის ფუნქციების ჩართვა/გამორთვა.
- კომპანიის ინდივიდუალური პირობები.
- ლიცენზიები, Trial და subscriptions.
- Brevo API Key-ის დამატება, შეცვლა და ტესტირება.
- SMSOffline API Key-ის დამატება, შეცვლა და ტესტირება.
- SMS/Email sender-ები, templates და quota-ები.
- სისტემის მონიტორინგი.

## 3. ტექნოლოგიური საფუძველი

- Client: Flutter / Dart / Riverpod.
- Backend: Python / FastAPI.
- Database: PostgreSQL / SQLAlchemy / Alembic.
- Cache/queue support: Redis.
- Offline storage: SQLite + უსაფრთხო ლოკალური დაშიფვრა.
- Delivery: Docker.
- Integration: REST API over HTTPS.
- Reports: Excel/PDF export service.

## 4. Multi-Tenant მოთხოვნები

თითოეულ კომპანიას უნდა ჰქონდეს:

- უნიკალური company code.
- უნიკალური subdomain/tenant identifier.
- საკუთარი თანამშრომლები, ფილიალები, ადმინისტრატორები და მოწყობილობები.
- საკუთარი მონაცემთა კონტექსტი და subscription/license.

Tenant isolation არის უსაფრთხოების ძირითადი invariant: ერთი tenant-ის user, API request, background job, report, cache key, file ან event ვერ უნდა ხედავდეს სხვა tenant-ის მონაცემებს. Tenant context უნდა განისაზღვროს სერვერის მხარეს authenticated identity-დან და არ უნდა იყოს მხოლოდ client-ის მიერ მიწოდებულ პარამეტრზე დამოკიდებული.

## 5. უსაფრთხოება და საიდუმლოებები

- ყველა გარე კავშირი: HTTPS/TLS.
- Brevo და SMSOffline secret keys ინახება მხოლოდ server-side Secret Storage-ში; არასდროს შედის Flutter აპში, bundle-ში, source control-ში, logs-ში ან API response-ში.
- Owner-ის secret-management endpoint-ები აბრუნებს მხოლოდ masked metadata-ს, არა სრულ გასაღებს.
- RBAC/permission checks სრულდება backend-ზე; UI-ს დამალვა უსაფრთხოების კონტროლი არ არის.
- Audit log აუცილებელია Owner-ისა და მაღალი რისკის ადმინისტრაციული მოქმედებებისთვის.
- მოწყობილობის რეგისტრაცია, session revocation, token rotation და rate limiting სავალდებულო დიზაინის ნაწილია.
- PII, ხელფასი, დოკუმენტები და attendance data უნდა იყოს მინიმალური წვდომის პრინციპით დაცული.

## 6. Offline და სინქრონიზაცია

- Employee/Admin მუშაობენ მაქსიმუმ 48 საათის offline window-ში.
- ლოკალური queue ინახავს ოპერაციებს idempotency key-ით.
- sync იყოფა pull/push ეტაპებად და აქვს retry/backoff.
- კონფლიქტის პოლიტიკა განისაზღვრება დომენის მიხედვით; payroll/attendance-ზე ბრმა last-write-wins დაუშვებელია.
- 48 საათის გასვლის შემდეგ აპი გადადის restricted state-ში და მოითხოვს სერვერთან ვალიდაციას.
- ლოკალური DB, tokens და sensitive cache უნდა იყოს encrypted at rest და secure key store-ის მეშვეობით დაცული.

## 7. Verification Interface

ექვსნიშნა PIN არ იქმნება. მოსვლა-წასვლის იდენტიფიკაციის მეთოდი ამ ეტაპზე შეგნებულად არ აირჩევა. შეიქმნება გაფართოებადი backend/domain interface, მაგალითად `VerificationProvider`, რომელსაც შემდგომში შეიძლება დაემატოს QR, NFC, biometric, device-based ან სხვა პროვაიდერი ისე, რომ Attendance domain-ის ძირითადი კოდი არ გადაიწეროს.

## 8. HR ფუნქციური მოდულები

1. თანამშრომლები.
2. განყოფილებები, პოზიციები, ფილიალები.
3. სამუშაო გრაფიკები.
4. დასწრება და სამუშაო საათები.
5. შესვენებები.
6. დაგვიანებები და გაცდენები.
7. შვებულებები.
8. ხელფასები და ბონუსები.
9. დოკუმენტები.
10. KPI და შეფასებები.
11. დისციპლინა.
12. რეკრუტინგი.
13. ტრენინგები.
14. ანონიმური გამოკითხვები.
15. შიდა განცხადებები.
16. Push/SMS/Email notifications.
17. Excel/PDF reports.

## 9. UX/UI მოთხოვნები

- მთავარი ენა: ქართული; შემდგომში შესაძლებელი უნდა იყოს localization.
- Premium ხარისხის ვიზუალური სისტემა.
- Dark/Light Mode.
- Flutter Material 3-ზე დაფუძნებული თანმიმდევრული design tokens.
- Accessibility: readable typography, contrast, touch targets, screen-reader semantics.
- responsive layouts Windows-ის ფართო ეკრანისთვის და mobile breakpoints-ისთვის.
- მოწოდებული OTO-HR ლოგო გამოიყენება ბრენდის asset-ად და შენახულია `assets/branding/oto-hr-logo.png`-ში. Flutter-ის თითოეულ აპში asset reference უნდა იყოს ცენტრალიზებული და არა დუბლირებული სხვადასხვა feature-ში.

## 10. არ ფუნქციონირებს Stage 0-ში

ამ ეტაპზე არ იქმნება ბიზნეს-ფუნქციები, API endpoints, DB migrations, Flutter screens, authentication flow ან deployment pipeline. შეიქმნა მხოლოდ პროექტის სტრუქტურის საწყისი დირექტორიები და ეს დოკუმენტაცია.

## 11. მიღების კრიტერიუმები Stage 0-ისთვის

- მოთხოვნები სრულად დაფიქსირებულია ამ დოკუმენტში.
- არქიტექტურა, roadmap, პროგრესი და გადაწყვეტილებები ცალკე დოკუმენტებშია.
- ეტაპები და დამოკიდებულებები მკაფიოდაა აღწერილი.
- დაუდასტურებელი დეტალები მონიშნულია როგორც გადაწყვეტილების მომთხოვნი საკითხები.
