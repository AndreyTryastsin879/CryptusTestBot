from app import app
from flask import request

import re

from models import Message, Blockchain
from functions import *


class BotState:
    def __init__(self):
        self.selected_buttons_params = {}
        self.message_id_variable = None
        self.client_txn_hash = None
        self.client_message_id_variable = None
        self.message_hash_alert = None

    def reset_state(self):
        self.selected_buttons_params = {}
        self.message_id_variable = None
        self.client_txn_hash = None
        self.client_message_id_variable = None
        self.message_hash_alert = None


bot_state = BotState()


def check_txn_status_and_answer(chat_id, client_user_name, client_txn_hash, show_send_hash_message,
                                show_send_email_message):

    selected_blockchain_name = bot_state.selected_buttons_params['selected_blockchain']
    total_price_for_payment = bot_state.selected_buttons_params['total_price']
    selected_tariff_channel_id = bot_state.selected_buttons_params['tariff_channel_id']
    selected_blockchain = Blockchain.query.filter(
        Blockchain.name == selected_blockchain_name).first()

    status = check_payment_by_txn(selected_blockchain.tx_hash_api_endpoint,
                                  client_txn_hash,
                                  selected_blockchain.api_key,
                                  selected_blockchain.address_for_payments,
                                  total_price_for_payment)

    if status == 'Ok':
        if 'ready_to_renew' in bot_state.selected_buttons_params:
            bot_state.selected_buttons_params['Payment_status'] = 'Confirmed'
            send_menu_with_text_custom_buttons(chat_id, 'Вы успешно продлили тариф.',
                                               None, None)

            edit_menu_with_text_custom_buttons(chat_id, bot_state.message_id_variable,
                                               show_send_hash_message.text,
                                               None, None)

            selected_tariff = bot_state.selected_buttons_params['tariff_name']
            total_price_pnl = bot_state.selected_buttons_params['total_price_pnl']
            period_in_months = bot_state.selected_buttons_params['period_in_months']

            email = get_client_previous_subscription_info(spreadsheet_key, worksheet_name,
                                                          chat_id, selected_tariff,
                                                          'Почта')

            end_of_subscription_date = get_client_previous_subscription_info(spreadsheet_key, worksheet_name,
                                                                             chat_id, selected_tariff,
                                                                             'Дата окончания подписки')

            read_update_google_sheet_renew_client_subscription(spreadsheet_key, worksheet_name,
                                                               chat_id, client_user_name, email,
                                                               selected_tariff, selected_tariff_channel_id,
                                                               total_price_for_payment,
                                                               total_price_pnl, period_in_months,
                                                               end_of_subscription_date)

            change_status_of_previous_subscription_after_renewal(spreadsheet_key, worksheet_name,
                                                                 chat_id, selected_tariff,
                                                                 end_of_subscription_date)

        else:
            print('запрос почты')
            bot_state.selected_buttons_params['payment_status'] = 'Confirmed'
            send_menu_with_text_custom_buttons(chat_id, show_send_email_message.text,
                                               None, None)

            edit_menu_with_text_custom_buttons(chat_id, bot_state.message_id_variable,
                                               show_send_hash_message.text,
                                               None, None)

    elif status == 'Hash not correct':
        list_of_buttons = ['Поддержка']
        send_menu_with_text_custom_buttons(chat_id,
                                           'Ошибка. Скорее всего вы прислали некорректный хэш транзакции. Пришлите хэш еще раз.',
                                           list_of_buttons, None)

    elif status == 'Not correct wallet for payment':
        list_of_buttons = ['Поддержка']
        send_menu_with_text_custom_buttons(chat_id,
                                           'В платеже указан неверный адрес кошелька для оплаты тарифа. Проверьте и пришлите хэш транзакции c корректным адресом.',
                                           list_of_buttons, None)

    elif status == 'Txn not confirmed':
        list_of_buttons = ['Повторить запрос', 'Поддержка']
        send_menu_with_text_custom_buttons(chat_id,
                                           'Транзакции еще не подтверждена. Дождитесь статуса CONFIRMED и повторите запрос.',
                                           list_of_buttons, None)

    elif status == 'Sent not requested currency':
        list_of_buttons = ['Поддержка']
        send_menu_with_text_custom_buttons(chat_id,
                                           f'В платеже указана неверная валюта. Отправьте {total_price_for_payment} USDT, затем пришлите хэш транзакции повторно.',
                                           list_of_buttons, None)

    elif status == 'Not enough for payment':
        list_of_buttons = ['Поддержка']
        send_menu_with_text_custom_buttons(chat_id,
                                           f'В платеже указана неверная сумма. Отправьте {total_price_for_payment} USDT, затем пришлите хэш транзакции повторно.',
                                           list_of_buttons, None)


