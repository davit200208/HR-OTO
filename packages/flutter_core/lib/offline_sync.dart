import 'dart:convert';
import 'dart:math';

/// Server-issued signed lease. The client never extends it locally.
class OfflineLease {
  OfflineLease({required this.issuedAt, required this.expiresAt, required this.serverVersion, required this.signature});
  final DateTime issuedAt, expiresAt;
  final int serverVersion;
  final String signature;
  bool valid(DateTime now, DateTime? lastServerTime) =>
      now.isBefore(expiresAt) && (lastServerTime == null || !now.isBefore(lastServerTime.subtract(const Duration(minutes: 5))));
  Duration remaining(DateTime now) => expiresAt.difference(now).isNegative ? Duration.zero : expiresAt.difference(now);
}

class OfflinePolicy {
  const OfflinePolicy({this.maxAge = const Duration(hours: 48)});
  final Duration maxAge;
  bool allowsMutation(OfflineLease lease, DateTime now) => lease.valid(now, null);
  bool isRestricted(OfflineLease lease, DateTime now) => !allowsMutation(lease, now);
}

class SyncEvent {
  SyncEvent({required this.id, required this.idempotencyKey, required this.entity, required this.payload, required this.baseVersion});
  final String id, idempotencyKey, entity;
  final Map<String, dynamic> payload;
  final int baseVersion;
  int attempts = 0;
  String status = 'pending';
}

class SyncConflict {
  SyncConflict({required this.event, required this.serverVersion, required this.serverPayload});
  final SyncEvent event;
  final int serverVersion;
  final Map<String, dynamic> serverPayload;
}

class LocalOutbox {
  final List<SyncEvent> _events = [];
  List<SyncEvent> get pending => List.unmodifiable(_events.where((e) => e.status == 'pending'));
  void add(SyncEvent event) { if (_events.every((e) => e.idempotencyKey != event.idempotencyKey)) _events.add(event); }
  void markSent(String id) { _events.firstWhere((e) => e.id == id).status = 'sent'; }
  void markRetry(String id) { final event = _events.firstWhere((e) => e.id == id); event.attempts++; event.status = 'pending'; }
  void markConflict(String id) { _events.firstWhere((e) => e.id == id).status = 'conflict'; }
}

class OfflineSyncCoordinator {
  OfflineSyncCoordinator({required this.lease, required this.outbox, this.syncCursor = 0});
  OfflineLease lease;
  final LocalOutbox outbox;
  int syncCursor;
  bool online = false;
  bool get restricted => !lease.valid(DateTime.now().toUtc(), null);
  Duration get remaining => lease.remaining(DateTime.now().toUtc());
  void updateOnline(bool value) => online = value;
  void applyServerCursor(int cursor, OfflineLease renewedLease) { if (cursor >= syncCursor) syncCursor = cursor; lease = renewedLease; }
}

String randomEventId() => '${DateTime.now().microsecondsSinceEpoch}-${Random().nextInt(1 << 32)}';
String idempotencyKey(String eventId) => base64Url.encode(utf8.encode('hr-oto:$eventId')).replaceAll('=', '');
