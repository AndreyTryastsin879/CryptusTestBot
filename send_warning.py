import requests

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

from functions import URL, send_message, worksheet_name, spreadsheet_key, get_google_sheet_create_dataframe

credentials = ServiceAccountCredentials.from_json_keyfile_name('ageless-sol-365111-e7f79a255cd5.json',
                                                               ['https://spreadsheets.google.com/feeds',
                                                                'https://www.googleapis.com/auth/drive'])


def send_message_to_client_to_renew_subscription(chat_id, channel_name, displayed_text):
    keyboard = {'inline_keyboard': [[{'text': f'Продлить {channel_name}', 'callback_data': channel_name}]]}

    answer = {'chat_id': chat_id,
              'text': displayed_text,
              'reply_markup': keyboard}

    send_message(answer)


def send_kick_message_to_client(chat_id, displayed_text):
    answer = {'chat_id': chat_id,
              'text': displayed_text
              }

    send_message(answer)


def delete_client_from_chat(channel_id, user_id):
    url = URL + 'kickChatMember'
    answer = {'chat_id': channel_id, 'user_id': user_id}
    response = requests.post(url, json=answer)
    print(response.json())


try:
    gc = gspread.authorize(credentials)

    worksheet = gc.open_by_key(spreadsheet_key).worksheet(worksheet_name)

    df = get_google_sheet_create_dataframe(worksheet)

    df_active_users = df[df['Статус подписки'] == 'Active']
    df_active_users_got_warning = df_active_users[df_active_users['Количество предупреждений'] > 0]

    list_of_clients_with_warning = df_active_users_got_warning['Телеграм ID'].to_list()
    list_of_unique_clients_with_warning = list(set(list_of_clients_with_warning))

    for chat_id in list_of_unique_clients_with_warning:
        print(chat_id)

        slice_by_id_dict = (df_active_users_got_warning[df_active_users_got_warning['Телеграм ID'] == chat_id]
                            .to_dict('records'))

        for row in slice_by_id_dict:
            number_of_warnings, channel_name, channel_id = row['Количество предупреждений'], row['Выбранный тариф'], row['ID Канала']

            if number_of_warnings == 1:
                displayed_text = f'Ваша подписка на канал {channel_name} истекает через 3 суток. Продлите подписку.'
                send_message_to_client_to_renew_subscription(chat_id, channel_name, displayed_text)

            elif number_of_warnings == 2:
                displayed_text = f'Ваша подписка на канал {channel_name} истекает через 2 суток. Продлите подписку.'
                send_message_to_client_to_renew_subscription(chat_id, channel_name, displayed_text)

            elif number_of_warnings == 3:
                displayed_text = f'Ваша подписка на канал {channel_name} истекает через 1 сутки. Продлите подписку.'
                send_message_to_client_to_renew_subscription(chat_id, channel_name, displayed_text)

            elif number_of_warnings >= 4:
                delete_client_from_chat(channel_id, chat_id)

                displayed_text = f'Вы удалены из канала {channel_name}.'

                answer = {'chat_id': chat_id,
                          'text': displayed_text
                          }
                send_message(answer)

                row_index = df[(df['Телеграм ID'] == chat_id) & (df['Выбранный тариф'] == channel_name) &
                               (df['Количество предупреждений'] >= 4)].index

                df.loc[row_index, 'Статус подписки'] = 'Inactive'

                updated_data = [df.columns.tolist()] + df.values.tolist()

                worksheet.update('A1', updated_data)

except Exception as e:
    print(f"Отправка сообщения о продлении или удалении Ошибка: {str(e)}")