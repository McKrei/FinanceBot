import sqlite3
import datetime as dt
from openpyexcel import load_workbook
import data_save
import asyncio

db = sqlite3.connect('data/finance.db')
cursor = db.cursor()


def write_db(table, category, amount, message):
	cursor.execute(f'''
		SELECT MAX(id)
		FROM {table}
	''')
	income_id = cursor.fetchone()[0]
	if not income_id: income_id = 0
	income_id += 1
	date = str(dt.datetime.now())[:10]
	subcategory = message.split()[0].lower()
	cursor.execute(f'''
		INSERT INTO {table} VALUES
		({income_id}, '{subcategory}','{category}', {amount}, '{date}', '{message}')
	''')
	db.commit()
	return income_id


def del_op(table, operation_id):
	cursor.execute(f'''
		DELETE FROM {table}
		WHERE (id) = {operation_id}
	''')
	db.commit()
	return


def sum_month_income_and_expense(month=0):
	try:
		if month == 0:
			month = str(dt.datetime.now())[:7]
		if len(month) == 7: month += '-01'
		cursor.execute(f'''
			SELECT (Food + Transport + Home + Services + Rest + Other + Health + Clothes) as sum_limits
			FROM limits
			WHERE date = DATE('{month}');
			''')

		sum_limit = cursor.fetchone()[0]
		cursor.execute(f'''
			SELECT SUM(amount)
			FROM expense
			WHERE date >= DATE('{month}') and date < DATE('{month}', '+1 month');
			''')
		sum_expense = cursor.fetchone()[0]
		cursor.execute(f'''
			SELECT SUM(amount)
			FROM income
			WHERE date >= DATE('{month}') and date < DATE('{month}', '+1 month');
			''')
		sum_income = cursor.fetchone()[0]

		# Проверка на наличие данных 
		sum_expense = 0 if not sum_expense else sum_expense
		sum_income  = 0 if not sum_income else sum_income
		
		return sum_income, sum_limit - sum_expense, sum_expense
		
	except TypeError:
		print(f'sum_month_income_and_expense\n{dt.datetime.now()}, {month = }')


def operation_list(date=0, order_by='date', only_table=False, year=None):
	'''
	Получаем месяц в формате '2022-01' тогда вернем лист за месяц
	Если не передаем, вернем лист с операциями за сегодня
	Еще может принять запрос за определенный день '2022-01-16'
	Если указанна функция year '2022' выдаст данные за год
	only_table можно указать если нужны чистые данные из таблиц или таблицы
	'''
	if year:
		date = year + '-01-01'
		before_date = f'"{date}","+1 year"'

	elif date == 0:
		date = str(dt.datetime.now())[:10]
		before_date = f'"{date}","+1 month"'

	elif len(date) == 10:
		before_date = f'"{date}","+1 day"'

	elif len(date) == 7:
		date += '-01'
		before_date = f'"{date}","+1 month"'

	cursor.execute(f'''
		SELECT id, category, amount, date
		FROM expense
		WHERE date >= DATE('{date}') and date < DATE({before_date})
		ORDER BY {order_by};
		''')
	expense_list = cursor.fetchall()

	if only_table == 'expense':
		return expense_list

	cursor.execute(f'''
		SELECT id, category, amount, date
		FROM income
		WHERE date >= DATE('{date}') and date < DATE({before_date})
		ORDER BY {order_by};
		''')
	income_list = cursor.fetchall()

	if only_table == 'income':
		return income_list

	if only_table == 'all':
		return income_list, expense_list


	return data_save.operation_str(income_list, expense_list)


def r_limits(date, period='month'):
	'''
	Создаем словарь с лимитами на запрошенный месяц или год
	'''
	cursor.execute(f'''
		SELECT *
		FROM limits
		WHERE date >= DATE('{date}') AND date < DATE('{date}', '+1 {period}')
		''')
	l = cursor.fetchall()

	if not l: return 			# Проверка на наличе данных

	d = data_save.expense
	result_dict = {key: [sum([el[i+1] for el in l])] for i, key in enumerate(d)}
	
	return result_dict


