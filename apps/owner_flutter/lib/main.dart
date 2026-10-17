import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:hr_oto_design_system/hr_oto_design_system.dart';
import 'package:http/http.dart' as http;

const apiBaseUrl = String.fromEnvironment('HR_OTO_API_URL', defaultValue: 'http://localhost:8000/api/v1');
final ownerApiProvider = Provider<OwnerApi>((_) => OwnerApi(apiBaseUrl));

class ApiException implements Exception {
  const ApiException(this.message);
  final String message;
  @override
  String toString() => message;
}

class OwnerApi {
  OwnerApi(this.baseUrl);
  final String baseUrl;
  final FlutterSecureStorage storage = const FlutterSecureStorage();
  String? accessToken;
  String? refreshToken;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (accessToken != null) 'Authorization': 'Bearer $accessToken',
      };

  Future<void> login(String email, String password, String? mfaCode) async {
    final response = await http.post(Uri.parse('$baseUrl/auth/login'), headers: _headers, body: jsonEncode({
      'email': email, 'password': password, if (mfaCode != null && mfaCode.isNotEmpty) 'mfa_code': mfaCode,
    }));
    final data = _decode(response) as Map<String, dynamic>;
    accessToken = data['access_token'] as String;
    refreshToken = data['refresh_token'] as String;
    await storage.write(key: 'owner_access_token', value: accessToken);
    await storage.write(key: 'owner_refresh_token', value: refreshToken);
  }

  Future<void> logout() async {
    if (accessToken != null) await http.post(Uri.parse('$baseUrl/auth/logout'), headers: _headers);
    accessToken = null;
    refreshToken = null;
    await storage.delete(key: 'owner_access_token');
    await storage.delete(key: 'owner_refresh_token');
  }

  Future<DashboardData> dashboard() async => DashboardData.fromJson(_decode(await _get('/owner/dashboard')) as Map<String, dynamic>);

  Future<List<Company>> companies({String search = '', String? status, String? licenseStatus}) async {
    final query = <String, String>{if (search.isNotEmpty) 'search': search, if (status != null) 'status': status, if (licenseStatus != null) 'license_status': licenseStatus};
    final uri = Uri.parse('$baseUrl/companies').replace(queryParameters: query);
    final response = await http.get(uri, headers: _headers);
    return (_decode(response) as List).map((item) => Company.fromJson(item as Map<String, dynamic>)).toList();
  }

  Future<Company> createCompany(Map<String, dynamic> input) async => Company.fromJson(_decode(await _post('/companies', input)) as Map<String, dynamic>);
  Future<Company> updateCompany(String id, Map<String, dynamic> input) async => Company.fromJson(_decode(await _patch('/companies/$id', input)) as Map<String, dynamic>);
  Future<Company> companyDetails(String id) async => Company.fromJson(_decode(await _get('/companies/$id')) as Map<String, dynamic>);
  Future<List<PackagePlan>> packages() async => (_decode(await _get('/owner/packages')) as List).map((item) => PackagePlan.fromJson(item as Map<String, dynamic>)).toList();
  Future<PackagePlan> createPackage(Map<String, dynamic> input) async => PackagePlan.fromJson(_decode(await _post('/owner/packages', input)) as Map<String, dynamic>);
  Future<void> updatePackage(String id, Map<String, dynamic> input) async { await _patch('/owner/packages/$id', input); }
  Future<void> addPriceVersion(String id, Map<String, dynamic> input) async { await _post('/owner/packages/$id/prices', input); }
  Future<void> updateFeature(String id, String key, bool enabled) async { _decode(await http.put(Uri.parse('$baseUrl/owner/packages/$id/features/$key'), headers: _headers, body: jsonEncode({'enabled': enabled}))); }
  Future<void> updateLimit(String id, String key, int value) async { _decode(await http.put(Uri.parse('$baseUrl/owner/packages/$id/limits/$key'), headers: _headers, body: jsonEncode({'value': value}))); }
  Future<void> assignSubscription(String tenantId, Map<String, dynamic> input) async { await _post('/owner/companies/$tenantId/subscription', input); }
  Future<void> grantTrial(String tenantId, Map<String, dynamic> input) async { await _post('/owner/companies/$tenantId/trial', input); }
  Future<void> createOverride(String tenantId, Map<String, dynamic> input) async { await _post('/owner/companies/$tenantId/overrides', input); }
  Future<Map<String, dynamic>> createCompanyOwner(String id, Map<String, dynamic> input) async => _decode(await _post('/companies/$id/owner', input)) as Map<String, dynamic>;
  Future<List<AuditEntry>> auditLog() async => (_decode(await _get('/owner/audit-log')) as List).map((item) => AuditEntry.fromJson(item as Map<String, dynamic>)).toList();
  Future<List<Map<String, dynamic>>> providers() async => ( _decode(await _get('/owner/integrations/providers')) as List).cast<Map<String, dynamic>>();
  Future<Map<String, dynamic>> updateProvider(String provider, Map<String, dynamic> input) async => _decode(await _patch('/owner/integrations/providers/$provider', input)) as Map<String, dynamic>;
  Future<Map<String, dynamic>> testProvider(String provider) async => _decode(await _post('/owner/integrations/providers/$provider/test-connection', {'confirmation': 'CONFIRM'})) as Map<String, dynamic>;
  Future<Map<String, dynamic>> rotateProvider(String provider, String key) async => _decode(await _post('/owner/integrations/providers/$provider/secret', {'api_key': key, 'confirmation': 'CONFIRM'})) as Map<String, dynamic>;

  Future<http.Response> _get(String path) => http.get(Uri.parse('$baseUrl$path'), headers: _headers);
  Future<http.Response> _post(String path, Map<String, dynamic> body) => http.post(Uri.parse('$baseUrl$path'), headers: _headers, body: jsonEncode(body));
  Future<http.Response> _patch(String path, Map<String, dynamic> body) => http.patch(Uri.parse('$baseUrl$path'), headers: _headers, body: jsonEncode(body));
  dynamic _decode(http.Response response) {
    dynamic data;
    try { data = response.body.isEmpty ? <String, dynamic>{} : jsonDecode(response.body); } catch (_) { data = <String, dynamic>{}; }
    if (response.statusCode < 200 || response.statusCode >= 300) throw ApiException(data is Map && data['detail'] != null ? data['detail'].toString() : 'API request failed');
    return data;
  }
}

