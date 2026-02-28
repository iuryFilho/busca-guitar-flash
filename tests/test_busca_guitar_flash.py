import unittest

import busca_guitar_flash


class BuscaGuitarFlashTestCase(unittest.TestCase):
    def test_get_song_set_returns_empty_for_html_without_table(self):
        html = "<html><body><p>Sem tabela</p></body></html>"

        songs = busca_guitar_flash.get_song_set(html)

        self.assertEqual(songs, set())

    def test_get_song_set_extracts_name_and_link(self):
        html = """
        <table>
            <tr><td><a href=\"/music-1\">Music One</a></td></tr>
            <tr><td><a href=\"/music-2\">Music Two</a></td></tr>
        </table>
        """

        songs = busca_guitar_flash.get_song_set(html)

        self.assertEqual(
            songs,
            {
                ("Music One", "/music-1"),
                ("Music Two", "/music-2"),
            },
        )

    def test_search_song_is_case_insensitive(self):
        song_set = {
            ("Master of Puppets", "/mop"),
            ("Nothing Else Matters", "/nem"),
        }

        results = busca_guitar_flash.search_song("PUPPETS", song_set)

        self.assertEqual(results, {("Master of Puppets", "/mop")})

    def test_inf_gen_with_stop(self):
        numbers = list(busca_guitar_flash.inf_gen(3))

        self.assertEqual(numbers, [0, 1, 2])


if __name__ == "__main__":
    unittest.main()
