import datetime as dt
import re
import asyncio

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.utils import executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import visualization
import data_save
import markups as nav
import requests_db as rdb
from activate_bot import token, users_id


bot = Bot(token=token)
dp = Dispatcher(bot)


def auth(func):
    async def wrapper(message):
        if message['from']['id'] not in users_id:
            return
        return await func(message)

    return wrapper



@dp.message_handler(content_types=["sticker"])
async def send_sticker(message: types.Message):
    # Получим ID Стикера
    sticker_id = message.sticker.file_id
    data_save.random_sticker(sticker_id)
    await bot.send_message(message.from_user.id,\
        f'Sticker ID:')


@dp.message_handler(commands=['help'])
@auth
async def start_command(message: types.Message):
    await bot.send_message(message.from_user.id,data_save.message_help)


@dp.message_handler(commands=['start'])
@auth
async def help_command(message: types.Message):
    await bot.send_message(message.from_user.id,\
    'Привет {0.first_name}'.format(message.from_user),\
    reply_markup=nav.main_menu)


@dp.message_handler(Text(startswith='/id_'))
@auth
async def id_command(message: types.Message):
    id = message.text[5:]
    table = 'income' if message.text[4] == 'i' else 'expense'
    result = rdb.get_info_operation(id, table)
    if result:
        category, amount, date, mes = result
        msg = f'{date[6:]} {data_save.all_category_dict[category]} {amount}руб.\n{mes}'
        await bot.send_message(message.from_user.id, msg,\
            reply_markup=InlineKeyboardMarkup(row_width=2).add(\
            InlineKeyboardButton('Удалить', callback_data=f'del {table} {id}'),\
            InlineKeyboardButton('Выбрать дату', callback_data=f'date_op {table} {id} now')))
    else:
        await bot.send_message(message.from_user.id, 'Операция не найдина!')


@dp.message_handler(Text(equals='Меню'))
@auth
async def open_menu(message: types.Message):
    await bot.send_sticker(message.from_user.id,\
        data_save.random_sticker(),\
        reply_markup=nav.main_menu)


@dp.message_handler(Text(equals='Деньги'))
@auth
async def money_now(message: types.Message):
    money = rdb.money_sum_mount()
    await bot.send_message(
        message.from_user.id, 
        f'{money:,} рублей.', 
        reply_markup=nav.main_menu)


@dp.message_handler(Text(equals='Отчеты'))
@auth
async def report_menu(message: types.Message):
    await bot.send_message(message.from_user.id, rdb.operation_list())
    table =  data_save.sum_table(*rdb.sum_month_income_and_expense())
    await bot.send_message(message.from_user.id,\
        f'<pre>{table}</pre>',\
        parse_mode=types.ParseMode.HTML,\
        reply_markup=nav.report_menu)


@dp.message_handler(Text(startswith='Лимиты'))
@auth
async def limit_menu(message: types.Message):
    if message.text == 'Лимиты':
        table = data_save.limits_table(rdb.get_limits())        
        await bot.send_message(message.from_user.id,\
            f'<pre>{table}</pre>',\
            parse_mode=types.ParseMode.HTML,\
            reply_markup=nav.main_menu)
    
    else:
        limit_list = list(map(int, re.findall(r'\d+', message.text)))
        if sum(limit_list) != 45000 and len(limit_list) != 8:
            await bot.send_sticker(message.from_user.id,\
            '''Ошибка! Должно быть:\n
            Сумма лимитов = 45 000\nКоличество категория = 8''',\
            reply_markup=nav.main_menu)
            
        else:
            rdb.update_monthly_limit(limit_list)
            table = data_save.limits_table(limit_list)

            await bot.send_message(message.from_user.id,\
            f'<pre>{table}</pre>',\
            parse_mode=types.ParseMode.HTML,\
            reply_markup=InlineKeyboardMarkup(row_width=2).add(\
            InlineKeyboardButton('Отмена', callback_data=f'limit return'),\
            InlineKeyboardButton('Сохранить', callback_data=f'limit save')))


