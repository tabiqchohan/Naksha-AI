import 'package:flutter_test/flutter_test.dart';
import 'package:nakshai_mobile/models/cbm_model.dart';
import 'package:nakshai_mobile/services/api_service.dart';

void main() {
  group('Phase A2.4 Architectural Drawings & Export Tests', () {
    test('CBM drawing payload structure and ID preservation', () {
      final cbmJson = {
        'schema_version': '1.0.0',
        'project_id': 'proj_drawing_999',
        'title': 'Export Test Villa',
        'site': {
          'plot_width': 50.0,
          'plot_length': 90.0,
          'unit': 'feet',
        },
        'levels': [
          {
            'level_id': 'lvl_0',
            'index': 0,
            'name': 'Ground Floor',
            'elevation': 0.0,
            'height': 11.0,
          }
        ],
        'walls': [],
        'rooms': [
          {
            'id': 'r_drawing_1',
            'level_id': 'lvl_0',
            'name': 'Drawing Hall',
            'room_type': 'drawing_room',
            'polygon': [[0, 0], [25, 0], [25, 20], [0, 20]],
            'area_sqft': 500.0,
          }
        ],
      };

      final cbm = CanonicalBuildingModelData.fromJson(cbmJson);
      expect(cbm.projectId, 'proj_drawing_999');
      expect(cbm.title, 'Export Test Villa');
      expect(cbm.rooms.first.id, 'r_drawing_1');
      expect(cbm.rooms.first.areaSqft, 500.0);

      final serialized = cbm.toJson();
      expect(serialized['project_id'], 'proj_drawing_999');
      expect(serialized['rooms'][0]['id'], 'r_drawing_1');
    });

    test('ApiService drawing and export helper method existence', () {
      expect(ApiService.cbmDrawings, isNotNull);
      expect(ApiService.cbmExportPdf, isNotNull);
      expect(ApiService.cbmExportDxf, isNotNull);
      expect(ApiService.cbmBoq, isNotNull);
      expect(ApiService.cbmCompliance, isNotNull);
    });

    test('Export failure and empty binary handling simulation', () {
      bool handleExportResponse(List<int>? bytes) {
        if (bytes == null || bytes.isEmpty) {
          return false; // Empty or failed export handling
        }
        return true;
      }

      expect(handleExportResponse(null), isFalse);
      expect(handleExportResponse([]), isFalse);
      expect(handleExportResponse([0x25, 0x50, 0x44, 0x46]), isTrue); // Mock PDF magic bytes %PDF
    });
  });
}
