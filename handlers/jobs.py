from aiogram import Router, F, types
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from database.models import db
from config import JOB_POSITIONS, ADMIN_IDS
from datetime import datetime

router = Router()


class JobStates(StatesGroup):
    waiting_name = State()
    waiting_age = State()
    waiting_experience = State()
    waiting_about = State()


@router.callback_query(F.data == "mode_jobs")
async def show_jobs_menu(call: CallbackQuery):
    builder = InlineKeyboardBuilder()
    for i, job in enumerate(JOB_POSITIONS):
        builder.button(
            text=f"{job['title']} — {job['city']}",
            callback_data=f"jobinfo_{i}"
        )
    builder.button(text="📝 ОТПРАВИТЬ АНКЕТУ", callback_data="job_apply")
    builder.button(text="◀️ СМЕНИТЬ РЕЖИМ", callback_data="main_menu")
    builder.adjust(1)
    
    await call.message.edit_text(
        "🧪 <b>WHITE MYSTIC LAB — ВАКАНСИИ</b>\n\n"
        "🔥 <b>Актуальные позиции:</b>\n"
        "• 🧪 Лаборант — от 300 000 ₽\n"
        "• 📦 Кладмен — от 150 000 ₽\n"
        "• 💪 Охрана — от 250 000 ₽\n"
        "• 🏭 Складмен — от 180 000 ₽\n"
        "• 👑 Куратор — от 350 000 ₽\n\n"
        "Выберите вакансию или отправьте анкету.\n"
        "Или используйте команду /anketa",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("jobinfo_"))
async def show_job_info(call: CallbackQuery):
    idx = int(call.data.split("_")[1])
    
    if idx >= len(JOB_POSITIONS):
        await call.answer("Вакансия не найдена")
        return
    
    job = JOB_POSITIONS[idx]
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 ОТКЛИКНУТЬСЯ", callback_data=f"jobapply_{idx}")
    builder.button(text="◀️ НАЗАД", callback_data="mode_jobs")
    builder.adjust(1)
    
    await call.message.edit_text(
        f"{job['title']}\n\n"
        f"📝 <b>Описание:</b>\n{job['desc']}\n\n"
        f"💰 <b>Зарплата:</b> {job['salary']}\n"
        f"📍 <b>Город:</b> {job['city']}\n"
        f"📋 <b>Требования:</b> {job['requirements']}\n\n"
        f"Нажмите «ОТКЛИКНУТЬСЯ» чтобы заполнить анкету.",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "job_apply")
async def apply_any_job(call: CallbackQuery, state: FSMContext):
    await state.update_data(job_idx=None)
    await state.set_state(JobStates.waiting_name)
    
    await call.message.edit_text(
        "📝 <b>АНКЕТА СОТРУДНИКА</b>\n\n"
        "Шаг 1/4\n\n"
        "<b>Введите ваше имя или псевдоним:</b>\n\n"
        "Отправьте сообщение с именем.",
        reply_markup=InlineKeyboardBuilder().button(
            text="❌ ОТМЕНА", callback_data="mode_jobs"
        ).as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("jobapply_"))
async def apply_specific_job(call: CallbackQuery, state: FSMContext):
    idx = int(call.data.split("_")[1])
    await state.update_data(job_idx=idx)
    await state.set_state(JobStates.waiting_name)
    
    await call.message.edit_text(
        "📝 <b>АНКЕТА СОТРУДНИКА</b>\n\n"
        "Шаг 1/4\n\n"
        "<b>Введите ваше имя или псевдоним:</b>\n\n"
        "Отправьте сообщение с именем.",
        reply_markup=InlineKeyboardBuilder().button(
            text="❌ ОТМЕНА", callback_data="mode_jobs"
        ).as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.message(Command("anketa"))
async def cmd_anketa(message: Message, state: FSMContext):
    """Команда для начала анкеты"""
    await state.update_data(job_idx=None)
    await state.set_state(JobStates.waiting_name)
    await message.answer(
        "📝 <b>АНКЕТА СОТРУДНИКА</b>\n\n"
        "Шаг 1/4\n\n"
        "<b>Введите ваше имя или псевдоним:</b>\n\n"
        "Отправьте сообщение с именем.",
        parse_mode="HTML"
    )


@router.message(JobStates.waiting_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(JobStates.waiting_age)
    
    await message.answer(
        "📝 Шаг 2/4\n\n"
        "<b>Введите ваш возраст:</b>",
        parse_mode="HTML"
    )


@router.message(JobStates.waiting_age)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(JobStates.waiting_experience)
    
    await message.answer(
        "📝 Шаг 3/4\n\n"
        "<b>Опишите ваш опыт работы (кратко):</b>",
        parse_mode="HTML"
    )


@router.message(JobStates.waiting_experience)
async def process_experience(message: Message, state: FSMContext):
    await state.update_data(experience=message.text)
    await state.set_state(JobStates.waiting_about)
    
    await message.answer(
        "📝 Шаг 4/4\n\n"
        "<b>Расскажите о себе. Почему мы должны взять именно вас?</b>",
        parse_mode="HTML"
    )


@router.message(JobStates.waiting_about)
async def process_about(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    
    job_idx = data.get('job_idx')
    if job_idx is not None and job_idx < len(JOB_POSITIONS):
        job_title = JOB_POSITIONS[job_idx]['title']
    else:
        job_title = "Не указана"
    
    # Сохраняем анкету
    try:
        db.insert('job_applications', {
            'user_id': message.from_user.id,
            'name': data['name'],
            'age': data['age'],
            'experience': data['experience'],
            'about': message.text,
            'position': job_title,
            'username': message.from_user.username or '',
            'created_at': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Error saving application: {e}")
    
    # Уведомляем админов
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(
                admin_id,
                f"📝 <b>НОВАЯ АНКЕТА!</b>\n\n"
                f"👤 {data['name']}, {data['age']} лет\n"
                f"📋 Вакансия: {job_title}\n"
                f"💼 Опыт: {data['experience']}\n"
                f"📝 О себе: {message.text[:200]}\n"
                f"🆔 User: <code>{message.from_user.id}</code>\n"
                f"👤 @{message.from_user.username}",
                reply_markup=InlineKeyboardBuilder().button(
                    text="📩 НАПИСАТЬ", url=f"tg://user?id={message.from_user.id}"
                ).as_markup(),
                parse_mode="HTML"
            )
        except:
            pass
    
    await message.answer(
        "✅ <b>АНКЕТА ОТПРАВЛЕНА!</b>\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📅 Возраст: {data['age']}\n"
        f"📋 Вакансия: {job_title}\n\n"
        "🔍 <b>Ваша анкета на рассмотрении.</b>\n"
        "Куратор свяжется с вами в ближайшее время.",
        parse_mode="HTML"
    )
