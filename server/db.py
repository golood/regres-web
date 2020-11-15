#!/usr/bin/python3
import datetime

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
                            port=config.POSTGRES_PORT)
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

        return result_id

    @staticmethod
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

    def addResults(self, data, id_task=None, percent=0):
        '''
        Добавляет к задаче новые результаты вычислений.
        :param data: результаты вычислений.
        :param id_task: идентификатор задачи.
        :param percent: величина, на которую продвинулось решение заачи.
        '''

        repoWorker = WorkerRepo()

        if id_task == None:
            id_task = self.create_task()


        id_res = self.set_results(data)
        self.add_tasks_to_result(id_task, id_res)
        repoWorker.updateCount(id_task, percent)


    def getTask(self, id):
        '''
        Получает результаты вычислений в задаче.
        :param id: идентификатор задачи.
        :return: массив с результатами вычислений.
        '''

        conn = get_connection()

        with conn.cursor() as cursor:
            conn.autocommit = True

            select = '''SELECT r.alfa, r.epselon, r.e, r.bias_estimates, r.n1, r.n2
                        FROM tasks t
                          JOIN tasks_to_resalt ttr on t.id = ttr.id_tasks
                          JOIN result r on ttr.id_result = r.id
                        WHERE t.id = %s'''
            cursor.execute(select, (id,))

            rows = cursor.fetchall()

            line = []
            for row in rows:
                line.append(row)

        conn.close()
        return line

    def getTaskByBestBiasEstimates(self, id, filterId, sotringId):
        '''
        Получает результаты вычислений в задаче.
        :param id: идентификатор задачи.
        :param filterId: идентификатор фильтра.
        :param sotringId: идентификатор сортировки.
        :return: массив с результатами вычислений.
        '''

        filter_p = ' LIMIT 20'
        sorting_p = ' ORDER BY r.bias_estimates::numeric '

        if filterId == 0:
            filter_p = ' LIMIT 20'
        elif filterId == 1:
            filter_p = ' LIMIT 40'
        elif filterId == 2:
            filter_p = ' LIMIT 100'
        elif filterId == 3:
            filter_p = ' LIMIT 1000'

        if sotringId == 0:
            sorting_p = ' ORDER BY r.bias_estimates::numeric DESC '
        elif sotringId == 1:
            sorting_p = ' ORDER BY r.bias_estimates::numeric '
        elif sotringId == 2:
            sorting_p = ' ORDER BY r.e::numeric DESC '
        elif sotringId == 3:
            sorting_p = ' ORDER BY r.e::numeric '

        conn = get_connection()

        with conn.cursor() as cursor:
            conn.autocommit = True

            select = '''SELECT r.alfa, r.epselon, r.e, r.bias_estimates, r.n1, r.n2
                        FROM tasks t
                          JOIN tasks_to_resalt ttr on t.id = ttr.id_tasks
                          JOIN result r on ttr.id_result = r.id
                        WHERE t.id = %s''' + sorting_p + filter_p
            cursor.execute(select, (id,))

            rows = cursor.fetchall()

            line = []
            for row in rows:
                line.append(row)

        conn.close()
        return line


class WorkerRepo:
    '''
    Репозитория для работы с данными работника.
    Работник имеет следующие статусы:
        # build - формирование задачи.
        # in_progress - задача в процессе выполнения.
        # done - задача выполнена.
        # wait - задача стоит в очереди на выполнение.
    '''

    def getNewIndex(self):
        '''
        Получает новый идентификатор.
        :return: новый идентификатор.
        '''

        conn = get_connection()

        with conn.cursor() as cursor:
            conn.autocommit = True

            select = "select nextval('worker_id_seq')"

            cursor.execute(select)

            id = cursor.fetchone()[0]

        conn.close()
        return id

    def createNewWorker(self, userId):
        '''
        Создаёт нового работника.
        :param userId: идентификатор пользователя.
        :param name: имя нового работника.
        :return: идентификатор работника.
        '''

        id = self.getNewIndex()

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            insert = 'INSERT INTO worker (id, status, user_id, count) VALUES (%s, %s, %s, %s)'

            values = (id, 'build', userId, 0)

            cursor.execute(insert, values)

        conn.close()
        return id

    def buildWorker(self, id, name, taskId):
        '''
        Строит работника, задаёт имя задачи. Привязывает задачу к работнику.
        :param id: идентификатор работника.
        :param name: имя задачи.
        :param taskId: идентификатор задачи.
        '''

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            update = 'UPDATE worker SET name = %s, task_id = %s WHERE id = %s'

            values = (name, taskId, id,)

            cursor.execute(update, values)
        conn.close()

    def runWorker(self, id):
        '''
        Запуск работника. В случае успешного запуска метод возвращает True.
        :param id: идентификатор работника.
        :return: True, если удалось запустить работника.
                 False, если стоит блокировка на запуск работника.
        '''

        repoBloker = BlockerRepo()

        if repoBloker.isAllowedRunNewWorker():
            conn = get_connection()
            with conn.cursor() as cursor:
                conn.autocommit = True

                dateTime = datetime.datetime.now()
                update = "UPDATE worker SET status = 'in_progress', count = 0, time_start = %s WHERE id = %s"

                values = (dateTime, id,)
                cursor.execute(update, values)
                repoBloker.addRunWorker()

            conn.close()
            return True
        else:
            return False

    def updateCount(self, taskId, count):
        '''
        Обновляет прогресс выполнения работника.
        :param taskId: идентификатор задачи.
        :param count: величина, на которую прогресс увеличился.
        '''

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            select = 'SELECT count FROM worker WHERE task_id = %s'
            cursor.execute(select, (taskId,))
            count_db = cursor.fetchone()[0]

            update = 'UPDATE worker SET count = %s WHERE task_id = %s'

            values = (float(count_db) + count, taskId)

            cursor.execute(update, values)
        conn.close()

    def complete(self, taskId):
        '''
        Помечает, что работник завершил работу. Снимает блокировку на
        1 работника.
        '''

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            select = 'SELECT id FROM worker WHERE task_id = %s'
            cursor.execute(select, (taskId,))
            id = cursor.fetchone()[0]

            dateTime = datetime.datetime.now()
            update = 'UPDATE worker SET count = %s, status = %s, time_end = %s WHERE id = %s'

            values = (100, 'done', dateTime, id,)

            cursor.execute(update, values)

        repo = BlockerRepo()
        repo.delRunWorker()
        conn.close()

    def isComplete(self, taskId):
        '''
        Проверяет, выполнилась ли задача.
        :return: True -задача выполнена
                 False - задача в процессе выполнения.
        '''

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            select = 'SELECT count FROM worker WHERE task_id = %s'

            cursor.execute(select, (taskId,))
            count = cursor.fetchone()[0]

        conn.close()
        return int(count) >= 100

    def getTaskInLastWorkerByUser(self, userId):
        '''
        Получает идентификатор задачи для последнего работника пользователя.
        :param userId: идентификатор пользователя.
        :return: идентификатор задачи.
        '''

        id = None
        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            select = "SELECT task_id FROM worker WHERE user_id = %s ORDER BY id DESC LIMIT 1"
            cursor.execute(select, (userId,))
            answer = cursor.fetchone()
            id = None if answer is None else answer[0]

        conn.close()
        return id

    def isDone(self, taskId):
        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            select = "SELECT status, count FROM worker WHERE task_id = %s"
            cursor.execute(select, (taskId,))
            status, count = cursor.fetchone()

            conn.close()
            return [status, float(count)]

    def isRun(self, workerId):
        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            select = "SELECT status FROM worker WHERE id = %s"
            cursor.execute(select, (workerId,))

            var = cursor.fetchone()[0] in ('in_progress', 'done')
            conn.close()
            return var


