#!/usr/bin/python3
import datetime

import deprecation
import psycopg2
from psycopg2.extras import execute_values

import server.config as config
import server.utill as util


def get_connection():
    """
    Получает соединения с БД.
    :return: соединение с БД.
    """

    conn = psycopg2.connect(dbname=config.POSTGRES_DB,
                            user=config.POSTGRES_USER,
                            password=config.POSTGRES_PASSWORD,
                            host=config.POSTGRES_HOST,
                            port=config.POSTGRES_PORT,
                            async_=True)
    return conn


class UserSessionRepo:
    """
    Репозитория для получения, записи данных пользователя сессии.
    """

    @staticmethod
    def add(session_id, ip):
        """
        Добавляет данные о новой сессии.

        :param session_id: клиентский идентификатор сессии.
        :param ip: адрес клиента.
        :return: серверный идентификатор клиента сессии.
        """

        conn = get_connection()

        with conn.cursor() as cursor:
            conn.autocommit = True
            date_time = datetime.datetime.now()
            values = (session_id, date_time, date_time, ip)

            insert = 'INSERT INTO user_session (session_id, date_create, date_last_active, ip_adress) ' \
                     + 'VALUES (%s, %s, %s, %s) RETURNING id'

            cursor.execute(insert, values)

            answer = cursor.fetchone()[0]

        conn.close()
        return answer

    @staticmethod
    def update_user_active(user_id):
        """
        Обновляет время последней активности клиента.
        :param user_id: серверный идентификатор клиента.
        """

        conn = get_connection()

        with conn.cursor() as cursor:
            conn.autocommit = True
            date_time = datetime.datetime.now()
            values = (date_time, user_id)

            update = 'UPDATE user_session SET date_last_active = %s WHERE id = %s'

            cursor.execute(update, values)
        conn.close()


class LoadFilesRepo:
    """
    Репозиторий для получения, записи данных для файлов.
    """

    @staticmethod
    def add_file(user_id, filename):
        """
        Привязывает загруженный файл к пользователю..
        :param user_id: идентификатор пользователя.
        :param filename: имя файла.
        :return: идентификатор файла.
        """

        conn = get_connection()

        with conn.cursor() as cursor:
            conn.autocommit = True
            values = (user_id, filename)

            insert = 'INSERT INTO load_files (user_id, file_name) ' \
                     + 'VALUES (%s, %s) RETURNING id'

            cursor.execute(insert, values)

            answer = cursor.fetchone()[0]

        conn.close()
        return answer


class MatrixRepo:
    """
    Репозиторий для работы с данными матриц.
    """

    @staticmethod
    def get_new_index():
        """
        Получает новый индентификатор.
        :return: новый идентификатор.
        """

        conn = get_connection()

        with conn.cursor() as cursor:
            conn.autocommit = True

            select = "select nextval('files_id_seq')"

            cursor.execute(select)

            answer = cursor.fetchone()[0]

        conn.close()
        return answer

    def add_matrix(self, matrix):
        """
        Добавляет матрицу с числовыми значениями.
        :param matrix: матрица вида [[],[],].
        :return: идентификатор матрицы.
        """

        matrix_id = self.get_new_index()

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            insert = 'INSERT INTO matrix (id, row_id, column_id, value) VALUES %s'

            values = []
            row_id = 0
            for row in matrix:
                column_id = 0
                for item in row:
                    values.append((matrix_id, row_id, column_id, str(item),))
                    column_id += 1
                row_id += 1

            execute_values(cur=cursor, sql=insert, argslist=values, page_size=200)

        conn.close()
        return matrix_id

    @staticmethod
    def get_matrix(matrix_id):
        """
        Получает матрицу.
        :param matrix_id: идентификатор матрицы.
        :return: матрицу с числовыми значениями вида [[],[],]
        """

        matrix = []

        conn = get_connection()

        with conn.cursor() as cursor:
            conn.autocommit = True

            select = 'SELECT row_id, column_id, "value" FROM matrix WHERE id = %s ORDER BY row_id, column_id'
            cursor.execute(select, (matrix_id,))

            rows = cursor.fetchall()

            row_num = 0
            line = []
            for row in rows:
                if row_num == int(row[0]):
                    line.append(util.format_number(row[2]))
                else:
                    matrix.append(line)
                    row_num += 1
                    line = [util.format_number(row[2])]
            matrix.append(line)

        conn.close()
        return matrix

    def set_row(self, row):
        """
        Добавляет массив чисел.
        :param row: массив чисел.
        :return: идентификатор массива.
        """

        row_id = self.get_new_index()

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            insert = 'INSERT INTO matrix (id, row_id, column_id, value) VALUES %s'

            values = []
            column_id = 0
            for item in row:
                values.append((row_id, 0, column_id, str(item),))
                column_id += 1

            execute_values(cur=cursor, sql=insert, argslist=values, page_size=200)

        conn.close()
        return row_id

    @staticmethod
    def get_row(row_id):
        """
        Получает массив чисел.
        :param row_id: идентификатор массива.
        :return: массив чисел.
        """

        conn = get_connection()

        with conn.cursor() as cursor:
            conn.autocommit = True

            select = 'SELECT row_id, column_id, "value" FROM matrix WHERE id = %s ORDER BY row_id, column_id'
            cursor.execute(select, (row_id,))

            rows = cursor.fetchall()

            line = []
            for row in rows:
                line.append(util.format_number(row[2]))

        conn.close()
        return line


