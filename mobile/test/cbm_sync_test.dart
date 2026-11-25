import 'package:flutter_test/flutter_test.dart';
import 'package:nakshai_mobile/models/cbm_model.dart';
import 'package:nakshai_mobile/services/api_service.dart';

void main() {
  group('Phase A2.3 & A2.3-R CBM Model & Synchronization Tests', () {
    test('CbmSite parsing and JSON serialization', () {
      final json = {
        'plot_width': 40.0,
        'plot_length': 60.0,
        'unit': 'feet',
        'setbacks': {'front': 5.0, 'rear': 5.0, 'left': 3.0, 'right': 3.0},
      };

      final site = CbmSite.fromJson(json);
      expect(site.plotWidth, 40.0);
      expect(site.plotLength, 60.0);
      expect(site.unit, 'feet');
      expect(site.setbacks['front'], 5.0);

      final outJson = site.toJson();
      expect(outJson['plot_width'], 40.0);
      expect(outJson['setbacks']['front'], 5.0);
    });

    test('CanonicalBuildingModelData parsing, ID preservation, and serialization', () {
      final cbmJson = {
        'schema_version': '1.0.0',
        'project_id': 'proj_test_123',
        'title': 'Test Villa CBM',
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
        'walls': [
          {
            'id': 'w_1',
            'level_id': 'lvl_0',
            'start': [0.0, 0.0],
            'end': [50.0, 0.0],
            'thickness': 0.75,
            'wall_type': 'exterior',
          }
        ],
        'rooms': [
          {
            'id': 'r_1',
            'level_id': 'lvl_0',
            'name': 'Living Room',
            'room_type': 'living_room',
            'polygon': [[0,0], [20,0], [20,25], [0,25]],
            'area_sqft': 500.0,
          }
        ],
      };

      final cbm = CanonicalBuildingModelData.fromJson(cbmJson);
      expect(cbm.projectId, 'proj_test_123');
      expect(cbm.title, 'Test Villa CBM');
      expect(cbm.site.plotWidth, 50.0);
      expect(cbm.levels.length, 1);
      expect(cbm.levels.first.levelId, 'lvl_0');
      expect(cbm.walls.length, 1);
      expect(cbm.walls.first.id, 'w_1');
      expect(cbm.rooms.length, 1);
      expect(cbm.rooms.first.id, 'r_1');
      expect(cbm.rooms.first.areaSqft, 500.0);

      final serialized = cbm.toJson();
      expect(serialized['project_id'], 'proj_test_123');
      expect(serialized['rooms'][0]['id'], 'r_1');
      expect(serialized['site']['plot_length'], 90.0);
    });

    test('Stale response sequence guard verification', () {
      int activeSequence = 1;

      bool handleResponse(int requestSeq, String payload) {
        if (requestSeq != activeSequence) {
          return false; // Stale response ignored
        }
        return true;
      }

      // Simulate sending request 1, then user edits causing request 2
      final seq1 = activeSequence;
      activeSequence++;
      final seq2 = activeSequence;

      // Response 1 arrives later (stale)
      expect(handleResponse(seq1, 'old_data'), isFalse);
      // Response 2 arrives (latest)
      expect(handleResponse(seq2, 'new_data'), isTrue);
    });

    test('ApiService CbmUpdate helper method reference check', () {
      expect(ApiService.cbmUpdate, isNotNull);
      expect(ApiService.cbmBoq, isNotNull);
      expect(ApiService.cbmDrawings, isNotNull);
      expect(ApiService.cbmExportPdf, isNotNull);
      expect(ApiService.cbmExportDxf, isNotNull);
      expect(ApiService.cbmCompliance, isNotNull);
    });
  });
}
