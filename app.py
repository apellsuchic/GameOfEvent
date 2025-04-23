"""Work_WEB-APP"""
import csv
import sqlite3
from flask import Flask, render_template, request, jsonify, url_for, redirect, session
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


app = Flask(__name__)
app.secret_key = '' # Нужен свой ключ
DB_PATH = '/home/data.sqlite' # Путь к базе данных.

@app.route('/add_dell', methods=['POST'])
def work_witd_data():
    """Добавление/удаление data"""
    do = request.form.get('table')
    name = request.form['zone']
    categor = request.form.get('category')
    if do == 'add_zone':
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""INSERT INTO Zone (zone_name, category)
                               VALUES (?, ?)""", (name, categor))
                conn.commit()
        except sqlite3.OperationalError:
            error = "Укажите категорию новой зоны!"
            return render_template('learn.html', error=error)
    elif do == 'del_zone':
        if not find_zone(name):
            error = "Не правильное имя игровой зоны!"
            return render_template('learn.html', error=error)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Zone WHERE zone_name=?", (name,))
            conn.commit()
    elif do == 'add_worker':
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Workers (name) VALUES  (?)", (name,))
            conn.commit()
    else:
        if not find_worker(name):
            error = "Не правильное имя работника!"
            return render_template('learn.html', error=error)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Workers WHERE name=?", (name,))
            conn.commit()
    return render_template('learn.html')


@app.route('/autocomplete')
def autocomplete():
    """Автозаполнение поля ввода"""
    zone = request.args.get('zone', '')
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Объединяем выборку из двух таблиц
        cursor.execute(f"""SELECT zone_name FROM Zone WHERE zone_name LIKE '%{zone}%'
                       UNION SELECT name FROM Workers WHERE name LIKE '%{zone}%'""")
        suggestions = [row[0] for row in cursor.fetchall()]
    return jsonify(suggestions)

@app.route('/learn')
def learn_def():
    """Страница статистики"""
    if is_logged_in():
        return render_template('learn.html')
    else:
        return redirect(url_for('login'))

def is_logged_in():
    """Проверка авторизации"""
    if 'logged_in' in session and session['logged_in']:
        return True
    return False


@app.route('/')
def log():
    """Страница входа"""
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Форма авторизации"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = {'sasha': '222'} # Логин и пароль для входа
        # Лучше эти данные хранить в отдельном файле, чтобы использовать перменные,
        # а не сами значения.
        for i, k in users.items():
            if i == username and k == password:
                session['logged_in'] = True
                return render_template('index.html')
            else:
                return render_template('login.html')
    else:
        return render_template('login.html')


@app.route('/stat')
def exit_def():
    """Страница статистики"""
    if is_logged_in():
        return render_template('stat.html')
    else:
        return redirect(url_for('login'))


def write_file(dic):
    """Запись в csv"""
    with open('data.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Category', 'Count'])
        for key, value in dic.items():
            writer.writerow([key, value])


def add_to_inventory(new_inventory):
    """Добавление нового инвентория в csv"""
    invent = {}
    ii = [item[0] for item in new_inventory]
    for i in ii:
        invent.setdefault(i, 0)
        invent[i] += 1
        write_file(invent)


def find_workers(date1, date2):
    """This function"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Выборка по именам и количеством проектов в месяце
        cursor.execute(f"""SELECT Categories.name FROM Project_Zone
                    JOIN Zone ON Zone.id = Project_Zone.zone_id
                    JOIN Categories ON Categories.id = Zone.category
                    JOIN Project ON Project.id = Project_Zone.project_id
                    WHERE Project.data BETWEEN '{date1}' AND '{date2}';""")
        add_to_inventory(cursor.fetchall())
        sns.set_theme() # Создание темы графика
        datak = pd.read_csv("data.csv")
        datak.sort_values(by='Count', inplace=True, ascending=False)
        # Создание датафрейма для того, чтобы seaborn мог работать с данными
        plt.figure(figsize=(7, 5))
        # Установка коректного размера поля.
        sns.barplot(x="Category", y="Count", data=datak)
        plt.xticks(rotation=45, ha='right')
        plt.locator_params(axis='y', integer=True)
        plt.tight_layout()
        plt.savefig("static/category_zone.jpg")
        # Создание графика с барами


def find_project(date1, date2):
    """This function"""
    with sqlite3.connect(DB_PATH) as conn:
        # Выборка по именам и количеством проектов в месяце
        data = f"""SELECT Project.id, Project.data, Count(Project_Zone.zone_id) AS count_zone
                            FROM Project
                            JOIN Project_Zone ON Project_Zone.project_id = Project.id
                            JOIN Zone ON Zone.id = Project_Zone.zone_id
                            WHERE Project.data BETWEEN '{date1}' AND '{date2}'
                            GROUP BY Project.id;"""
        sns.set_theme() # Создание темы графика
        datak = pd.read_sql(data, conn)
        # Создание датафрейма для того, чтобы seaborn мог работать с данными
        # Установка коректного размера поля.
        plt.figure(figsize=(12, 4))
        sns.barplot(x="data", y="count_zone", hue='id', data=datak, dodge=True, width=1.1)
        plt.xticks(rotation=45, ha='right')
        plt.locator_params(axis='y', integer=True)
        plt.tight_layout()
        plt.savefig("static/count_zone.jpg")
        # Создание графика с барами


