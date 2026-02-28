import os
import unittest
from unittest.mock import patch

os.environ.setdefault("FLASK_SECRET_KEY", "test-secret-key-with-at-least-32-characters")
os.environ.setdefault("ADMIN_PASSWORD", "test-admin-password-strong-123")

import src.app as web_app


class AppHelpersTestCase(unittest.TestCase):
    def test_to_absolute_link_with_relative_path(self):
        result = web_app._to_absolute_link("/custom/song.asp?id=10")
        self.assertEqual(result, "https://guitarflash.com/custom/song.asp?id=10")

    def test_to_absolute_link_with_absolute_url(self):
        absolute = "https://guitarflash.com/custom/song.asp?id=10"
        result = web_app._to_absolute_link(absolute)
        self.assertEqual(result, absolute)


class AppSecurityTestCase(unittest.TestCase):
    def test_validated_admin_user_rejects_empty_value(self):
        with patch.dict(os.environ, {"ADMIN_USERNAME": ""}, clear=False):
            with self.assertRaises(RuntimeError):
                web_app._get_validated_admin_user()

    def test_validated_admin_user_accepts_value(self):
        with patch.dict(os.environ, {"ADMIN_USERNAME": "bgf-admin"}, clear=False):
            self.assertEqual(web_app._get_validated_admin_user(), "bgf-admin")

    def test_validated_admin_password_rejects_weak_value(self):
        with patch.dict(os.environ, {"ADMIN_PASSWORD": "admin123"}, clear=False):
            with self.assertRaises(RuntimeError):
                web_app._get_validated_admin_password()

    def test_validated_admin_password_accepts_strong_value(self):
        strong_password = "Senha-Admin-Forte-2026"
        with patch.dict(os.environ, {"ADMIN_PASSWORD": strong_password}, clear=False):
            self.assertEqual(web_app._get_validated_admin_password(), strong_password)


class AppRoutesTestCase(unittest.TestCase):
    def setUp(self):
        web_app.app.config["TESTING"] = True
        web_app.app.config["SECRET_KEY"] = "test-secret"
        self.client = web_app.app.test_client()

    def _login_admin_session(self):
        with self.client.session_transaction() as sess:
            sess["is_admin"] = True

    @patch("src.app._read_songs")
    def test_index_renders_song_list(self, mock_read_songs):
        mock_read_songs.return_value = {
            ("Song A", "/song-a"),
            ("Another Song", "/another-song"),
        }

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Song A", response.data)
        self.assertIn(b"Another Song", response.data)

    @patch("src.app._read_songs")
    def test_index_search_filters_results(self, mock_read_songs):
        mock_read_songs.return_value = {
            ("Master of Puppets", "/mop"),
            ("Nothing Else Matters", "/nem"),
        }

        response = self.client.get("/?q=puppets")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Master of Puppets", response.data)
        self.assertNotIn(b"Nothing Else Matters", response.data)

    def test_admin_update_requires_authentication(self):
        response = self.client.get("/admin/update")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login?next=/admin/update", response.location)

    def test_admin_login_with_invalid_credentials(self):
        response = self.client.post(
            "/admin/login",
            data={"username": "invalid", "password": "invalid", "next": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Credenciais inválidas".encode("utf-8"), response.data)

    def test_admin_login_success_redirects_to_update(self):
        response = self.client.post(
            "/admin/login",
            data={
                "username": web_app.ADMIN_USERNAME,
                "password": web_app.ADMIN_PASSWORD,
                "next": "/admin/update",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/admin/update"))

    @patch("src.app._refresh_songs")
    @patch("src.app._read_songs")
    def test_admin_update_with_invalid_pages(self, mock_read_songs, mock_refresh_songs):
        mock_read_songs.return_value = {("Song", "/song")}
        self._login_admin_session()

        response = self.client.post("/admin/update", data={"pages": "0"})

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Informe um número de páginas válido".encode("utf-8"),
            response.data,
        )
        mock_refresh_songs.assert_not_called()

    @patch("src.app._refresh_songs")
    @patch("src.app._read_songs")
    def test_admin_update_success_message(self, mock_read_songs, mock_refresh_songs):
        mock_read_songs.return_value = {("Song", "/song")}
        mock_refresh_songs.return_value = {
            ("Song A", "/song-a"),
            ("Song B", "/song-b"),
        }
        self._login_admin_session()

        response = self.client.post("/admin/update", data={"pages": "3"})

        self.assertEqual(response.status_code, 200)
        self.assertIn("Lista atualizada com 2 músicas.".encode("utf-8"), response.data)
        mock_refresh_songs.assert_called_once_with(3)


if __name__ == "__main__":
    unittest.main()
