import asyncio
import html
import os
import threading

from flask import Flask
from telethon import Button, TelegramClient, events, utils
from telethon.errors import AuthKeyDuplicatedError
from telethon.sessions import StringSession


# ============================================================
# إعدادات حساب Telegram واحد من Environment Variables
# ============================================================


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"متغير البيئة المطلوب غير موجود: {name}")
    return value


try:
    API_ID = int(required_env("API_ID"))
except ValueError as exc:
    raise RuntimeError("قيمة API_ID يجب أن تكون رقمًا صحيحًا") from exc

API_HASH = required_env("API_HASH")
SESSION_STRING = required_env("SESSION_STRING")

# يمكن تركها كما هي؛ القيمة الافتراضية هي الوجهة المطلوبة.
ALERT_TARGET = os.environ.get("ALERT_TARGET", "ha88664422").strip().lstrip("@")

# معرّف الوجهة المطلوبة: نستخدم الشكلين لتجنب إعادة معالجة رسائلها.
TARGET_CHAT_ID = 3958977817
TARGET_CHAT_ID_FULL = -1003958977817
TARGET_CHAT_USERNAME = ALERT_TARGET.lower()


# ============================================================
# التصفية غير المشددة مثل النسخة الأخيرة
# ============================================================

KEYWORDS = ["يساعدني", "يحل", "يحِل", "يسوي"]

# الرسائل التي تحتوي على إحدى هذه العبارات لا تُحوّل.
EXCLUDED = [
    "بأسعار", "بسعر", "٩٠", "١٢٠", "٦٠", "80", "90", "60", "120", "روم", "باسعار", "للتواصل", "مشكلتها", "مشكلتي",
    "تخصص", "التخصص", "مشكلة", "المشكله", "تواصل واتس", "التواصل",
    "للحجز", "خصم خاص", "عرض خاص", "تدفعون لهم بعد", "الدفع بعد",
    "نقدم لك", "نقدم لكم", "خدماتنا", "خدمة تعليمية", "تواصل الآن",
    "تواصل معنا", "تواصلوا معنا", "يحلف", "إذا تبون", "مايسوي",
    "ذي تسوي", "ذا يسوي", "انا اسوي", "يبي", "اعرف حد", "اعرف واحد",
    "الموزونات", "المنصة", "الموازونة", "انقبل", "التحويل", "رغبات",
    "الرغبات", "قبول", "القبول", "يسوي له", "هذا يحل", "اسوي له",
    "يحتاج إلى حد", "يحتاج حد", "اعرف شخص", "القيد", "قيد", "منصه",
    "اذا تبون", "يحليلك", "موراضي", "يحلوين", "يحلليلك", "نقدم",
    "أقدم", "اقدم", "شسوي", "ما يسوي", "مشكله", "الدعم", "المنصه",
    "الاستيب", "الستيب", "ستيب", "للقبول", "بالقبول", "تبي",
    "الذي حابب",
]


# ============================================================
# Flask وHealth Check
# ============================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "I am alive!", 200


@app.route("/health")
def health():
    return "OK", 200


def run_flask_app() -> None:
    port = int(os.environ.get("PORT", "10000"))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,
    )


# ============================================================
# دوال التصفية والروابط
# ============================================================


def contains_keyword(text: str) -> bool:
    if not text:
        return False

    normalized = text.lower()
    if any(keyword.lower() in normalized for keyword in KEYWORDS):
        return True

    abgha_phrases = [
        "ابغى حد", "أبغى حد", "ابغى احد", "أبغى احد",
        "ابغى خصوصي", "أبغى خصوصي", "ابغى شخص", "أبغى شخص",
        "ابغى واحد", "أبغى واحد",
    ]
    if any(phrase.lower() in normalized for phrase in abgha_phrases):
        return True

    yusaed_phrases = [
        "احد يساعد", "أحد يساعد", "من يساعد", "حد يساعد", "شخص يساعد",
    ]
    return any(phrase.lower() in normalized for phrase in yusaed_phrases)


def build_chat_link(chat, chat_id, message_id):
    if getattr(chat, "username", None):
        return f"https://t.me/{chat.username}/{message_id}"

    try:
        chat_id_text = str(chat_id)
        if chat_id_text.startswith("-100"):
            short_id = chat_id_text[4:]
            return f"https://t.me/c/{short_id}/{message_id}"
    except Exception:
        pass

    return None