def report_month(month=0, other=None):
	if month == 0:
		month = str(dt.datetime.now())[:7]
	if len(month) == 2:
		month = str(dt.datetime.now().year) + '-' + month
	month += '-01'
	cursor.execute(f'''
		SELECT category, SUM(amount)
		FROM expense
		WHERE date >= DATE('{month}') AND date < DATE('{month}', '+1 month')
		GROUP BY category;
		''')
	sum_amount = cursor.fetchall()
	dict = r_limits(month)
	
	# Возврат для проверки. 
	if other:
		for el in sum_amount:
			dict[el[0]][0] -= el[1]
		return dict


	if not dict:
		return None, None
		
	if sum_amount:
		for el in sum_amount:
			dict[el[0]].append(el[1])	

	sum_income, sum_limit, sum_expense = sum_month_income_and_expense(month)
	table_expense = data_save.table_month_expense(dict, sum_expense, sum_limit)
	
	if sum_income and sum_income > 0:
		cursor.execute(f'''
			SELECT category, SUM(amount)
			FROM income
			WHERE date >= DATE('{month}') AND date < DATE('{month}', '+1 month')
			GROUP BY category;
			''')
		sum_amount = cursor.fetchall()
		table_income = data_save.table_month_income(sum_amount, sum_income)	

	elif not sum_income:
		table_income = 'Нет доходов'

	return table_expense, table_income


def get_limits(date=0):
	if date == 0:
		date = str(dt.datetime.now())[:7]
	if len(date) == 7: date += '-01'
	cursor.execute(f'''
		SELECT *
		FROM monthly_limit
		WHERE date == '{date}'
		''')
	limits = cursor.fetchone()
	if not limits: 
		return 'Нет данных'

	return limits[1:]

def update_monthly_limit(list, date=0, table='monthly_limit'):
	if date == 0:
		date = str(dt.datetime.now())[:7] + '-01'
	
	cursor.execute(f'''
		UPDATE {table} 
		SET Food = {list[0]},
			Transport = {list[1]},
			Home = {list[2]},
			Services = {list[3]},
			Rest = {list[4]},
			Other = {list[5]},
			Health = {list[6]},
			Clothes = {list[7]}
		WHERE date = '{date}'	
	''')
	db.commit()
	return 


def change_limit_in_db(result):
	if result == 'save':
		data = get_limits()
		update_monthly_limit(data, '0000-00-00')
	else:
		data = get_limits('0000-00-00')
		update_monthly_limit(data)
	return


def get_sum_day_in_month(month):
	month += '-01'
	cursor.execute(f'''
		SELECT date, sum(amount)
		FROM expense
		WHERE date >= DATE('{month}') AND date < DATE('{month}', '+1 month')
		GROUP BY date
	''')
	result = cursor.fetchall()
	return result

def get_last_month(minus_day=1):
	# Возвращает прошлый месяц в формате '2022-01'
	first = dt.date.today().replace(day=1) - dt.timedelta(days=minus_day)
	last_month = first.strftime("%Y-%m")
	return last_month


def limit_per_mont(month, month_limit='0000-00-00'):
	# Считаем все категории с учетом лимитов
	dict_expense = report_month(month, True)
	limit = list(get_limits(month_limit))
	result = [dict_expense[key][0] + limit[i] for i, key in enumerate(dict_expense)]
	return result

def new_month(date):
	''' Записываем лимиты в таблички в начале месяца '''

	# Проверка на наличие данных в monthly_limit и запись
	cursor.execute(f"SELECT * FROM monthly_limit WHERE date = '{date}'")
	if not cursor.fetchone():
		limit = [date] + list(get_limits('0000-00-00'))
		cursor.execute('INSERT INTO monthly_limit VALUES (?,?,?,?,?,?,?,?,?)', limit)
		db.commit()

	# Проверка на наличие данных в limits и запись
	cursor.execute(f"SELECT * FROM limits WHERE date = '{date}'")
	if not cursor.fetchone():
		result = limit_per_mont(get_last_month())
		cursor.execute('INSERT INTO limits VALUES (?,?,?,?,?,?,?,?,?)', [date] + result)
		db.commit()
	
	# Записываем кол-во ДС на начало месяца
	write_money(date)




def update_table_limits_now_month():
	month = str(dt.datetime.now())[:7]
	last_month = get_last_month()
	limit = limit_per_mont(last_month, month)
	update_monthly_limit(limit, month + '-01', 'limits')



def check_sum_and_limit_update():
	''' Проверка на соответствие валидности данных в лимитах '''
	result = False
	now_month = str(dt.datetime.now())[:7] + '-01'
	last_month = get_last_month()
	now_expense_list = limit_per_mont(last_month)
	cursor.execute(f"SELECT * FROM limits WHERE date = '{now_month}'")
	limits = cursor.fetchone()

	if limits:
		last_expense_list = list(limits[1:])
	else:
		return
	for last, now in zip(last_expense_list, now_expense_list):
		if last != now:
			result = True
			break
	if result == True:
		update_monthly_limit(now_expense_list, now_month, 'limits')

	


def update_operation(table, op_id, date):
	cursor.execute(f'''
	UPDATE {table}
	SET date = '{date}'
	WHERE id = {op_id}	
	''')
	db.commit()


def get_info_operation(id, table):
	cursor.execute(f'''
	SELECT category, amount, date, message
	FROM {table}
	WHERE id = {id}	
	''')
	return cursor.fetchone()


