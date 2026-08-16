import unittest
from unittest.mock import Mock, patch

try:
    from NGIN.api import create_app
except ModuleNotFoundError as error:
    if error.name not in {"flask", "flask_cors"}:
        raise
    create_app = None


@unittest.skipIf(create_app is None, "Flask dependencies are not installed")
class TestApi(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True})
        self.client = self.app.test_client()

    def test_api_index_documents_campaign_endpoint(self):
        response = self.client.get("/api")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["endpoints"][0]["path"], "/api/generate_campaign")

    @patch("NGIN.api.load_json_from_file", side_effect=[{"story": []}, {"world_size": "small"}])
    @patch("NGIN.api.NGIN")
    def test_generate_campaign_returns_serialized_engine_state(self, mock_ngin, mock_load_json):
        mock_ngin.return_value.state.toJSON.return_value = {"ID": "state", "Nodetype": "state"}

        response = self.client.get("/api/generate_campaign")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["ID"], "state")
        mock_ngin.assert_called_once_with({"story": []}, {"world_size": "small"}, is_console=False)
        self.assertEqual(mock_load_json.call_count, 2)
