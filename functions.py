import requests
import datetime
from dateutil.relativedelta import relativedelta

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

from config import URL, worksheet_name, spreadsheet_key

credentials = ServiceAccountCredentials.from_json_keyfile_name('ageless-sol-365111-e7f79a255cd5.json',
                                                               ['https://spreadsheets.google.com/feeds',
                                                                'https://www.googleapis.com/auth/drive'])

gc = gspread.authorize(credentials)


def send_message(answer):
    url = URL + 'sendMessage'
    answer['parse_mode'] = 'HTML'
    response = requests.post(url, json=answer)
    print(response.json())
    return response.json()


def answer_callback_query(callback_query_id, text):
    url = URL + 'answerCallbackQuery'
    answer = {
        'callback_query_id': callback_query_id,
        'text': text,
        'show_alert': False
    }
    response = requests.post(url, json=answer)
    return response.json()


def edit_message(answer):
    url = URL + 'editMessageText'
    answer['parse_mode'] = 'HTML'
    response = requests.post(url, json=answer)
    print(response.json())
    return response.json()


def create_invite_link(answer):
    url = URL + 'createChatInviteLink'
    response = requests.post(url, json=answer)
    print(response.json())
    return response.json()


def create_invite_link_for_private_channel(channel_id, client_username, payment_date):
    answer = {'chat_id': channel_id, 'name': f'{client_username} {payment_date}',
              'member_limit': 1}
    print(answer)
    create_invite_link(answer)


def delete_message(answer):
    url = URL + 'deleteMessage'
    response = requests.post(url, json=answer)
    print(response.json())
    return response.json()


def delete_client_message(chat_id, message_id):
    answer = {'chat_id': chat_id, 'message_id': message_id}
    delete_message(answer)


def get_list_step_and_create_keyboard(list_of_objects, step):
    start = 0
    end = len(list_of_objects)

    list_of_ready_buttons = []
    for number in range(start, end, step):

        limited_list = list_of_objects[number:number + step]

        list_of_buttons_dicts = []
        for element in limited_list:
            d = dict()
            d['text'] = element.name
            d['callback_data'] = element.name
            list_of_buttons_dicts.append(d)

        list_of_ready_buttons.append(list_of_buttons_dicts)
        start += step

    keyboard = dict()
    keyboard['inline_keyboard'] = list_of_ready_buttons

    return keyboard


def even_numbers_of_buttons_adjust_menu(list_of_objects):
    if len(list_of_objects) == 2:
        step = 2
        return get_list_step_and_create_keyboard(list_of_objects, step)
    else:
        step = len(list_of_objects) // 2
        return get_list_step_and_create_keyboard(list_of_objects, step)


def uneven_numbers_of_buttons_adjust_menu(list_of_objects):
    list_of_objects_without_last_element = list_of_objects[0:-1]

    keyboard = even_numbers_of_buttons_adjust_menu(list_of_objects_without_last_element)

    keyboard['inline_keyboard'].append([{'text': list_of_objects[-1].name, 'callback_data': list_of_objects[-1].name}])

    return keyboard


def adjust_menu_depending_on_number(list_of_objects):
    if len(list_of_objects) == 1:
        return get_list_step_and_create_keyboard(list_of_objects, 1)

    elif len(list_of_objects) % 2 == 0:
        return even_numbers_of_buttons_adjust_menu(list_of_objects)

    else:
        return uneven_numbers_of_buttons_adjust_menu(list_of_objects)


def send_message_with_text_only_return_response(chat_id, displayed_text):
    answer = {'chat_id': chat_id, 'text': displayed_text}

    response = send_message(answer)

    return response['result']['message_id']


def send_message_with_text_and_keyboard_return_response(chat_id, displayed_text, keyboard):
    answer = {'chat_id': chat_id, 'text': displayed_text,
              'reply_markup': keyboard}

    response = send_message(answer)

    return response['result']['message_id']


def edit_message_with_text_only_return_response(chat_id, message_id, displayed_text):
    answer = {'chat_id': chat_id, 'message_id': message_id, 'text': displayed_text}

    response = edit_message(answer)

    return response['result']['message_id']


def edit_message_with_text_and_keyboard_return_response(chat_id, message_id, displayed_text, keyboard):
    answer = {'chat_id': chat_id, 'message_id': message_id,
              'text': displayed_text, 'reply_markup': keyboard}

    response = edit_message(answer)

    return response['result']['message_id']


def send_menu_with_models_from_db(chat_id, displayed_text, list_of_objects):
    keyboard = adjust_menu_depending_on_number(list_of_objects)

    return send_message_with_text_and_keyboard_return_response(chat_id, displayed_text, keyboard)


