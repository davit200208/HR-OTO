import 'package:flutter_test/flutter_test.dart';
import 'package:hr_oto_employee/main.dart';

void main() {
  testWidgets('Employee foundation window renders', (tester) async {
    await tester.pumpWidget(const EmployeeApp());
    expect(find.text('HR-OTO Employee'), findsWidgets);
    expect(find.text('Company Code'), findsOneWidget);
  });
}