@dp.message_handler(Text(equals=data_save.report_list))
@auth
async def choice_report(message: types.Message):
    if message.text == 'Выбрать Месяц!':
        await bot.send_sticker(message.from_user.id,\
            data_save.random_sticker(),\
            reply_markup=nav.choice_month_menu)
        return
    
    await bot.send_sticker(message.from_user.id,\
        data_save.random_sticker(),\
        reply_markup=nav.main_menu)

    # Проверка на месяц
    month = data_save.month_dict.get(message.text)
    if message.text == 'Месяц' or month:
        if month: 
            date = str(dt.datetime.now().year) + '-' + month
        else:
            date = str(dt.datetime.now())[:7]
        
        table_expense, table_income = rdb.report_month(date)
        buttons_list = [
            InlineKeyboardButton('Операции', callback_data=f'list {date}'),
            InlineKeyboardButton('По дням', callback_data=f'day_inline {date}')
        ]
    # Проверка на год
    elif message.text == 'Год':
        date = dt.datetime.now().year
        table_expense, table_income = rdb.report_year()
        buttons_list = [
            InlineKeyboardButton('График', callback_data=f'visual plots {date}')
        ]

    # Проверка на запрос в будущие. 
    if not table_expense and not table_income: 
        await bot.send_message(message.from_user.id,\
            'Будущие не предсказываю 😜',\
            reply_markup=nav.main_menu)
        return

    buttons_list.append(
        InlineKeyboardButton('Пирожок', callback_data=f'visual pie {date}')
    )

    await bot.send_message(message.from_user.id,\
        f'<pre>{table_expense}\n{table_income}</pre>',\
        parse_mode=types.ParseMode.HTML,\
        reply_markup=InlineKeyboardMarkup(row_width=2).add(*buttons_list))


@dp.message_handler()
@auth
async def processing_mes(message: types.Message):
    try:      
        summ = int(re.findall(r'\d+', message.text)[0])
        if not summ:
            await bot.send_message(message.from_user.id, 'Не вижу суммы!')
            return

        mes = message.text.strip().split()[0].lower()
        category, table, mes_cat = data_save.find_cat(mes)
        if not category:
            but_list = []
            for el in data_save.expense:
                but_list.append(InlineKeyboardButton(f'{data_save.expense[el][1]} ➖',\
                    callback_data=f'add expense {el} {summ} {mes}'))

            for el in data_save.income:
                but_list.append(InlineKeyboardButton(f'{data_save.income[el][1]} ➕',\
                    callback_data=f'add income {el} {summ} {mes}'))

            await bot.send_message(message.from_user.id,\
            f'Не нашел категорию, Куда записать {summ}руб?',\
            reply_markup=InlineKeyboardMarkup(row_width=2).add(*but_list))
            return

        operation_id = rdb.write_db(table, category, summ, message.text)

        await bot.send_message(message.from_user.id,\
            f'Записал:\n{mes_cat} {summ}руб',\
            reply_markup=InlineKeyboardMarkup(row_width=2).add(\
            InlineKeyboardButton('Отмена', callback_data=f'del {table} {operation_id}'),\
            InlineKeyboardButton('Дата', callback_data=f'date_op {table} {operation_id} now')))

    except Exception:
        await bot.send_message(message.from_user.id, 'Я тебя не понял')





@dp.callback_query_handler(Text(startswith='add '))
async def operation_add(callback: types.CallbackQuery):
    table, category, summ, mes = callback.data.split()[1:]
    operation_id = rdb.write_db(table, category, summ, mes)

    await callback.message.answer(f'Записал:\n{category} {summ}руб',\
        reply_markup=InlineKeyboardMarkup().add(\
        InlineKeyboardButton('Отмена', callback_data=f'del {table} {operation_id}'),\
        InlineKeyboardButton('Дата', callback_data=f'date_op {table} {operation_id} now')))
    await callback.answer()


@dp.callback_query_handler(Text(startswith='del '))
async def operation_del(callback: types.CallbackQuery):
    table, operation_id = callback.data.split()[1:]
    rdb.del_op(table, operation_id)
    await callback.answer('Отмена операции!')


@dp.callback_query_handler(Text(startswith='limit '))
async def change_limit(callback: types.CallbackQuery):
    inf = callback.data.split()[1]
    rdb.change_limit_in_db(inf)
    if inf == 'save':
        await callback.answer('Лимиты сохранены')
        rdb.update_table_limits_now_month()
    else:
        await callback.answer('Лимиты отменены')


