import os
import datetime
import telebot
import google.generativeai as genai
from dotenv import load_dotenv

# Carga limpia usando override=True para garantizar que se lean cambios en .env
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(base_dir, ".env"), override=True)

# Configuración
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN_FRACTAL"))

# Permitir múltiples usuarios (separados por coma)
# Permitir múltiples usuarios (separados por coma)
raw_ids = os.getenv("MY_USER_ID", "")
# EMERGENCY HARDCODE: Force Luca's ID to be accepted
ALLOWED_IDS = [6527908321, 8224826198]
print(f"DEBUG RAW: '{raw_ids}' -> ALLOWED: {ALLOWED_IDS}", flush=True)
ADMIN_ID = ALLOWED_IDS[0] if ALLOWED_IDS else None

# Usamos el nombre exacto de tu lista
model = genai.GenerativeModel('gemini-flash-latest')

def save_to_inbox(content):
    inbox_dir = os.path.join(base_dir, "inbox")
    if not os.path.exists(inbox_dir):
        os.makedirs(inbox_dir)
    
    # FULL STORAGE: Guardamos todo el contenido como pidió el usuario
    lean_content = content
    
    # Buscar el siguiente número disponible
    existing_files = [f for f in os.listdir(inbox_dir) if f.startswith("idea_") and f.endswith(".md")]
    numbers = []
    for f in existing_files:
        try:
            num = int(f.replace("idea_", "").replace(".md", ""))
            numbers.append(num)
        except ValueError:
            continue
    
    next_num = max(numbers) + 1 if numbers else 1
    file_name = f"idea_{next_num}.md"
    file_path = os.path.join(inbox_dir, file_name)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(lean_content)
    
    # Sincronización automática (Git Push) - NO BLOQUEANTE
    try:
        import subprocess
        sync_script = os.path.join(base_dir, "auto_sync.sh")
        if os.path.exists(sync_script):
            subprocess.Popen(["/bin/bash", sync_script], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL,
                           start_new_session=True)
        else:
            # Fallback directo
            subprocess.Popen(
                f"cd '{base_dir}' && git add inbox/ && git commit -m 'Auto-sync' && git push origin main",
                shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True)
    except Exception as e:
        print(f"Error en sincronización Git: {e}")
        
    return file_path


@bot.message_handler(commands=['update_server'])
def update_server(m):
    if m.from_user.id != ADMIN_ID:
        return
    bot.reply_to(m, "🚀 Iniciando actualización del servidor...")
    try:
        import subprocess
        from pathlib import Path
        
        # Script de actualización que se ejecuta en segundo plano
        update_script = f"""#!/bin/bash
cd "{base_dir}"
git pull
sudo systemctl restart bot-fractal bot-air
"""
        
        # Crear archivo temporal con el script
        script_path = Path(base_dir) / "update_temp.sh"
        with open(script_path, 'w') as f:
            f.write(update_script)
        
        # Dar permisos de ejecución
        os.chmod(script_path, 0o755)
        
        # Ejecutar en segundo plano
        subprocess.Popen(
            ["/bin/bash", str(script_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        bot.send_message(
            m.chat.id,
            "✅ Actualización iniciada.\n\n"
            "📥 Git pull ejecutándose...\n"
            "🔄 Servicios reiniciándose...\n\n"
            "El bot podría desconectarse brevemente."
        )
        logger.info(f"Update server iniciado por admin {m.from_user.id}")
        
    except Exception as e:
        bot.reply_to(m, f"❌ Error: {e}")

# FIX CRÍTICO: Agregar content_types para aceptar archivos, fotos, etc.
@bot.message_handler(func=lambda m: m.from_user.id in ALLOWED_IDS, content_types=['audio', 'photo', 'voice', 'video', 'document', 'text', 'location', 'contact', 'sticker'])
def handle(m):
    try:
        # Si es un archivo/foto, intentar usar el caption si existe
        user_input = m.text or m.caption
        
        if not user_input:
            # Si mandan un archivo sin caption, responder algo genérico o analizar la imagen (futuro)
            bot.reply_to(m, "📂 Archivo recibido. Guardando referencia...")
            user_input = f"[Archivo recibido: {m.document.file_name if m.document else 'Media'}]"

        # Generación directa
        res = model.generate_content(user_input)
        txt = res.text
        
        # Guardar en inbox
        file_path = None
        try:
            file_path = save_to_inbox(txt)
            # FAILSAFE: Enviar también el archivo generado por Telegram
            if file_path and os.path.exists(file_path):
                with open(file_path, 'rb') as doc:
                    bot.send_document(m.chat.id, doc, caption="📂 Copia de seguridad del archivo generado")
        except Exception as e:
            print(f"Error guardando/enviando: {e}")
        
        # Paginación para Telegram
        for i in range(0, len(txt), 4000):
            bot.send_message(m.chat.id, txt[i:i+4000])
    except Exception as e:
        bot.reply_to(m, f"Error: {e}")

# DEBUG: Handler para usuarios NO autorizados
@bot.message_handler(func=lambda m: True, content_types=['audio', 'photo', 'voice', 'video', 'document', 'text', 'location', 'contact', 'sticker'])
def handle_unauthorized(m):
    id = m.from_user.id
    print(f"⚠️ Acceso denegado o ID no reconocido: {id} en ALLOWED? {id in ALLOWED_IDS}", flush=True)

print(f"Bot activo. IDs permitidos: {ALLOWED_IDS}", flush=True)
bot.remove_webhook()
bot.polling()