class DashboardData {
  DashboardData.fromJson(Map<String, dynamic> json)
      : total = json['total_companies'] as int, active = json['active_companies'] as int, blocked = json['blocked_companies'] as int,
        trial = json['trial_companies'] as int, activeLicenses = json['active_licenses'] as int, expiredLicenses = json['expired_licenses'] as int,
        revenue = json['monthly_revenue'] as int;
  final int total, active, blocked, trial, activeLicenses, expiredLicenses, revenue;
}

class Company {
  Company.fromJson(Map<String, dynamic> json)
      : id = json['id'].toString(), name = json['name'].toString(), code = json['company_code'].toString(), subdomain = json['subdomain'].toString(),
        status = json['status'].toString(), licenseStatus = json['license_status'].toString(), revenue = json['monthly_revenue'] as int;
  final String id, name, code, subdomain, status, licenseStatus;
  final int revenue;
}

class AuditEntry {
  AuditEntry.fromJson(Map<String, dynamic> json) : action = json['action'].toString(), target = json['target_type'].toString(), details = json['details'].toString();
  final String action, target, details;
}

class PackagePlan {
  PackagePlan.fromJson(Map<String, dynamic> json)
      : id = json['id'].toString(), code = json['code'].toString(), name = json['name'].toString(), description = json['description'].toString(),
        active = json['is_active'] as bool, archived = json['is_archived'] as bool, monthly = json['monthly_price']?.toString() ?? '—', annual = json['annual_price']?.toString() ?? '—',
        currency = json['currency']?.toString() ?? 'GEL', features = Map<String, bool>.from(json['features'] as Map? ?? {}), limits = Map<String, dynamic>.from(json['limits'] as Map? ?? {});
  final String id, code, name, description, monthly, annual, currency;
  final bool active, archived;
  final Map<String, bool> features;
  final Map<String, dynamic> limits;
}

void main() => runApp(const ProviderScope(child: OwnerApp()));

class OwnerApp extends StatefulWidget {
  const OwnerApp({super.key});
  @override
  State<OwnerApp> createState() => _OwnerAppState();
}

class _OwnerAppState extends State<OwnerApp> {
  ThemeMode mode = ThemeMode.system;
  bool authenticated = false;
  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'HR-OTO Owner', debugShowCheckedModeBanner: false, theme: HrOtoTheme.light(), darkTheme: HrOtoTheme.dark(), themeMode: mode,
        home: authenticated ? OwnerWorkspace(onLogout: () => setState(() => authenticated = false), onToggleTheme: _toggleTheme) : OwnerLogin(onLoggedIn: () => setState(() => authenticated = true)),
      );
  void _toggleTheme() => setState(() => mode = mode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark);
}

class OwnerLogin extends ConsumerStatefulWidget {
  const OwnerLogin({super.key, required this.onLoggedIn});
  final VoidCallback onLoggedIn;
  @override
  ConsumerState<OwnerLogin> createState() => _OwnerLoginState();
}