@dp.callback_query_handler(Text(startswith='list '))
async def operation_print(callback: types.CallbackQuery):
    msg = callback.data.split()
    date = msg[1]
    order_by = 'date' if len(msg) == 2 else 'category'
    operation = rdb.operation_list(date, order_by)
    await callback.message.answer(operation, reply_markup=InlineKeyboardMarkup().add(\
        InlineKeyboardButton('По категориям', callback_data=f'list {date} cat')))

    await callback.answer()


@dp.callback_query_handler(Text(startswith='day_inline '))
async def day_inline(callback: types.CallbackQuery):
    month = callback.data.split()[1]
    result = rdb.get_sum_day_in_month(month)
    if not result:
        await callback.answer('Операций не было!')
    but_inline_list = []
    for el in result:
        but_inline_list.append(\
            InlineKeyboardButton(f'{el[0][8:]}. {el[1]}руб.', callback_data=f'list {el[0]}'))

    await callback.message.answer(f'Операции за {month}',\
        reply_markup=InlineKeyboardMarkup(row_width=1).add(*but_inline_list))
    
    await callback.answer()


async def button_list_day(last_day, table, op_id, month):
    button_list = []
    for i in range(1, last_day):
        day = str(i)
        day = day if len(day) == 2 else '0' + day
        date = month + day
        button_list.append(InlineKeyboardButton(f'{i}',\
            callback_data=f'u {table} {op_id} {date}'))
    return button_list

@dp.callback_query_handler(Text(startswith='date_op '))
async def date_operation(callback: types.CallbackQuery):
    table, op_id, when = callback.data.split()[1:]
    now_day = dt.datetime.now().day

    if when == 'last' or now_day == 1:
        first          = dt.date.today().replace(day=1) - dt.timedelta(days=1)
        last_day       = first.day + 1
        last_m         = first.month
        date           = str(dt.date.today().replace(month=last_m))[:8]
        but_inline_now = await button_list_day(last_day, table, int(op_id), date)
        message_text   = 'Прошлый месяц'
    
    else:
        date           = str(dt.date.today())[:8]
        but_inline_now = await button_list_day(now_day, table, int(op_id), date)
        message_text   = 'Текущий месяц'
        but_inline_now.append(InlineKeyboardButton(f'Прошлый',\
            callback_data=f'date_op {table} {op_id} last'))


    await callback.message.answer(message_text,\
        reply_markup=InlineKeyboardMarkup(row_width=5).add(*but_inline_now))
    
    await callback.answer()


@dp.callback_query_handler(Text(startswith='u '))
async def update_operation_list(callback: types.CallbackQuery):
    table, op_id, date = callback.data.split()[1:]
    rdb.update_operation(table, int(op_id), date)
    await callback.answer(f'Save {date}')


@dp.callback_query_handler(Text(startswith='visual '))
async def visualization_data(callback: types.CallbackQuery):
    figure, date = callback.data.split()[1:]
    
    if figure == 'pie':
        result = visualization.create_pie(date)
        if not result:
            await callback.answer('Нету данных')
        else:
            with open('data/saved_figure.png', "rb") as photo:
                await callback.message.answer_photo(photo)


    elif figure == 'plots':
        result = visualization.year_plots(date)

        if not result:
            await callback.answer('Нету данных')

        else:
            for path in data_save.path_plots:
                with open(path, "rb") as photo:
                    await callback.message.answer_photo(photo)

    await callback.answer()

    
async def loop_checking():
    wait = 3_600
    while True:
        date_now = dt.datetime.now()

        if date_now.day == 1:
            # Генерим новые лимиты на месяц
            date = str(date_now)[:10]
            rdb.new_month(date)

            # Переносим БД в эксель и отправляем пользователю первому в списке
            path = rdb.to_excel()
            file = open(path,"rb")            
            await bot.send_document(users_id[0], file)
            file.close()
        
        # отправляем напоминание о внесение ДС
        if date_now.hour == 18:
            await users_notification()
            wait = 14_400

        # проверка данных в таблицах на валидность! 
        rdb.check_sum_and_limit_update()
        rdb.change_limit_in_db('return')

        await asyncio.sleep(wait)


async def users_notification():
    mes = data_save.notification 
    for user in users_id:
        await bot.send_message(user, mes)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(loop_checking()) 
    executor.start_polling(dp)
