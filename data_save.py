import random

from prettytable import PrettyTable


def sum_table(sum_income, sum_income_limit, sum_expense):
	table = PrettyTable()	
	table.field_names = ['Доходы', sum_income]	
	table.add_row(['Расходы', 'Остаток'])
	table.add_row([sum_expense, sum_income_limit])
	return table

def table_month_expense(dict, sum_expense, sum_income_limit):
	table = PrettyTable()
	table.field_names = ['Кат-ия', 'Расходы', 'Ост.']
	for key, val in dict.items():
		if len(val) == 1:
			table.add_row([all_category_dict[key].split()[0], 0, val[0]])
		elif len(val) == 2:
			table.add_row([all_category_dict[key].split()[0], val[1], val[0] - val[1]])
	table.add_row(['Сумма', sum_expense, sum_income_limit])
	return table


def table_month_income(list, sum_income, name='Доход'):
	table = PrettyTable()
	table.field_names = ['Катигория', name]
	for el in list:
		table.add_row([all_category_dict[el[0]], f'{el[1]:,}'])
	table.add_row(['Сумма', f'{sum_income:,}'])
	return table


category_excel_dict = {
	'Food': 'C',
	'Transport': 'D',
	'Home': 'E',
	'Services': 'F',
	'Rest': 'G',
	'Other': 'H',
	'Health': 'I',
	'Clothes': 'J',
	'Vika': 'M',
	'Evgeniy': 'N',
	'Cash': 'O'
}
		
month_dict = {
	'Январь': '01',
	'Февраль': '02',
	'Март': '03',
	'Апрель': '04',
	'Май': '05',
	'Июнь': '06',
	'Июль': '07',
	'Август': '08',
	'Сентябрь': '09',
	'Октябрь': '10',
	'Ноябрь': '11',
	'Декабрь': '12'
}

inverted_month_dict = {v: k for k, v in month_dict.items()}

path_plots = (
	'data/plot_Incomes.png',
	'data/plot_Expense.png',	
	'data/plot_Incomes and Expense.png'
)

report_list = ('Выбрать Месяц!',
	'Месяц',
	'Год',
	'Январь',
	'Февраль',
	'Март',
	'Апрель',
	'Май',
	'Июнь',
	'Июль',
	'Август',
	'Сентябрь',
	'Октябрь',
	'Ноябрь',
	'Декабрь'
)			

expense = {
	'Food': ('Food', 'Еда\Быт', 'еда', 'быт', 'сома'),
	'Transport': ('Transport', 'Транспорт', 'транспорт', 'машина', 'бензин'),
	'Home': ('Home', 'Дом/Тех-ка', 'дом', 'техника', 'аренда'),
	'Services': ('Services', 'Услуги/Налоги/ком-ка', 'услуги', 'налоги', 'связь'),
	'Rest': ('Rest', 'Отдых/Досуг', 'отдых', 'досуг', 'бухло'),
	'Other': ('Other', 'Другое', 'другое', 'техника', 'аренда', 'расход', 'фигня'),
	'Health': ('Health', 'Здоровье/Лекарства', 'здоровье', 'лекарства'),
	'Clothes': ('Clothes', 'Одежда/Развитие', 'одежда', 'развитие', 'курсы')
}

income = {
	'Vika': ('Vika', 'Вика ЗП', 'вика', 'вика зп'),
	'Evgeniy': ('Evgeniy', 'Женя ЗП', 'женя', 'женя зп'),
	'Cash': ('Cash', 'Доход', 'шабашка', 'доход', 'левак', 'возврат', 'подарок', 'наличка')
}

all_category_dict = {
	'Food': 'Еда & Быт',
	'Transport': 'Транспорт',
	'Home': 'Дом & Тех-ка',
	'Services': 'Услуги',
	'Rest': 'Отдых & Досуг',
	'Other': 'Другое',
	'Health': 'Здоровье',
	'Clothes': 'Одежда',
	'Vika': 'Вика ЗП',
	'Evgeniy': 'Женя ЗП',
	'Cash': 'Шабашки'
}

notification = random.choice([
	'А ты внес расходы сегодня!',
	'Пора!',
	'Я знаю, что ты не сделал сегодня!\n Пора внести расходы',
	'Будь лапочкой отправь расходы'
])


message_help = '''
	Для старта работы в боте введи /start
	Для записи операции используй формулу:
	Категория СУММА комментарий(не обязательно) Еда 100 кофе
	Если ошибся с категорией, бот выдаст ошибку и варианты выбора.

	Для изменения лимитов на текущий месяц и все последующие,
	используется следующая команда:
	Лимиты (лимит на еду) (транспорт) (Дом) ....
	Пример: Лимиты 16000 10000 8000 2000 3000 2000 2000 2000
	В сумме должно получиться 45000

	Все остальное интуитивно понятно!	
'''


sticker_list = ['CAACAgIAAxkBAAPRYem-0F6qF6mJfOajDPi_HmL0nWAAAuQRAAKEcVlIZsvazGS6RV4jBA']

def random_sticker(sticker=None):
	if not sticker:
		return random.choice(sticker_list)
	if sticker in sticker_list:
		return
	elif len(sticker_list) == 10:
		sticker_list.remove(random.choice(sticker_list))
	else: sticker_list.append(sticker)
	

def find_cat(text):
	for cat in expense:
		if text in expense[cat]:
			return cat, 'expense', expense[cat][1]
	for cat in income:
		if text in income[cat]:
			return cat, 'income', income[cat][1]
	return None, None, None

def operation_str(income_list, expense_list):
	result_expense_str = ''
	result_income_str = ''
	if income_list:
		result_income_str += 'Доходы:\n'
		for i, el in enumerate(income_list):
			result_income_str += \
				f'{i+1}. {el[3][5:]} {all_category_dict[el[1]]}: {el[2]} руб. /id_i{el[0]}\n'

	if expense_list:
		result_expense_str += 'Расходы:\n'
		for i, el in enumerate(expense_list):
			result_expense_str += \
				f'{i+1}. {el[3][5:]} {all_category_dict[el[1]]}: {el[2]} руб. /id_e{el[0]}\n'
	result = result_expense_str + result_income_str
	if not result: return 'Нет операций за данный период'
	return result



def limits_table(list):
	if list == 'Нет данных': 
		return list
	table = PrettyTable()
	table.field_names = ['Катигория', 'Лимит']
	for i, key in enumerate(expense):
		table.add_row([expense[key][1], list[i]])
	table.add_row(['Сумма', sum(list)])
	return table