class _OwnerLoginState extends ConsumerState<OwnerLogin> {
  final email = TextEditingController(), password = TextEditingController(), mfa = TextEditingController();
  bool loading = false;
  String? error;
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 460),
          child: Card(
            margin: const EdgeInsets.all(24),
            child: Padding(
              padding: const EdgeInsets.all(32),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const HrOtoLogo(size: 100),
                  const SizedBox(height: 20),
                  Text('HR-OTO Owner', style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800)),
                  const SizedBox(height: 8),
                  const Text('დამოუკიდებელი Super Admin მართვის ცენტრი'),
                  const SizedBox(height: 24),
                  TextField(controller: email, decoration: const InputDecoration(labelText: 'ელფოსტა', prefixIcon: Icon(Icons.email_outlined))),
                  const SizedBox(height: 12),
                  TextField(controller: password, obscureText: true, decoration: const InputDecoration(labelText: 'პაროლი', prefixIcon: Icon(Icons.lock_outline))),
                  const SizedBox(height: 12),
                  TextField(controller: mfa, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'MFA კოდი (თუ ჩართულია)', prefixIcon: Icon(Icons.verified_user_outlined))),
                  if (error != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(error!, style: TextStyle(color: Theme.of(context).colorScheme.error))),
                  const SizedBox(height: 20),
                  SizedBox(width: double.infinity, child: FilledButton.icon(onPressed: loading ? null : _login, icon: const Icon(Icons.login), label: Text(loading ? 'მიმდინარეობს...' : 'შესვლა'))),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
  Future<void> _login() async { setState(() { loading = true; error = null; }); try { await ref.read(ownerApiProvider).login(email.text.trim(), password.text, mfa.text.trim()); widget.onLoggedIn(); } on ApiException catch (e) { setState(() => error = e.message); } catch (_) { setState(() => error = 'სერვერთან დაკავშირება ვერ მოხერხდა'); } finally { if (mounted) setState(() => loading = false); } }
}

class OwnerWorkspace extends StatefulWidget {
  const OwnerWorkspace({super.key, required this.onLogout, required this.onToggleTheme});
  final VoidCallback onLogout, onToggleTheme;
  @override
  State<OwnerWorkspace> createState() => _OwnerWorkspaceState();
}

class _OwnerWorkspaceState extends State<OwnerWorkspace> {
  int index = 0;
  final labels = const ['Dashboard', 'კომპანიები', 'პაკეტები', 'Integrations', 'Audit Log'];
  final icons = const [Icons.dashboard_outlined, Icons.business_outlined, Icons.inventory_2_outlined, Icons.notifications_active_outlined, Icons.history];
  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.sizeOf(context).width >= 760;
    final pages = const [OwnerDashboard(), CompaniesPage(), PackagesPage(), IntegrationsPage(), AuditPage()];
    return Scaffold(appBar: AppBar(title: Text('HR-OTO Owner • ${labels[index]}'), actions: [IconButton(onPressed: widget.onToggleTheme, icon: const Icon(Icons.brightness_6_outlined)), IconButton(onPressed: widget.onLogout, icon: const Icon(Icons.logout))]), body: Row(children: [if (wide) NavigationRail(selectedIndex: index, onDestinationSelected: (value) => setState(() => index = value), labelType: NavigationRailLabelType.all, destinations: [for (var i = 0; i < labels.length; i++) NavigationRailDestination(icon: Icon(icons[i]), label: Text(labels[i]))]), if (wide) const VerticalDivider(width: 1), Expanded(child: pages[index])]), bottomNavigationBar: wide ? null : NavigationBar(selectedIndex: index, onDestinationSelected: (value) => setState(() => index = value), destinations: [for (var i = 0; i < labels.length; i++) NavigationDestination(icon: Icon(icons[i]), label: labels[i])]));
  }
}

