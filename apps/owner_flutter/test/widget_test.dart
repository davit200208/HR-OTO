import 'package:flutter_test/flutter_test.dart';
import 'package:hr_oto_owner/main.dart';

void main() {
  testWidgets('Owner foundation window renders', (tester) async {
    await tester.pumpWidget(const OwnerApp());
    expect(find.text('HR-OTO Owner'), findsWidgets);
    expect(find.text('Foundation მზად არის'), findsOneWidget);
  });
}

