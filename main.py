from data import token, my_id, db_dbname, db_host, db_user, db_password, my_token, group_id, main_album_id
from keyboards import no2dow, no2_v_dow, no2dow_short, no2dow_gen
from keyboards import k_main_menu, k_in_subject__createFor, k_show_materials, k_add_materials, k_confirmation_delete_subject, \
    k_add_to_specific_day__create, k_back, k_back_to_main_menu, k_delete_materials, k_recover_materials, k_confirmation_delete_all_materials, \
    k_choose_materials_to_delete, k_choose_materials_to_recover, k_edit_materials, k_edit_specific_material, k_add_to_specific_day_to_specific_place
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import vk_api.keyboard as kb
import requests
from time import sleep
from datetime import datetime, date, timedelta
import psycopg2
import random
import schedule
from multiprocessing import Process
import threading


session = vk_api.VkApi(token=token)
vk = session.get_api()
longpoll = VkLongPoll(session)
session_me = vk_api.VkApi(token=my_token)
vk_me = session_me.get_api()
connection = psycopg2.connect(dbname=db_dbname,
                              host=db_host,
                              user=db_user,
                              password=db_password)
curr = connection.cursor()

print("Бот запущен")


def process(buddy_id, msg, any_photos, sticker_id=None):
    query = f"SELECT status, sex, id, subject_user_is_in_rn, current_subject_name FROM users WHERE vk_id = {buddy_id}"
    curr.execute(query)
    result = curr.fetchall()
    if not result:
        vk.messages.send(user_id=buddy_id, message="Вступительное сообщение с описанием функций бота", random_id=0, keyboard=k_main_menu)
        person = vk.users.get(user_ids=f'{buddy_id}', fields='sex,screen_name')[0]
        query = f'''INSERT INTO users (name, surname, sex, profile_link, vk_id, status) VALUES('{person["first_name"]}', '{person["last_name"]}', '{"male" if person["sex"] == 2 else "female"}', 'vk.com/{person["screen_name"]}', {person["id"]}, 'main_menu');'''
        curr.execute(query)
        connection.commit()
        return

    status = result[0][0]
    sex = result[0][1]
    db_id = result[0][2]
    subject_user_is_in_rn = result[0][3]
    current_subject_name = result[0][4]
    dayIsEmpty = False
    if status == 'add_to_specific_day':
        query = f"SELECT date_of_lecture FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
        curr.execute(query)
        adding_date = curr.fetchall()[0][0]
        query = f"SELECT TRUE FROM materials WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND date_of_lecture = '{adding_date}' AND deletion_time IS NULL LIMIT 1;"
        curr.execute(query)
        if curr.fetchall():
            dayIsEmpty = False
        else:
            dayIsEmpty = True

    answeredSticker = False
    if sticker_id:
        if sticker_id in [20081, 8617, 20406, 60526, 12995, 8796]:  # спасибо-стикеры
            answer_stickers = [20082, 20663, 71081]
            rand = random.randrange(len(answer_stickers))
            kbrd = ''
            if status == 'main_menu': kbrd = k_main_menu
            elif status == 'choose_subject': kbrd = k_back_to_main_menu
            elif status == 'in_subject': kbrd = k_in_subject__createFor(current_subject_name)
            elif status == 'show_materials': kbrd = k_show_materials
            elif status == 'add_materials': kbrd = k_add_materials
            elif status == 'add_subject' or status == 'delete_subject' or \
                status == 'choose_adding_day_from_list' or status == 'choose_showing_day_from_list' or \
                status == 'choose_deleting_day_from_list' or status == 'choose_recovering_day_from_list' or \
                status == 'choose_editing_day_from_list' or status == 'choose_material_to_edit': kbrd = k_back
            elif status == 'confirmation_delete_subject': kbrd = k_confirmation_delete_subject
            elif status == 'add_to_specific_day': kbrd = k_add_to_specific_day__create(dayIsEmpty=dayIsEmpty)
            elif status == 'add_to_specific_day_to_specific_place': kbrd = k_add_to_specific_day_to_specific_place
            elif status == 'delete_materials': kbrd = k_delete_materials
            elif status == 'recover_materials': kbrd = k_recover_materials
            elif status == 'confirmation_delete_all_materials': kbrd = k_confirmation_delete_all_materials
            elif status == 'choose_materials_to_delete': kbrd = k_choose_materials_to_delete
            elif status == 'choose_materials_to_recover': kbrd = k_choose_materials_to_recover
            elif status == 'edit_materials': kbrd = k_edit_materials
            elif status == 'edit_specific_material': kbrd = k_edit_specific_material
            vk.messages.send(user_id=buddy_id, sticker_id=answer_stickers[rand], random_id=0, keyboard=kbrd)
            answeredSticker = True
        else:
            vk.messages.send(user_id=buddy_id, sticker_id=sticker_id, random_id=0)
        # print(sticker_id)
    if buddy_id == my_id and msg.lower() == "exit":
        curr.close()
        connection.close()
        exit(0)

    photos = []
    if any_photos:
        getPhotosFromLastMessage(buddy_id, photos)

    if status == 'main_menu':
        if msg == "Выбрать предмет":
            query = f"SELECT name FROM subjects WHERE user_id = {buddy_id};"
            curr.execute(query)
            subjects = [el[0] for el in curr.fetchall()]
            if subjects:
                keyboards = makeInlineKeyboardsFromList(subjects)
                for kbrd, nos in keyboards.items():
                    vk.messages.send(user_id=buddy_id, message=f"{nos[0]} - {nos[1]}" if nos[0] != nos[1] else f"{nos[0]}", random_id=0, keyboard=kbrd)
                vk.messages.send(user_id=buddy_id, message="Выбери предмет методом тыка пальца на него", random_id=0, keyboard=k_back_to_main_menu)
                updateUserStatus(buddy_id, 'choose_subject')
            else:
                vk.messages.send(user_id=buddy_id, message="У тебя пока нет предметов, надо сначала добавить их)", random_id=0, keyboard=k_main_menu)
        elif msg == "Добавить":
            vk.messages.send(user_id=buddy_id, message="Напиши название нового предмета", random_id=0, keyboard=k_back)
            updateUserStatus(buddy_id, 'add_subject')
        elif msg == "Удалить":
            query = f"SELECT name FROM subjects WHERE user_id = {buddy_id};"
            curr.execute(query)
            subjects = [el[0] for el in curr.fetchall()]
            if subjects:
                keyboards = makeInlineKeyboardsFromList(subjects)
                for kbrd, nos in keyboards.items():
                    vk.messages.send(user_id=buddy_id, message=f"{nos[0]} - {nos[1]}" if nos[0] != nos[1] else f"{nos[0]}", random_id=0, keyboard=kbrd)
                vk.messages.send(user_id=buddy_id, message="Ткни на предмет, который надо удалить", random_id=0, keyboard=k_back)
                updateUserStatus(buddy_id, 'delete_subject')
            else:
                vk.messages.send(user_id=buddy_id, message="Удалять пока нечего, предлагаю сначала добавить 🙄", random_id=0, keyboard=k_main_menu)
        elif msg == "Список предметов":
            query = f"SELECT name FROM subjects WHERE user_id = {buddy_id};"
            curr.execute(query)
            subjects = [el[0] for el in curr.fetchall()]
            if subjects:
                answer = "Твои предметы:\n"
                for i in range(len(subjects)):
                    answer += f"\n{i + 1}) {subjects[i]}"
                vk.messages.send(user_id=buddy_id, message=answer, random_id=0, keyboard=k_main_menu)
            else:
                vk.messages.send(user_id=buddy_id, message="Пока нет ни одного предмета", random_id=0, keyboard=k_main_menu)
        elif not answeredSticker:
            vk.messages.send(user_id=buddy_id, sticker_id=(13897 if random.randrange(2) == 0 else 77708), random_id=0, keyboard=k_main_menu)

    elif status == 'choose_subject':
        if msg == "Главное меню":
            updateUserStatus(buddy_id, 'main_menu')
            vk.messages.send(user_id=buddy_id, message="Без проблем 😉", random_id=0, keyboard=k_main_menu)
        else:
            query = f"SELECT id FROM subjects WHERE name = '{msg}' AND user_id = {buddy_id};"
            curr.execute(query)
            result = curr.fetchall()
            if result:
                query = f"UPDATE users SET status = 'in_subject', subject_user_is_in_rn = {result[0][0]}, current_subject_name = '{msg}' WHERE vk_id = {buddy_id};"
                curr.execute(query)
                connection.commit()
                vk.messages.send(user_id=buddy_id, message=f"Ты находишься в меню предмета \"{msg}\"! Можешь отправлять фотки и писать сообщения, которые нужно сохранить 😁", random_id=0, keyboard=k_in_subject__createFor(msg))
            elif not answeredSticker:
                vk.messages.send(user_id=buddy_id, sticker_id=(13897 if random.randrange(2) == 0 else 77708), random_id=0)
                vk.messages.send(user_id=buddy_id, message="\"...терпеливо продолжает ждать пока ты выберешь предмет...\"", random_id=0, keyboard=k_back)

    elif status == 'in_subject':
        if msg == "Добавить в определенный день":
            updateUserStatus(buddy_id, 'add_materials')
            vk.messages.send(user_id=buddy_id, message="В какой день добавить?", random_id=0, keyboard=k_add_materials)
        elif msg == "Посмотреть материалы":
            query = f"SELECT COUNT(*) FROM materials WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND deletion_time IS NULL;"
            curr.execute(query)
            rows_amount = curr.fetchall()[0][0]
            if rows_amount:
                updateUserStatus(buddy_id, 'show_materials')
                vk.messages.send(user_id=buddy_id, message="Какие материалы показать?", random_id=0, keyboard=k_show_materials)
            else:
                vk.messages.send(user_id=buddy_id, message=f"Ты пока ничего не добавлял{'а' if sex == 'female' else ''} в этот предмет, самое время начать я считаю)", random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
        elif msg == "Восстановить":
            query = f"SELECT COUNT(*) FROM materials WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND deletion_time IS NOT NULL;"
            curr.execute(query)
            rows_amount = curr.fetchall()[0][0]
            if rows_amount:
                updateUserStatus(buddy_id, 'recover_materials')
                vk.messages.send(user_id=buddy_id, message="Что ты хочешь восстановить?", random_id=0, keyboard=k_recover_materials)
            else:
                vk.messages.send(user_id=buddy_id, message=f"Ты либо еще ничего не удалял{'а' if sex == 'female' else ''} в этом предмете, либо уже все что можно восстановил{'а' if sex == 'female' else ''})", random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
        elif msg == "Удалить":
            query = f"SELECT COUNT(*) FROM materials WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND deletion_time IS NULL;"
            curr.execute(query)
            rows_amount = curr.fetchall()[0][0]
            if rows_amount:
                updateUserStatus(buddy_id, 'delete_materials')
                vk.messages.send(user_id=buddy_id, message="Что ты хочешь удалить?", random_id=0, keyboard=k_delete_materials)
            else:
                vk.messages.send(user_id=buddy_id, message=f"Ты пока ничего не добавлял{'а' if sex == 'female' else ''} в этот предмет", random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
        elif msg == "Редактировать":
            query = f"SELECT TRUE FROM materials WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND deletion_time IS NULL;"
            curr.execute(query)
            if curr.fetchall():
                updateUserStatus(buddy_id, 'edit_materials')
                vk.messages.send(user_id=buddy_id, message="Какой материал ты хочешь отредактировать?", random_id=0, keyboard=k_edit_materials)
            else:
                vk.messages.send(user_id=buddy_id, message=f"Ты пока ничего не добавлял{'а' if sex == 'female' else ''} в этот предмет", random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
        elif msg == "Другой предмет":
            query = f"SELECT name FROM subjects WHERE user_id = {buddy_id};"
            curr.execute(query)
            subjects = [el[0] for el in curr.fetchall()]
            if len(subjects) == 1:
                vk.messages.send(user_id=buddy_id, message="У тебя пока только один предмет - этот)", random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
            else:
                keyboards = makeInlineKeyboardsFromList(subjects)
                for kbrd, nos in keyboards.items():
                    vk.messages.send(user_id=buddy_id, message=f"{nos[0]} - {nos[1]}" if nos[0] != nos[1] else f"{nos[0]}", random_id=0, keyboard=kbrd)
                vk.messages.send(user_id=buddy_id, message="Выбери предмет методом тыка пальца на него", random_id=0, keyboard=k_back_to_main_menu)
                updateUserStatus(buddy_id, 'choose_subject')
        elif msg == "Главное меню":
            updateUserStatus(buddy_id, 'main_menu')
            vk.messages.send(user_id=buddy_id, message="Как скажешь", random_id=0, keyboard=k_main_menu)
        elif msg == "" and photos == []:
            if not answeredSticker:
                vk.messages.send(user_id=buddy_id, sticker_id=(13897 if random.randrange(2) == 0 else 77708), random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
        elif msg == f'"{current_subject_name}"':
            vk.messages.send(user_id=buddy_id, message="Да да, вот в таком ты предмете сейчас находишься, а эта кнопка ничего не делает, представляешь?)", random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
        else:
            assert(msg != "" or photos != [])
            photos = list(map(lambda x: addPhotoToAlbum(x), photos))
            query = f"INSERT INTO materials (user_id, subject_id, photo_link, caption, date_of_lecture, adding_time) " \
                    f"VALUES({db_id}, {subject_user_is_in_rn}, '{photos[0] if len(photos) > 0 else ''}', '{msg}', NOW()::DATE, NOW()::TIMESTAMP) RETURNING id;"
            curr.execute(query)
            last_material_id = curr.fetchall()[0][0]
            query = f"SELECT id, showing_order FROM showing_orders WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND date_of_lecture = NOW()::DATE;"
            curr.execute(query)
            result = curr.fetchall()
            record_id = 0
            if result:
                record_id = result[0][0]
                order_array = result[0][1]
                order_array.append(last_material_id)
            else:
                order_array = [last_material_id]
            for i in range(1, len(photos)):
                query = f"INSERT INTO materials (user_id, subject_id, photo_link, caption, date_of_lecture, adding_time) " \
                        f"VALUES({db_id}, {subject_user_is_in_rn}, '{photos[i]}', '', NOW()::DATE, NOW()::TIMESTAMP + INTERVAL '{i} MILLISECOND') RETURNING id;"
                curr.execute(query)
                last_material_id = curr.fetchall()[0][0]
                order_array.append(last_material_id)
            order_array = f"'{{{', '.join(list(map(str, order_array)))}}}'"
            if result:
                query = f"UPDATE showing_orders SET showing_order = {order_array} WHERE id = {record_id};"
                curr.execute(query)
            else:
                query = f"INSERT INTO showing_orders (user_id, subject_id, date_of_lecture, showing_order) VALUES({db_id}, {subject_user_is_in_rn}, NOW()::DATE, {order_array});"
                curr.execute(query)
            connection.commit()
            if msg != "":
                answer = "Сохранил запись"
                if len(photos) > 0:
                    answer += f" и {pickUpRightWordEnding(len(photos), 'фотографию', 'фотографии', 'фотографий', writeNumber1=False)}"
            else:
                answer = f"Сохранил {pickUpRightWordEnding(len(photos), 'фотографию', 'фотографии', 'фотографий', writeNumber1=False)}"
            answer += " ✅"
            vk.messages.send(user_id=buddy_id, message=answer, random_id=0, keyboard=k_in_subject__createFor(current_subject_name))

    elif status == 'show_materials':
        if msg == "Просмотр материалов":
            vk.messages.send(user_id=buddy_id, message="Эта кнопка носит чисто информационную функцию, не нажимай больше сюда ☺", random_id=0, keyboard=k_show_materials)
        elif msg == "За сегодня":
            query = f"SELECT showing_order FROM showing_orders WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND date_of_lecture = NOW()::DATE;"
            curr.execute(query)
            result = curr.fetchall()
            if result:
                order_array = result[0][0]
                join_part = "JOIN (VALUES"
                for i in range(len(order_array)):
                    if i == 0: join_part += f" ({order_array[i]}, {i + 1})"
                    else: join_part += f", ({order_array[i]}, {i + 1})"
                join_part += ") AS x(id, ordering) ON materials.id = x.id "
                join_part += f"WHERE materials.user_id = {db_id} AND materials.subject_id = {subject_user_is_in_rn} AND materials.date_of_lecture = NOW()::DATE AND materials.deletion_time IS NULL "
                join_part += "ORDER BY x.ordering"
                query = f"SELECT caption, photo_link FROM materials {join_part};"
                curr.execute(query)
                result = combineMaterialsIntoGroups(curr.fetchall())
                updateUserStatus(buddy_id, 'in_subject')
                for i in range(len(result)):
                    if i == len(result) - 1:
                        vk.messages.send(user_id=buddy_id, message=result[i][0], attachment=result[i][1], random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
                    else:
                        vk.messages.send(user_id=buddy_id, message=result[i][0], attachment=result[i][1], random_id=0)
            else:
                vk.messages.send(user_id=buddy_id, message=f"Сегодня ты пока ничего не добавлял{'а' if sex == 'female' else ''}", random_id=0, keyboard=k_show_materials)
        elif msg == "За прошлый раз":
            query = f"SELECT DISTINCT date_of_lecture FROM materials WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND deletion_time IS NULL ORDER BY date_of_lecture DESC LIMIT 2;"
            curr.execute(query)
            result = curr.fetchall()
            if result and (result[0][0] != date.today() or len(result) == 2):
                if result[0][0] == date.today():
                    result.pop(0)
                updateUserStatus(buddy_id, 'in_subject')
                previous_date = result[0][0]
                query = f"SELECT showing_order FROM showing_orders WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND date_of_lecture = '{previous_date}';"
                curr.execute(query)
                order_array = curr.fetchall()[0][0]
                join_part = "JOIN (VALUES"
                for i in range(len(order_array)):
                    if i == 0: join_part += f" ({order_array[i]}, {i + 1})"
                    else: join_part += f", ({order_array[i]}, {i + 1})"
                join_part += ") AS x(id, ordering) ON materials.id = x.id "
                join_part += f"WHERE materials.user_id = {db_id} AND materials.subject_id = {subject_user_is_in_rn} AND materials.date_of_lecture = '{previous_date}' AND materials.deletion_time IS NULL "
                join_part += "ORDER BY x.ordering"
                query = f"SELECT caption, photo_link FROM materials {join_part};"
                curr.execute(query)
                result = combineMaterialsIntoGroups(curr.fetchall())
                how_many_days = pickUpRightWordEnding((date.today() - previous_date).days, "день", "дня", "дней")
                vk.messages.send(user_id=buddy_id, message=f"Материалы, сохраненные в прошлый раз, {how_many_days} назад ({no2_v_dow[previous_date.weekday()]} {previous_date.strftime('%d.%m.%y')})", random_id=0)
                for i in range(len(result)):
                    if i == len(result) - 1:
                        vk.messages.send(user_id=buddy_id, message=result[i][0], attachment=result[i][1], random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
                    else:
                        vk.messages.send(user_id=buddy_id, message=result[i][0], attachment=result[i][1], random_id=0)
            else:
                vk.messages.send(user_id=buddy_id, message=f"До сегодняшего дня ты сюда ничего не добавлял{'а' if sex == 'female' else ''}", random_id=0, keyboard=k_show_materials)
        elif msg == "Сразу все" or msg == "Сразу всё":
            updateUserStatus(buddy_id, 'in_subject')
            query = f"SELECT DISTINCT date_of_lecture FROM materials WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND deletion_time IS NULL ORDER BY date_of_lecture;"
            curr.execute(query)
            unique_dates = [el[0] for el in curr.fetchall()]
            assert(unique_dates != [])
            for unique_date in unique_dates:
                if unique_date != unique_dates[0]:
                    for _ in range(2):
                        vk.messages.send(user_id=buddy_id, message='⏬', random_id=0)
                how_many_days = pickUpRightWordEnding((date.today() - unique_date).days, "день", "дня", "дней")
                if how_many_days == "0 дней":
                    message = "Материалы, сохраненные сегодня 👇"
                elif how_many_days == "1 день":
                    message = "Материалы, сохраненные вчера 👇"
                else:
                    message = f"Материалы, сохраненные {how_many_days} назад ({no2_v_dow[unique_date.weekday()]} {unique_date.strftime('%d.%m.%y')}) 👇"
                vk.messages.send(user_id=buddy_id, message=message, random_id=0)
                query = f"SELECT showing_order FROM showing_orders WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND date_of_lecture = '{unique_date}';"
                curr.execute(query)
                order_array = curr.fetchall()[0][0]
                join_part = "JOIN (VALUES"
                for i in range(len(order_array)):
                    if i == 0: join_part += f" ({order_array[i]}, {i + 1})"
                    else: join_part += f", ({order_array[i]}, {i + 1})"
                join_part += ") AS x(id, ordering) ON materials.id = x.id "
                join_part += f"WHERE materials.user_id = {db_id} AND materials.subject_id = {subject_user_is_in_rn} AND materials.date_of_lecture = '{unique_date}' AND materials.deletion_time IS NULL "
                join_part += "ORDER BY x.ordering"
                query = f"SELECT caption, photo_link FROM materials {join_part};"
                curr.execute(query)
                result = combineMaterialsIntoGroups(curr.fetchall())
                for i in range(len(result)):
                    if i == len(result) - 1 and unique_date == unique_dates[-1]:
                        vk.messages.send(user_id=buddy_id, message=result[i][0], attachment=result[i][1], random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
                    else:
                        vk.messages.send(user_id=buddy_id, message=result[i][0], attachment=result[i][1], random_id=0)
        elif msg == "Выбрать дату из списка":
            makeListOfDates_intoInlineKb(buddy_id, db_id, subject_user_is_in_rn, 'IS NULL', 'choose_showing_day_from_list', "За какой день показать материалы?")
        elif msg == "Назад":
            updateUserStatus(buddy_id, 'in_subject')
            vk.messages.send(user_id=buddy_id, message="Лады 🤝", random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
        elif not answeredSticker:
            vk.messages.send(user_id=buddy_id, sticker_id=(13897 if random.randrange(2) == 0 else 77708), random_id=0, keyboard=k_show_materials)

    elif status == 'add_materials':
        if msg == "Неделю назад" or msg == "Две недели назад":
            adding_date = date.today() - timedelta(days=(7 if msg == "Неделю назад" else 14))
            query = f"INSERT INTO intermediate_information (user_id, subject_name, date_of_lecture) VALUES({db_id}, '{current_subject_name}', '{adding_date}');"
            curr.execute(query)
            updateUserStatus(buddy_id, 'add_to_specific_day')
            message = "Можешь добавлять сюда свои материалы, и они сохраняться именно под этой датой)"
            query = f"SELECT TRUE FROM materials WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND date_of_lecture = '{adding_date}' AND deletion_time IS NULL LIMIT 1;"
            curr.execute(query)
            if curr.fetchall():
                dayIsEmpty = False
                message += f" Если хочешь добавить материал в какое-то определенное место, а не в конец дня, нажми кнопку \"Добавить в определенное место\" ⬇"
                query = f"SELECT showing_order FROM showing_orders WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND date_of_lecture = '{adding_date}';"
                curr.execute(query)
                result = curr.fetchall()
                order_array = result[0][0]
                join_part = "JOIN (VALUES"
                for i in range(len(order_array)):
                    if i == 0: join_part += f" ({order_array[i]}, {i + 1})"
                    else: join_part += f", ({order_array[i]}, {i + 1})"
                join_part += ") AS x(id, ordering) ON materials.id = x.id "
                join_part += f"WHERE materials.user_id = {db_id} AND materials.subject_id = {subject_user_is_in_rn} AND materials.date_of_lecture = '{adding_date}' AND materials.deletion_time IS NULL "
                join_part += "ORDER BY x.ordering"
                query = f"SELECT caption, photo_link FROM materials {join_part};"
                curr.execute(query)
                result = combineMaterialsIntoGroups(curr.fetchall())
                vk.messages.send(user_id=buddy_id, message=f"Материалы, сохраненные {'неделю ' if msg == 'Неделю назад' else 'две недели '}назад ({no2_v_dow[adding_date.weekday()]} {adding_date.strftime('%d.%m.%y')}) 👇", random_id=0)
                for i in range(len(result)):
                    vk.messages.send(user_id=buddy_id, message=result[i][0], attachment=result[i][1], random_id=0)
            else:
                dayIsEmpty = True
                message = f"Добро пожаловать {no2_v_dow[adding_date.weekday()]} {adding_date.strftime('%d.%m.%y')} ({'неделю ' if msg == 'Неделю назад' else 'две недели '}назад)! " + message
            vk.messages.send(user_id=buddy_id, message=message, random_id=0, keyboard=k_add_to_specific_day__create(dayIsEmpty))
        elif msg == "Ввести дату/выбрать из списка":
            query = f"SELECT TRUE FROM materials WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND deletion_time IS NULL;"
            curr.execute(query)
            if curr.fetchall():
                final_phrase = f"В какой день ты хотел{'а' if sex == 'female' else ''} бы добавить материал? В данном списке показаны все дни, когда ты "\
                               f"добавлял{'а' if sex == 'female' else ''} материалы в этот предмет, однако "\
                               f"не обязательно выбирать именно из них. Ты можешь сам{'а' if sex == 'female' else ''} ввести любую дату в формате \"дд.мм.гггг\" "\
                               f"или \"дд.мм.гг\" и добавить туда сколько угодно материала 😉👍"
                makeListOfDates_intoInlineKb(buddy_id, db_id, subject_user_is_in_rn, 'IS NULL', 'choose_adding_day_from_list', final_phrase)
            else:
                updateUserStatus(buddy_id, 'choose_adding_day_from_list')
                final_phrase = f"В какой день ты хотел{'а' if sex == 'female' else ''} бы добавить материал? Введи желаемую дату в формате \"дд.мм.гггг\" или \"дд.мм.гг\""
                vk.messages.send(user_id=buddy_id, message=final_phrase, random_id=0, keyboard=k_back)
        elif msg == "Меню предмета":
            updateUserStatus(buddy_id, 'in_subject')
            vk.messages.send(user_id=buddy_id, message="Да пожалуйста!", random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
        elif not answeredSticker:
            vk.messages.send(user_id=buddy_id, sticker_id=(13897 if random.randrange(2) == 0 else 77708), random_id=0, keyboard=k_add_materials)

    elif status == 'add_subject':
        if msg == "Назад":
            updateUserStatus(buddy_id, 'main_menu')
            vk.messages.send(user_id=buddy_id, message="Возвращаю 😉", random_id=0, keyboard=k_main_menu)
        else:
            if msg == "":
                vk.messages.send(user_id=buddy_id, message="Хотелось бы текст увидеть какой-нибудь...", random_id=0, keyboard=k_back)
            elif "&quot;" in msg or "'" in msg:
                vk.messages.send(user_id=buddy_id, message="Название предмета не должно содержать кавычек. Попробуй еще раз", random_id=0, keyboard=k_back)
            else:
                query = f"SELECT TRUE FROM subjects WHERE name = '{msg}';"
                curr.execute(query)
                if curr.fetchall():
                    vk.messages.send(user_id=buddy_id, message="Такое имя уже существует! Назови новый предмет как-нибудь по-другому)", random_id=0, keyboard=k_back)
                else:
                    query = f"INSERT INTO subjects (name, user_id) VALUES('{msg}', {buddy_id});"
                    curr.execute(query)
                    connection.commit()
                    updateUserStatus(buddy_id, 'main_menu')
                    vk.messages.send(user_id=buddy_id, message=f"Добавлен новый предмет: \"{msg}\" 👍", random_id=0, keyboard=k_main_menu)

    elif status == 'delete_subject':
        if msg == "Назад":
            updateUserStatus(buddy_id, 'main_menu')
            vk.messages.send(user_id=buddy_id, message=f"Да пожалуйста 👌", random_id=0, keyboard=k_main_menu)
        else:
            if msg == "":
                vk.messages.send(user_id=buddy_id, message="Нужен текст, а еще лучше нажми на кнопку ⬆", random_id=0, keyboard=k_back)
            else:
                query = f"SELECT EXISTS (SELECT TRUE FROM subjects WHERE name = '{msg}' and user_id = {buddy_id});"
                curr.execute(query)
                if curr.fetchall()[0][0]:
                    query = f"INSERT INTO intermediate_information (subject_name, user_id) VALUES('{msg}', {buddy_id});"
                    curr.execute(query)
                    updateUserStatus(buddy_id, 'confirmation_delete_subject')
                    vk.messages.send(user_id=buddy_id, message=f"Предупреждаю, ВСЕ материалы предмета \"{msg}\" будут НАВСЕГДА удалены. Уверен{'а' if sex == 'female' else ''} в своем выборе?", random_id=0, keyboard=k_confirmation_delete_subject)
                else:
                    vk.messages.send(user_id=buddy_id, message="Такого предмета не существует, повтори попытку", random_id=0, keyboard=k_back)

    elif status == 'confirmation_delete_subject':
        if msg == "Да":
            query = f"SELECT subject_name FROM intermediate_information WHERE user_id = {buddy_id};"
            curr.execute(query)
            subject = curr.fetchall()
            assert(len(subject) == 1)
            subject_name = subject[0][0]
            query = f"DELETE FROM intermediate_information WHERE user_id = {buddy_id};"
            curr.execute(query)

            query = f"SELECT id FROM subjects WHERE user_id = {buddy_id} AND name = '{subject_name}';"
            curr.execute(query)
            subject_id_toDelete = curr.fetchall()[0][0]
            query = f"DELETE FROM showing_orders WHERE user_id = {db_id} AND subject_id = {subject_id_toDelete};"
            curr.execute(query)

            query = f"DELETE FROM materials WHERE " \
                    f"user_id IN (SELECT id FROM users WHERE vk_id = {buddy_id}) AND " \
                    f"subject_id IN (SELECT id FROM subjects WHERE name = '{subject_name}')" \
                    f"RETURNING materials.photo_link;"
            curr.execute(query)
            photo_links = [el[0] for el in curr.fetchall()]
            for photo_link in photo_links:
                if photo_link:
                    vk_me.photos.delete(owner_id=-group_id, photo_id=int(photo_link[photo_link.rfind('_') + 1:]))
            query = f"DELETE FROM subjects WHERE name = '{subject_name}' AND user_id = {buddy_id}"
            curr.execute(query)

            updateUserStatus(buddy_id, 'main_menu')
            vk.messages.send(user_id=buddy_id, message="Удалил ✅", random_id=0, keyboard=k_main_menu)
        elif msg == "НИНАДА":
            query = f"DELETE FROM intermediate_information WHERE user_id = {buddy_id}"
            curr.execute(query)
            updateUserStatus(buddy_id, 'main_menu')
            vk.messages.send(user_id=buddy_id, message="Ну ладно", random_id=0, keyboard=k_main_menu)
        elif not answeredSticker:
            vk.messages.send(user_id=buddy_id, sticker_id=(13897 if random.randrange(2) == 0 else 77708), random_id=0, keyboard=k_confirmation_delete_subject)

    elif status == 'choose_adding_day_from_list':
        if msg == "Назад":
            updateUserStatus(buddy_id, 'add_materials')
            vk.messages.send(user_id=buddy_id, message="Вернул 😉", random_id=0, keyboard=k_add_materials)
        else:
            try:
                if msg.find(' ') == -1 and msg.count('.') == 2:
                    year = int(msg[msg.rfind('.') + 1:])
                    if year < 100:
                        year += 2000
                    adding_date = date(year, int(msg[msg.find('.') + 1:msg.rfind('.')]), int(msg[:msg.find('.')]))
                else:
                    if msg == "Сегодня":
                        adding_date = date.today()
                    elif msg == "Вчера":
                        adding_date = date.today() - timedelta(days=1)
                    else:
                        dateString = msg[msg.find(' ') + 1:msg.find(' ') + 9]
                        adding_date = date(2000 + int(dateString[6:]), int(dateString[3:5]), int(dateString[:2]))
            except ValueError:
                vk.messages.send(user_id=buddy_id, sticker_id=(13897 if random.randrange(2) == 0 else 77708), random_id=0, keyboard=k_back)
                vk.messages.send(user_id=buddy_id, message="К сожалению, я не смог распознать твою дату. Она должна быть в формате \"дд.мм.гггг\" или \"дд.мм.гг\". Например, \"28.07.23\"", random_id=0, keyboard=k_back)
                return
            except Exception as e:
                log_message = f"choose_adding_day_from_list\nError: {str(e)}\n{datetime.now().strftime('%d.%m.%Y, %H:%M:%S')}\n\n"
                with open("ErrorLog.txt", "a", encoding="utf-8") as file:
                    file.write(log_message)
                curr.close()
                connection.close()
                exit(-1)
            message = "Можешь добавлять сюда свои материалы, и они сохраняться именно под этой датой)"
            how_many_days = pickUpRightWordEnding((date.today() - adding_date).days, "день", "дня", "дней")
            query = f"SELECT TRUE FROM materials WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND date_of_lecture = '{adding_date}' AND deletion_time IS NULL LIMIT 1;"
            curr.execute(query)
            if curr.fetchall():
                dayIsEmpty = False
                query = f"SELECT showing_order FROM showing_orders WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND date_of_lecture = '{adding_date}';"
                curr.execute(query)
                result = curr.fetchall()
                order_array = result[0][0]
                join_part = "JOIN (VALUES"
                for i in range(len(order_array)):
                    if i == 0: join_part += f" ({order_array[i]}, {i + 1})"
                    else: join_part += f", ({order_array[i]}, {i + 1})"
                join_part += ") AS x(id, ordering) ON materials.id = x.id "
                join_part += f"WHERE materials.user_id = {db_id} AND materials.subject_id = {subject_user_is_in_rn} AND materials.date_of_lecture = '{adding_date}' AND materials.deletion_time IS NULL "
                join_part += "ORDER BY x.ordering"
                query = f"SELECT caption, photo_link FROM materials {join_part};"
                curr.execute(query)
                result = combineMaterialsIntoGroups(curr.fetchall())
                if how_many_days == "0 дней":
                    message_before_sending_materials = "Материалы, сохраненные сегодня 👇"
                elif how_many_days == "1 день":
                    message_before_sending_materials = "Материалы, сохраненные вчера 👇"
                else:
                    message_before_sending_materials = f"Материалы, сохраненные {how_many_days} назад ({no2_v_dow[adding_date.weekday()]} {adding_date.strftime('%d.%m.%y')}) 👇"
                vk.messages.send(user_id=buddy_id, message=message_before_sending_materials, random_id=0)
                for i in range(len(result)):
                    vk.messages.send(user_id=buddy_id, message=result[i][0], attachment=result[i][1], random_id=0)
            else:
                dayIsEmpty = True
                greeting = f"Добро пожаловать {no2_v_dow[adding_date.weekday()]} {adding_date.strftime('%d.%m.%y')}"
                if (date.today() - adding_date).days > 0:
                    greeting += f" ({how_many_days} назад)! "
                else:
                    greeting += "! "
                message = greeting + message
            query = f"INSERT INTO intermediate_information (user_id, subject_name, date_of_lecture) VALUES({db_id}, '{current_subject_name}', '{adding_date}');"
            curr.execute(query)
            updateUserStatus(buddy_id, 'add_to_specific_day')
            if not dayIsEmpty:
                message += f" Если хочешь добавить материал в какое-то определенное место, а не в конец дня, нажми кнопку \"Добавить в определенное место\" ⬇"
            vk.messages.send(user_id=buddy_id, message=message, random_id=0, keyboard=k_add_to_specific_day__create(dayIsEmpty))

    elif status == 'add_to_specific_day':
        if msg == "Добавить в определенное место" and not dayIsEmpty:
            updateUserStatus(buddy_id, 'add_to_specific_day_to_specific_place')
            query = f"SELECT date_of_lecture FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
            curr.execute(query)
            adding_date = curr.fetchall()[0][0]
            query = f"SELECT showing_order FROM showing_orders WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND date_of_lecture = '{adding_date}';"
            curr.execute(query)
            order_array = curr.fetchall()[0][0]
            join_part = "JOIN (VALUES"
            for i in range(len(order_array)):
                if i == 0: join_part += f" ({order_array[i]}, {i + 1})"
                else: join_part += f", ({order_array[i]}, {i + 1})"
            join_part += ") AS x(id, ordering) ON materials.id = x.id "
            join_part += f"WHERE materials.user_id = {db_id} AND materials.subject_id = {subject_user_is_in_rn} AND materials.date_of_lecture = '{adding_date}' AND materials.deletion_time IS NULL "
            join_part += "ORDER BY x.ordering"
            query = f"SELECT caption, photo_link FROM materials {join_part};"
            curr.execute(query)
            result = curr.fetchall()
            how_many_days = pickUpRightWordEnding((date.today() - adding_date).days, "день", "дня", "дней")
            if how_many_days == "0 дней":
                message_before_sending_materials = "Материалы, сохраненные сегодня 👇"
            elif how_many_days == "1 день":
                message_before_sending_materials = "Материалы, сохраненные вчера 👇"
            else:
                message_before_sending_materials = f"Материалы, сохраненные {how_many_days} назад ({no2_v_dow[adding_date.weekday()]} {adding_date.strftime('%d.%m.%y')}) 👇"
            vk.messages.send(user_id=buddy_id, message=message_before_sending_materials, random_id=0)
            for i in range(len(result)):
                vk.messages.send(user_id=buddy_id, message=f"[{i + 1}]\n{result[i][0]}", attachment=result[i][1], random_id=0)
            vk.messages.send(user_id=buddy_id, message=f"Как видишь, все материалы теперь пронумерованы. Чтобы добавить новый материал в определенное место, напиши в первой строке сообщения номер места, куда хочешь его добавить (начиная с единицы), а со следующей строки текст твоей записи (если он есть). Если не укажешь номер желаемой строки, я добавлю твой материал на первое место 😉", random_id=0, keyboard=k_add_to_specific_day_to_specific_place)
        elif msg == "Добавить в другой день":
            query = f"DELETE FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
            curr.execute(query)
            updateUserStatus(buddy_id, 'add_materials')
            vk.messages.send(user_id=buddy_id, message="Да легко 😎", random_id=0, keyboard=k_add_materials)
        elif msg == "Главное меню":
            query = f"DELETE FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
            curr.execute(query)
            updateUserStatus(buddy_id, 'main_menu')
            vk.messages.send(user_id=buddy_id, message="Да легко 😎", random_id=0, keyboard=k_main_menu)
        elif msg == "Меню предмета":
            query = f"DELETE FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
            curr.execute(query)
            updateUserStatus(buddy_id, 'in_subject')
            vk.messages.send(user_id=buddy_id, message="Вернул 😉", random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
        elif msg == "" and photos == []:
            if not answeredSticker:
                vk.messages.send(user_id=buddy_id, sticker_id=(13897 if random.randrange(2) == 0 else 77708), random_id=0, keyboard=k_add_to_specific_day__create(dayIsEmpty))
        else:
            photos = list(map(lambda x: addPhotoToAlbum(x), photos))
            query = f"SELECT date_of_lecture FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
            curr.execute(query)
            adding_date = curr.fetchall()[0][0]
            query = f"SELECT id, showing_order FROM showing_orders WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND date_of_lecture = '{adding_date}'"
            curr.execute(query)
            result = curr.fetchall()
            record_id = 0
            if result:
                record_id = result[0][0]
                order_array = result[0][1]
            else:
                order_array = []
            query = f"INSERT INTO materials (user_id, subject_id, photo_link, caption, date_of_lecture, adding_time) " \
                    f"VALUES({db_id}, {subject_user_is_in_rn}, '{photos[0] if len(photos) > 0 else ''}', '{msg}', '{adding_date}', NOW()::TIMESTAMP) RETURNING id;"
            curr.execute(query)
            last_material_id = curr.fetchall()[0][0]
            order_array.append(last_material_id)
            for i in range(1, len(photos)):
                query = f"INSERT INTO materials (user_id, subject_id, photo_link, caption, date_of_lecture, adding_time) " \
                        f"VALUES({db_id}, {subject_user_is_in_rn}, '{photos[i]}', '', '{adding_date}', NOW()::TIMESTAMP + INTERVAL '{i} MILLISECOND') RETURNING id;"
                curr.execute(query)
                last_material_id = curr.fetchall()[0][0]
                order_array.append(last_material_id)
            order_array = f"'{{{', '.join(list(map(str, order_array)))}}}'"
            if result:
                query = f"UPDATE showing_orders SET showing_order = {order_array} WHERE id = {record_id};"
                curr.execute(query)
                clarification = ' в конец дня'
            else:
                query = f"INSERT INTO showing_orders (user_id, subject_id, date_of_lecture, showing_order) VALUES({db_id}, {subject_user_is_in_rn}, '{adding_date}', {order_array});"
                curr.execute(query)
                clarification = ''
            connection.commit()
            if msg != "":
                answer = f"Сохранил{clarification} запись"
                if len(photos) > 0:
                    answer += f" и {pickUpRightWordEnding(len(photos), 'фотографию', 'фотографии', 'фотографий', writeNumber1=False)}"
            else:
                answer = f"Сохранил{clarification} {pickUpRightWordEnding(len(photos), 'фотографию', 'фотографии', 'фотографий', writeNumber1=False)}"
            answer += " ✅"
            vk.messages.send(user_id=buddy_id, message=answer, random_id=0, keyboard=k_add_to_specific_day__create(False))

    elif status == 'add_to_specific_day_to_specific_place':
        if msg == "Добавить в другой день":
            query = f"DELETE FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
            curr.execute(query)
            updateUserStatus(buddy_id, 'add_materials')
            vk.messages.send(user_id=buddy_id, message="Да легко 😎", random_id=0, keyboard=k_add_materials)
        elif msg == "Главное меню":
            query = f"DELETE FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
            curr.execute(query)
            updateUserStatus(buddy_id, 'main_menu')
            vk.messages.send(user_id=buddy_id, message="Да легко 😎", random_id=0, keyboard=k_main_menu)
        elif msg == "Меню предмета":
            query = f"DELETE FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
            curr.execute(query)
            updateUserStatus(buddy_id, 'in_subject')
            vk.messages.send(user_id=buddy_id, message="Вернул 😉", random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
        elif msg == "Назад":
            updateUserStatus(buddy_id, 'add_to_specific_day')
            query = f"SELECT date_of_lecture FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
            curr.execute(query)
            adding_date = curr.fetchall()[0][0]
            how_many_days = pickUpRightWordEnding((date.today() - adding_date).days, "день", "дня", "дней")
            vk.messages.send(user_id=buddy_id, message=f"Можешь продолжать добавлять материалы в конец дня {no2_v_dow[adding_date.weekday()]}, {adding_date.strftime('%d.%m.%y')} ({how_many_days} назад) 😉", random_id=0, keyboard=k_add_to_specific_day__create(False))
        elif msg == "" and photos == []:
            if not answeredSticker:
                vk.messages.send(user_id=buddy_id, sticker_id=(13897 if random.randrange(2) == 0 else 77708), random_id=0, keyboard=k_add_to_specific_day_to_specific_place)
        else:
            photos = list(map(lambda x: addPhotoToAlbum(x), photos))
            query = f"SELECT date_of_lecture FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
            curr.execute(query)
            adding_date = curr.fetchall()[0][0]
            query = f"SELECT id, showing_order FROM showing_orders WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND date_of_lecture = '{adding_date}'"
            curr.execute(query)
            result = curr.fetchall()
            assert(result != [])
            record_id = result[0][0]
            order_array = result[0][1]
            query = f"SELECT id FROM materials WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND date_of_lecture = '{adding_date}' AND deletion_time IS NOT NULL;"
            curr.execute(query)
            deleted_materials = {el[0] for el in curr.fetchall()}
            place = -1
            if msg.find('\n') != -1:
                try:
                    place = int(msg[:msg.find('\n')])
                    place = max(1, place)
                    msg = msg[msg.find('\n') + 1:]
                    assert (msg != '')
                except:
                    pass
            else:
                try:
                    place = int(msg)
                    msg = ''
                except:
                    pass
            if place == -1:  # юзер не написал номер места => добавляем в самое начало дня, даже если в начале есть удаленные (добавляем перед ними)
                place = 1
            else:
                rightful_place = 0
                while rightful_place < len(order_array) and order_array[rightful_place] in deleted_materials:
                    rightful_place += 1
                place = min(place, len(order_array))
                while place > 0:
                    place -= 1
                    rightful_place += 1
                    while rightful_place <= len(order_array) and order_array[rightful_place - 1] in deleted_materials:
                        rightful_place += 1
                place = rightful_place
            query = f"INSERT INTO materials (user_id, subject_id, photo_link, caption, date_of_lecture, adding_time) " \
                    f"VALUES({db_id}, {subject_user_is_in_rn}, '{photos[0] if len(photos) > 0 else ''}', '{msg}', '{adding_date}', NOW()::TIMESTAMP) RETURNING id;"
            curr.execute(query)
            last_material_id = curr.fetchall()[0][0]
            order_array.insert(place - 1, last_material_id)
            place += 1
            for i in range(1, len(photos)):
                query = f"INSERT INTO materials (user_id, subject_id, photo_link, caption, date_of_lecture, adding_time) " \
                        f"VALUES({db_id}, {subject_user_is_in_rn}, '{photos[i]}', '', '{adding_date}', NOW()::TIMESTAMP + INTERVAL '{i} MILLISECOND') RETURNING id;"
                curr.execute(query)
                last_material_id = curr.fetchall()[0][0]
                while place < len(order_array) and order_array[place - 1] in deleted_materials:
                    place += 1
                order_array.insert(place - 1, last_material_id)
                place += 1
            query = f"UPDATE showing_orders SET showing_order = '{{{', '.join(list(map(str, order_array)))}}}' WHERE id = {record_id};"
            curr.execute(query)
            connection.commit()
            if msg != "":
                answer = "Добавил запись"
                if len(photos) > 0:
                    answer += f" и {pickUpRightWordEnding(len(photos), 'фотографию', 'фотографии', 'фотографий', writeNumber1=False)}"
            else:
                answer = f"Добавил {pickUpRightWordEnding(len(photos), 'фотографию', 'фотографии', 'фотографий', writeNumber1=False)}"
            answer += " ✅"
            vk.messages.send(user_id=buddy_id, message=answer, random_id=0)
            how_many_days = pickUpRightWordEnding((date.today() - adding_date).days, "день", "дня", "дней")
            vk.messages.send(user_id=buddy_id, message=f"Материалы {no2dow_gen[adding_date.weekday()]} {adding_date.strftime('%d.%m.%Y')} ({how_many_days} назад) на текущий момент:", random_id=0)
            join_part = "JOIN (VALUES"
            for i in range(len(order_array)):
                if i == 0: join_part += f" ({order_array[i]}, {i + 1})"
                else: join_part += f", ({order_array[i]}, {i + 1})"
            join_part += ") AS x(id, ordering) ON materials.id = x.id "
            join_part += f"WHERE materials.user_id = {db_id} AND materials.subject_id = {subject_user_is_in_rn} AND materials.date_of_lecture = '{adding_date}' AND materials.deletion_time IS NULL "
            join_part += "ORDER BY x.ordering"
            query = f"SELECT caption, photo_link FROM materials {join_part};"
            curr.execute(query)
            result = curr.fetchall()
            for i in range(len(result)):
                vk.messages.send(user_id=buddy_id, message=f"[{i + 1}]\n{result[i][0]}", attachment=result[i][1], random_id=0)
            vk.messages.send(user_id=buddy_id, message=f"Для добавления материала в определенное место напиши в первой строке сообщения желаемое место (начиная с единицы). Иначе я добавлю твой материал на первое место!", random_id=0, keyboard=k_add_to_specific_day_to_specific_place)

    elif status == 'choose_showing_day_from_list':
        if msg == "Назад":
            updateUserStatus(buddy_id, 'show_materials')
            vk.messages.send(user_id=buddy_id, message="Вернул 😉", random_id=0, keyboard=k_show_materials)
        else:
            try:
                if msg == "Сегодня":
                    materials_date = date.today()
                elif msg == "Вчера":
                    materials_date = date.today() - timedelta(days=1)
                else:
                    dateString = msg[msg.find(' ') + 1:msg.find(' ') + 9]
                    materials_date = date(2000 + int(dateString[6:]), int(dateString[3:5]), int(dateString[:2]))
                how_many_days = pickUpRightWordEnding((date.today() - materials_date).days, "день", "дня", "дней")
                if how_many_days == "0 дней":
                    message = "Материалы, сохраненные сегодня 👇"
                elif how_many_days == "1 день":
                    message = "Материалы, сохраненные вчера 👇"
                else:
                    message = f"Материалы, сохраненные {how_many_days} назад ({no2_v_dow[materials_date.weekday()]} {materials_date.strftime('%d.%m.%y')}) 👇"
                vk.messages.send(user_id=buddy_id, message=message, random_id=0)
                query = f"SELECT showing_order FROM showing_orders WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND date_of_lecture = '{materials_date}';"
                curr.execute(query)
                order_array = curr.fetchall()[0][0]
                join_part = "JOIN (VALUES"
                for i in range(len(order_array)):
                    if i == 0: join_part += f" ({order_array[i]}, {i + 1})"
                    else: join_part += f", ({order_array[i]}, {i + 1})"
                join_part += ") AS x(id, ordering) ON materials.id = x.id "
                join_part += f"WHERE materials.user_id = {db_id} AND materials.subject_id = {subject_user_is_in_rn} AND materials.date_of_lecture = '{materials_date}' AND materials.deletion_time IS NULL "
                join_part += "ORDER BY x.ordering"
                query = f"SELECT caption, photo_link FROM materials {join_part};"
                curr.execute(query)
                result = combineMaterialsIntoGroups(curr.fetchall())
                for i in range(len(result)):
                    if i == len(result) - 1:
                        vk.messages.send(user_id=buddy_id, message=result[i][0], attachment=result[i][1], random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
                    else:
                        vk.messages.send(user_id=buddy_id, message=result[i][0], attachment=result[i][1], random_id=0)
                updateUserStatus(buddy_id, 'in_subject')
            except ValueError:
                vk.messages.send(user_id=buddy_id, sticker_id=(13897 if random.randrange(2) == 0 else 77708), random_id=0, keyboard=k_back)
            except Exception as e:
                log_message = f"choose_showing_day_from_list\nError: {str(e)}\n{datetime.now().strftime('%d.%m.%Y, %H:%M:%S')}\n\n"
                with open("ErrorLog.txt", "a", encoding="utf-8") as file:
                    file.write(log_message)
                curr.close()
                connection.close()
                exit(-1)

    elif status == 'delete_materials':
        if msg == "Удалить последнее добавление":
            updateUserStatus(buddy_id, 'in_subject')
            query = f"SELECT caption, photo_link, date_of_lecture, id FROM materials WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND deletion_time IS NULL ORDER BY adding_time DESC LIMIT 1;"
            curr.execute(query)
            result = curr.fetchall()
            assert(result != [])
            caption = result[0][0]
            photo_link = result[0][1]
            date_of_lecture = result[0][2]
            id_toDelete = result[0][3]
            query = f"UPDATE materials SET deletion_time = NOW()::TIMESTAMP WHERE id = {id_toDelete};"
            curr.execute(query)
            connection.commit()
            if caption and photo_link:
                answer = "Удалил следующую запись и фотографию"
            elif caption:
                answer = "Удалил следующую запись"
            else:
                answer = "Удалил следующую фотографию"
            days_passed = (date.today() - date_of_lecture).days
            if days_passed == 0:
                answer += " (от сегодня):"
            elif days_passed == 1:
                answer += " (от вчера):"
            else:
                answer += f" (от {date_of_lecture.strftime('%d.%m.%y')}):"
            vk.messages.send(user_id=buddy_id, message=answer, random_id=0)
            vk.messages.send(user_id=buddy_id, message=caption, attachment=photo_link, random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
        elif msg == "Удалить что-то другое":
            makeListOfDates_intoInlineKb(buddy_id, db_id, subject_user_is_in_rn, 'IS NULL', 'choose_deleting_day_from_list', "Материалы какого дня нужно удалить?")
        elif msg == "Удалить все в этом предмете":
            updateUserStatus(buddy_id, 'confirmation_delete_all_materials')
            vk.messages.send(user_id=buddy_id, message="Предупреждаю, будут удалены ВСЕ материалы этого предмета за ВСЕ дни. Все четко?", random_id=0, keyboard=k_confirmation_delete_all_materials)
        elif msg == "Назад":
            updateUserStatus(buddy_id, 'in_subject')
            vk.messages.send(user_id=buddy_id, message="Ну как хочешь", random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
        elif not answeredSticker:
            vk.messages.send(user_id=buddy_id, sticker_id=(13897 if random.randrange(2) == 0 else 77708), random_id=0, keyboard=k_delete_materials)

    elif status == 'recover_materials':
        if msg == "Восстановить последнее удаление":
            updateUserStatus(buddy_id, 'in_subject')
            query = f"SELECT caption, photo_link, date_of_lecture, id FROM materials WHERE deletion_time IS NOT NULL AND user_id = {db_id} AND subject_id = {subject_user_is_in_rn} ORDER BY deletion_time DESC LIMIT 1;"
            curr.execute(query)
            result = curr.fetchall()
            assert(result != [])
            caption = result[0][0]
            photo_link = result[0][1]
            date_of_lecture = result[0][2]
            id_toRecover = result[0][3]
            query = f"UPDATE materials SET deletion_time = NULL WHERE id = {id_toRecover};"
            curr.execute(query)
            connection.commit()
            if caption and photo_link:
                answer = "Восстановил следующую запись и фотографию"
            elif caption:
                answer = "Восстановил следующую запись"
            else:
                answer = "Восстановил следующую фотографию"
            days_passed = (date.today() - date_of_lecture).days
            if days_passed == 0:
                answer += " (от сегодня):"
            elif days_passed == 1:
                answer += " (от вчера):"
            else:
                answer += f" (от {date_of_lecture.strftime('%d.%m.%y')}):"
            vk.messages.send(user_id=buddy_id, message=answer, random_id=0)
            vk.messages.send(user_id=buddy_id, message=caption, attachment=photo_link, random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
        elif msg == "Восстановить что-то другое":
            makeListOfDates_intoInlineKb(buddy_id, db_id, subject_user_is_in_rn, 'IS NOT NULL', 'choose_recovering_day_from_list', "Материалы какого дня нужно восстановить?")
        elif msg == "Назад":
            updateUserStatus(buddy_id, 'in_subject')
            vk.messages.send(user_id=buddy_id, message="Да без б", random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
        elif not answeredSticker:
            vk.messages.send(user_id=buddy_id, sticker_id=(13897 if random.randrange(2) == 0 else 77708), random_id=0, keyboard=k_recover_materials)

    elif status == 'confirmation_delete_all_materials':
        if msg == "Нееее":
            updateUserStatus(buddy_id, 'in_subject')
            vk.messages.send(user_id=buddy_id, message="Ну ладно, как скажешь", random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
        elif msg == "Удаляй!":
            updateUserStatus(buddy_id, 'in_subject')
            query = f"SELECT caption, photo_link, id FROM materials WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn};"
            curr.execute(query)
            result = curr.fetchall()
            id_toDelete = []
            amount_caption, amount_photo = 0, 0
            for material in result:
                id_toDelete.append(material[2])
                if material[0]:
                    amount_caption += 1
                if material[1]:
                    amount_photo += 1
            query = f"UPDATE materials SET deletion_time = NOW()::TIMESTAMP WHERE id = ANY('{{{', '.join(list(map(str, id_toDelete)))}}}');"
            curr.execute(query)
            connection.commit()
            answer = "Удалил "
            if amount_caption:
                answer += pickUpRightWordEnding(amount_caption, "запись", "записи", "записей", writeNumber1=False)
            if amount_photo:
                if amount_caption:
                    answer += " и "
                answer += pickUpRightWordEnding(amount_photo, "фотографию", "фотографии", "фотографий", writeNumber1=False)
            answer += " 👌"
            vk.messages.send(user_id=buddy_id, message=answer, random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
        elif not answeredSticker:
            vk.messages.send(user_id=buddy_id, sticker_id=(13897 if random.randrange(2) == 0 else 77708), random_id=0, keyboard=k_confirmation_delete_all_materials)

    elif status == 'choose_deleting_day_from_list':
        if msg == "Назад":
            updateUserStatus(buddy_id, 'delete_materials')
            vk.messages.send(user_id=buddy_id, message="Окей 🙂", random_id=0, keyboard=k_delete_materials)
        else:
            try:
                if msg == "Сегодня":
                    materials_date = date.today()
                elif msg == "Вчера":
                    materials_date = date.today() - timedelta(days=1)
                else:
                    dateString = msg[msg.find(' ') + 1:msg.find(' ') + 9]
                    materials_date = date(2000 + int(dateString[6:]), int(dateString[3:5]), int(dateString[:2]))
                how_many_days = pickUpRightWordEnding((date.today() - materials_date).days, "день", "дня", "дней")
                if how_many_days == "0 дней":
                    message = "Материалы, сохраненные сегодня 👇"
                elif how_many_days == "1 день":
                    message = "Материалы, сохраненные вчера 👇"
                else:
                    message = f"Материалы, сохраненные {how_many_days} назад ({no2_v_dow[materials_date.weekday()]} {materials_date.strftime('%d.%m.%y')}) 👇"
                vk.messages.send(user_id=buddy_id, message=message, random_id=0)
                query = f"SELECT showing_order FROM showing_orders WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND date_of_lecture = '{materials_date}'"
                curr.execute(query)
                order_array = curr.fetchall()[0][0]
                join_part = "JOIN (VALUES"
                for i in range(len(order_array)):
                    if i == 0: join_part += f" ({order_array[i]}, {i + 1})"
                    else: join_part += f", ({order_array[i]}, {i + 1})"
                join_part += ") AS x(id, ordering) ON materials.id = x.id "
                join_part += f"WHERE materials.user_id = {db_id} AND materials.subject_id = {subject_user_is_in_rn} AND materials.date_of_lecture = '{materials_date}' AND materials.deletion_time IS NULL "
                join_part += "ORDER BY x.ordering"
                query = f"SELECT caption, photo_link, materials.id FROM materials {join_part};"
                curr.execute(query)
                result = curr.fetchall()
                materials_order = [el[2] for el in result]
                query = f"INSERT INTO intermediate_information (user_id, subject_name, date_of_lecture, materials_order) " \
                        f"VALUES({db_id}, '{current_subject_name}', '{materials_date}', '{{{', '.join(list(map(str, materials_order)))}}}');"
                curr.execute(query)
                connection.commit()
                for i in range(len(result)):
                    vk.messages.send(user_id=buddy_id, message=f"[{i + 1}]\n{result[i][0]}", attachment=result[i][1], random_id=0)
                updateUserStatus(buddy_id, 'choose_materials_to_delete')
                vk.messages.send(user_id=buddy_id, message="Напиши через запятую номера материалов, которые хочешь удалить ⬇", random_id=0, keyboard=k_choose_materials_to_delete)
            except ValueError:
                vk.messages.send(user_id=buddy_id, sticker_id=(13897 if random.randrange(2) == 0 else 77708), random_id=0, keyboard=k_back)
            except Exception as e:
                log_message = f"choose_deleting_day_from_list\nError: {str(e)}{datetime.now().strftime('%d.%m.%Y, %H:%M:%S')}\n\n"
                with open("ErrorLog.txt", "a", encoding="utf-8") as file:
                    file.write(log_message)
                curr.close()
                connection.close()
                exit(-1)

    elif status == 'choose_materials_to_delete':
        if msg == "Удалить все":
            amount_caption, amount_photo = 0, 0
            query = f"SELECT date_of_lecture FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
            curr.execute(query)
            result = curr.fetchall()
            assert (len(result) == 1)
            materials_date = result[0][0]
            query = f"SELECT caption, photo_link, id FROM materials WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND date_of_lecture = '{materials_date}' AND deletion_time IS NULL ORDER BY adding_time"
            curr.execute(query)
            result = curr.fetchall()
            for material in result:
                if material[0]:
                    amount_caption += 1
                if material[1]:
                    amount_photo += 1
                query = f"UPDATE materials SET deletion_time = NOW()::TIMESTAMP WHERE id = {material[2]};"
                curr.execute(query)
            query = f"DELETE FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
            curr.execute(query)
            updateUserStatus(buddy_id, 'in_subject')
            answer = "Удалил "
            if amount_caption:
                answer += pickUpRightWordEnding(amount_caption, "запись", "записи", "записей", writeNumber1=False)
            if amount_photo:
                if amount_caption:
                    answer += " и "
                answer += pickUpRightWordEnding(amount_photo, "фотографию", "фотографии", "фотографий", writeNumber1=False)
            answer += " ✅"
            vk.messages.send(user_id=buddy_id, message=answer, random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
        elif msg == "Назад":
            query = f"DELETE FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
            curr.execute(query)
            makeListOfDates_intoInlineKb(buddy_id, db_id, subject_user_is_in_rn, 'IS NULL', 'choose_deleting_day_from_list', "Материалы какого дня нужно удалить?")
        else:
            try:
                nos_toDelete = list(map(int, msg.split(',')))
                nos_toDelete = list(filter(lambda x: 0 < x < 100000, nos_toDelete))
                nos_toDelete.sort(reverse=True)
                amount_caption, amount_photo = 0, 0
                query = f"SELECT materials_order FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
                curr.execute(query)
                result = curr.fetchall()
                assert(len(result) == 1)
                materials_order = result[0][0]
                materialIds_toDelete = []
                nos_toDelete_successful = []
                for i in range(len(nos_toDelete)):
                    if nos_toDelete[i] > len(materials_order):
                        continue
                    nos_toDelete_successful.insert(0, nos_toDelete[i])
                    query = f"SELECT caption, photo_link FROM materials WHERE id = {materials_order[nos_toDelete[i] - 1]};"
                    curr.execute(query)
                    material = curr.fetchall()
                    if material:
                        materialIds_toDelete.append(materials_order[nos_toDelete[i] - 1])
                        caption = material[0][0]
                        photo_link = material[0][1]
                        if caption:
                            amount_caption += 1
                        if photo_link:
                            amount_photo += 1
                query = f"UPDATE materials SET deletion_time = NOW()::TIMESTAMP WHERE id = ANY('{{{', '.join(list(map(str, materialIds_toDelete)))}}}');"
                curr.execute(query)
                if amount_caption or amount_photo:
                    query = f"DELETE FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
                    curr.execute(query)
                    answer = "Удалил материал"
                    if len(nos_toDelete_successful) == 1:
                        answer += f" № {nos_toDelete_successful[0]}: "
                    else:
                        answer += f"ы № {', '.join(list(map(str, nos_toDelete_successful[:-1])))} и {nos_toDelete_successful[-1]}: "
                    if amount_caption:
                        answer += pickUpRightWordEnding(amount_caption, "запись", "записи", "записей", writeNumber1=False)
                    if amount_photo:
                        if amount_caption:
                            answer += " и "
                        answer += pickUpRightWordEnding(amount_photo, "фотографию", "фотографии", "фотографий", writeNumber1=False)
                    answer += " ✅"
                    query = f"SELECT COUNT(*) FROM materials WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND deletion_time IS NULL;"
                    curr.execute(query)
                    rows_amount = curr.fetchall()[0][0]
                    if rows_amount:
                        updateUserStatus(buddy_id, 'delete_materials')
                        vk.messages.send(user_id=buddy_id, message=answer, random_id=0, keyboard=k_delete_materials)
                    else:
                        updateUserStatus(buddy_id, 'in_subject')
                        vk.messages.send(user_id=buddy_id, message=answer, random_id=0)
                        vk.messages.send(user_id=buddy_id, message="Больше в этом предмете нечего удалять!", random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
                else:
                    vk.messages.send(user_id=buddy_id, message="Таких номеров нет 🙄", random_id=0, keyboard=k_choose_materials_to_delete)
            except:
                vk.messages.send(user_id=buddy_id, sticker_id=(13897 if random.randrange(2) == 0 else 77708), random_id=0, keyboard=k_choose_materials_to_delete)

    elif status == 'choose_recovering_day_from_list':
        if msg == "Назад":
            updateUserStatus(buddy_id, 'recover_materials')
            vk.messages.send(user_id=buddy_id, message="Окей 🙂", random_id=0, keyboard=k_recover_materials)
        else:
            try:
                if msg == "Сегодня":
                    materials_date = date.today()
                elif msg == "Вчера":
                    materials_date = date.today() - timedelta(days=1)
                else:
                    dateString = msg[msg.find(' ') + 1:msg.find(' ') + 9]
                    materials_date = date(2000 + int(dateString[6:]), int(dateString[3:5]), int(dateString[:2]))
                how_many_days = pickUpRightWordEnding((date.today() - materials_date).days, "день", "дня", "дней")
                if how_many_days == "0 дней":
                    message = "Удаленные материалы, которые были изначально сохранены сегодня 👇"
                elif how_many_days == "1 день":
                    message = "Удаленные материалы, которые были изначально сохранены вчера 👇"
                else:
                    message = f"Удаленные материалы, которые были изначально сохранены {how_many_days} назад ({no2_v_dow[materials_date.weekday()]} {materials_date.strftime('%d.%m.%y')}) 👇"
                vk.messages.send(user_id=buddy_id, message=message, random_id=0)
                query = f"SELECT showing_order FROM showing_orders WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND date_of_lecture = '{materials_date}'"
                curr.execute(query)
                order_array = curr.fetchall()[0][0]
                join_part = "JOIN (VALUES"
                for i in range(len(order_array)):
                    if i == 0: join_part += f" ({order_array[i]}, {i + 1})"
                    else: join_part += f", ({order_array[i]}, {i + 1})"
                join_part += ") AS x(id, ordering) ON materials.id = x.id "
                join_part += f"WHERE materials.user_id = {db_id} AND materials.subject_id = {subject_user_is_in_rn} AND materials.date_of_lecture = '{materials_date}' AND materials.deletion_time IS NOT NULL "
                join_part += "ORDER BY x.ordering"
                query = f"SELECT caption, photo_link, materials.id FROM materials {join_part};"
                curr.execute(query)
                result = curr.fetchall()
                materials_order = [el[2] for el in result]
                query = f"INSERT INTO intermediate_information (user_id, subject_name, date_of_lecture, materials_order) " \
                        f"VALUES({db_id}, '{current_subject_name}', '{materials_date}', '{{{', '.join(list(map(str, materials_order)))}}}');"
                curr.execute(query)
                connection.commit()
                for i in range(len(result)):
                    vk.messages.send(user_id=buddy_id, message=f"[{i + 1}]\n{result[i][0]}", attachment=result[i][1], random_id=0)
                updateUserStatus(buddy_id, 'choose_materials_to_recover')
                vk.messages.send(user_id=buddy_id, message="Напиши через запятую номера материалов, которые хочешь восстановить ⬇", random_id=0, keyboard=k_choose_materials_to_recover)
            except ValueError:
                vk.messages.send(user_id=buddy_id, sticker_id=(13897 if random.randrange(2) == 0 else 77708), random_id=0, keyboard=k_back)
            except Exception as e:
                log_message = f"choose_recovering_day_from_list\nError: {str(e)}{datetime.now().strftime('%d.%m.%Y, %H:%M:%S')}\n\n"
                with open("ErrorLog.txt", "a", encoding="utf-8") as file:
                    file.write(log_message)
                curr.close()
                connection.close()
                exit(-1)

    elif status == 'choose_materials_to_recover':
        if msg == "Восстановить все":
            amount_caption, amount_photo = 0, 0
            query = f"SELECT date_of_lecture FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
            curr.execute(query)
            result = curr.fetchall()
            assert (len(result) == 1)
            materials_date = result[0][0]
            query = f"SELECT caption, photo_link, id FROM materials WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND date_of_lecture = '{materials_date}' AND deletion_time IS NOT NULL ORDER BY adding_time"
            curr.execute(query)
            result = curr.fetchall()
            for material in result:
                if material[0]:
                    amount_caption += 1
                if material[1]:
                    amount_photo += 1
                query = f"UPDATE materials SET deletion_time = NULL WHERE id = {material[2]};"
                curr.execute(query)
            query = f"DELETE FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
            curr.execute(query)
            updateUserStatus(buddy_id, 'in_subject')
            answer = "Восстановил "
            if amount_caption:
                answer += pickUpRightWordEnding(amount_caption, "запись", "записи", "записей", writeNumber1=False)
            if amount_photo:
                if amount_caption:
                    answer += " и "
                answer += pickUpRightWordEnding(amount_photo, "фотографию", "фотографии", "фотографий", writeNumber1=False)
            answer += " ✅"
            vk.messages.send(user_id=buddy_id, message=answer, random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
        elif msg == "Назад":
            query = f"DELETE FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
            curr.execute(query)
            makeListOfDates_intoInlineKb(buddy_id, db_id, subject_user_is_in_rn, 'IS NOT NULL', 'choose_recovering_day_from_list', "Материалы какого дня нужно восстановить?")
        else:
            try:
                nos_toRecover = list(map(int, msg.split(',')))
                nos_toRecover = list(filter(lambda x: 0 < x < 100000, nos_toRecover))
                nos_toRecover.sort(reverse=True)
                amount_caption, amount_photo = 0, 0
                query = f"SELECT materials_order FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
                curr.execute(query)
                result = curr.fetchall()
                assert (len(result) == 1)
                materials_order = result[0][0]
                materialIds_toRecover = []
                nos_toRecover_successful = []
                for i in range(len(nos_toRecover)):
                    if nos_toRecover[i] > len(materials_order):
                        continue
                    nos_toRecover_successful.insert(0, nos_toRecover[i])
                    query = f"SELECT caption, photo_link FROM materials WHERE id = {materials_order[nos_toRecover[i] - 1]};"
                    curr.execute(query)
                    material = curr.fetchall()
                    if material:
                        materialIds_toRecover.append(materials_order[nos_toRecover[i] - 1])
                        caption = material[0][0]
                        photo_link = material[0][1]
                        if caption:
                            amount_caption += 1
                        if photo_link:
                            amount_photo += 1
                query = f"UPDATE materials SET deletion_time = NULL WHERE id = ANY('{{{', '.join(list(map(str, materialIds_toRecover)))}}}');"
                curr.execute(query)
                if amount_caption or amount_photo:
                    query = f"DELETE FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
                    curr.execute(query)
                    answer = "Восстановил материал"
                    if len(nos_toRecover_successful) == 1:
                        answer += f" № {nos_toRecover_successful[0]}: "
                    else:
                        answer += f"ы № {', '.join(list(map(str, nos_toRecover_successful[:-1])))} и {nos_toRecover_successful[-1]}: "
                    if amount_caption:
                        answer += pickUpRightWordEnding(amount_caption, "запись", "записи", "записей", writeNumber1=False)
                    if amount_photo:
                        if amount_caption:
                            answer += " и "
                        answer += pickUpRightWordEnding(amount_photo, "фотографию", "фотографии", "фотографий", writeNumber1=False)
                    answer += " ✅"
                    query = f"SELECT COUNT(*) FROM materials WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND deletion_time IS NOT NULL;"
                    curr.execute(query)
                    rows_amount = curr.fetchall()[0][0]
                    if rows_amount:
                        updateUserStatus(buddy_id, 'recover_materials')
                        vk.messages.send(user_id=buddy_id, message=answer, random_id=0, keyboard=k_recover_materials)
                    else:
                        updateUserStatus(buddy_id, 'in_subject')
                        vk.messages.send(user_id=buddy_id, message=answer, random_id=0)
                        vk.messages.send(user_id=buddy_id, message="Больше в этом предмете нечего восстанавливать!", random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
                else:
                    vk.messages.send(user_id=buddy_id, message="Таких номеров нет 🙄", random_id=0, keyboard=k_choose_materials_to_recover)
            except:
                vk.messages.send(user_id=buddy_id, sticker_id=(13897 if random.randrange(2) == 0 else 77708), random_id=0, keyboard=k_choose_materials_to_recover)

    elif status == 'edit_materials':
        if msg == "Редактирование материалов":
            vk.messages.send(user_id=buddy_id, message="Эта кнопка носит чисто информационную функцию, не нажимай больше сюда 🙂", random_id=0, keyboard=k_edit_materials)
        elif msg == "Предоследний" or msg == "Последний":
            query = f"SELECT showing_order FROM showing_orders WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND date_of_lecture = '{date.today()}';"
            curr.execute(query)
            order_array = curr.fetchall()
            if not order_array:
                vk.messages.send(user_id=buddy_id, message=f"Ты пока ничего не добавлял{'а' if sex == 'female' else ''} сегодня", random_id=0, keyboard=k_edit_materials)
                return
            order_array = order_array[0][0]
            join_part = "JOIN (VALUES"
            for i in range(len(order_array)):
                if i == 0: join_part += f" ({order_array[i]}, {i + 1})"
                else: join_part += f", ({order_array[i]}, {i + 1})"
            join_part += ") AS x(id, ordering) ON materials.id = x.id "
            join_part += f"WHERE materials.user_id = {db_id} AND materials.subject_id = {subject_user_is_in_rn} AND materials.date_of_lecture = '{date.today()}' AND materials.deletion_time IS NULL "
            join_part += "ORDER BY x.ordering DESC LIMIT 2;"
            query = f"SELECT caption, photo_link, materials.id FROM materials {join_part};"
            curr.execute(query)
            result = curr.fetchall()
            if len(result) == 1 and msg == "Предоследний":
                vk.messages.send(user_id=buddy_id, message="За сегодня был добавлен только один материал 😐", random_id=0, keyboard=k_edit_materials)
                return
            if msg == "Предоследний":
                caption, photo_link, material_id = result[1]
                vk.messages.send(user_id=buddy_id, message="Предпоследний материал за сегодня 👇", random_id=0)
                vk.messages.send(user_id=buddy_id, message=caption, attachment=photo_link, random_id=0)
            else:
                caption, photo_link, material_id = result[0]
                vk.messages.send(user_id=buddy_id, message="Последний материал за сегодня 👇", random_id=0)
                vk.messages.send(user_id=buddy_id, message=caption, attachment=photo_link, random_id=0)
            query = f"INSERT INTO intermediate_information (user_id, subject_name, material_id) VALUES({db_id}, '{current_subject_name}', {material_id});"
            curr.execute(query)
            updateUserStatus(buddy_id, 'edit_specific_material')
            message = f"{'Введи отредактированный текст, который должен быть вместо этого' if caption else 'Чтобы добавить сюда текст, напиши его в сообщении'}. Чтобы {'заменить фотографию в данном материале,' if photo_link else 'добавить фотографию в данный материал,'} просто отправь ее одним сообщением с новым текстом (если собираешься {'и ' if photo_link and caption else ''}его {'менять' if caption else 'добавлять'})"
            if photo_link:
                message += ". Если хочешь удалить данную фотографию, напиши в первой строке сообщения дефис (или знак минус)"
            if caption:
                message += f"{'. А для ' if photo_link else '. Для '}того, чтобы убрать текст из материала, напиши многоточие..."
            vk.messages.send(user_id=buddy_id, message=message, random_id=0, keyboard=k_edit_specific_material)
        elif msg == "Последний добавленный материал":
            query = f"SELECT caption, photo_link, date_of_lecture, id FROM materials WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} ORDER BY adding_time DESC LIMIT 1;"
            curr.execute(query)
            result = curr.fetchall()
            caption = result[0][0]
            photo_link = result[0][1]
            material_date = result[0][2]
            last_added_material_id = result[0][3]
            how_many_days = pickUpRightWordEnding((date.today() - material_date).days, "день", "дня", "дней")
            if how_many_days == "0 дней":
                message = "Материал, сохраненный сегодня 👇"
            elif how_many_days == "1 день":
                message = "Материал, сохраненный вчера 👇"
            else:
                message = f"Материал, сохраненный {how_many_days} назад ({no2_v_dow[material_date.weekday()]} {material_date.strftime('%d.%m.%y')}) 👇"
            vk.messages.send(user_id=buddy_id, message=message, random_id=0)
            vk.messages.send(user_id=buddy_id, message=caption, attachment=photo_link, random_id=0)
            message = f"{'Введи отредактированный текст, который должен быть вместо этого' if caption else 'Чтобы добавить сюда текст, напиши его в сообщении'}. Чтобы {'заменить фотографию в данном материале,' if photo_link else 'добавить фотографию в данный материал,'} просто отправь ее одним сообщением с новым текстом (если собираешься {'и ' if photo_link and caption else ''}его {'менять' if caption else 'добавлять'})"
            if photo_link:
                message += ". Если хочешь удалить данную фотографию, напиши в первой строке сообщения дефис (или знак минус)"
            if caption:
                message += f"{'. А для ' if photo_link else '. Для '}того, чтобы убрать текст из материала, напиши многоточие..."
            query = f"INSERT INTO intermediate_information (user_id, subject_name, material_id) VALUES({db_id}, '{current_subject_name}', {last_added_material_id});"
            curr.execute(query)
            updateUserStatus(buddy_id, 'edit_specific_material')
            vk.messages.send(user_id=buddy_id, message=message, random_id=0, keyboard=k_edit_specific_material)
        elif msg == "Выбрать из списка":
            makeListOfDates_intoInlineKb(buddy_id, db_id, subject_user_is_in_rn, 'IS NULL', 'choose_editing_day_from_list', "Материал какого дня нужно отредактировать?")
        elif msg == "Назад":
            updateUserStatus(buddy_id, 'in_subject')
            vk.messages.send(user_id=buddy_id, message="Назад так назад)", random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
        elif not answeredSticker:
            vk.messages.send(user_id=buddy_id, sticker_id=(13897 if random.randrange(2) == 0 else 77708), random_id=0, keyboard=k_edit_materials)

    elif status == 'choose_editing_day_from_list':
        if msg == "Назад":
            updateUserStatus(buddy_id, 'edit_materials')
            vk.messages.send(user_id=buddy_id, message="Окей 🙂", random_id=0, keyboard=k_edit_materials)
        else:
            try:
                if msg == "Сегодня":
                    materials_date = date.today()
                elif msg == "Вчера":
                    materials_date = date.today() - timedelta(days=1)
                else:
                    dateString = msg[msg.find(' ') + 1:msg.find(' ') + 9]
                    materials_date = date(2000 + int(dateString[6:]), int(dateString[3:5]), int(dateString[:2]))
                how_many_days = pickUpRightWordEnding((date.today() - materials_date).days, "день", "дня", "дней")
                if how_many_days == "0 дней":
                    message = "Материалы, сохраненные сегодня 👇"
                elif how_many_days == "1 день":
                    message = "Материалы, сохраненные вчера 👇"
                else:
                    message = f"Материалы, сохраненные {how_many_days} назад ({no2_v_dow[materials_date.weekday()]} {materials_date.strftime('%d.%m.%y')}) 👇"
                vk.messages.send(user_id=buddy_id, message=message, random_id=0)
                query = f"SELECT showing_order FROM showing_orders WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND date_of_lecture = '{materials_date}';"
                curr.execute(query)
                order_array = curr.fetchall()[0][0]
                join_part = "JOIN (VALUES"
                for i in range(len(order_array)):
                    if i == 0: join_part += f" ({order_array[i]}, {i + 1})"
                    else: join_part += f", ({order_array[i]}, {i + 1})"
                join_part += ") AS x(id, ordering) ON materials.id = x.id "
                join_part += f"WHERE materials.user_id = {db_id} AND materials.subject_id = {subject_user_is_in_rn} AND materials.date_of_lecture = '{materials_date}' AND materials.deletion_time IS NULL "
                join_part += "ORDER BY x.ordering"
                query = f"SELECT caption, photo_link, materials.id FROM materials {join_part};"
                curr.execute(query)
                result = curr.fetchall()
                materials_order = [el[2] for el in result]
                query = f"INSERT INTO intermediate_information (user_id, subject_name, date_of_lecture, materials_order) " \
                        f"VALUES({db_id}, '{current_subject_name}', '{materials_date}', '{{{', '.join(list(map(str, materials_order)))}}}');"
                curr.execute(query)
                connection.commit()
                for i in range(len(result)):
                    vk.messages.send(user_id=buddy_id, message=f"[{i + 1}]\n{result[i][0]}", attachment=result[i][1], random_id=0)
                updateUserStatus(buddy_id, 'choose_material_to_edit')
                vk.messages.send(user_id=buddy_id, message="Напиши номер материала, который хочешь отредактировать ⬇", random_id=0, keyboard=k_back)
            except ValueError:
                vk.messages.send(user_id=buddy_id, sticker_id=(13897 if random.randrange(2) == 0 else 77708), random_id=0, keyboard=k_back)
            except Exception as e:
                log_message = f"choose_editing_day_from_list\nError: {str(e)}{datetime.now().strftime('%d.%m.%Y, %H:%M:%S')}\n\n"
                with open("ErrorLog.txt", "a", encoding="utf-8") as file:
                    file.write(log_message)
                curr.close()
                connection.close()
                exit(-1)

    elif status == 'choose_material_to_edit':
        if msg == "Назад":
            query = f"DELETE FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
            curr.execute(query)
            makeListOfDates_intoInlineKb(buddy_id, db_id, subject_user_is_in_rn, 'IS NULL', 'choose_editing_day_from_list', "Материал какого дня нужно отредактировать?")
        else:
            try:
                material_no = int(msg)
                query = f"SELECT materials_order FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
                curr.execute(query)
                result = curr.fetchall()
                assert (len(result) == 1)
                materials_order = result[0][0]
                if material_no < 1 or material_no > len(materials_order):
                    vk.messages.send(user_id=buddy_id, message=f"Номера материалов могут быть только от 1 до {len(materials_order)} включительно", random_id=0, keyboard=k_back)
                else:
                    query = f"SELECT caption, photo_link, date_of_lecture FROM materials WHERE id = {materials_order[material_no - 1]};"
                    curr.execute(query)
                    result = curr.fetchall()
                    material_date = result[0][2]
                    how_many_days = pickUpRightWordEnding((date.today() - material_date).days, "день", "дня", "дней")
                    if how_many_days == "0 дней":
                        message = "Материал, сохраненный сегодня 👇"
                    elif how_many_days == "1 день":
                        message = "Материал, сохраненный вчера 👇"
                    else:
                        message = f"Материал, сохраненный {how_many_days} назад ({no2_v_dow[material_date.weekday()]} {material_date.strftime('%d.%m.%y')}) 👇"
                    vk.messages.send(user_id=buddy_id, message=message, random_id=0)
                    vk.messages.send(user_id=buddy_id, message=result[0][0], attachment=result[0][1], random_id=0)
                    query = f"UPDATE intermediate_information SET material_id = {materials_order[material_no - 1]} WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
                    curr.execute(query)
                    connection.commit()
                    updateUserStatus(buddy_id, 'edit_specific_material')
                    message = f"{'Введи отредактированный текст, который должен быть вместо этого' if result[0][0] else 'Чтобы добавить сюда текст, напиши его в сообщении'}. Чтобы {'заменить фотографию в данном материале,' if result[0][1] else 'добавить фотографию в данный материал,'} просто отправь ее одним сообщением с новым текстом (если собираешься {'и ' if result[0][1] and result[0][0] else ''}его {'менять' if result[0][0] else 'добавлять'})"
                    if result[0][1]:
                        message += ". Если хочешь удалить данную фотографию, напиши в первой строке сообщения дефис (или знак минус)"
                    if result[0][0]:
                        message += f"{'. А для ' if result[0][1] else '. Для '}того, чтобы убрать текст из материала, напиши многоточие..."
                    vk.messages.send(user_id=buddy_id, message=message, random_id=0, keyboard=k_edit_specific_material)
            except:
                vk.messages.send(user_id=buddy_id, sticker_id=(13897 if random.randrange(2) == 0 else 77708), random_id=0, keyboard=k_back)

    elif status == 'edit_specific_material':
        if msg == "Редактировать другой материал":
            query = f"DELETE FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
            curr.execute(query)
            updateUserStatus(buddy_id, 'edit_materials')
            vk.messages.send(user_id=buddy_id, message="Как хочешь 😉", random_id=0, keyboard=k_edit_materials)
        elif msg == "Главное меню":
            query = f"DELETE FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
            curr.execute(query)
            updateUserStatus(buddy_id, 'main_menu')
            vk.messages.send(user_id=buddy_id, message="Как хочешь 😉", random_id=0, keyboard=k_main_menu)
        elif msg == "Меню предмета":
            query = f"DELETE FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
            curr.execute(query)
            updateUserStatus(buddy_id, 'in_subject')
            vk.messages.send(user_id=buddy_id, message="Вернул 🙂", random_id=0, keyboard=k_in_subject__createFor(current_subject_name))
        elif msg == "" and photos == []:
            if not answeredSticker:
                vk.messages.send(user_id=buddy_id, sticker_id=(13897 if random.randrange(2) == 0 else 77708), random_id=0, keyboard=k_edit_specific_material)
        else:
            photos = list(map(lambda x: addPhotoToAlbum(x), photos))
            if len(photos) > 1:
                vk.messages.send(user_id=buddy_id, message="В одном материале может содержаться максимум одна фотография. Пожалуйста, повтори попытку", random_id=0, keyboard=k_edit_specific_material)
                return
            query = f"SELECT material_id FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
            curr.execute(query)
            material_id = curr.fetchall()[0][0]
            query = f"SELECT caption, photo_link FROM materials WHERE id = {material_id};"
            curr.execute(query)
            result = curr.fetchall()
            caption = result[0][0]
            photo_link = result[0][1]
            if msg in {'-', '–', '—'} and not caption and photo_link:
                vk.messages.send(user_id=buddy_id, message="Нельзя удалить фотографию, потому что нет текста, в материале должно быть хотя бы что-то одно", random_id=0, keyboard=k_edit_specific_material)
                return
            if msg == "..." and not photo_link and not photos:
                vk.messages.send(user_id=buddy_id, message="Нельзя удалить текст, потому что нет фотографии, в материале должно быть хотя бы что-то одно", random_id=0, keyboard=k_edit_specific_material)
                return
            if msg == "":
                changeCaption = False
            elif msg[0] in {'-', '–', '—'} and (len(msg) == 1 or msg[1] == '\n'):
                if not photos:
                    vk_me.photos.delete(owner_id=-group_id, photo_id=int(photo_link[photo_link.rfind('_') + 1:]))
                    query = f"UPDATE materials SET photo_link = '' WHERE id = {material_id};"
                    curr.execute(query)
                if len(msg) == 1:
                    changeCaption = False
                else:
                    changeCaption = True
                    msg = msg[2:]
            else:
                changeCaption = True
                if msg == "...":
                    msg = ''
            if changeCaption or photos:
                query = f'''UPDATE materials SET caption = {f"'{msg}'" if changeCaption else 'caption'}, photo_link = {f"'{photos[0]}'" if photos else 'photo_link'} WHERE id = {material_id};'''
                curr.execute(query)
            if photos and photo_link:
                vk_me.photos.delete(owner_id=-group_id, photo_id=int(photo_link[photo_link.rfind('_') + 1:]))
            vk.messages.send(user_id=buddy_id, message="Готово! Теперь этот материал выглядит вот так:", random_id=0)
            query = f"DELETE FROM intermediate_information WHERE user_id = {db_id} AND subject_name = '{current_subject_name}';"
            curr.execute(query)
            updateUserStatus(buddy_id, 'edit_materials')
            query = f"SELECT caption, photo_link FROM materials WHERE id = {material_id};"
            curr.execute(query)
            result = curr.fetchall()
            vk.messages.send(user_id=buddy_id, message=result[0][0], attachment=result[0][1], random_id=0)
            vk.messages.send(user_id=buddy_id, message="Что еще надо отредактировать? 😃", random_id=0, keyboard=k_edit_materials)

    else:
        with open("ErrorLog.txt", "a", encoding="utf-8") as file:
            file.write(f"Получен несуществующий статус\n\n")
        exit(-1)


def combineMaterialsIntoGroups(materials: tuple):
    combinedMaterials = []
    photoGroup = ''
    for material in materials:
        if material[0] == '':
            if photoGroup:
                photoGroup += f",{material[1]}"
            else:
                photoGroup = material[1]
        else:
            if photoGroup:
                combinedMaterials.append(['', photoGroup])
                photoGroup = ''
            combinedMaterials.append(material)
    if photoGroup:
        combinedMaterials.append(['', photoGroup])
    return tuple(combinedMaterials)


def makeListOfDates_intoInlineKb(buddy_id, db_id, subject_user_is_in_rn, deletion_time__value, next_status, final_phrase):
    query = f"SELECT DISTINCT date_of_lecture FROM materials WHERE user_id = {db_id} AND subject_id = {subject_user_is_in_rn} AND deletion_time {deletion_time__value} ORDER BY date_of_lecture DESC;"
    curr.execute(query)
    unique_dates = [el[0] for el in curr.fetchall()]
    assert (unique_dates != [])
    updateUserStatus(buddy_id, next_status)
    buttons_names = []
    for unique_date in unique_dates:
        if unique_date == date.today():
            buttons_names.append("Сегодня")
        elif unique_date == date.today() - timedelta(days=1):
            buttons_names.append("Вчера")
        else:
            days_passed = (date.today() - unique_date).days
            if days_passed % 7 == 0:
                when = f"{no2dow_short[unique_date.weekday()]}, {unique_date.strftime('%d.%m.%y')} ({pickUpRightWordEnding(int(days_passed / 7), 'неделю', 'недели', 'недель', writeNumber1=False)} назад)"
            else:
                when = f"{no2dow[unique_date.weekday()]}, {unique_date.strftime('%d.%m.%y')}"
            buttons_names.append(when)
    kbrds = makeInlineKeyboardsFromList(buttons_names)
    for kbrd in kbrds:
        vk.messages.send(user_id=buddy_id, message='...', random_id=0, keyboard=kbrd)
    vk.messages.send(user_id=buddy_id, message=final_phrase, random_id=0, keyboard=k_back)


def pickUpRightWordEnding(number, ones: str, two_three_four: str, rest: str, writeNumber1=True):
    phrase = f"{number} "
    if not writeNumber1 and number == 1:
        phrase = ''
    if number % 10 == 1 and number % 100 != 11:
        phrase += ones
    elif (number % 10 == 2 or number % 10 == 3 or number % 10 == 4) and not (12 <= number % 100 <= 14):
        phrase += two_three_four
    else:
        phrase += rest
    return phrase


def updateUserStatus(user_id, new_status):
    query = f"UPDATE users SET status = '{new_status}' WHERE vk_id = {user_id};"
    curr.execute(query)
    connection.commit()


def makeInlineKeyboardsFromList(array):
    result = {}
    kbrd = kb.VkKeyboard(inline=True)
    kbrd.add_button(array[0])
    for i in range(1, len(array)):
        if i % 6 == 0:
            result[kbrd.get_keyboard()] = [i - 5, i]
            kbrd = kb.VkKeyboard(inline=True)
            kbrd.add_button(array[i])
        else:
            kbrd.add_line()
            kbrd.add_button(array[i])
    result[kbrd.get_keyboard()] = [len(array) - (len(array) - 1) % 6, len(array)]
    return result


def getPhotosFromLastMessage(buddy_id, photos):
    lastMsg = vk.messages.getHistory(user_id=str(buddy_id), count=1)["items"][0]
    for attachment in lastMsg["attachments"]:
        if attachment["type"] == "photo":
            att = attachment["photo"]
            y_url = next(filter(lambda x: x['type'] == 'y', att['sizes']))['url']
            photos.append(y_url)


def addPhotoToAlbum(photo_link, album_id=main_album_id):
    with open("image_material.jpg", "wb") as file:
        file.write(requests.get(photo_link).content)
    upload_url = vk_me.photos.getUploadServer(album_id=album_id, group_id=group_id)['upload_url']
    to_save = requests.post(upload_url, files={'photo': open("image_material.jpg", "rb")}).json()
    picture = vk_me.photos.save(album_id=to_save['aid'], group_id=to_save['gid'], server=to_save['server'], photos_list=to_save['photos_list'], hash=to_save['hash'])[0]
    return f'photo{picture["owner_id"]}_{picture["id"]}'


def deletePhotosPermanently():
    connection_temp = psycopg2.connect(dbname=db_dbname,
                                       host=db_host,
                                       user=db_user,
                                       password=db_password)
    curr_temp = connection_temp.cursor()
    current_time = datetime.today()
    query = f"SELECT materials.id, materials.user_id, subject_id, caption, photo_link, date_of_lecture, adding_time, deletion_time, users.name, users.surname, users.profile_link, subjects.name " \
            f"FROM materials " \
            f"JOIN users ON materials.user_id = users.id " \
            f"JOIN subjects ON materials.subject_id = subjects.id " \
            f"WHERE deletion_time IS NOT NULL;"
    curr_temp.execute(query)
    result = curr_temp.fetchall()
    file = open("ScheduleLog.txt", "w")
    file.write(f"{current_time.strftime('%d.%m.%Y %H:%M:%S')}\n\n")
    ids_toDelete_fromDB = []
    photos_toDelete_fromVk = []
    for material in result:
        material_id, user_id, subject_id, caption, photo_link, date_of_lecture, adding_time, deletion_time, user_name, user_surname, profile_link, subject_name = material
        days_left = 30 - (current_time - deletion_time).days - 1
        if days_left < 0:
            days_left = "удален"
            ids_toDelete_fromDB.append(material_id)
            photos_toDelete_fromVk.append(photo_link)
        elif days_left == 0: days_left = "<1 дня"
        else: days_left = pickUpRightWordEnding(days_left, "день", "дня", "дней")
        file.write(f"Идентификатор материала: {material_id}")
        file.write(f"\nДо удаления навсегда: {days_left}")
        file.write(f"\nПользователь: {user_name} {user_surname} ({user_id})")
        file.write(f"\nСсылка на профиль: {profile_link}")
        file.write(f"\nПредмет: \"{subject_name}\" ({subject_id})")
        file.write(f"\nДата лекции: {date_of_lecture.strftime('%d.%m.%Y')}")
        file.write(f"\nВремя добавления: {adding_time.strftime('%d.%m.%y %H:%M:%S.%f')}")
        file.write(f"\nВремя удаления: {deletion_time.strftime('%d.%m.%y %H:%M:%S.%f')}")
        if caption: caption = "\"" + caption + "\""
        else: caption = "нет"
        file.write(f"\nФотография: {photo_link if photo_link else 'нет'}\nТекст: {caption}\n\n")
    file.close()
    query = f"DELETE FROM materials WHERE id = ANY('{{{', '.join(list(map(str, ids_toDelete_fromDB)))}}}');"
    curr_temp.execute(query)
    connection_temp.commit()
    curr_temp.close()
    connection_temp.close()
    for photo_link in photos_toDelete_fromVk:
        vk_me.photos.delete(owner_id=-group_id, photo_id=int(photo_link[photo_link.rfind('_') + 1:]))


def startProcess():
    Process(target=startSchedule, args=()).start()


def startSchedule():
    schedule.every().day.at("00:00").do(deletePhotosPermanently)
    while True:
        schedule.run_pending()
        sleep(60)


if __name__ == '__main__':
    startProcess()
    while True:
        try:
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.from_user and event.to_me:
                    anyPhotos = False
                    stickerId = None
                    for ii in range(1, len(event.attachments)):
                        if f"attach{ii}_type" not in event.attachments:
                            break
                        if event.attachments[f"attach{ii}_type"] == 'sticker':
                            stickerId = int(event.attachments[f"attach{ii}"])
                            break
                        if event.attachments[f"attach{ii}_type"] == 'photo':
                            anyPhotos = True
                            break
                    threading.Thread(process(event.user_id, event.text.replace('&quot;', '"'), anyPhotos, stickerId), daemon=True).start()
        except requests.exceptions.ConnectionError as ex:
            logg_message = f"Error: {str(ex)}\n{datetime.now().strftime('%d.%m.%Y, %H:%M:%S')}\n\n"
            with open("ErrorLog.txt", "a", encoding="utf-8") as f:
                f.write(logg_message)
            print(logg_message)
            sleep(1)
        except requests.exceptions.ReadTimeout as ex:
            logg_message = f"Error: {str(ex)}\n{datetime.now().strftime('%d.%m.%Y, %H:%M:%S')}\n\n"
            with open("ErrorLog.txt", "a", encoding="utf-8") as f:
                f.write(logg_message)
            print(logg_message)
            sleep(1)