class OwnerDashboard extends ConsumerStatefulWidget { const OwnerDashboard({super.key}); @override ConsumerState<OwnerDashboard> createState() => _OwnerDashboardState(); }
class _OwnerDashboardState extends ConsumerState<OwnerDashboard> {
  late Future<DashboardData> future;
  @override void initState() { super.initState(); future = ref.read(ownerApiProvider).dashboard(); }
  @override Widget build(BuildContext context) => RefreshIndicator(onRefresh: () async => setState(() => future = ref.read(ownerApiProvider).dashboard()), child: FutureBuilder<DashboardData>(future: future, builder: (context, snapshot) { if (snapshot.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator()); if (snapshot.hasError) return _ErrorState(message: snapshot.error.toString(), onRetry: () => setState(() => future = ref.read(ownerApiProvider).dashboard())); final d = snapshot.data!; return ListView(padding: const EdgeInsets.all(24), children: [Text('სისტემის მიმოხილვა', style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800)), const SizedBox(height: 20), Wrap(spacing: 16, runSpacing: 16, children: [_MetricCard('ყველა კომპანია', d.total, Icons.business, Colors.blue), _MetricCard('აქტიური', d.active, Icons.check_circle_outline, Colors.green), _MetricCard('დაბლოკილი', d.blocked, Icons.block, Colors.red), _MetricCard('Trial', d.trial, Icons.timer_outlined, Colors.orange), _MetricCard('აქტიური ლიცენზია', d.activeLicenses, Icons.verified_outlined, Colors.teal), _MetricCard('ვადაგასული', d.expiredLicenses, Icons.warning_amber, Colors.deepOrange)]), const SizedBox(height: 20), Card(child: ListTile(leading: const Icon(Icons.payments_outlined), title: const Text('საწყისი თვიური შემოსავალი'), subtitle: Text('${d.revenue} ₾', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800)), trailing: const Icon(Icons.trending_up))) ]); }));
}

