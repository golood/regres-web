import json
import unittest

from server.models import CalculationMode


class TestCalculationMode(unittest.TestCase):
    def test_json_dump(self):
        data = {
            "one": 1,
            "string": 'sfsf',
            "mode": CalculationMode.STANDARD
        }

        expected = '{"one": 1, "string": "sfsf", "mode": "STANDARD"}'
        actual = json.dumps(data)

        self.assertEqual(expected, actual)
        self.assertEqual(data, json.loads(actual))


if __name__ == '__main__':
    unittest.main()
