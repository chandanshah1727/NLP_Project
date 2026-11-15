"""API tests use an isolated temporary SQLite database, never project records."""
import unittest
import io
from PIL import Image

from fastapi.testclient import TestClient
from backend.app import app
from backend.services.analytics_service import summarize
from backend.database import WasteRecord

client = TestClient(app)

class WasteAPITests(unittest.TestCase):
    def test_health(self):
        self.assertEqual(client.get("/").status_code, 200)

    def test_empty_analytics(self):
        data = client.get("/analytics/summary").json()
        self.assertEqual(data["total_records"], 0)
        self.assertEqual(data["compliance_percentage"], 0)

    def test_create_retrieve_update_delete(self):
        created = client.post("/records", json={"waste_category":"plastic","confidence":99.3,"location":"Hostel","selected_bin":"Residual Waste"})
        self.assertEqual(created.status_code, 201, created.text)
        record_id = created.json()["record_id"]
        self.assertFalse(created.json()["record"]["correct_segregation"])
        self.assertEqual(client.get(f"/records/{record_id}").status_code, 200)
        self.assertEqual(client.get("/records", params={"search":"plastic","limit":1}).json()["total"], 1)
        self.assertEqual(client.get("/records", params={"limit":1,"offset":1}).json()["items"], [])
        updated = client.put(f"/records/{record_id}", json={"selected_bin":"Recyclable","location":"Library"})
        self.assertTrue(updated.json()["record"]["correct_segregation"])
        self.assertEqual(client.get("/analytics/summary").json()["compliance_percentage"], 100)
        self.assertIn("categories", client.get("/analytics/categories").json())
        self.assertTrue(client.get("/analytics/trends").json())
        self.assertEqual(client.delete(f"/records/{record_id}").status_code, 204)
        self.assertEqual(client.get(f"/records/{record_id}").status_code, 404)

    def test_invalid_values_and_upload(self):
        self.assertEqual(client.post("/records", json={"waste_category":"unknown","confidence":50,"location":"Hostel","selected_bin":"Residual Waste"}).status_code, 422)
        self.assertEqual(client.post("/records", json={"waste_category":"glass","confidence":50,"location":"Airport","selected_bin":"Recyclable"}).status_code, 422)
        self.assertEqual(client.post("/predict", files={"file":("bad.txt",b"not image","text/plain")}).status_code, 415)
        self.assertEqual(client.get("/alerts").status_code, 200)

    def test_invalid_image_content(self):
        response = client.post("/predict", files={"file":("broken.png",b"not an image","image/png")})
        self.assertEqual(response.status_code, 400)

    def test_prediction_uses_existing_model(self):
        image = Image.new("RGB", (224, 224), color=(60, 130, 90))
        stream = io.BytesIO()
        image.save(stream, format="PNG")
        response = client.post("/predict", files={"file":("sample.png",stream.getvalue(),"image/png")})
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertIn(payload["predicted_class"], {"battery","cardboard","glass","metal","organic","paper","plastic","textile","trash"})
        self.assertGreaterEqual(payload["confidence"], 0)
        self.assertIn("recommended_bin", payload)

    def test_compliance_empty(self):
        self.assertEqual(summarize([])["compliance_percentage"], 0)

    def test_invalid_date_range(self):
        response = client.get("/records", params={"start":"2026-11-14","end":"2026-11-13"})
        self.assertEqual(response.status_code, 422)

if __name__ == "__main__": unittest.main()