def check_tariff_in_sheet_and_update(chat_id, client_user_name, email,
                                     total_price_for_payment, total_price_pnl, period_in_months,
                                     tariff):

    send_menu_with_text_custom_buttons(chat_id, 'Записываю ваши данные.', None, None)

    status = check_tariff_in_google_sheets(chat_id, tariff.name)

    if status == 'Exist':
        end_of_subscription_date = get_client_previous_subscription_info(spreadsheet_key,
                                                                         worksheet_name,
                                                                         chat_id,
                                                                         tariff.name,
                                                                         'Дата окончания подписки')

        read_update_google_sheet_renew_client_subscription(spreadsheet_key, worksheet_name,
                                                           chat_id, client_user_name, email,
                                                           tariff.name, tariff.channel_id,
                                                           total_price_for_payment,
                                                           total_price_pnl,
                                                           period_in_months,
                                                           end_of_subscription_date)

        change_status_of_previous_subscription_after_renewal(spreadsheet_key,
                                                             worksheet_name,
                                                             chat_id, tariff.name,
                                                             end_of_subscription_date)

    else:
        read_update_google_sheet_create_invite_link(spreadsheet_key, worksheet_name,
                                                    chat_id, client_user_name, email,
                                                    tariff.name, tariff.channel_id, tariff.price,
                                                    total_price_pnl, period_in_months, tariff.channel_id)


