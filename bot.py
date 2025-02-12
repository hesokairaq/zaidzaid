from pyrogram import Client, filters
from pyrogram.types import Message
from youtube_dl import YoutubeDL
import subprocess
import os

# تهيئة البوت
app = Client("my_music_bot", bot_token="7952337935:AAHEpuXAlFi8iq1MsoNCi6ffUdLdEZ6OfBU")

# متغيرات لإدارة حالة التشغيل
is_playing = False
process = None

# أمر تشغيل الأغنية
@app.on_message(filters.command("شغل"))
def play_music(client: Client, message: Message):
    global is_playing, process

    # التأكد من عدم وجود تشغيل حالياً
    if is_playing:
        message.reply("⚠️ متسمع اكو اغنية جاي تشتغل!")
        return

    # الحصول على اسم الأغنية أو الرابط من الرسالة
    if len(message.command) < 2:
        message.reply("❗️ يرجى إرسال اسم الأغنية أو رابط اليوتيوب بعد الأمر /play.")
        return
    query = " ".join(message.command[1:])

    # تحميل الصوت من اليوتيوب
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'song.%(ext)s',
        'default_search': 'ytsearch',
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)
        if 'entries' in info:
            info = info['entries'][0]
        file_path = ydl.prepare_filename(info).replace(".webm", ".mp3")

    # تشغيل الأغنية في المكالمة الصوتية
    try:
        # الانضمام إلى المكالمة الصوتية
        chat_id = message.chat.id
        client.join_group_call(chat_id, file_path)

        # تشغيل الملف الصوتي باستخدام FFmpeg
        process = subprocess.Popen([
            "ffmpeg", "-i", file_path, "-f", "s16le", "-ac", "2", "-ar", "48000", "pipe:1"
        ], stdout=subprocess.PIPE)

        # إرسال الصوت إلى المكالمة
        client.send_audio(chat_id, process.stdout)
        is_playing = True
        message.reply(f"🎶 بدأ تشغيل: {info['title']}")
    except Exception as e:
        message.reply(f"❌ حدث خطأ: {e}")

# أمر إيقاف التشغيل
@app.on_message(filters.command("ايقاف"))
def stop_music(client: Client, message: Message):
    global is_playing, process

    # التأكد من وجود تشغيل حالياً
    if not is_playing:
        message.reply("⚠️ لا يوجد أغنية قيد التشغيل!")
        return

    # إيقاف التشغيل
    if process:
        process.terminate()
        process = None
    is_playing = False
    message.reply("⏹️ تم إيقاف التشغيل.")

    # مغادرة المكالمة الصوتية
    try:
        client.leave_group_call(message.chat.id)
    except Exception as e:
        message.reply(f"❌ حدث خطأ أثناء مغادرة المكالمة: {e}")

# تشغيل البوت
app.run()