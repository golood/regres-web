import json
import unittest
import app
import unittest.mock as mock
from server.models import MetaData


class Test(unittest.TestCase):
    def setUp(self):
        app.app.config['SECRET_KEY'] = 'sekrit!'
        self.app = app.app.test_client()
        self.data = json.dumps({
            'session_id': '',
            'user_session_id': '',

            'mnk': '',
            'mnm': '',
            'mao': '',
            'mco': '',

            'freeChlen': '',
            'file_id': '',
            'load_matrix_id': '',
            'work_matrix_id': '',

            'len_x_load_matrix': '',
            'len_load_matrix': '',
            'len_x_work_matrix': '',
            'len_work_matrix': '',

            'index_y': '',

            'matrix_y_index': '',
            'matrix_x_index': '',

            'index_h1': '',
            'index_h2': '',
            'answer': ''
        })

    def test_allowed_file(self):
        self.assertTrue(app.allowed_file('file.txt'))
        self.assertFalse(app.allowed_file('file.pdf'))
        self.assertFalse(app.allowed_file('file'))

    def test_get_meta_data_with_session(self):
        app.is_object_session = mock.Mock(return_value=True)
        app.get_object_session = mock.Mock(return_value=self.data)

        app.get_meta_data()

        app.is_object_session.assert_called_once_with('meta_data')
        app.get_object_session.assert_called_once_with('meta_data')

    def test_get_meta_data_without_session(self):
        app.is_object_session = mock.Mock(return_value=False)
        app.MetaData.add_session = mock.Mock()
        app.set_object_session = mock.Mock()

        m = mock.MagicMock()
        m.headers.environ = {"HTTP_USER_AGENT": 'test', 'REMOTE_ADDR': 'test'}

        with mock.patch("app.request", m):
            actual = app.get_meta_data()

        self.assertEqual(MetaData(None), actual)
        app.MetaData.add_session.assert_called_once()
        app.is_object_session.assert_called_once_with('meta_data')
        app.set_object_session.assert_called_once()

    def test_redirect_to_main(self):
        app.is_object_session = mock.Mock(return_value=False)
        app.get_meta_data = mock.MagicMock()
        app.update_time_active = mock.Mock()

        resp = self.app.get('/answer', follow_redirects=True)

        self.assertTrue('<title>Решение регрессионных уравнений</title>' in resp.data.decode("utf-8"))

    def test_main(self):
        app.is_object_session = mock.Mock(return_value=False)
        app.update_time_active = mock.Mock()
        app.get_meta_data = mock.Mock(return_value=MetaData(None))
        app.MetaData.update_time_active = mock.Mock()

        resp = self.app.get('/')

        self.assertEqual(200, resp.status_code)
        self.assertEqual(4439, resp.content_length)

    def tearDown(self):
        del self.app


if __name__ == '__main__':
    unittest.main()