@app.route('/', methods=['POST', 'GET'])
def index():
    show_tariff_menu = Message.query.filter(Message.slug == 'show_menu_tariffs').first()
    show_periods_menu = Message.query.filter(Message.slug == 'show_menu_periods').first()
    show_blockchains_menu = Message.query.filter(Message.slug == 'show_menu_blockchains').first()
    show_payment_message = Message.query.filter(Message.slug == 'show_payment_message').first()
    show_send_hash_message = Message.query.filter(Message.slug == 'show_send_hash_message').first()
    show_send_email_message = Message.query.filter(Message.slug == 'show_send_email_message').first()
    show_invite_message = Message.query.filter(Message.slug == 'show_invite_message').first()

    if request.method == 'POST':
        response = request.get_json()
        print(response)

        try:
            chat_id = response['message']['chat']['id']
            client_user_name = response['message']['from']['username']
            message = response['message']['text']
            client_message_id = response['message']['message_id']

            if message == '/start':
                bot_state.client_message_id_variable = client_message_id
                try:
                    ready_for_renewal = bot_state.selected_buttons_params['ready_to_renew']
                    delete_client_message(chat_id, bot_state.client_message_id_variable)
                    bot_state.selected_buttons_params.pop('ready_to_renew')

                except Exception as e:
                    print(f"Блок /start Ошибка: {str(e)}")

                    message_id = send_menu_with_models_from_db(chat_id, show_tariff_menu.text, show_tariff_menu.tariffs)
                    bot_state.message_id_variable = message_id

            elif re.search('[0-9].*[A-z]', message) and message != '/start':
                bot_state.client_message_id_variable = client_message_id
                try:
                    wait_for_txn_hash = bot_state.selected_buttons_params['wait_for_txn_hash']
                    bot_state.client_txn_hash = message
                    if len(message) > 60:
                        print(message)
                        check_txn_status_and_answer(chat_id, client_user_name,
                                                    bot_state.client_txn_hash,
                                                    show_send_hash_message,
                                                    show_send_email_message)

                    else:
                        message_id = send_menu_with_text_custom_buttons(chat_id, 'Это не похоже на хэш транзакции',
                                                                        None, None)
                        bot_state.message_hash_alert = message_id

                except Exception as e:
                    print(f"Блок проверки hash Ошибка: {str(e)}")
                    bot_state.client_message_id_variable = client_message_id
                    delete_client_message(chat_id, bot_state.client_message_id_variable)

            elif re.search('.*@.*\.[A-z]{2,}', message) and message != '/start':
                try:
                    print(message)
                    payment_status = bot_state.selected_buttons_params['payment_status']
                    tariff_name = bot_state.selected_buttons_params['tariff_name']
                    total_price_for_payment = bot_state.selected_buttons_params['total_price']
                    total_price_pnl = bot_state.selected_buttons_params['total_price_pnl']
                    period_in_months = bot_state.selected_buttons_params['period_in_months']

                    if tariff_name == '3 + 1 бесплатно':
                        for tariff in show_tariff_menu.tariffs:
                            if tariff.name != '3 + 1 бесплатно':
                                check_tariff_in_sheet_and_update(chat_id, client_user_name, message,
                                                                 total_price_for_payment, total_price_pnl,
                                                                 period_in_months,
                                                                 tariff)
                        bot_state.reset_state()
                        send_menu_with_text_custom_buttons(chat_id, show_invite_message.text,
                                                           None, None)
                    else:
                        for tariff in show_tariff_menu.tariffs:
                            if tariff.name == tariff_name:

                                check_tariff_in_sheet_and_update(chat_id, client_user_name, message,
                                                                 total_price_for_payment, total_price_pnl,
                                                                 period_in_months,
                                                                 tariff)
                        bot_state.reset_state()
                        send_menu_with_text_custom_buttons(chat_id, show_invite_message.text,
                                                       None, None)
                except Exception as e:
                    print(f"Блок проверки email Ошибка: {str(e)}")

                    bot_state.client_message_id_variable = client_message_id
                    delete_client_message(chat_id, bot_state.client_message_id_variable)

            elif "@" not in message or re.search('.*\.[A-z]{2,}', message) is None:
                try:
                    print(message)
                    payment_status = bot_state.selected_buttons_params['payment_status']
                    send_menu_with_text_custom_buttons(chat_id, 'Некорректный email. Пришлите адрес вида example@site.ru.',
                                                       None, None)
                except Exception as e:
                    print(f"Блок проверки email на отсутствие символов Ошибка: {str(e)}")
                    bot_state.client_message_id_variable = client_message_id
                    delete_client_message(chat_id, bot_state.client_message_id_variable)

            else:
                bot_state.client_message_id_variable = client_message_id
                delete_client_message(chat_id, bot_state.client_message_id_variable)

        except Exception as e:
            print(f"Первый блок TRY Ошибка: {str(e)}")

            try:
                print(response)
                chat_id = response['callback_query']['message']['chat']['id']
                client_user_name = response['callback_query']['from']['username']
                callback_query_data = response['callback_query']['data']
                callback_query_id = response['callback_query']['id']

                if 'back' in callback_query_data:
                    pass
                else:
                    answer_callback_query(callback_query_id, f'Вы выбрали: {callback_query_data}')

                if 'Продлите подписку' in response['callback_query']['message']['text']:
                    bot_state.selected_buttons_params['ready_to_renew'] = True
                    message_to_renew_id = response['callback_query']['message']['message_id']

                    if message_to_renew_id < bot_state.message_id_variable:
                        delete_client_message(chat_id, bot_state.message_id_variable)
                        delete_client_message(chat_id, bot_state.client_message_id_variable)
                        bot_state.selected_buttons_params.pop('ready_to_renew')
                        bot_state.message_id_variable = message_to_renew_id
                    else:
                        bot_state.message_id_variable = message_to_renew_id

                for tariff in show_tariff_menu.tariffs:
                    if tariff.name == callback_query_data:
                        bot_state.selected_buttons_params['tariff_name'] = tariff.name
                        bot_state.selected_buttons_params['tariff_price'] = tariff.price
                        bot_state.selected_buttons_params['tariff_channel_id'] = tariff.channel_id
                        message_id = edit_menu_with_models_from_db(chat_id, bot_state.message_id_variable, show_periods_menu.text,
                                                                   show_periods_menu.periods, 'back_to_tariffs')
                        bot_state.message_id_variable = message_id

                for period in show_periods_menu.periods:
                    if period.name == callback_query_data:
                        bot_state.selected_buttons_params['period_in_months'] = period.period_in_months
                        bot_state.selected_buttons_params['total_price'] = (bot_state.selected_buttons_params['tariff_price'] *
                                                                            bot_state.selected_buttons_params['period_in_months'] *
                                                                            period.percentage_of_tariff_price / 100)

                        bot_state.selected_buttons_params['total_price_pnl'] = (bot_state.selected_buttons_params['total_price'] /
                                                                                bot_state.selected_buttons_params['period_in_months'])

                        message_id = edit_menu_with_models_from_db(chat_id, bot_state.message_id_variable,
                                                                   show_blockchains_menu.text,
                                                                   show_blockchains_menu.blockchains, 'back_to_periods')
                        bot_state.message_id_variable = message_id

                for blockchain in show_blockchains_menu.blockchains:
                    if blockchain.name == callback_query_data:
                        bot_state.selected_buttons_params['selected_blockchain'] = blockchain.name
                        bot_state.selected_buttons_params['payment_address'] = blockchain.address_for_payments

                        payment_address = bot_state.selected_buttons_params['payment_address']
                        total_price = bot_state.selected_buttons_params['total_price']
                        displayed_text = show_payment_message.text.format(total_price, payment_address)

                        list_of_buttons = ['Я оплатил']

                        message_id = edit_menu_with_text_custom_buttons(chat_id, bot_state.message_id_variable, displayed_text,
                                                                        list_of_buttons, 'back_to_blockchain')
                        bot_state.message_id_variable = message_id

                if callback_query_data == 'Я оплатил':
                    bot_state.selected_buttons_params['wait_for_txn_hash'] = True
                    message_id = edit_menu_with_text_custom_buttons(chat_id, bot_state.message_id_variable,
                                                                    show_send_hash_message.text,
                                                                    None, 'back_to_payment_message')
                    bot_state.message_id_variable = message_id

                if callback_query_data == 'Повторить запрос':
                    check_txn_status_and_answer(chat_id, client_user_name,
                                                bot_state.client_txn_hash, show_send_hash_message,
                                                show_send_email_message)

                if callback_query_data == 'back_to_tariffs':
                    bot_state.message_id_variable = edit_menu_with_models_from_db(chat_id, bot_state.message_id_variable,
                                                                                  show_tariff_menu.text,
                                                                                  show_tariff_menu.tariffs, None)

                elif callback_query_data == 'back_to_periods':
                    bot_state.message_id_variable = edit_menu_with_models_from_db(chat_id, bot_state.message_id_variable,
                                                                                  show_periods_menu.text,
                                                                                  show_periods_menu.periods, 'back_to_tariffs')

                elif callback_query_data == 'back_to_blockchain':
                    bot_state.message_id_variable = edit_menu_with_models_from_db(chat_id, bot_state.message_id_variable,
                                                                                  show_blockchains_menu.text,
                                                                                  show_blockchains_menu.blockchains,
                                                                                  'back_to_periods')

                elif callback_query_data == 'back_to_payment_message':
                    bot_state.selected_buttons_params.pop('wait_for_txn_hash')

                    payment_address = bot_state.selected_buttons_params['payment_address']
                    total_price = bot_state.selected_buttons_params['total_price']
                    displayed_text = show_payment_message.text.format(total_price, payment_address)

                    list_of_buttons = ['Я оплатил']

                    message_id = edit_menu_with_text_custom_buttons(chat_id, bot_state.message_id_variable, displayed_text,
                                                                    list_of_buttons, 'back_to_blockchain')
                    bot_state.message_id_variable = message_id

                    if bot_state.message_hash_alert:
                        delete_client_message(chat_id, bot_state.message_hash_alert)
                        delete_client_message(chat_id, bot_state.client_message_id_variable)

            except Exception as e:
                print(f"Блок проверки callback query Ошибка: {str(e)}")

    return '<h1>Hello bot</h1>'
