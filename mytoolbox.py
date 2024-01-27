
#Librairies utiles
from datetime import datetime, timedelta


def nearest_table_date(user_date, db_table_dates):
    # doc regex date : https://docs.python.org/fr/3.6/library/datetime.html#strftime-and-strptime-behavior
    user_date_object = datetime.strptime(user_date, "%Y-%m-%d")
    nearest_date_index = -1
    for i, date in enumerate(db_table_dates):
        table_date_object = datetime.strptime(date, "%Y-%m-%d")
        if table_date_object < user_date_object:
            if i == 0:
                old_diff = abs((table_date_object - user_date_object).days)
            else:
                new_diff = abs((table_date_object - user_date_object).days)
                if new_diff < old_diff:
                    old_diff = new_diff
                    nearest_date_index = i
    if nearest_date_index == -1:
        return None
    else:
        return db_table_dates[nearest_date_index]