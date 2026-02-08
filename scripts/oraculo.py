
import os
import requests
import json
import sys
import datetime
import re

# El Oraculo detecta donde estas parado para usar la memoria local
API_KEY = os.getenv("GOOGLE_API_KEY")
current_dir = os.getcwd()

# Aseguramos que PegasoMemory use el DIR actual
from pegaso_memory import PegasoMemory
memory = PegasoMemory() 

MEMORY_DIR = memory.MEMORY_DIR
THREADS_DIR = memory.THREADS_DIR

if not API_KEY:
    print("❌ Error: No se encontro GOOGLE_API_KEY.")
    sys.exit(1)

def diagnostico_modelos():
    print("🔍 Diagnosticando modelos disponibles...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print("✅ Modelos encontrados:")
            for m in models:
                print(f"  - {m['name']}")
            return True
        else:
            print(f"❌ Error de Diagnostico ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error de conexion: {e}")
        return False

def chat_oraculo():
    # Este es el nombre exacto que aparecio en tu lista y suele tener cuota libre
    model_to_use = "gemini-flash-latest" 

    print(f"--- 🦅 ORACULO PEGASO (Modelo: {model_to_use}) ---")
    print("Escribe 'salir' para terminar.")
    
    full_transcript = ""

    while True:
        raw_input = input(">> Operador: ")
        user_input = raw_input.strip()
        
        # Volvemos a los comandos simples
        if user_input.lower() in ['salir', 'exit', 'quit']:
            break
        
        if not user_input: continue
        # Usamos v1beta que es donde vimos la lista
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_to_use}:generateContent?key={API_KEY}"
        headers = {'Content-Type': 'application/json'}
        payload = {"contents": [{"parts": [{"text": user_input}]}]}
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                print(f"❌ Error {response.status_code}: {response.text}")
                continue
            
            data = response.json()
            answer = data['candidates'][0]['content']['parts'][0]['text']
            print(f"\n>> Gemini: {answer}\n")
            full_transcript += f"Operador: {user_input}\nGemini: {answer}\n\n"
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            break

    # Al salir, guardamos la charla INTEGRAL
    if full_transcript:
        print("💾 Sincronizando memoria activa...")
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(THREADS_DIR, f"{timestamp}_Charla.md")
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# Registro de Charla - {timestamp}\n\n")
            f.write(full_transcript)
        
        # GESTION AUTOMATICA: Si hay mas de 20, archivamos lo viejo solo
        memory.archive_old_threads(limit=20)
        
        # Sincronizamos con Git
        memory.sync_git()
        print(f"✅ Memoria actualizada y archivada.")

if __name__ == "__main__":
    chat_oraculo()