class CompaniesPage extends ConsumerStatefulWidget { const CompaniesPage({super.key}); @override ConsumerState<CompaniesPage> createState() => _CompaniesPageState(); }
class _CompaniesPageState extends ConsumerState<CompaniesPage> {
  final search = TextEditingController(); String? status; String? license; late Future<List<Company>> future;
  @override void initState() { super.initState(); future = _load(); }
  Future<List<Company>> _load() => ref.read(ownerApiProvider).companies(search: search.text, status: status, licenseStatus: license);
  void reload() => setState(() => future = _load());
  @override Widget build(BuildContext context) => Column(children: [Padding(padding: const EdgeInsets.fromLTRB(24, 24, 24, 12), child: Row(children: [Expanded(child: TextField(controller: search, onSubmitted: (_) => reload(), decoration: const InputDecoration(labelText: 'ძებნა: სახელი, კოდი ან subdomain', prefixIcon: Icon(Icons.search)))), const SizedBox(width: 12), DropdownButton<String?>(value: status, hint: const Text('სტატუსი'), items: const [DropdownMenuItem<String?>(value: null, child: Text('ყველა სტატუსი')), DropdownMenuItem(value: 'active', child: Text('აქტიური')), DropdownMenuItem(value: 'blocked', child: Text('დაბლოკილი'))], onChanged: (v) { setState(() => status = v); reload(); }), const SizedBox(width: 12), FilledButton.icon(onPressed: () => _companyDialog(), icon: const Icon(Icons.add), label: const Text('კომპანია'))])), Expanded(child: FutureBuilder<List<Company>>(future: future, builder: (context, snapshot) { if (snapshot.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator()); if (snapshot.hasError) return _ErrorState(message: snapshot.error.toString(), onRetry: reload); final items = snapshot.data ?? []; if (items.isEmpty) return const Center(child: Text('კომპანიები ვერ მოიძებნა')); return ListView.separated(padding: const EdgeInsets.symmetric(horizontal: 24), itemCount: items.length, separatorBuilder: (_, __) => const SizedBox(height: 8), itemBuilder: (context, i) { final c = items[i]; return Card(child: ListTile(leading: CircleAvatar(child: Text(c.name.substring(0, 1).toUpperCase())), title: Text(c.name), subtitle: Text('${c.code} • ${c.subdomain} • ${c.licenseStatus}'), trailing: Wrap(spacing: 4, children: [IconButton(tooltip: 'დეტალური პროფილი', onPressed: () => _details(c), icon: const Icon(Icons.info_outline)), IconButton(tooltip: 'კომერციული პარამეტრები', onPressed: () => _commercialDialog(c), icon: const Icon(Icons.tune_outlined)), IconButton(tooltip: 'რედაქტირება', onPressed: () => _companyDialog(c), icon: const Icon(Icons.edit_outlined)), IconButton(tooltip: c.status == 'blocked' ? 'გააქტიურება' : 'დაბლოკვა', onPressed: () => _toggle(c), icon: Icon(c.status == 'blocked' ? Icons.lock_open : Icons.block)), IconButton(tooltip: 'Company Owner', onPressed: () => _ownerDialog(c), icon: const Icon(Icons.person_add_alt_1_outlined))]))); }); }))]);
  Future<void> _toggle(Company c) async { try { await ref.read(ownerApiProvider).updateCompany(c.id, {'status': c.status == 'blocked' ? 'active' : 'blocked'}); reload(); } catch (e) { _snack(e.toString()); } }
  Future<void> _details(Company c) async { try { final detail = await ref.read(ownerApiProvider).companyDetails(c.id); if (!mounted) return; showDialog(context: context, builder: (_) => AlertDialog(title: Text(detail.name), content: Text('Company ID: ${detail.id}\nCode: ${detail.code}\nSubdomain: ${detail.subdomain}\nStatus: ${detail.status}\nLicense: ${detail.licenseStatus}\nMonthly revenue: ${detail.revenue} ₾'), actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('დახურვა'))])); } catch (e) { _snack(e.toString()); } }
  Future<void> _companyDialog([Company? company]) async { final name = TextEditingController(text: company?.name), code = TextEditingController(text: company?.code), subdomain = TextEditingController(text: company?.subdomain), email = TextEditingController(), ownerName = TextEditingController(), password = TextEditingController(); final form = GlobalKey<FormState>(); await showDialog(context: context, builder: (dialogContext) => AlertDialog(title: Text(company == null ? 'კომპანიის დამატება' : 'კომპანიის რედაქტირება'), content: Form(key: form, child: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [TextFormField(controller: name, decoration: const InputDecoration(labelText: 'კომპანიის სახელი'), validator: (v) => v == null || v.length < 2 ? 'აუცილებელია' : null), TextFormField(controller: code, enabled: company == null, decoration: const InputDecoration(labelText: 'Company Code'), validator: (v) => v == null || v.length < 3 ? 'აუცილებელია' : null), TextFormField(controller: subdomain, decoration: const InputDecoration(labelText: 'Subdomain'), validator: (v) => v == null || v.length < 3 ? 'აუცილებელია' : null), if (company == null) ...[TextFormField(controller: ownerName, decoration: const InputDecoration(labelText: 'Company Owner სახელი')), TextFormField(controller: email, decoration: const InputDecoration(labelText: 'Company Owner ელფოსტა')), TextFormField(controller: password, obscureText: true, decoration: const InputDecoration(labelText: 'საწყისი პაროლი'))]]))), actions: [TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('გაუქმება')), FilledButton(onPressed: () async { if (!form.currentState!.validate()) return; try { if (company == null) { await ref.read(ownerApiProvider).createCompany({'name': name.text, 'company_code': code.text, 'subdomain': subdomain.text, 'owner_email': email.text, 'owner_name': ownerName.text, 'owner_password': password.text}); } else { await ref.read(ownerApiProvider).updateCompany(company.id, {'name': name.text, 'subdomain': subdomain.text}); } if (dialogContext.mounted) Navigator.pop(dialogContext); reload(); } catch (e) { _snack(e.toString()); } }, child: const Text('შენახვა'))])); }
  Future<void> _ownerDialog(Company c) async { final email = TextEditingController(), name = TextEditingController(), password = TextEditingController(); await showDialog(context: context, builder: (dialogContext) => AlertDialog(title: Text('Company Owner • ${c.name}'), content: Column(mainAxisSize: MainAxisSize.min, children: [TextField(controller: name, decoration: const InputDecoration(labelText: 'სახელი')), TextField(controller: email, decoration: const InputDecoration(labelText: 'ელფოსტა')), TextField(controller: password, obscureText: true, decoration: const InputDecoration(labelText: 'პაროლი'))]), actions: [TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('გაუქმება')), FilledButton(onPressed: () async { try { await ref.read(ownerApiProvider).createCompanyOwner(c.id, {'full_name': name.text, 'email': email.text, 'password': password.text}); if (dialogContext.mounted) Navigator.pop(dialogContext); _snack('Company Owner შეიქმნა'); } catch (e) { _snack(e.toString()); } }, child: const Text('შექმნა'))])); }
  Future<void> _commercialDialog(Company company) async {
    final packages = await ref.read(ownerApiProvider).packages();
    if (!mounted || packages.isEmpty) return;
    PackagePlan selected = packages.first;
    final monthly = TextEditingController(text: selected.monthly == '—' ? '' : selected.monthly);
    final annual = TextEditingController(text: selected.annual == '—' ? '' : selected.annual);
    final trialDays = TextEditingController(text: '14');
    final featureKey = TextEditingController();
    final limitKey = TextEditingController();
    final limitValue = TextEditingController();
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: Text('კომერციული პარამეტრები • ${company.name}'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                DropdownButton<PackagePlan>(
                  value: selected,
                  isExpanded: true,
                  items: [for (final item in packages) DropdownMenuItem(value: item, child: Text('${item.name} • ${item.monthly} ${item.currency}/თვე'))],
                  onChanged: (value) {
                    if (value == null) return;
                    setDialogState(() {
                      selected = value;
                      monthly.text = value.monthly == '—' ? '' : value.monthly;
                      annual.text = value.annual == '—' ? '' : value.annual;
                    });
                  },
                ),
                TextField(controller: monthly, decoration: const InputDecoration(labelText: 'შეთანხმებული თვიური ფასი')),
                TextField(controller: annual, decoration: const InputDecoration(labelText: 'შეთანხმებული წლიური ფასი')),
                const Divider(),
                TextField(controller: trialDays, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Trial დღეები (0 = არ შეცვალო)')),
                TextField(controller: featureKey, decoration: const InputDecoration(labelText: 'Feature override key')),
                TextField(controller: limitKey, decoration: const InputDecoration(labelText: 'Limit override key')),
                TextField(controller: limitValue, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Limit override value')),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('გაუქმება')),
            FilledButton(
              onPressed: () async {
                try {
                  await ref.read(ownerApiProvider).assignSubscription(company.id, {'package_id': selected.id, 'agreed_monthly_price': num.parse(monthly.text), 'agreed_annual_price': num.parse(annual.text), 'currency': selected.currency, 'starts_at': DateTime.now().toUtc().toIso8601String()});
                  final days = int.tryParse(trialDays.text) ?? 0;
                  if (days > 0) await ref.read(ownerApiProvider).grantTrial(company.id, {'ends_at': DateTime.now().toUtc().add(Duration(days: days)).toIso8601String(), 'reason': 'Owner UI grant'});
                  if (featureKey.text.trim().isNotEmpty) await ref.read(ownerApiProvider).createOverride(company.id, {'kind': 'feature', 'key': featureKey.text.trim(), 'bool_value': true, 'effective_from': DateTime.now().toUtc().toIso8601String(), 'reason': 'Owner UI override'});
                  if (limitKey.text.trim().isNotEmpty) await ref.read(ownerApiProvider).createOverride(company.id, {'kind': 'limit', 'key': limitKey.text.trim(), 'int_value': int.parse(limitValue.text), 'effective_from': DateTime.now().toUtc().toIso8601String(), 'reason': 'Owner UI override'});
                  if (dialogContext.mounted) Navigator.pop(dialogContext);
                  _snack('კომერციული პარამეტრები განახლდა');
                } catch (e) {
                  _snack(e.toString());
                }
              },
              child: const Text('შენახვა'),
            ),
          ],
        ),
      ),
    );
  }
  void _snack(String message) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
}