def send_menu_with_text_custom_buttons(chat_id, displayed_text, list_of_buttons, return_button_callback_data):
    keyboard = dict()
    keyboard['inline_keyboard'] = []

    if list_of_buttons and return_button_callback_data:
        for button in list_of_buttons:
            keyboard['inline_keyboard'].append([{'text': button, 'callback_data': button}])

        keyboard['inline_keyboard'].append([{'text': 'Назад', 'callback_data': return_button_callback_data}])

        return send_message_with_text_and_keyboard_return_response(chat_id, displayed_text, keyboard)

    elif return_button_callback_data and list_of_buttons is None:
        keyboard['inline_keyboard'].append([{'text': 'Назад', 'callback_data': return_button_callback_data}])

        return send_message_with_text_and_keyboard_return_response(chat_id, displayed_text, keyboard)

    elif return_button_callback_data is None and list_of_buttons:
        for button in list_of_buttons:
            keyboard['inline_keyboard'].append([{'text': button, 'callback_data': button}])

        return send_message_with_text_and_keyboard_return_response(chat_id, displayed_text, keyboard)

    else:
        return send_message_with_text_only_return_response(chat_id, displayed_text)


def edit_menu_with_models_from_db(chat_id, message_id, displayed_text, list_of_objects, return_button_callback_data):
    keyboard = adjust_menu_depending_on_number(list_of_objects)
    if return_button_callback_data:
        keyboard['inline_keyboard'].append([{'text': 'Назад', 'callback_data': return_button_callback_data}])

        return edit_message_with_text_and_keyboard_return_response(chat_id, message_id, displayed_text, keyboard)

    else:
        return edit_message_with_text_and_keyboard_return_response(chat_id, message_id, displayed_text, keyboard)


def edit_menu_with_text_custom_buttons(chat_id, message_id, displayed_text, list_of_buttons,
                                       return_button_callback_data):
    keyboard = dict()
    keyboard['inline_keyboard'] = []

    if list_of_buttons and return_button_callback_data:

        for button in list_of_buttons:
            keyboard['inline_keyboard'].append([{'text': button, 'callback_data': button}])

        keyboard['inline_keyboard'].append([{'text': 'Назад', 'callback_data': return_button_callback_data}])

        return edit_message_with_text_and_keyboard_return_response(chat_id, message_id, displayed_text, keyboard)

    if return_button_callback_data and list_of_buttons is None:
        keyboard['inline_keyboard'].append([{'text': 'Назад', 'callback_data': return_button_callback_data}])

        return edit_message_with_text_and_keyboard_return_response(chat_id, message_id, displayed_text, keyboard)

    else:
        return edit_message_with_text_only_return_response(chat_id, message_id, displayed_text)


def get_auth_headers(token):
    return {'Authorization': f'OAuth {token}'}


def check_payment_by_txn(api_enpoint, hash_param, token, my_address, amount_must_be_paid):
    check_txn_by_hash = api_enpoint + hash_param
    request = requests.get(check_txn_by_hash, headers=get_auth_headers(token))
    response = request.json()

    if len(response) > 1:

        txn_status = response['confirmed']
        if txn_status == True:
            try:
                token_data = response['tokenTransferInfo']
                to_address = token_data['to_address']

                if to_address == my_address:
                    symbol = token_data['symbol']
                    if symbol == 'USDT':
                        payment_amount = token_data['amount_str']
                        final_payment_amount = float(payment_amount) / 1000000
                        if final_payment_amount == amount_must_be_paid:
                            return 'Ok'
                        else:
                            return 'Not enough for payment'
                    else:
                        return 'Sent not requested currency'
                else:
                    return 'Not correct wallet for payment'
            except:
                return 'Sent not requested currency'
        else:
            return 'Txn not confirmed'

    else:
        return 'Hash not correct'


def get_google_sheet_create_dataframe(worksheet):

    data = worksheet.get_all_values()
    df = pd.DataFrame(data)

    df = pd.DataFrame(data[1:], columns=data[0])

    df['Телеграм ID'] = df['Телеграм ID'].astype(int)
    df['Количество предупреждений'] = df['Количество предупреждений'].astype(int)

    return df


