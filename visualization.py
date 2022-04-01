import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import requests_db as rdb
import data_save


def create_pie(month):
    data = rdb.operation_list(month, only_table='expense')
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
    ax1.set_title("Расходы за месяц", size=15, weight="bold")
    plt.setp(autotexts, size=13, weight="bold")
    plt.savefig('data/saved_figure.png')
    
    return True

if __name__ == '__main__':
	create_pie('2022-03')