class PackagesPage extends ConsumerStatefulWidget { const PackagesPage({super.key}); @override ConsumerState<PackagesPage> createState() => _PackagesPageState(); }
class _PackagesPageState extends ConsumerState<PackagesPage> {
  late Future<List<PackagePlan>> future;
  @override void initState() { super.initState(); future = ref.read(ownerApiProvider).packages(); }
  void reload() => setState(() => future = ref.read(ownerApiProvider).packages());
  @override
  Widget build(BuildContext context) => Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(24),
            child: Row(
              children: [
                Expanded(child: Text('პაკეტები, ფასები და ლიმიტები', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800))),
                FilledButton.icon(onPressed: () => _dialog(), icon: const Icon(Icons.add), label: const Text('ახალი პაკეტი')),
              ],
            ),
          ),
          Expanded(
            child: FutureBuilder<List<PackagePlan>>(
              future: future,
              builder: (context, snapshot) {
                if (snapshot.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
                if (snapshot.hasError) return _ErrorState(message: snapshot.error.toString(), onRetry: reload);
                final items = snapshot.data ?? [];
                return ListView.separated(
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  itemCount: items.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 8),
                  itemBuilder: (_, i) {
                    final p = items[i];
                    return Card(
                      child: ExpansionTile(
                        title: Text('${p.name} (${p.code})'),
                        subtitle: Text('${p.monthly} ${p.currency}/თვე • ${p.annual} ${p.currency}/წელი'),
                        trailing: Wrap(
                          children: [
                            IconButton(tooltip: 'რედაქტირება', onPressed: () => _dialog(p), icon: const Icon(Icons.edit_outlined)),
                            IconButton(tooltip: p.archived ? 'გააქტიურება' : 'არქივირება', onPressed: () async { await ref.read(ownerApiProvider).updatePackage(p.id, {'archive': !p.archived}); reload(); }, icon: Icon(p.archived ? Icons.unarchive_outlined : Icons.archive_outlined)),
                          ],
                        ),
                        children: [
                          Padding(
                            padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text('Features: ${p.features.entries.where((e) => e.value).map((e) => e.key).join(', ')}'), const SizedBox(height: 8), Text('Limits: ${p.limits.entries.map((e) => '${e.key}=${e.value}').join(' • ')}')]),
                          ),
                        ],
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      );
  Future<void> _dialog([PackagePlan? current]) async { final code = TextEditingController(text: current?.code), name = TextEditingController(text: current?.name), description = TextEditingController(text: current?.description), monthly = TextEditingController(text: current?.monthly == '—' ? '' : current?.monthly), annual = TextEditingController(text: current?.annual == '—' ? '' : current?.annual), currency = TextEditingController(text: current?.currency ?? 'GEL'), features = TextEditingController(text: current?.features.keys.where((key) => current!.features[key] == true).join(', ') ?? 'employees, attendance, leave, reports'), employees = TextEditingController(text: current?.limits['employees']?.toString() ?? '15'), administrators = TextEditingController(text: current?.limits['administrators']?.toString() ?? '2'), managers = TextEditingController(text: current?.limits['managers']?.toString() ?? '3'), branches = TextEditingController(text: current?.limits['branches']?.toString() ?? '1'), devices = TextEditingController(text: current?.limits['devices']?.toString() ?? '20'), storage = TextEditingController(text: current?.limits['storage_mb']?.toString() ?? '1024'), sms = TextEditingController(text: current?.limits['sms_quota']?.toString() ?? '100'), email = TextEditingController(text: current?.limits['email_quota']?.toString() ?? '1000'); final form = GlobalKey<FormState>(); final limits = {'employees': employees, 'administrators': administrators, 'managers': managers, 'branches': branches, 'devices': devices, 'storage_mb': storage, 'sms_quota': sms, 'email_quota': email}; await showDialog(context: context, builder: (dialogContext) => AlertDialog(title: Text(current == null ? 'პაკეტის შექმნა' : 'პაკეტის რედაქტირება'), content: SizedBox(width: 540, child: SingleChildScrollView(child: Form(key: form, child: Column(children: [TextFormField(controller: name, decoration: const InputDecoration(labelText: 'სახელი'), validator: (v) => v == null || v.length < 2 ? 'აუცილებელია' : null), TextFormField(controller: code, enabled: current == null, decoration: const InputDecoration(labelText: 'კოდი (მაგ. START)'), validator: (v) => v == null || v.length < 2 ? 'აუცილებელია' : null), TextField(controller: description, decoration: const InputDecoration(labelText: 'აღწერა')), Row(children: [Expanded(child: TextFormField(controller: monthly, decoration: const InputDecoration(labelText: 'თვიური ფასი'), validator: (v) => num.tryParse(v ?? '') == null ? 'რიცხვი' : null)), const SizedBox(width: 8), Expanded(child: TextFormField(controller: annual, decoration: const InputDecoration(labelText: 'წლიური ფასი'), validator: (v) => num.tryParse(v ?? '') == null ? 'რიცხვი' : null)), const SizedBox(width: 8), SizedBox(width: 80, child: TextField(controller: currency, decoration: const InputDecoration(labelText: 'ვალუტა')))]), TextField(controller: features, decoration: const InputDecoration(labelText: 'Features (მძიმით გამოყოფილი)')), const SizedBox(height: 8), const Align(alignment: Alignment.centerLeft, child: Text('ლიმიტები')), for (final entry in limits.entries) TextField(controller: entry.value, keyboardType: TextInputType.number, decoration: InputDecoration(labelText: entry.key))])))), actions: [TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('გაუქმება')), FilledButton(onPressed: () async { if (!form.currentState!.validate()) return; final featureMap = {for (final key in features.text.split(',').map((e) => e.trim()).where((e) => e.isNotEmpty)) key: true}; final limitMap = {for (final entry in limits.entries) entry.key: int.tryParse(entry.value.text) ?? 0}; try { if (current == null) { await ref.read(ownerApiProvider).createPackage({'code': code.text.toUpperCase(), 'name': name.text, 'description': description.text, 'monthly_price': num.parse(monthly.text), 'annual_price': num.parse(annual.text), 'currency': currency.text.toUpperCase(), 'features': featureMap, 'limits': limitMap}); } else { await ref.read(ownerApiProvider).updatePackage(current.id, {'name': name.text, 'description': description.text}); await ref.read(ownerApiProvider).addPriceVersion(current.id, {'monthly_price': num.parse(monthly.text), 'annual_price': num.parse(annual.text), 'currency': currency.text.toUpperCase(), 'discount_percent': 0, 'effective_from': DateTime.now().toUtc().toIso8601String()}); for (final entry in featureMap.entries) { await ref.read(ownerApiProvider).updateFeature(current.id, entry.key, entry.value); } for (final entry in limitMap.entries) { await ref.read(ownerApiProvider).updateLimit(current.id, entry.key, entry.value); } } if (dialogContext.mounted) Navigator.pop(dialogContext); reload(); } catch (e) { if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()))); } }, child: const Text('შენახვა'))])); }
}