def create_row_in_google_sheet(worksheet, client_tg_id, client_tg_username,
                               client_email, selected_tariff, selected_tariff_channel_id,
                               period_in_months, date_of_subscription, total_payment,
                               total_price_pnl, end_of_subscription):

    list_of_values_for_sheet = list()
    list_of_values_for_sheet.append(client_tg_id)
    list_of_values_for_sheet.append(client_tg_username)
    list_of_values_for_sheet.append(client_email)
    list_of_values_for_sheet.append(selected_tariff)
    list_of_values_for_sheet.append(selected_tariff_channel_id)
    list_of_values_for_sheet.append(period_in_months)
    list_of_values_for_sheet.append(date_of_subscription.strftime('%d-%m-%Y'))
    list_of_values_for_sheet.append(total_payment)
    list_of_values_for_sheet.append(total_price_pnl)
    list_of_values_for_sheet.append(end_of_subscription.strftime('%d-%m-%Y'))
    list_of_values_for_sheet.append('Active')
    list_of_values_for_sheet.append(0)

    worksheet.insert_row(list_of_values_for_sheet, index=2)


def read_update_google_sheet_create_invite_link(spreadsheet_key, worksheet_name,
                                                client_tg_id, client_tg_username, client_email,
                                                selected_tariff, selected_tariff_channel_id, total_payment,
                                                total_price_pnl, period_in_months, paid_channel_id):

    worksheet = gc.open_by_key(spreadsheet_key).worksheet(worksheet_name)

    date_of_subscription = datetime.datetime.now().date()
    end_of_subscription = date_of_subscription + relativedelta(months=period_in_months)

    create_row_in_google_sheet(worksheet, client_tg_id, client_tg_username,
                               client_email, selected_tariff, selected_tariff_channel_id,
                               period_in_months, date_of_subscription, total_payment,
                               total_price_pnl, end_of_subscription)

    create_invite_link_for_private_channel(paid_channel_id, client_tg_username,
                                           date_of_subscription.strftime('%d-%m-%Y'))


def get_client_previous_subscription_info(spreadsheet_key, worksheet_name,
                                          client_tg_id, selected_tafiff,
                                          column_name_to_get_value):

    worksheet = gc.open_by_key(spreadsheet_key).worksheet(worksheet_name)

    df = get_google_sheet_create_dataframe(worksheet)

    df_active_users = df[df['Статус подписки'] == 'Active']
    # df_active_users_got_warning = df_active_users[df_active_users['Количество предупреждений'] > 0]

    # value = (df_active_users_got_warning[(df_active_users_got_warning['Телеграм ID'] == client_tg_id) &
    #                                      (df_active_users_got_warning['Выбранный тариф'] == selected_tafiff)]
    #                                     [column_name_to_get_value].values[0])

    value = (df_active_users[(df_active_users['Телеграм ID'] == client_tg_id) &
                             (df_active_users['Выбранный тариф'] == selected_tafiff)]
    [column_name_to_get_value].values[0])

    return value


def check_tariff_in_google_sheets(client_tg_id, tariff):
    worksheet = gc.open_by_key(spreadsheet_key).worksheet(worksheet_name)

    df = get_google_sheet_create_dataframe(worksheet)

    df_client_id_slice = df[df['Телеграм ID'] == client_tg_id]
    df_client_active_subscription = df_client_id_slice[df_client_id_slice['Статус подписки'] == 'Active']
    search_tariff = df_client_active_subscription[df_client_active_subscription['Выбранный тариф'] == tariff]
    if len(search_tariff) > 0:
        return 'Exist'


def read_update_google_sheet_renew_client_subscription(spreadsheet_key, worksheet_name,
                                                       client_tg_id, client_tg_username, client_email,
                                                       selected_tariff, selected_tariff_channel_id, total_payment,
                                                       total_price_pnl, period_in_months, previous_end_of_subscription):

    worksheet = gc.open_by_key(spreadsheet_key).worksheet(worksheet_name)

    date_of_subscription_renewal = datetime.datetime.now().date()
    end_of_subscription = datetime.datetime.strptime(previous_end_of_subscription, "%d-%m-%Y").date()
    new_end_of_subscription = end_of_subscription + relativedelta(months=period_in_months)

    create_row_in_google_sheet(worksheet, client_tg_id, client_tg_username,
                               client_email, selected_tariff, selected_tariff_channel_id,
                               period_in_months, date_of_subscription_renewal, total_payment,
                               total_price_pnl, new_end_of_subscription)


def change_status_of_previous_subscription_after_renewal(spreadsheet_key, worksheet_name,
                                                         client_tg_id, selected_tariff,
                                                         previous_end_of_subscription):
    worksheet = gc.open_by_key(spreadsheet_key).worksheet(worksheet_name)

    df = get_google_sheet_create_dataframe(worksheet)

    row_index = df[(df['Телеграм ID'] == client_tg_id) & (df['Выбранный тариф'] == selected_tariff) &
                   (df['Дата окончания подписки'] == previous_end_of_subscription)].index

    df.loc[row_index, 'Статус подписки'] = 'Renewed'

    updated_data = [df.columns.tolist()] + df.values.tolist()

    worksheet.update('A1', updated_data)
