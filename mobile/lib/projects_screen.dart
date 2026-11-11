import 'package:flutter/material.dart';
import 'services/api_service.dart';
import 'services/language_service.dart';
import 'login_screen.dart';
import 'screens/floor_plan_editor_screen.dart';

class ProjectsScreen extends StatefulWidget {
  const ProjectsScreen({super.key});

  @override
  State<ProjectsScreen> createState() => _ProjectsScreenState();
}

class _ProjectsScreenState extends State<ProjectsScreen> {
  List projects = [];
  bool loading = true;
  bool loggedIn = false;
  String status = '';

  @override
  void initState() {
    super.initState();
    loadProjects();
  }

  Future<void> loadProjects() async {
    final token = await ApiService.token();
    if (token == null || token.isEmpty) {
      setState(() {
        loading = false;
        loggedIn = false;
      });
      return;
    }
    setState(() {
      loggedIn = true;
      loading = true;
    });
    try {
      final data = await ApiService.get('/projects/list', auth: true);
      setState(() => projects = data is List ? data : []);
    } catch (e) {
      setState(() => status = e.toString());
    }
    setState(() => loading = false);
  }

  Future<void> _confirmDelete(String projectId) async {
    final lang = LanguageScope.of(context);
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(lang.t('Delete project?', 'منصوبہ حذف کریں؟')),
        content: Text(lang.t('This action cannot be undone.', 'یہ عمل واپس نہیں ہو سکتا۔')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: Text(lang.t('Cancel', 'منسوخ'))),
          TextButton(onPressed: () => Navigator.pop(dialogContext, true), child: Text(lang.t('Delete', 'حذف کریں'), style: const TextStyle(color: Colors.red))),
        ],
      ),
    );
    if (confirmed == true) await deleteProject(projectId);
  }

  Future<void> deleteProject(String projectId) async {
    final lang = LanguageScope.of(context);
    try {
      await ApiService.delete('/projects/$projectId', auth: true);
      await loadProjects();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('${lang.t('Delete failed', 'حذف ناکام')}: $e')));
    }
  }

  Future<void> openProject(Map p) async {
    final lang = LanguageScope.of(context);
    try {
      final data = await ApiService.get('/projects/${p['project_id']}', auth: true);
      if (!mounted) return;
      await Navigator.push(context, MaterialPageRoute(builder: (_) => FloorPlanEditorScreen(initialPlan: Map<String, dynamic>.from(data as Map))));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('${lang.t('Open failed', 'کھولنا ناکام')}: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final lang = LanguageScope.of(context);
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: Text(lang.t('My Projects', 'میرے منصوبے'), style: const TextStyle(color: Color(0xFF0F172A))),
        actions: [if (loggedIn) IconButton(onPressed: loadProjects, icon: const Icon(Icons.refresh))],
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : !loggedIn
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.folder_open, size: 64, color: Color(0xFFCBD5E1)),
                      const SizedBox(height: 16),
                      Text(lang.t('Sign in to view projects', 'منصوبے دیکھنے کے لیے سائن ان کریں'), style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: () async {
                          final result = await Navigator.push(context, MaterialPageRoute(builder: (_) => const LoginScreen()));
                          if (result == true) loadProjects();
                        },
                        child: Text(lang.t('Sign In', 'سائن ان')),
                      ),
                    ],
                  ),
                )
              : projects.isEmpty
                  ? Center(child: Padding(padding: const EdgeInsets.all(24), child: Text(status.isEmpty ? lang.t('No projects yet. Create your first floor plan!', 'ابھی کوئی منصوبہ نہیں۔ اپنا پہلا فلور پلان بنائیں!') : status, textAlign: TextAlign.center)))
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: projects.length,
                      itemBuilder: (context, index) {
                        final p = Map<String, dynamic>.from(projects[index] as Map);
                        return Container(
                          margin: const EdgeInsets.only(bottom: 12),
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE2E8F0))),
                          child: Row(
                            children: [
                              Container(width: 44, height: 44, decoration: BoxDecoration(color: const Color(0xFFDBEAFE), borderRadius: BorderRadius.circular(10)), child: const Icon(Icons.home_work, color: Color(0xFF2563EB))),
                              const SizedBox(width: 12),
                              Expanded(
                                child: InkWell(
                                  onTap: () => openProject(p),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text((p['title'] ?? lang.t('Untitled', 'بلا عنوان')).toString(), style: const TextStyle(fontWeight: FontWeight.bold)),
                                      Text('${p['plot_width']}x${p['plot_length']} ft · ${p['building_type']}', style: const TextStyle(fontSize: 12, color: Color(0xFF64748B))),
                                    ],
                                  ),
                                ),
                              ),
                              IconButton(icon: const Icon(Icons.open_in_new, color: Color(0xFF2563EB)), onPressed: () => openProject(p)),
                              IconButton(icon: const Icon(Icons.delete_outline, color: Colors.red), onPressed: () => _confirmDelete(p['project_id'].toString())),
                            ],
                          ),
                        );
                      },
                    ),
    );
  }
}