class BlockerRepo:
    '''
    Репозиторий для работы с блокировщиком фоновых задач.
    '''

    def isAllowedRunNewWorker(self):
        '''
        Проверяет возможность запустить работника.
        :return: True, если можно запустить,
                 False, если нельзя.
        '''

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            select = 'SELECT 1 FROM blocker WHERE id = 0 AND limit_worker > run_worker'

            cursor.execute(select)
            answer = cursor.fetchone()
            conn.close()

            if answer:
                return True
            else:
                return False

    def addRunWorker(self):
        '''
        Добавляет запущенного работника.
        '''

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

    def delRunWorker(self):
        '''
        Удаляет запущенного рабоника.
        '''

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

class ServiceRepo:
    '''
    Репозиторий для работы с сервисами решения регерессионных уравнений.
    '''

    def getNewIndexPage(self):
        '''
        Получает новый идентификатор пачки задач.
        :return: новый идентификатор.
        '''

        conn = get_connection()

        with conn.cursor() as cursor:
            conn.autocommit = True

            select = "select nextval('page_id_seq')"

            cursor.execute(select)

            id = cursor.fetchone()[0]

        conn.close()
        return id

    def getServiceId(self):
        '''
        Получает идентификатор запущенного сервиса с самой короткой очередью запланированных задач.
        :return: идентификатор сервиса.
        '''

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            select = '''SELECT s.id
                        FROM service_list s
                          LEFT join queue_task q ON s.id = q.service_id AND q.complete IS FALSE
                        WHERE s.launch IS TRUE
                        GROUP BY s.id
                        ORDER BY count(q.id)
                        LIMIT 1'''

            cursor.execute(select)
            id = cursor.fetchone()[0]
        conn.close()

        return id

    def getRuningServiceIds(self):
        '''
        Получает идентификаторы всех запущенных сервисов.
        :return: лист с идентификаторами сервисов.
        '''

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            select = "SELECT id FROM service_list WHERE launch IS TRUE AND (now() AT TIME ZONE 'Asia/Irkutsk' - last_active)::time < '00:00:12'::time"

            cursor.execute(select)
            rows = cursor.fetchall()

            line = []
            for row in rows:
                line.append(row)

        conn.close()
        return line


    def addQueueTaskByBestService(self, tasks, task_id, parcent):
        '''
        Добавляет в очередь массив задачь для одного сервиса.
        :param tasks: массив задач.
        '''

        service_id = self.getServiceId()

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True
            page = self.getNewIndexPage()
            insert = 'INSERT INTO queue_task (service_id, complete, task, task_id, parcent, page) VALUES %s'

            values = []
            for item in tasks:
                values.append((service_id, False, item, task_id, parcent, page))

            execute_values(cur=cursor, sql=insert, argslist=values, page_size=200)
        conn.close()

    def addQueueTask(self, tasks, task_id, parcent, serviceId):
        '''
        Добавляет в очередь массив задачь для одного сервиса.
        :param tasks: массив задач.
        '''

        conn = get_connection()
        with conn.cursor() as cursor:
            conn.autocommit = True
            page = self.getNewIndexPage()
            insert = 'INSERT INTO queue_task (service_id, complete, task, task_id, parcent, page) VALUES %s'

            values = []
            for item in tasks:
                values.append((serviceId, False, item, task_id, parcent, page))

            execute_values(cur=cursor, sql=insert, argslist=values, page_size=200)
        conn.close()