def find_wor(date1, date2):
    """This function"""
    with sqlite3.connect(DB_PATH) as conn:
        data = f"""SELECT Workers.name, Count(Project_Workers.worker_id) AS count_work
                        FROM Workers
                        JOIN Project_Workers ON Project_Workers.worker_id = Workers.id
                        JOIN Project ON Project_Workers.project_id = Project.id
						WHERE Project.data BETWEEN '{date1}' AND '{date2}'
                        GROUP BY Workers.name;"""
        # Выборка по именам и количеством проектов в месяце
        sns.set_theme() # Создание темы графика
        datak = pd.read_sql(data, conn)
        datak.sort_values(by='count_work', inplace=True, ascending=False)
        # Создание датафрейма для того, чтобы seaborn мог работать с данными
        plt.figure(figsize=(12, 7))
        # Установка коректного размера поля.
        sns.barplot(x="name", y="count_work", data=datak)
        plt.tight_layout()
        plt.savefig("static/count_work.jpg")
        # Создание графика с барами


def find_pr_zon(date1, date2):
    """This function"""
    with sqlite3.connect(DB_PATH) as conn:
        # Выборка по именам и количеством проектов в месяце
        data = f"""SELECT Zone.zone_name, Count(Project_Zone.zone_id) AS count_zone
                    FROM Project_Zone
                    JOIN Project ON Project.id = Project_Zone.project_id
                    JOIN Zone ON Zone.id = Project_Zone.zone_id
                    WHERE Project.data BETWEEN '{date1}' AND '{date2}'
                    GROUP BY Zone.zone_name"""
        sns.set_theme() # Создание темы графика
        datak = pd.read_sql(data, conn)
        datak.sort_values(by='count_zone', inplace=True, ascending=False)
        # Создание датафрейма для того, чтобы seaborn мог работать с данными
        plt.figure(figsize=(15, 5))
        # Установка коректного размера поля.
        sns.barplot(x="zone_name", y="count_zone", data=datak)
        plt.xticks(rotation=45, ha='right')
        plt.locator_params(axis='y', integer=True)
        plt.tight_layout()
        plt.savefig("static/project_zone.jpg")
        # Создание графика с барами


@app.route("/data_stat")
def data_stat(date1, date2):
    """Возвращает данные о количестве проектов и зон в указанный период"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT count(Zone.zone_name) FROM Zone;')
        zones = cursor.fetchone()[0]
        cursor.execute('SELECT count(Project.id) FROM Project;')
        all_project = cursor.fetchone()[0]
        cursor.execute(f'''SELECT count(Project.id) FROM Project
                        WHERE Project.data BETWEEN '{date1}' AND '{date2}';''')
        project_in_date = cursor.fetchone()[0]
        cursor.execute(f'''SELECT count(Zone.zone_name) FROM Project_Zone
                        JOIN Project ON Project.id = Project_Zone.project_id
                        JOIN Zone ON Zone.id = Project_Zone.zone_id
                        WHERE Project.data BETWEEN '{date1}' AND '{date2}';''')
        zone_in_date = cursor.fetchall()[0][0]
    return  project_in_date, zone_in_date, all_project, zones


@app.route('/exit')
def logout():
    """Выход из аккаунта"""
    session.pop('logged_in', None)
    return redirect(url_for('login'))



@app.route('/graf', methods=['POST'])
def graf_data():
    """Отправляет данные в графические изображения"""
    date1 = request.form['date1']
    date2 = request.form['date2']
    find_workers(date1, date2)
    find_project(date1, date2)
    find_wor(date1, date2)
    find_pr_zon(date1, date2)
    data = data_stat(date1, date2)
    plt.close('all')
    return render_template('stat.html', data=data)


@app.route('/index')
def validate_sesseon():
    """Проверка входа"""
    if is_logged_in():
        return render_template('index.html')
    else:
        return redirect(url_for('login'))


@app.route('/about')
def about():
    """Инфа обо мне"""
    return render_template('about.html')


@app.route('/remov')
def valid_log():
    """Проверка входа"""
    if is_logged_in():
        return render_template('remov.html')
    else:
        return redirect(url_for('login'))


@app.route('/remove_project', methods=['POST'])
def remove_project():
    """Удаление проекта"""
    id_project = request.form['id']
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Project_Zone WHERE project_id=?", (id_project,))
        cursor.execute("DELETE FROM Project_Workers WHERE project_id=?", (id_project,))
        cursor.execute("DELETE FROM Project WHERE id=?", (id_project,))
        conn.commit()
    return render_template('remov.html')


@app.route('/get_zones')
def list_zone_names():
    """Получение списка зон из базы данных"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT zone_name FROM Zone")
        rows = cursor.fetchall()
        zone_names=[row[0] for row in rows]
    return jsonify(zone_names)


