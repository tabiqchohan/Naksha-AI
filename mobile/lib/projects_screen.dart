import 'package:flutter/material.dart';
import 'services/api_service.dart';
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
  void initState() { super.initState(); loadProjects(); }

  Future<void> loadProjects() async {
    final token = await ApiService.token();
    if (token == null || token.isEmpty) { setState(() { loading = false; loggedIn = false; }); return; }
    setState(() { loggedIn = true; loading = true; });
    try {
      final data = await ApiService.get('/projects/list', auth: true);
      setState(() => projects = data is List ? data : []);
    } catch (e) { setState(() => status = e.toString()); }
    setState(() => loading = false);
  }

  Future<void> deleteProject(String projectId) async {
    try { await ApiService.delete('/projects/$projectId', auth: true); await loadProjects(); }
    catch (e) { if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Delete failed: $e'))); }
  }

  Future<void> openProject(Map p) async {
    try {
      final data = await ApiService.get('/projects/${p['project_id']}', auth: true);
      if (!mounted) return;
      await Navigator.push(context, MaterialPageRoute(builder: (_) => FloorPlanEditorScreen(initialPlan: Map<String, dynamic>.from(data as Map))));
    } catch (e) { if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Open failed: $e'))); }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(backgroundColor: Colors.white, elevation: 0, title: const Text('My Projects', style: TextStyle(color: Color(0xFF0F172A))), actions: [if (loggedIn) IconButton(onPressed: loadProjects, icon: const Icon(Icons.refresh))]),
      body: loading ? const Center(child: CircularProgressIndicator()) : !loggedIn ? Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        const Icon(Icons.folder_open, size: 64, color: Color(0xFFCBD5E1)),
        const SizedBox(height: 16),
        const Text('Sign in to view projects', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
        const SizedBox(height: 16),
        ElevatedButton(onPressed: () async { final result = await Navigator.push(context, MaterialPageRoute(builder: (_) => const LoginScreen())); if (result == true) loadProjects(); }, child: const Text('Sign In')),
      ])) : projects.isEmpty ? Center(child: Padding(padding: const EdgeInsets.all(24), child: Text(status.isEmpty ? 'No projects yet. Create your first floor plan!' : status, textAlign: TextAlign.center))) : ListView.builder(padding: const EdgeInsets.all(16), itemCount: projects.length, itemBuilder: (context, index) {
        final p = Map<String, dynamic>.from(projects[index] as Map);
        return Container(margin: const EdgeInsets.only(bottom: 12), padding: const EdgeInsets.all(16), decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE2E8F0))), child: Row(children: [
          Container(width: 44, height: 44, decoration: BoxDecoration(color: const Color(0xFFDBEAFE), borderRadius: BorderRadius.circular(10)), child: const Icon(Icons.home_work, color: Color(0xFF2563EB))),
          const SizedBox(width: 12),
          Expanded(child: InkWell(onTap: ()=>openProject(p), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text((p['title'] ?? 'Untitled').toString(), style: const TextStyle(fontWeight: FontWeight.bold)), Text('${p['plot_width']}x${p['plot_length']} ft · ${p['building_type']}', style: const TextStyle(fontSize: 12, color: Color(0xFF64748B)))]))),
          IconButton(icon: const Icon(Icons.open_in_new, color: Color(0xFF2563EB)), onPressed: () => openProject(p)),
          IconButton(icon: const Icon(Icons.delete_outline, color: Colors.red), onPressed: () => deleteProject(p['project_id'].toString())),
        ]));
      }),
    );
  }
}
