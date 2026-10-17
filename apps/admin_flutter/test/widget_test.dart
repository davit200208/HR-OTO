import 'package:flutter_test/flutter_test.dart';
import 'package:hr_oto_admin/main.dart';

void main() {
  testWidgets('Admin foundation window renders', (tester) async {
    await tester.pumpWidget(const AdminApp());
    expect(find.text('HR-OTO Admin'), findsWidgets);
    expect(find.text('Foundation მზად არის'), findsOneWidget);
  });
}

