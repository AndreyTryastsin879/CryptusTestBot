import datetime

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

from functions import worksheet_name, spreadsheet_key, get_google_sheet_create_dataframe

credentials = ServiceAccountCredentials.from_json_keyfile_name('ageless-sol-365111-e7f79a255cd5.json',
                                                               ['https://spreadsheets.google.com/feeds',
                                                                'https://www.googleapis.com/auth/drive'])

try:
    gc = gspread.authorize(credentials)

    current_date = datetime.datetime.now().date()

    worksheet = gc.open_by_key(spreadsheet_key).worksheet(worksheet_name)

    df = get_google_sheet_create_dataframe(worksheet)

    # Преобразование типов столбцов
    df['Дата окончания подписки'] = pd.to_datetime(df['Дата окончания подписки'], format='%d-%m-%Y').dt.date

    # Обновление значений в DataFrame
    mask = df['Статус подписки'] == 'Active'
    df['Осталось дней'] = (df.loc[mask, 'Дата окончания подписки'].apply(lambda x: x - current_date)).dt.days

    mask_3_days = df['Осталось дней'] == 3
    df.loc[mask_3_days, 'Количество предупреждений'] += 1

    mask_2_days = df['Осталось дней'] == 2
    df.loc[mask_2_days, 'Количество предупреждений'] += 1

    mask_1_day = df['Осталось дней'] == 1
    df.loc[mask_1_day, 'Количество предупреждений'] += 1

    mask_1_day = df['Осталось дней'] == 0
    df.loc[mask_1_day, 'Количество предупреждений'] += 1

    mask_3_warnings = df['Количество предупреждений'] == 4

    df['Дата окончания подписки'] = pd.to_datetime(df['Дата окончания подписки'], format='%Y-%m-%d')
    df['Дата окончания подписки'] = df['Дата окончания подписки'].dt.strftime('%d-%m-%Y')
    df.drop(columns='Осталось дней', inplace=True)

    # Обновление данных в Google Sheets
    updated_data = [df.columns.tolist()] + df.values.tolist()
    worksheet.update('A1', updated_data)

except Exception as e:
    print(f"Проверка окончания даты подписки Ошибка: {str(e)}")