''' ### ФУНКЦИИ ДЛЯ ЗАПИСИ ДАННЫХ ПРОШЛОГО МЕСЯЦА В EXCEL ### '''

def get_data_month(month, table):
	# Запрашиваем данные из БД по указанной таблице и за указанный месяц
	execute = f'''
		SELECT date, category, sum(amount) as sum
		FROM '{table}'
		WHERE date >= DATE('{month}') and date < DATE('{month}', '+1 month')
		GROUP BY date, category
	'''
	cursor.execute(execute)
	data = cursor.fetchall()
	return data


def writing_table(date, data, dict_expense_last, limit_now_month):

	month, year = int(date[5:7]), date[:4] 				# Получаем год, месяц 
	filename    = f'data/Family budget {year}.xlsx'		# Эксель файл
	wb 		    = load_workbook(filename=filename)		# Открываем файл
	wb.active   = month 								# Открываем лист соответствующий месяцу
	sheet       = wb.active 

	for to_date, cat, number in data:
		en_date = str(int(to_date[-2:]) + 3)			# Получаем номер строки
		en_cat  = data_save.category_excel_dict[cat]	# Получаем номер столбца
		sheet[en_cat + en_date] = number				# Записываем ячейку

	for i, item in enumerate(dict_expense_last.items()):
		en_cat  = data_save.category_excel_dict[item[0]]# Получаем номер строки 
		sheet[en_cat + '36'] = limit_now_month[i]		# Записываем лимит по категории
		sheet[en_cat + '38'] = item[1][0]				# Записываем остаток с прошлого месяца

	wb.save(filename)									# Сохраняем файл
	return filename


def to_excel():
	# Получаем прошлый месяц
	month = get_last_month() + '-01'
	data  = get_data_month(month, 'expense') + get_data_month(month, 'income')

	# Получаем словарь затрат предыдущего месяца
	dict_expense_last = report_month(get_last_month(32), True)

	# Получаем лимиты прошлого месяца	
	limit_now_month = get_limits(month)

	filename = writing_table(month, data, dict_expense_last, limit_now_month)
	return filename



''' ### Отчет за год! ### '''

def report_year(date=None):
	
	if not date:							# Если год не передают, берем текущий!
		date = str(dt.datetime.now().year)
	date += '-01-01'

	cursor.execute(f'''
		SELECT category, SUM(amount) as sum
		FROM expense
		WHERE date >= DATE('{date}') AND date < DATE('{date}', '+1 year')
		GROUP BY category
		ORDER BY sum DESC;
		''')

	sum_amount = cursor.fetchall() 			# Получаем сумму расходов! 
	
	if not sum_amount: 						# Проверка на наличие лимитов
		return None, None

	sum_expense = sum(dict(sum_amount).values())
	table_expense = data_save.table_month_income(sum_amount, sum_expense, 'Расходы')

	cursor.execute(f'''
		SELECT category, SUM(amount) as sum
		FROM income
		WHERE date >= DATE('{date}') AND date < DATE('{date}', '+1 year')
		GROUP BY category
		ORDER BY sum DESC;
		''')

	sum_amount = cursor.fetchall()
	
	if sum_amount:
		sum_income = sum(dict(sum_amount).values())
		table_income = data_save.table_month_income(sum_amount, sum_income)	

	else:
		table_income = 'Нет доходов'
		
	return table_expense, table_income

def money_sum_mount(month=None):
	''' Считаем ДС которые в данный момент есть (должны быть) в наличии '''
	if not month:
		month = str(dt.datetime.now())[:7] + '-01'
	cursor.execute(f'''
		SELECT sum	FROM money_sum	WHERE date = '{month}'
		''')
	begin_mount = cursor.fetchone()[0]
	sum_income, _, sum_expense = sum_month_income_and_expense(month)
	return begin_mount + (sum_income - sum_expense)


def write_money(mount=None):
	''' Делаем запись в таблицу money_sum, сразу делаем проверку
	на наличие изменений в таблице, если добавились новые записи'''

	if not mount:
		mount = str(dt.datetime.now())[:7] + '-01'

	last_month = get_last_month()
	last_sum_money = money_sum_mount(last_month)
	sum_money = cursor.execute(f"SELECT * FROM money_sum WHERE date = '{mount}'")

	if not sum_money:
		cursor.execute(f'INSERT INTO money_sum VALUES ({mount}, {last_sum_money})')

	elif sum_money != last_sum_money:
		cursor.execute(
			f'UPDATE money_sum SET sum = {last_sum_money} WHERE date {mount}'
			)
	db.commit()

if __name__ == '__main__':
	print(money_sum_mount())
