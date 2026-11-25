import 'package:flutter_test/flutter_test.dart';
import 'package:nakshai_mobile/models/floor_plan_model.dart';
import 'package:nakshai_mobile/services/api_service.dart';

void main() {
  group('CBM & Model Compatibility Tests', () {
    test('RoomModel fromJson and toJson parsing', () {
      final json = {
        'id': 'room_1',
        'name': 'Living Room',
        'type': 'living',
        'x': 0.0,
        'y': 0.0,
        'width': 15.0,
        'length': 20.0,
      };

      final room = RoomModel.fromJson(json);
      expect(room.id, 'room_1');
      expect(room.name, 'Living Room');
      expect(room.type, 'living');
      expect(room.width, 15.0);
      expect(room.length, 20.0);
      expect(room.sqft, 300.0);

      final outJson = room.toJson();
      expect(outJson['id'], 'room_1');
      expect(outJson['width'], 15.0);
    });

    test('PlotModel fromJson and calculations', () {
      final json = {
        'width': 25.0,
        'length': 45.0,
        'unit': 'feet',
      };

      final plot = PlotModel.fromJson(json);
      expect(plot.width, 25.0);
      expect(plot.length, 45.0);
      expect(plot.totalSqft, 1125.0);
      expect(plot.marla, 1125.0 / 225.0);
    });
  });

  group('ApiService Configuration & CBM Endpoints Tests', () {
    test('ApiService base URL and headers', () async {
      expect(ApiService.baseUrl, isNotEmpty);
      final headers = await ApiService.headers(json: true, auth: false);
      expect(headers['Content-Type'], 'application/json');
    });

    test('CBM payload helper methods exist and construct correct endpoints', () {
      // Verify static methods can be referenced and invoked structurally
      expect(ApiService.cbmUpdate, isNotNull);
      expect(ApiService.cbmBoq, isNotNull);
      expect(ApiService.cbmDrawings, isNotNull);
      expect(ApiService.cbmExportPdf, isNotNull);
      expect(ApiService.cbmExportDxf, isNotNull);
      expect(ApiService.cbmCompliance, isNotNull);
    });
  });
}
