import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt

import requests_db as rdb
import data_save


def create_pie(date, year = None):

    if len(date) == 4:          # Проверяем на запрос, на год
        year = date

    data = rdb.operation_list(date, only_table='expense', year=year)
    if not data:
        return 
    df = pd.DataFrame(data)
    df = df.groupby(1).agg({2: np.sum}).sort_values(2, ascending=False)
    amount = df[2].values
    name_cat = [f'{data_save.all_category_dict[cat]}\n {num:,}' \
        for cat, num in zip(df.index, amount)]


    fig1, ax1 = plt.subplots(figsize=(10,10))

    wedges, texts, autotexts = ax1.pie(
        amount,
        labels=name_cat,
        textprops={'fontsize':14, 'color':'k'},
        autopct='%1.2f%%',
        startangle=180
        )

    ax1.axis('equal')
    ax1.legend(loc='upper right', bbox_to_anchor=(1.0, 1.0), fontsize=14)
    ax1.set_title("Расходы", size=15, weight="bold")
    plt.setp(autotexts, size=13, weight="bold")
    plt.savefig('data/saved_figure.png')
    
    return True

def plots_year_data_preparation(data):
    df = pd.DataFrame(data, columns=['id', 'category', 'amount', 'date'])
    df.date = df.date.apply(lambda x: data_save.inverted_month_dict[x[5:-3]])
    df.category = df.category.apply(lambda x: data_save.all_category_dict[x])
    
    year = df.groupby(['date', 'category']).agg({'amount': np.sum}).sort_index(ascending=False)
    data_dict = year.amount.to_dict()
    months = list(data_save.month_dict.keys())[:len((set(df.date.values)))]
    category = list(set(df.category.values))
    
    data_list = [[data_dict.get((month, cat), 0) for month in months] for cat in category]
    
    months_sum_dict = df.groupby('date').agg({'amount': np.sum}).sort_index(ascending=False).amount.to_dict()

    return (months, data_list, category), months_sum_dict


def create_plots(data, title):
    months, data_list, category = data
    fig, ax = plt.subplots(1, 1, figsize=(5 + len(months), 10))
    ax.spines[:].set_visible(False)

    plt.title(title, size=15, weight="bold")
    plt.xlabel('Месяц', size=14)
    plt.ylabel('Значение', size=14)

    for i, y_list in enumerate(data_list):
        plt.plot(months, y_list, label=category[i], marker='>')
        for x, y in enumerate(y_list):
            plt.text(x, y * 1.02, y, horizontalalignment='center', fontsize=12)

    plt.legend(fontsize=13)
    plt.savefig(f'data/plot_{title}.png')

def year_plots(year):
    income, expense = rdb.operation_list(year=year, only_table='all')
    if not income and not expense:
        return

    data_income, dict_income = plots_year_data_preparation(income)
    create_plots(data_income, 'Incomes')

    data_expense, dict_expense = plots_year_data_preparation(expense)
    create_plots(data_expense, 'Expense')
        
    month = dt.datetime.now().month
    months = list(data_save.month_dict.keys())[:month]
    category = ['Доход', 'Расход']
    data = [[d.get(month, 0) for month in months]for d in (dict_income, dict_expense)]    
    data_set = (months, data, category)
    create_plots(data_set, 'Incomes and Expense')

    return True

if __name__ == '__main__':
	create_pie('2022', year='2022')