class ResultRepo:
    """
    Репозитория для работы с данными результов вычислений.
    """

    @staticmethod
    def get_new_index():
        """
        Получает новый идентификатор результов вычислений.
        :return: новый идентификатор.
        """

        conn = get_connection()

        with conn.cursor() as cursor:
            conn.autocommit = True

            select = "select nextval('result_id_seq')"

            cursor.execute(select)

            result_id = cursor.fetchone()[0]

        conn.close()
        return result_id

    @staticmethod
    @deprecation.deprecated(deprecated_in='1.1.0', removed_in='1.3.0')
    def set_result(result):
        """
        Добавляет результаты вычислений.
        :param result: результаты вычислений.
        :return: идентификатор результатов вычислений.
        """

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            insert = 'INSERT INTO result (alfa, epselon, e, bias_estimates, n1, n2) VALUES (%s, %s, %s, %s, %s, %s) ' \
                     'RETURNING id'

            values = (str(result[0]),
                      str(result[1]),
                      str(result[2]),
                      str(result[3]),
                      str(result[4]),
                      str(result[5]),)

            cursor.execute(insert, values)

        conn.close()
        return cursor.fetchone()[0]

    @staticmethod
    def set_results(results):
        """
        Добавляет результаты вычислений.
        :param results: результаты вычислений.
        :return: идентификатор результатов вычислений.
        """

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            insert = 'INSERT INTO result (alfa, epselon, e, bias_estimates, n1, n2) VALUES %s RETURNING id'

            values = []
            for item in results:
                values.append((str(item[0]),
                               str(item[1]),
                               str(item[2]) if str(item[2]) not in 'Infinity' else None,
                               str(item[3]) if str(item[3]) not in 'Infinity' else None,
                               str(item[4]),
                               str(item[5]),))

            id_res = execute_values(cur=cursor, sql=insert, argslist=values, fetch=True, page_size=200)

        conn.close()
        return id_res

    @staticmethod
    def create_task(type_task=None):
        """
        Создаёт новый идентификатор для задачи.
        :param type_task: тип задачи.
        :return: новый идентификатор.
        """

        conn = get_connection()

        with conn.cursor() as cursor:
            conn.autocommit = True

            select = "select nextval('tasks_id_seq')"

            cursor.execute(select)
            task_id = cursor.fetchone()[0]

            insert = 'INSERT INTO tasks (id, type) VALUES (%s, %s)'
            cursor.execute(insert, (task_id, type_task))

        conn.close()
        return task_id

    @staticmethod
    def add_tasks_to_result(id_task, id_res):
        """
        Добавляет связь задачи к результатам вычислений.
        :param id_task: идентификатор задачи.
        :param id_res: идентификатор результатов вычислений.
        """

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            insert = 'INSERT INTO tasks_to_resalt (id_tasks, id_result) VALUES %s'

            values = []
            for item in id_res:
                values.append((id_task, item,))

            execute_values(cur=cursor, sql=insert, argslist=values, page_size=200)
        conn.close()

    def add_results(self, data, id_task=None, percent=0):
        """
        Добавляет к задаче новые результаты вычислений.
        :param data: результаты вычислений.
        :param id_task: идентификатор задачи.
        :param percent: величина, на которую продвинулось решение заачи.
        """

        if id_task is None:
            id_task = self.create_task()

        id_res = self.set_results(data)
        self.add_tasks_to_result(id_task, id_res)
        WorkerRepo.update_count(id_task, percent)

    @staticmethod
    @deprecation.deprecated(deprecated_in='1.1.0', removed_in='1.3.0')
    def get_task(task_id):
        """
        Получает результаты вычислений в задаче.
        :param task_id: идентификатор задачи.
        :return: массив с результатами вычислений.
        """

        conn = get_connection()

        with conn.cursor() as cursor:
            conn.autocommit = True

            select = '''SELECT r.alfa, r.epselon, r.e, r.bias_estimates, r.n1, r.n2
                        FROM tasks t
                          JOIN tasks_to_resalt ttr on t.id = ttr.id_tasks
                          JOIN result r on ttr.id_result = r.id
                        WHERE t.id = %s'''
            cursor.execute(select, (task_id,))

            rows = cursor.fetchall()

            line = []
            for row in rows:
                line.append(row)

        conn.close()
        return line

    @staticmethod
    def get_task_by_best_bias_estimates(task_id, filter_id, sorting_id):
        """
        Получает результаты вычислений в задаче.
        :param task_id: идентификатор задачи.
        :param filter_id: идентификатор фильтра.
        :param sorting_id: идентификатор сортировки.
        :return: массив с результатами вычислений.
        """

        filter_p = ' LIMIT 20'
        sorting_p = ' ORDER BY r.bias_estimates::numeric '

        if filter_id == 0:
            filter_p = ' LIMIT 20'
        elif filter_id == 1:
            filter_p = ' LIMIT 40'
        elif filter_id == 2:
            filter_p = ' LIMIT 100'
        elif filter_id == 3:
            filter_p = ' LIMIT 1000'

        if sorting_id == 0:
            sorting_p = ' ORDER BY r.bias_estimates::numeric DESC '
        elif sorting_id == 1:
            sorting_p = ' ORDER BY r.bias_estimates::numeric '
        elif sorting_id == 2:
            sorting_p = ' ORDER BY r.e::numeric DESC '
        elif sorting_id == 3:
            sorting_p = ' ORDER BY r.e::numeric '

        conn = get_connection()

        with conn.cursor() as cursor:
            conn.autocommit = True

            select = '''SELECT r.alfa, r.epselon, r.e, r.bias_estimates, r.n1, r.n2
                        FROM tasks t
                          JOIN tasks_to_resalt ttr on t.id = ttr.id_tasks
                          JOIN result r on ttr.id_result = r.id
                        WHERE t.id = %s''' + sorting_p + filter_p
            cursor.execute(select, (task_id,))

            rows = cursor.fetchall()

            line = []
            for row in rows:
                line.append(row)

        conn.close()
        return line