def is_target_chat(event, chat) -> bool:
    if event.chat_id in (TARGET_CHAT_ID, TARGET_CHAT_ID_FULL):
        return True

    chat_username = getattr(chat, "username", None)
    return bool(
        chat_username
        and chat_username.lower().lstrip("@") == TARGET_CHAT_USERNAME
    )


# ============================================================
# معالجة الرسائل
# ============================================================


client = TelegramClient(
    StringSession(SESSION_STRING),
    API_ID,
    API_HASH,
)


@client.on(events.NewMessage(incoming=True))
async def handler(event):
    # تجاهل الوجهة قبل أي معالجة حتى لا يعيد البوت رسائله إلى نفسه.
    if event.chat_id in (TARGET_CHAT_ID, TARGET_CHAT_ID_FULL):
        return

    try:
        text = event.message.message or ""

        # التصفية غير المشددة: كلمة مفتاحية، ومن دون كلمة مستبعدة.
        if not text:
            return
        if not contains_keyword(text):
            return
        if any(word.lower() in text.lower() for word in EXCLUDED):
            return

        chat = await event.get_chat()
        if is_target_chat(event, chat):
            return

        sender = await event.get_sender()
        sender_name = utils.get_display_name(sender) if sender else "مجهول"

        if sender and getattr(sender, "username", None):
            sender_user_field = f"@{sender.username}"
        elif sender and getattr(sender, "id", None):
            sender_user_field = sender_name
        else:
            sender_user_field = "لا يوجد"

        chat_title = (
            getattr(chat, "title", None)
            or getattr(chat, "first_name", None)
            or "المجموعة"
        )
        chat_id = event.chat_id
        chat_link = build_chat_link(chat, chat_id, event.message.id)
        sender_id = (
            sender.id
            if sender and getattr(sender, "id", None)
            else "غير معروف"
        )

        header = (
            "📢 رسالة مهمة:\n\n"
            f"👤 المرسل: {html.escape(sender_name)}\n"
            f"🆔  : tg://openmessage?user_id={sender_id}\n"
            f"🔗 اليوزر : {html.escape(sender_user_field)}\n"
            f"📍 المجموعة: {html.escape(chat_title)}\n"
            f"🔗 رابط الرسالة: "
            f"{chat_link if chat_link else 'لا يمكن توليد رابط عام'}\n"
            "— الرسالة محوله 👇 —"
        )

        buttons = []
        if chat_link:
            buttons.append([Button.url("🔗 الانتقال إلى الرسالة", chat_link)])

        await client.send_message(ALERT_TARGET, header, buttons=buttons)

        try:
            await client.forward_messages(ALERT_TARGET, event.message)
        except Exception as forward_error:
            print(f"تعذر إعادة التوجيه: {forward_error!r}")
            await client.send_message(
                ALERT_TARGET,
                "💬 (لم أستطع إعادة توجيه الرسالة — أدرج النص أدناه):\n\n"
                + text,
            )

    except Exception as error:
        # خطأ رسالة واحدة لا يوقف البوت.
        print(f"خطأ في معالجة الرسالة: {error!r}")


async def run_client() -> None:
    retry_delay = 15

    while True:
        try:
            print("محاولة الاتصال بحساب Telegram...")
            await client.start()
            print("Userbot started — listening...")
            await client.run_until_disconnected()
            print("انقطع الاتصال بحساب Telegram")

        except AuthKeyDuplicatedError as error:
            print(
                "فشل نهائي بسبب AuthKeyDuplicatedError: "
                f"{error!r}. أنشئ SESSION_STRING جديدة للحساب."
            )
            return

        except Exception as error:
            print(
                f"خطأ مستقل: {error!r}. "
                f"ستتم إعادة المحاولة بعد {retry_delay} ثانية."
            )

        finally:
            try:
                if client.is_connected():
                    await client.disconnect()
            except Exception as disconnect_error:
                print(f"تعذر إغلاق الاتصال القديم: {disconnect_error!r}")

        await asyncio.sleep(retry_delay)


async def main() -> None:
    flask_thread = threading.Thread(
        target=run_flask_app,
        name="flask-health-server",
        daemon=True,
    )
    flask_thread.start()

    print("سيتم تشغيل بوت الحساب الواحد بشكل مستقل...")
    await run_client()

    # إبقاء Flask حيًا حتى لو توقفت جلسة Telegram.
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("تم إيقاف البرنامج يدويًا")
