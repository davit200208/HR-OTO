import 'dart:convert';
import 'package:cryptography/cryptography.dart';
import 'package:sqflite/sqflite.dart';

/// SQLite stores only ciphertext. The AES key must come from platform Secure Storage.
class EncryptedOfflineStore {
  EncryptedOfflineStore(this.db, this.key);
  final Database db;
  final SecretKey key;
  final _cipher = AesGcm.with256bits();

  Future<void> put(String collection, String id, Map<String, dynamic> value) async {
    final box = await _cipher.encrypt(utf8.encode(jsonEncode(value)), secretKey: key);
    final blob = jsonEncode({'nonce': base64UrlEncode(box.nonce), 'ciphertext': base64UrlEncode(box.cipherText), 'mac': base64UrlEncode(box.mac.bytes)});
    await db.insert('offline_records', {'collection': collection, 'id': id, 'ciphertext': blob, 'updated_at': DateTime.now().toUtc().toIso8601String()}, conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<Map<String, dynamic>?> get(String collection, String id) async {
    final rows = await db.query('offline_records', where: 'collection = ? AND id = ?', whereArgs: [collection, id], limit: 1);
    if (rows.isEmpty) return null;
    final value = jsonDecode(rows.single['ciphertext']! as String) as Map<String, dynamic>;
    final box = SecretBox(base64Url.decode(value['ciphertext']), nonce: base64Url.decode(value['nonce']), mac: Mac(base64Url.decode(value['mac'])));
    return jsonDecode(utf8.decode(await _cipher.decrypt(box, secretKey: key))) as Map<String, dynamic>;
  }
}

const offlineSchema = '''CREATE TABLE IF NOT EXISTS offline_records (collection TEXT NOT NULL, id TEXT NOT NULL, ciphertext TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY(collection, id));''';
const outboxSchema = '''CREATE TABLE IF NOT EXISTS offline_outbox (event_id TEXT PRIMARY KEY, idempotency_key TEXT UNIQUE NOT NULL, entity TEXT NOT NULL, payload TEXT NOT NULL, base_version INTEGER NOT NULL, status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0);''';
