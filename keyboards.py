import vk_api.keyboard as kb


kbrd = kb.VkKeyboard(one_time=True)
kbrd.add_button("Выбрать предмет", color='primary')
kbrd.add_line()
kbrd.add_button("Удалить", color='primary')
kbrd.add_button("Добавить", color='primary')
kbrd.add_line()
kbrd.add_button("Список предметов", color='primary')
k_main_menu = kbrd.get_keyboard()


def k_in_subject__createFor(subject_name):
    assert(subject_name.strip() != "")
    kbrd = kb.VkKeyboard(one_time=True)
    kbrd.add_button(f'"{subject_name}"')
    kbrd.add_line()
    kbrd.add_button("Добавить в определенный день", color='primary')
    kbrd.add_line()
    kbrd.add_button("Посмотреть материалы", color='primary')
    kbrd.add_line()
    kbrd.add_button("Восстановить", color='primary')
    kbrd.add_button("Удалить", color='primary')
    kbrd.add_line()
    kbrd.add_button("Редактировать", color='primary')
    kbrd.add_line()
    kbrd.add_button("Главное меню")
    kbrd.add_button("Другой предмет")
    return kbrd.get_keyboard()


kbrd = kb.VkKeyboard(one_time=True)
kbrd.add_button("Просмотр материалов")
kbrd.add_line()
kbrd.add_button("За прошлый раз", color='primary')
kbrd.add_button("За сегодня", color='primary')
kbrd.add_line()
kbrd.add_button("Сразу все", color='primary')
kbrd.add_line()
kbrd.add_button("Выбрать дату из списка", color='primary')
kbrd.add_line()
kbrd.add_button("Назад")
k_show_materials = kbrd.get_keyboard()

kbrd = kb.VkKeyboard(one_time=True)
kbrd.add_button("Две недели назад", color='primary')
kbrd.add_button("Неделю назад", color='primary')
kbrd.add_line()
kbrd.add_button("Ввести дату/выбрать из списка", color='primary')
kbrd.add_line()
kbrd.add_button("Меню предмета")
k_add_materials = kbrd.get_keyboard()

kbrd = kb.VkKeyboard(one_time=True)
kbrd.add_button("НИНАДА", color='negative')
kbrd.add_button("Да", color='positive')
k_confirmation_delete_subject = kbrd.get_keyboard()

kbrd = kb.VkKeyboard(one_time=True)
kbrd.add_button("Назад")
k_back = kbrd.get_keyboard()


def k_add_to_specific_day__create(dayIsEmpty):
    kbrd = kb.VkKeyboard(one_time=True)
    if not dayIsEmpty:
        kbrd.add_button("Добавить в определенное место", color='primary')
        kbrd.add_line()
    kbrd.add_button("Добавить в другой день", color='primary')
    kbrd.add_line()
    kbrd.add_button("Главное меню")
    kbrd.add_button("Меню предмета")
    return kbrd.get_keyboard()


kbrd = kb.VkKeyboard(one_time=True)
kbrd.add_button("Добавить в другой день", color='primary')
kbrd.add_line()
kbrd.add_button("Назад")
kbrd.add_line()
kbrd.add_button("Главное меню")
kbrd.add_button("Меню предмета")
k_add_to_specific_day_to_specific_place = kbrd.get_keyboard()

kbrd = kb.VkKeyboard(one_time=True)
kbrd.add_button("Главное меню")
k_back_to_main_menu = kbrd.get_keyboard()

kbrd = kb.VkKeyboard(one_time=True)
kbrd.add_button("Удалить последнее добавление", color='primary')
kbrd.add_line()
kbrd.add_button("Удалить что-то другое", color='primary')
kbrd.add_line()
kbrd.add_button("Удалить все в этом предмете", color='primary')
kbrd.add_line()
kbrd.add_button("Назад")
k_delete_materials = kbrd.get_keyboard()

kbrd = kb.VkKeyboard(one_time=True)
kbrd.add_button("Восстановить последнее удаление", color='primary')
kbrd.add_line()
kbrd.add_button("Восстановить что-то другое", color='primary')
kbrd.add_line()
kbrd.add_button("Назад")
k_recover_materials = kbrd.get_keyboard()

kbrd = kb.VkKeyboard(one_time=True)
kbrd.add_button("Нееее", color='negative')
kbrd.add_button("Удаляй!", color='positive')
k_confirmation_delete_all_materials = kbrd.get_keyboard()

kbrd = kb.VkKeyboard(one_time=True)
kbrd.add_button("Удалить все", color='primary')
kbrd.add_line()
kbrd.add_button("Назад")
k_choose_materials_to_delete = kbrd.get_keyboard()

kbrd = kb.VkKeyboard(one_time=True)
kbrd.add_button("Восстановить все", color='primary')
kbrd.add_line()
kbrd.add_button("Назад")
k_choose_materials_to_recover = kbrd.get_keyboard()

kbrd = kb.VkKeyboard(one_time=True)
kbrd.add_button("Редактирование материалов")
kbrd.add_line()
kbrd.add_button("Предоследний", color='primary')
kbrd.add_button("Последний", color='primary')
kbrd.add_line()
kbrd.add_button("Последний добавленный материал", color='primary')
kbrd.add_line()
kbrd.add_button("Выбрать из списка", color='primary')
kbrd.add_line()
kbrd.add_button("Назад")
k_edit_materials = kbrd.get_keyboard()

kbrd = kb.VkKeyboard(one_time=True)
kbrd.add_button("Редактировать другой материал", color='primary')
kbrd.add_line()
kbrd.add_button("Главное меню")
kbrd.add_button("Меню предмета")
k_edit_specific_material = kbrd.get_keyboard()


no2dow = {
    0: "понедельник",
    1: "вторник",
    2: "среда",
    3: "четверг",
    4: "пятница",
    5: "суббота",
    6: "воскресенье",
}

no2_v_dow = {
    0: "в понедельник",
    1: "во вторник",
    2: "в среду",
    3: "в четверг",
    4: "в пятницу",
    5: "в субботу",
    6: "в воскресенье",
}

no2dow_short = {
    0: "пн",
    1: "вт",
    2: "ср",
    3: "чт",
    4: "пт",
    5: "сб",
    6: "вс",
}

no2dow_gen = {
    0: "понедельника",
    1: "вторника",
    2: "среды",
    3: "четверга",
    4: "пятницы",
    5: "субботы",
    6: "воскресенья",
}
