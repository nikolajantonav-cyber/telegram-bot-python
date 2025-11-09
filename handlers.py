# handlers.py
import json
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

import db
from keyboards import main_kb, cook_button, next_step_btn
from helpers import fmt_card_short, chef_tip, plan_3_days

# ===== FSM для добавления рецепта =====
class AddRecipe(StatesGroup):
    title = State()
    desc = State()
    ings = State()
    steps = State()
    tmin = State()

def register_handlers(dp: Dispatcher):

    # /start + /ping
    @dp.message_handler(commands=["start"])
    async def start_cmd(m: types.Message):
        await m.answer("Привет, шеф! 👋 Выбирай действие на клавиатуре:", reply_markup=main_kb())

    @dp.message_handler(commands=["ping"])
    async def ping(m: types.Message):
        await m.answer("pong ✅")

    # --- Статистика
    @dp.message_handler(lambda x: x.text == "📊 Статистика")
    async def stats_cmd(m: types.Message):
        s = db.stats(m.from_user.id)
        await m.answer(f"📊 <b>Статистика</b>\nОбщих рецептов: <b>{s['common']}</b>\n"
                       f"Твоих рецептов: <b>{s['mine']}</b>\nЗапусков готовки: <b>{s['cooked']}</b>")

    # --- Все рецепты
    @dp.message_handler(lambda x: x.text == "📖 Все рецепты")
    async def list_all(m: types.Message):
        rows = db.all_for_user(m.from_user.id)
        if not rows:
            await m.answer("Пока пусто.")
            return
        msg = ["<b>Все доступные рецепты:</b>"] + [f"#{r['id']} — {r['title']} (⏱️ {r['cook_time_min']} мин, 🔥 {r['total_kcal']} ккал)" for r in rows]
        await m.answer("\n".join(msg))

    # --- Быстрое блюдо (<=15 мин)
    @dp.message_handler(lambda x: x.text == "⏱️ Быстрое блюдо")
    async def quick(m: types.Message):
        rows = db.all_for_user(m.from_user.id, quick_only=True)
        if not rows:
            await m.answer("Нет быстрых блюд.")
            return
        msg = ["<b>До 15 минут:</b>"] + [f"#{r['id']} — {r['title']} (⏱️ {r['cook_time_min']} мин)" for r in rows]
        await m.answer("\n".join(msg))

    # --- Поиск
    @dp.message_handler(lambda x: x.text == "🔍 Поиск рецептов")
    async def search_start(m: types.Message):
        await m.answer("Введи слово/фразу для поиска (название/ингредиенты):")

    @dp.message_handler(lambda x: x.text and x.text not in {
        "🔍 Поиск рецептов","➕ Добавить рецепт","👣 Учение рецептов","📖 Все рецепты",
        "🗑️ Удалить рецепты","📊 Статистика","🎲 Случайный рецепт","🧠 Совет от шефа",
        "🥗 Из ингредиентов?","⏱️ Быстрое блюдо","📅 Рацион на 3 дня","Похудение","Набор массы",
        "⭐ Избранное","🧾 Список покупок"
    }, content_types=types.ContentTypes.TEXT)
    async def search_query(m: types.Message):
        q = m.text.strip()
        rows = db.search(q, m.from_user.id)
        if not rows:
            await m.answer("Ничего не найдено 😕")
            return
        msg = ["<b>Нашёл рецепты:</b>"] + [f"#{r['id']} — {r['title']}" for r in rows]
        msg.append("\nОтправь номер рецепта, чтобы открыть карточку.")
        await m.answer("\n".join(msg))

    # --- Показ карточки по номеру
    @dp.message_handler(lambda x: x.text and x.text.isdigit())
    async def show_by_id(m: types.Message):
        rid = int(m.text)
        r = db.by_id(rid, m.from_user.id)
        if not r:
            await m.answer("Рецепт не найден.")
            return
        await m.answer(fmt_card_short(r), reply_markup=cook_button(r["id"]))

    # --- Случайный рецепт
    @dp.message_handler(lambda x: x.text == "🎲 Случайный рецепт")
    async def random_recipe(m: types.Message):
        r = db.random_recipe(m.from_user.id)
        if not r:
            await m.answer("Рецептов пока нет 🤷")
            return
        await m.answer(fmt_card_short(r), reply_markup=cook_button(r["id"]))

    # --- Пошаговая готовка (кнопка)
    @dp.callback_query_handler(lambda c: c.data.startswith("cook:"))
    async def cook_flow(c: types.CallbackQuery):
        _, rid, idx = c.data.split(":"); rid = int(rid); idx = int(idx)
        r = db.by_id(rid, c.from_user.id)
        if not r:
            await c.answer("Рецепт не найден.", show_alert=True); return
        steps = json.loads(r["steps_json"])
        if idx >= len(steps):
            db.log_cook(c.from_user.id, rid)
            await c.message.reply("✅ Готово! Приятного аппетита 😋")
            await c.answer(); return
        text = f"<b>{r['title']}</b>\nШаг {idx+1}/{len(steps)}:\n\n{steps[idx]}"
        await c.message.edit_text(text, reply_markup=next_step_btn(rid, idx+1))
        await c.answer()

    # --- Из ингредиентов
    @dp.message_handler(lambda x: x.text == "🥗 Из ингредиентов?")
    async def ingred_start(m: types.Message):
        await m.answer("Введи список через запятую (например: курица, рис, помидор)")

    @dp.message_handler(lambda x: "," in (x.text or ""))
    async def ingred_find(m: types.Message):
        words = [w.strip() for w in m.text.split(",") if w.strip()]
        rows = db.by_ingredients(words, m.from_user.id)
        if not rows:
            await m.answer("Ничего не подобрал 😕")
            return
        msg = ["<b>Подходит:</b>"] + [f"#{r['id']} — {r['title']}" for r in rows]
        await m.answer("\n".join(msg))

    # --- Совет от шефа
    @dp.message_handler(lambda x: x.text == "🧠 Совет от шефа")
    async def tip(m: types.Message):
        from helpers import chef_tip as tip_fn
        await m.answer(tip_fn())

    # --- Рацион на 3 дня
    @dp.message_handler(lambda x: x.text == "📅 Рацион на 3 дня")
    async def ration_start(m: types.Message):
        await m.answer("Выбери цель: Похудение / Набор массы")

    @dp.message_handler(lambda x: x.text in {"Похудение","Набор массы"})
    async def ration_goal(m: types.Message):
        await m.answer(plan_3_days(m.text), parse_mode="HTML")

    # --- Добавить рецепт (FSM)
    @dp.message_handler(lambda x: x.text == "➕ Добавить рецепт", state="*")
    async def add_start(m: types.Message, state: FSMContext):
        await state.finish()
        await AddRecipe.title.set()
        await m.answer("Название рецепта?")

    @dp.message_handler(state=AddRecipe.title)
    async def add_title(m: types.Message, state: FSMContext):
        await state.update_data(title=m.text.strip())
        await AddRecipe.desc.set()
        await m.answer("Краткое описание:")

    @dp.message_handler(state=AddRecipe.desc)
    async def add_desc(m: types.Message, state: FSMContext):
        await state.update_data(desc=m.text.strip())
        await AddRecipe.ings.set()
        await m.answer("Вводи ингредиенты по одному в формате:\nНазвание; граммы; ккал\nКогда закончишь — напиши: ГОТОВО")

    @dp.message_handler(state=AddRecipe.ings)
    async def add_ings(m: types.Message, state: FSMContext):
        txt = m.text.strip()
        data = await state.get_data()
        items = data.get("ings", [])
        if txt.lower() == "готово":
            if not items:
                await m.answer("Нужно добавить хотя бы один ингредиент.")
                return
            await state.update_data(ings=items)
            await AddRecipe.steps.set()
            await m.answer("Введи шаги приготовления (каждый с новой строки). Когда закончишь — отправь: ГОТОВО")
            return
        try:
            name, grams, kcal = [p.strip() for p in txt.split(";")]
            grams = float(grams.replace(",", "."))
            kcal = float(kcal.replace(",", "."))
            items.append({"name": name, "grams": grams, "kcal": kcal})
            await state.update_data(ings=items)
            await m.answer("Добавлено ✅. Следующий или «ГОТОВО».")
        except Exception:
            await m.answer("Формат не распознан. Пример: Курица; 150; 240")

    @dp.message_handler(state=AddRecipe.steps)
    async def add_steps(m: types.Message, state: FSMContext):
        if m.text.strip().lower() == "готово":
            data = await state.get_data()
            if not data.get("steps_list"):
                await m.answer("Добавь хотя бы один шаг.")
                return
            await AddRecipe.tmin.set()
            await m.answer("Сколько минут готовить (целое число)?")
            return
        steps = (await state.get_data()).get("steps_list", [])
        for line in m.text.splitlines():
            s = line.strip()
            if s: steps.append(s)
        await state.update_data(steps_list=steps)
        await m.answer("Шаг(и) добавлен(ы). Добавь ещё или «ГОТОВО».")

    @dp.message_handler(state=AddRecipe.tmin)
    async def add_tmin(m: types.Message, state: FSMContext):
        try:
            tmin = int(m.text.strip())
            data = await state.get_data()
            db.add_user_recipe(
                m.from_user.id, data["title"], data["desc"],
                data["ings"], data["steps_list"], tmin
            )
            await state.finish()
            await m.answer("✅ Рецепт сохранён! Найти его можно через поиск или список.", reply_markup=main_kb())
        except Exception:
            await m.answer("Нужно целое число минут.")

    # --- Удалить рецепт (только свои)
    @dp.message_handler(lambda x: x.text == "🗑️ Удалить рецепты")
    async def del_hint(m: types.Message):
        await m.answer("Отправь ID рецепта, который ты хочешь удалить (только свои).")

    @dp.message_handler(lambda x: x.text and x.text.isdigit(), content_types=types.ContentTypes.TEXT)
    async def delete_by_id(m: types.Message):
        rid = int(m.text)
        ok = db.delete_user_recipe(rid, m.from_user.id)
        if ok:
            await m.answer("🗑️ Удалено.")
        else:
            await m.answer("Можно удалять только <b>свои</b> рецепты.")

    # --- Учение (подсказка)
    @dp.message_handler(lambda x: x.text == "👣 Учение рецептов")
    async def teach(m: types.Message):
        await m.answer("Открой рецепт по номеру и нажми «🍳 Хочу готовить» — начнётся пошаговая инструкция.")


    @dp.message_handler(lambda x: x.text == "⭐ Избранное")
    async def fav(m: types.Message):
        await m.answer("⭐ Избранное: пока простая заглушка. Можем подключить сохранение в БД по кнопке «В избранное».")

    @dp.message_handler(lambda x: x.text == "🧾 Список покупок")
    async def shop(m: types.Message):
        await m.answer("🧾 Список покупок: скопируй ингредиенты сюда — я соберу список (можно доработать под кнопки и БД).")

    # --- Фоллбэк (в самом конце!)
    @dp.message_handler()
    async def fallback(m: types.Message):
        await m.answer("Выбери действие на клавиатуре 👇", reply_markup=main_kb())