@app.route('/get_workers')
def list_worker_names():
    """Получение списка работников из базы данных"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM Workers")
        rows = cursor.fetchall()
        worker_names=[row[0] for row in rows]
    return jsonify(worker_names)


@app.route('/get_last_project')
def get_last_project():
    """Get the last project"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        b = """SELECT
                P.id,
                P.data,
                GROUP_CONCAT(DISTINCT Z.zone_name||' ') AS zones, 
                GROUP_CONCAT(DISTINCT W.name||' ') AS workers
                FROM Project AS P
                LEFT JOIN Project_Zone AS PZ ON P.id = PZ.project_id
                LEFT JOIN Zone AS Z ON PZ.zone_id = Z.id
                LEFT JOIN Project_Workers AS PW ON P.id = PW.project_id
                LEFT JOIN Workers AS W ON PW.worker_id = W.id
                GROUP BY P.id, P.data;"""
        cursor.execute(b)
        rows = cursor.fetchall()
        project_data = [{
        'id': row[0],
        'date': row[1],
        'zone': row[2],
        'worker': row[3],
        } for row in rows]
        project_data.reverse()
    return jsonify(project_data)


@app.route('/get_last_insurt_projects')
def get_last_insurt_projects():
    """Получения последнего добавленного проекта"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        a = """SELECT
                P.id,
                P.data,
                GROUP_CONCAT(DISTINCT Z.zone_name||' ') AS zones, 
                GROUP_CONCAT(DISTINCT W.name||' ') AS workers
                FROM Project AS P
                LEFT JOIN Project_Zone AS PZ ON P.id = PZ.project_id
                LEFT JOIN Zone AS Z ON PZ.zone_id = Z.id
                LEFT JOIN Project_Workers AS PW ON P.id = PW.project_id
                LEFT JOIN Workers AS W ON PW.worker_id = W.id
                WHERE P.id = (SELECT MAX(id) FROM Project) 
                GROUP BY P.id, P.data;"""
        cursor.execute(a)
        rows = cursor.fetchall()
        worker_names = [row for row in rows[0]]
    return jsonify(worker_names)


def find_zone(zones: list[str]):
    """Helper function"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        for zone in zones:
            if zone == '':
                return 0
            try:
                cursor.execute("SELECT id FROM Zone WHERE zone_name=?", (zone.lower(),))
                i = cursor.fetchall()[0][0]
                del i
                return 1
            except IndexError:
                return 0


def find_worker(workers: list[str]):
    """Helper function"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        for worker in workers:
            try:
                cursor.execute("SELECT id FROM Workers WHERE name=?", (worker.lower(),))
                i = cursor.fetchall()[0][0]
                del i
                return 1
            except IndexError:
                return 0


def insurt(date: str, zone: list[str], worker: list[str]):
    """Добавление проекта"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Project (data) VALUES (?)", (date,))
        conn.commit()
        cursor.execute("SELECT max(Project.id) FROM Project WHERE Project.data = ?", (date,))
        id_data = cursor.fetchone()[0]
        lenth = len(zone)
        lenth2 = len(worker)
        for i in range(lenth):
            cursor.execute("SELECT id FROM Zone WHERE zone_name = ?", (zone[i].lower(),))
            id_zone = cursor.fetchone()[0]
            cursor.execute("INSERT INTO Project_Zone VALUES (?, ?)", (id_data, id_zone))
            conn.commit()
        if worker:
            for iteam in range(lenth2):
                cursor.execute("SELECT id FROM Workers WHERE name =?", (worker[iteam].lower(),))
                id_worker = cursor.fetchone()[0]
                cursor.execute("INSERT INTO Project_Workers VALUES (?,?)", (id_data, id_worker))
                conn.commit()
                cursor.execute("""SELECT Workers.name FROM Workers
                            JOIN Project_Workers ON Project_Workers.worker_id = Workers.id
                            JOIN Project ON Project_Workers.project_id = Project.id
                            WHERE Project.data = ? AND Project.id = ?;""", (date, id_data))
        cursor.execute("SELECT id, data FROM Project WHERE data = ? AND id = ?", (date, id_data))
        cursor.execute("""SELECT Zone.zone_name FROM Zone
                        JOIN Project_Zone ON Project_Zone.zone_id = Zone.id
                        JOIN Project ON Project_Zone.project_id = Project.id
                        WHERE Project.data = ? AND Project.id = ?;""", (date, id_data))


@app.route('/add_data', methods=['POST'])
def add_data():
    """Добавление проекта"""
    date = request.form['date']
    zone = request.form.getlist('zone[]')
    worker = request.form.getlist('worker[]')

    if not find_zone(zone):
        error = "Не правильное имя игровой зоны!"
        return render_template('index.html', error=error)
    if worker:  # Если список работников не пустой
        if not find_worker(worker):
            error = "Не правильное имя работника!"
            return render_template('index.html', error=error)
    insurt(date, zone, worker)
    mes="Проект успешно добавлен"
    return render_template('index.html', mes=mes)


if __name__ == '__main__':
    app.run()
