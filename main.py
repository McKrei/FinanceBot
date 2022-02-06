import re
import asyncio

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.utils import executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import datetime as dt

import data_save
import markups as nav
import requests_db as rdb

from activate_bot import token


bot = Bot(token=token)
dp = Dispatcher(bot)


def auth(func):
    async def wrapper(message):
        if message['from']['id'] not in data_save.users_id:
            return
        return await func(message)

    return wrapper

@dp.message_handler(content_types=["sticker"])
async def send_sticker(message: types.Message):
    # Получим ID Стикера
    sticker_id = message.sticker.file_id
    data_save.random_sticker(sticker_id)
    await bot.send_message(message.from_user.id,\
        f'Sticker ID:\n{sticker_id}')


@dp.message_handler(commands=['start'])
@auth
async def start_command(message: types.Message):
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
            InlineKeyboardButton('Выбрать дату', callback_data=f'date_op {table} {id}')))
    else:
        await bot.send_message(message.from_user.id, 'Операция не найдина!')

# ('Evgeniy', 15810, '2022-02-04', 'Женя 15810')

@dp.message_handler(Text(equals='Меню'))
@auth
async def open_menu(message: types.Message):
    await bot.send_sticker(message.from_user.id,\
        data_save.random_sticker(),\
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

    if message.text == 'Месяц':
        date = str(dt.datetime.now())[:7]
        table_expense, table_income = rdb.report_month()

    month = data_save.month_dict.get(message.text)
    if month:
        date = str(dt.datetime.now().year) + '-' + month
        table_expense, table_income = rdb.report_month(month)

    if message.text == 'Год':
        await bot.send_message(message.from_user.id,\
            f'{message.text}: Тут будет отчет за год!',\
            reply_markup=nav.main_menu)
        return

    if not table_expense and not table_income: 
        await bot.send_message(message.from_user.id,\
            'Будущие не предсказываю 😜',\
            reply_markup=nav.main_menu)
        return

    await bot.send_message(message.from_user.id,\
        f'<pre>{table_expense}\n{table_income}</pre>',\
        parse_mode=types.ParseMode.HTML,\
        reply_markup=InlineKeyboardMarkup(row_width=2).add(\
        InlineKeyboardButton('Операции', callback_data=f'list {date}'),\
        InlineKeyboardButton('По дням', callback_data=f'day_inline {date}')))


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
            InlineKeyboardButton('Дата', callback_data=f'date_op {table} {operation_id}')))

    except Exception:
        await bot.send_message(message.from_user.id, 'Я тебя не понял')


@dp.callback_query_handler(Text(startswith='add '))
async def operation_add(callback: types.CallbackQuery):
    table, category, summ, mes = callback.data.split()[1:]
    operation_id = rdb.write_db(table, category, summ, mes)

    await callback.message.answer(f'Записал:\n{category} {summ}руб',\
        reply_markup=InlineKeyboardMarkup().add(\
        InlineKeyboardButton('Отмена', callback_data=f'del {table} {operation_id}'),\
        InlineKeyboardButton('Дата', callback_data=f'date_op {table} {operation_id}')))
    await callback.answer()


@dp.callback_query_handler(Text(startswith='del '))
async def operation_del(callback: types.CallbackQuery):
    table, operation_id = callback.data.split()[1:]
    rdb.del_op(table, operation_id)
    await callback.answer('Отмена операции!')


@dp.callback_query_handler(Text(startswith='limit '))
async def change_limit(callback: types.CallbackQuery):
    rdb.change_limit_in_db(callback.data.split()[1])
    if callback.data.split()[1] == 'save':
        await callback.answer('Лимиты сохраненны')
    else:
        await callback.answer('Лимиты отмененны')


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

@dp.callback_query_handler(Text(startswith='date_op '))
async def date_operation(callback: types.CallbackQuery):
    table, op_id = callback.data.split()[1], int(callback.data.split()[2])
    but_inline_now = []
    now_day = int(dt.datetime.now().day)
    for i in range(1, now_day):
        date = str(dt.date.today().replace(day=i))
        but_inline_now.append(InlineKeyboardButton(f'{i}',\
             callback_data=f'u {table} {op_id} {date}'))

    but_inline_now.append(InlineKeyboardButton(f'Прошлый',\
             callback_data=f'date_op_last {table} {op_id}'))

    await callback.message.answer(f'Текущий месяц',\
        reply_markup=InlineKeyboardMarkup(row_width=5).add(*but_inline_now))
    
    await callback.answer()


@dp.callback_query_handler(Text(startswith='date_op_last '))
async def date_operation_last_month(callback: types.CallbackQuery):
    table, op_id = callback.data.split()[1], int(callback.data.split()[2])
    but_inline_last = []
    first = dt.date.today().replace(day=1) - dt.timedelta(days=1)
    last_m_day = int(first.day)
    last_m = int(first.month)
    for i in range(1, last_m_day+1):
        date = str(dt.date.today().replace(month=last_m, day=i))
        but_inline_last.append(InlineKeyboardButton(f'{i}',\
             callback_data=f'u {table} {op_id} {date}'))

    await callback.message.answer(f'Прошлый месяц',\
        reply_markup=InlineKeyboardMarkup(row_width=5).add(*but_inline_last))
    
    await callback.answer()
    

@dp.callback_query_handler(Text(startswith='u '))
async def date_operation_last_month(callback: types.CallbackQuery):
    table, op_id, date = callback.data.split()[1:]
    rdb.update_operation(table, int(op_id), date)
    await callback.answer(f'Save {date}')



async def loop_checking(wait):
    while True:
        if str(dt.datetime.now().day) == '1':
            date = str(dt.datetime.now())[:10]
            rdb.new_month(date)
        rdb.change_limit_in_db('return')

        if str(dt.datetime.now().month) != '1':
            rdb.check_sum_and_limit_update()
        await asyncio.sleep(wait)



if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(loop_checking(86_400))
    executor.start_polling(dp)
