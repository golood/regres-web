from server.models import MetaData


def calculation_predict(results, meta_data: MetaData):
    task_id = 0
    for task in results:
        index_y = 0
        for line in meta_data.x_predict():
            y = []
            index_x = 0
            for x in line:
                y.append(x*task[1][0][index_x])
                index_x += 1

            y = sum(y)
            results[task_id][1][3].append(y)
            results[task_id][1][1].append(meta_data.y_predict()[index_y] - y)

        # точность прогноза
        s = 0
        for index in range(len(meta_data.get_load_data_rows_len())):
            if index < meta_data.range_value:
                continue
            s += abs((meta_data.y_all()[index] - results[task_id][1][3][index]) / meta_data.y_all()[index])

        s *= (1 / (len(meta_data.y_all()) - len(meta_data.y_predict())))
        s *= 100
        results[task_id][1][2].append(s)

        task_id += 1