class WorkerRepo:
    """
    Репозитория для работы с данными работника.
    Работник имеет следующие статусы:
        # build - формирование задачи.
        # in_progress - задача в процессе выполнения.
        # done - задача выполнена.
        # wait - задача стоит в очереди на выполнение.
    """

    @staticmethod
    def get_new_index():
        """
        Получает новый идентификатор.
        :return: новый идентификатор.
        """

        conn = get_connection()

        with conn.cursor() as cursor:
            conn.autocommit = True

            select = "select nextval('worker_id_seq')"

            cursor.execute(select)

            worker_id = cursor.fetchone()[0]

        conn.close()
        return worker_id

    def create_new_worker(self, user_id):
        """
        Создаёт нового работника.
        :param user_id: идентификатор пользователя.
        :return: идентификатор работника.
        """

        worker_id = self.get_new_index()

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            insert = 'INSERT INTO worker (id, status, user_id, count) VALUES (%s, %s, %s, %s)'

            values = (worker_id, 'build', user_id, 0)

            cursor.execute(insert, values)

        conn.close()
        return worker_id

    @staticmethod
    def build_worker(worker_id, name, task_id):
        """
        Строит работника, задаёт имя задачи. Привязывает задачу к работнику.
        :param worker_id: идентификатор работника.
        :param name: имя задачи.
        :param task_id: идентификатор задачи.
        """

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            update = 'UPDATE worker SET name = %s, task_id = %s WHERE id = %s'

            values = (name, task_id, worker_id,)

            cursor.execute(update, values)
        conn.close()

    @staticmethod
    def run_worker(worker_id):
        """
        Запуск работника. В случае успешного запуска метод возвращает True.
        :param worker_id: идентификатор работника.
        :return: True, если удалось запустить работника.
                 False, если стоит блокировка на запуск работника.
        """

        if BlockerRepo.is_allowed_run_new_worker():
            conn = get_connection()
            with conn.cursor() as cursor:
                conn.autocommit = True

                date_time = datetime.datetime.now()
                update = "UPDATE worker SET status = 'in_progress', count = 0, time_start = %s WHERE id = %s"

                values = (date_time, worker_id,)
                cursor.execute(update, values)
                BlockerRepo.add_run_worker()

            conn.close()
            return True
        else:
            return False

    @staticmethod
    def update_count(task_id, count):
        """
        Обновляет прогресс выполнения работника.
        :param task_id: идентификатор задачи.
        :param count: величина, на которую прогресс увеличился.
        """

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            select = 'SELECT count FROM worker WHERE task_id = %s'
            cursor.execute(select, (task_id,))
            count_db = cursor.fetchone()[0]

            update = 'UPDATE worker SET count = %s WHERE task_id = %s'

            values = (float(count_db) + count, task_id)

            cursor.execute(update, values)
        conn.close()

    @staticmethod
    def complete(task_id):
        """
        Помечает, что работник завершил работу. Снимает блокировку на 1 работника.
        """

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            select = 'SELECT id FROM worker WHERE task_id = %s'
            cursor.execute(select, (task_id,))
            worker_id = cursor.fetchone()[0]

            date_time = datetime.datetime.now()
            update = 'UPDATE worker SET count = %s, status = %s, time_end = %s WHERE id = %s'

            values = (100, 'done', date_time, worker_id,)

            cursor.execute(update, values)

        conn.close()
        BlockerRepo.del_run_worker()

    @staticmethod
    def is_complete(task_id):
        """
        Проверяет, выполнилась ли задача.
        :return: True -задача выполнена
                 False - задача в процессе выполнения.
        """

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            select = 'SELECT count FROM worker WHERE task_id = %s'

            cursor.execute(select, (task_id,))
            count = cursor.fetchone()[0]

        conn.close()
        return int(count) >= 100

    @staticmethod
    def get_task_in_last_worker_by_user(user_id):
        """
        Получает идентификатор задачи для последнего работника пользователя.
        :param user_id: идентификатор пользователя.
        :return: идентификатор задачи.
        """

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            select = "SELECT task_id FROM worker WHERE user_id = %s ORDER BY id DESC LIMIT 1"
            cursor.execute(select, (user_id,))
            answer = cursor.fetchone()
            task_id = None if answer is None else answer[0]

        conn.close()
        return task_id

    @staticmethod
    def is_done(task_id):
        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            select = "SELECT status, count FROM worker WHERE task_id = %s"
            cursor.execute(select, (task_id,))
            status, count = cursor.fetchone()

        conn.close()
        return [status, float(count)]

    @staticmethod
    def is_run(worker_id):
        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            select = "SELECT status FROM worker WHERE id = %s"
            cursor.execute(select, (worker_id,))

            worker_status = cursor.fetchone()[0] in ('in_progress', 'done')

        conn.close()
        return worker_status