class IntegrationsPage extends ConsumerStatefulWidget { const IntegrationsPage({super.key}); @override ConsumerState<IntegrationsPage> createState() => _IntegrationsPageState(); }
class _IntegrationsPageState extends ConsumerState<IntegrationsPage> {
  late Future<List<Map<String, dynamic>>> future;
  @override void initState() { super.initState(); future = ref.read(ownerApiProvider).providers(); }
  void reload() => setState(() => future = ref.read(ownerApiProvider).providers());
  @override
  Widget build(BuildContext context) => FutureBuilder<List<Map<String, dynamic>>>(
        future: future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
          if (snapshot.hasError) return _ErrorState(message: snapshot.error.toString(), onRetry: reload);
          final items = snapshot.data ?? const <Map<String, dynamic>>[];
          return ListView(
            padding: const EdgeInsets.all(24),
            children: [
              Text('Integrations → SMS & Email Providers', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800)),
              const SizedBox(height: 8),
              const Text('API Keys ინახება მხოლოდ სერვერულ Secret Storage-ში და UI-ში სრულად არასდროს ბრუნდება.'),
              const SizedBox(height: 20),
              for (final item in items)
                Card(
                  child: ListTile(
                    leading: Icon(item['provider'] == 'brevo' ? Icons.email_outlined : Icons.sms_outlined),
                    title: Text(item['provider'].toString().toUpperCase()),
                    subtitle: Text('${item['enabled'] == true ? 'აქტიური' : 'გამორთული'} • ${item['secret_configured'] == true ? item['secret_masked'] : 'Secret არ არის კონფიგურირებული'} • Test: ${item['last_test_status']}'),
                    trailing: Wrap(
                      spacing: 4,
                      children: [
                        IconButton(tooltip: 'Test Connection', onPressed: () async { final result = await ref.read(ownerApiProvider).testProvider(item['provider'].toString()); if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(result['live_verified'] == true ? 'რეალური provider connection წარმატებულია' : 'ტესტი ვერ დადასტურდა: ${result['error']}'))); reload(); }, icon: const Icon(Icons.wifi_tethering)),
                        IconButton(tooltip: item['enabled'] == true ? 'გამორთვა' : 'ჩართვა', onPressed: () async { await ref.read(ownerApiProvider).updateProvider(item['provider'].toString(), {'enabled': item['enabled'] != true}); reload(); }, icon: Icon(item['enabled'] == true ? Icons.toggle_on : Icons.toggle_off)),
                      ],
                    ),
                  ),
                ),
            ],
          );
        },
      );
}

