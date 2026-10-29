import 'package:flutter/material.dart';
import '../models/floor_plan_model.dart';
import '../widgets/floor_plan_painter.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

class FloorPlanEditorScreen extends StatefulWidget {
  const FloorPlanEditorScreen({super.key});

  @override
  State<FloorPlanEditorScreen> createState() => _FloorPlanEditorScreenState();
}

class _FloorPlanEditorScreenState extends State<FloorPlanEditorScreen> {
  final PlotModel _plot = PlotModel(width: 50, length: 60);
  int _selectedViewIndex = 0; // 0: 2D, 1: 3D
  String _buildingType = 'house';
  int _floors = 1;
  String _prompt = 'Generate 3 Bed, 2 Bath open layout for 50x40 plot.';
  bool _isGenerating = false;

  final List<RoomModel> _rooms = [
    RoomModel(
      id: 'r1',
      name: 'MASTER BED',
      type: 'master_bedroom',
      x: 0,
      y: 0,
      width: 26,
      length: 32,
      color: Colors.blue,
    ),
    RoomModel(
      id: 'r2',
      name: 'MASTER BED',
      type: 'bedroom',
      x: 0,
      y: 32,
      width: 26,
      length: 28,
      color: Colors.blueAccent,
    ),
    RoomModel(
      id: 'r3',
      name: 'BATH',
      type: 'attached_bath',
      x: 26,
      y: 0,
      width: 10,
      length: 18,
      color: Colors.teal,
    ),
    RoomModel(
      id: 'r4',
      name: 'KITCHEN',
      type: 'kitchen',
      x: 36,
      y: 0,
      width: 14,
      length: 32,
      color: Colors.amber,
    ),
    RoomModel(
      id: 'r5',
      name: 'LIVING ROOM',
      type: 'living_room',
      x: 26,
      y: 32,
      width: 24,
      length: 28,
      color: Colors.purple,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF1F5F9),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0284C7), // Mockup bright blue header
        elevation: 1,
        title: const Text(
          'NAKSHAI MOBILE - Project: Modern Home',
          style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
        ),
        actions: [
          // 2D / 3D Segmented Toggle (Matches Mockup)
          Container(
            margin: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                _buildViewToggle('2D', 0),
                _buildViewToggle('3D', 1),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.share, color: Colors.white, size: 18),
            onPressed: () {},
          ),
          IconButton(
            icon: const Icon(Icons.more_vert, color: Colors.white, size: 18),
            onPressed: () {},
          ),
        ],
      ),
      body: Row(
        children: [
          // Left Tool Strip (Matching Tablet Mockup)
          Container(
            width: 56,
            color: Colors.white,
            child: Column(
              children: [
                const Padding(
                  padding: EdgeInsets.only(top: 8, bottom: 4),
                  child: Text('TOOLS', style: TextStyle(fontSize: 8, fontWeight: FontWeight.bold, color: Colors.grey)),
                ),
                IconButton(icon: const Icon(Icons.add_box, color: Colors.blue, size: 22), tooltip: 'Add Room', onPressed: () {}),
                IconButton(icon: const Icon(Icons.grid_on, color: Colors.grey, size: 22), tooltip: 'Grid', onPressed: () {}),
                IconButton(icon: const Icon(Icons.straighten, color: Colors.grey, size: 22), tooltip: 'Measure', onPressed: () {}),
                IconButton(icon: const Icon(Icons.edit, color: Colors.grey, size: 22), tooltip: 'Edit', onPressed: () {}),
                IconButton(icon: const Icon(Icons.door_front_door, color: Colors.grey, size: 22), tooltip: 'Doors', onPressed: () {}),
                IconButton(icon: const Icon(Icons.window, color: Colors.grey, size: 22), tooltip: 'Windows', onPressed: () {}),
                IconButton(icon: const Icon(Icons.layers, color: Colors.grey, size: 22), tooltip: 'Layers', onPressed: () {}),
                IconButton(icon: const Icon(Icons.home_work, color: Colors.grey, size: 22), tooltip: 'Building Type', onPressed: () => _showBuildingTypeDialog()),
                IconButton(icon: const Icon(Icons.stairs, color: Colors.grey, size: 22), tooltip: 'Floors', onPressed: () => _showFloorsDialog()),
                const Spacer(),
                IconButton(icon: const Icon(Icons.auto_awesome, color: Colors.blue, size: 22), tooltip: 'AI Generate', onPressed: () => _showAIGenerateDialog()),
                IconButton(icon: const Icon(Icons.calculate, color: Colors.green, size: 22), tooltip: 'Estimate', onPressed: () {}),
                IconButton(icon: const Icon(Icons.picture_as_pdf, color: Colors.red, size: 22), tooltip: 'Export PDF', onPressed: () {}),
                IconButton(icon: const Icon(Icons.file_open, color: Colors.orange, size: 22), tooltip: 'Export DXF', onPressed: () {}),
                IconButton(icon: const Icon(Icons.settings, color: Colors.grey, size: 22), onPressed: () {}),
              ],
            ),
          ),

          // Main Canvas with Interactive Zoom/Pan
          Expanded(
            child: InteractiveViewer(
              minScale: 0.5,
              maxScale: 3.0,
              boundaryMargin: const EdgeInsets.all(50),
              child: Center(
                child: Container(
                  width: 500,
                  height: 600,
                  margin: const EdgeInsets.all(16),
                  child: CustomPaint(
                    painter: FloorPlanPainter(
                      plot: _plot,
                      rooms: _rooms,
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
      floatingActionButton: Column(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          FloatingActionButton.small(
            heroTag: 'ai_gen',
            backgroundColor: Colors.purple,
            child: const Icon(Icons.auto_awesome, color: Colors.white),
            onPressed: () => _showAIGenerateDialog(),
          ),
          const SizedBox(height: 8),
          FloatingActionButton.small(
            heroTag: 'add',
            backgroundColor: const Color(0xFF0284C7),
            child: const Icon(Icons.add, color: Colors.white),
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Use sidebar tools to add rooms, walls & furniture')),
              );
            },
          ),
        ],
      ),
    );
  }

  void _showBuildingTypeDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Select Building Type'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(title: const Text('Residential House'), leading: const Icon(Icons.home), onTap: () { setState(() => _buildingType = 'house'); Navigator.pop(context); }),
            ListTile(title: const Text('Commercial Plaza'), leading: const Icon(Icons.business), onTap: () { setState(() => _buildingType = 'plaza'); Navigator.pop(context); }),
            ListTile(title: const Text('Corner Shop'), leading: const Icon(Icons.store), onTap: () { setState(() => _buildingType = 'shop'); Navigator.pop(context); }),
            ListTile(title: const Text('Warehouse'), leading: const Icon(Icons.warehouse), onTap: () { setState(() => _buildingType = 'warehouse'); Navigator.pop(context); }),
            ListTile(title: const Text('Duplex'), leading: const Icon(Icons.home_work), onTap: () { setState(() => _buildingType = 'duplex'); Navigator.pop(context); }),
          ],
        ),
      ),
    );
  }

  void _showFloorsDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Select Floors'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(title: const Text('Ground Floor Only'), onTap: () { setState(() => _floors = 1); Navigator.pop(context); }),
            ListTile(title: const Text('G + 1 (Ground + First)'), onTap: () { setState(() => _floors = 2); Navigator.pop(context); }),
            ListTile(title: const Text('G + 2 (Ground + Two Floors)'), onTap: () { setState(() => _floors = 3); Navigator.pop(context); }),
          ],
        ),
      ),
    );
  }

  void _showAIGenerateDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.auto_awesome, color: Colors.purple),
            SizedBox(width: 8),
            Text('AI Generate Floor Plan'),
          ],
        ),
        content: SizedBox(
          width: 400,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextField(
                decoration: const InputDecoration(
                  labelText: 'Describe your requirement',
                  hintText: 'e.g., 5 Marla, 3 Bedrooms, 2 Baths, Open Kitchen',
                  border: OutlineInputBorder(),
                ),
                maxLines: 3,
                onChanged: (val) => _prompt = val,
              ),
              const SizedBox(height: 12),
              Text('Building Type: ${_buildingType.toUpperCase()} | Floors: ${_floors == 1 ? "Ground" : "G+${_floors-1}"}', style: const TextStyle(fontSize: 12, color: Colors.grey)),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          ElevatedButton.icon(
            icon: _isGenerating ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Icon(Icons.auto_awesome),
            label: Text(_isGenerating ? 'Generating...' : 'Generate'),
            onPressed: _isGenerating ? null : () async {
              Navigator.pop(context);
              await _generatePlan();
            },
          ),
        ],
      ),
    );
  }

  Future<void> _generatePlan() async {
    setState(() => _isGenerating = true);
    try {
      final response = await http.post(
        Uri.parse('http://10.0.2.2:8000/api/v1/plans/generate'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'prompt': _prompt,
          'plot_width': _plot.width,
          'plot_length': _plot.length,
          'building_type': _buildingType,
          'floors': _floors,
        }),
      );
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final roomsData = data['rooms'] as List;
        setState(() {
          _rooms.clear();
          for (var r in roomsData) {
            Color c = Colors.blue;
            final type = r['type'] ?? '';
            if (type.contains('kitchen')) c = Colors.amber;
            else if (type.contains('bath')) c = Colors.teal;
            else if (type.contains('living')) c = Colors.purple;
            else if (type.contains('garage')) c = Colors.grey;
            else if (type.contains('shop')) c = Colors.orange;
            else if (type.contains('stair')) c = Colors.blueGrey;
            _rooms.add(RoomModel(
              id: r['id'] ?? '',
              name: r['name'] ?? 'Room',
              type: type,
              x: (r['x'] as num).toDouble(),
              y: (r['y'] as num).toDouble(),
              width: (r['width'] as num).toDouble(),
              length: (r['length'] as num).toDouble(),
              color: c,
            ));
          }
        });
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Plan generated successfully!')),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    } finally {
      setState(() => _isGenerating = false);
    }
  }

  Widget _buildViewToggle(String label, int index) {
    final isSelected = _selectedViewIndex == index;
    return GestureDetector(
      onTap: () => setState(() => _selectedViewIndex = index),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: isSelected ? Colors.white : Colors.transparent,
          borderRadius: BorderRadius.circular(6),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? const Color(0xFF0284C7) : Colors.white,
            fontWeight: FontWeight.bold,
            fontSize: 11,
          ),
        ),
      ),
    );
  }
}