class BlockerRepo:
    """
    Репозиторий для работы с блокировщиком фоновых задач.
    """

    @staticmethod
    def is_allowed_run_new_worker():
        """
        Проверяет возможность запустить работника.
        :return: True, если можно запустить,
                 False, если нельзя.
        """

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            select = 'SELECT 1 FROM blocker WHERE id = 0 AND limit_worker > run_worker'

            cursor.execute(select)
            answer = cursor.fetchone()
            conn.close()

            conn.close()
            if answer:
                return True
            else:
                return False

    @staticmethod
    def add_run_worker():
        """
        Добавляет запущенного работника.
        """

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            select = 'SELECT run_worker FROM blocker WHERE id = 0'
            cursor.execute(select)
            run_worker = cursor.fetchone()[0]

            update = 'UPDATE  blocker SET run_worker = %s WHERE id = 0'

            value = (run_worker + 1,)
            cursor.execute(update, value)
        conn.close()

    @staticmethod
    def del_run_worker():
        """
        Удаляет запущенного рабоника.
        """

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            select = 'SELECT run_worker FROM blocker WHERE id = 0'
            cursor.execute(select)
            run_worker = cursor.fetchone()[0]

            update = 'UPDATE  blocker SET run_worker = %s WHERE id = 0'

            value = (run_worker - 1,)
            cursor.execute(update, value)
        conn.close()