class AuditPage extends ConsumerStatefulWidget { const AuditPage({super.key}); @override ConsumerState<AuditPage> createState() => _AuditPageState(); }
class _AuditPageState extends ConsumerState<AuditPage> { late Future<List<AuditEntry>> future; @override void initState() { super.initState(); future = ref.read(ownerApiProvider).auditLog(); } @override Widget build(BuildContext context) => FutureBuilder<List<AuditEntry>>(future: future, builder: (context, snapshot) { if (snapshot.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator()); if (snapshot.hasError) return _ErrorState(message: snapshot.error.toString(), onRetry: () => setState(() => future = ref.read(ownerApiProvider).auditLog())); final items = snapshot.data ?? []; return ListView.builder(padding: const EdgeInsets.all(24), itemCount: items.length, itemBuilder: (_, i) => Card(child: ListTile(leading: const Icon(Icons.history), title: Text(items[i].action), subtitle: Text('${items[i].target} • ${items[i].details}')))); }); }

class _MetricCard extends StatelessWidget { const _MetricCard(this.title, this.value, this.icon, this.color); final String title; final int value; final IconData icon; final Color color; @override Widget build(BuildContext context) => SizedBox(width: 210, child: Card(child: Padding(padding: const EdgeInsets.all(18), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Icon(icon, color: color), const SizedBox(height: 12), Text('$value', style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800)), Text(title)])))); }
class _ErrorState extends StatelessWidget { const _ErrorState({required this.message, required this.onRetry}); final String message; final VoidCallback onRetry; @override Widget build(BuildContext context) => Center(child: Column(mainAxisSize: MainAxisSize.min, children: [Text(message, textAlign: TextAlign.center), const SizedBox(height: 12), OutlinedButton(onPressed: onRetry, child: const Text('თავიდან ცდა'))])); }
