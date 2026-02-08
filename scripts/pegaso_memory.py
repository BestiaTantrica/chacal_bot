
import os
import json
import datetime
import re

# El motor ahora busca 'memory' en la carpeta donde estas parado
current_dir = os.getcwd()
MEMORY_DIR = os.path.join(current_dir, "memory")
THREADS_DIR = os.path.join(MEMORY_DIR, "threads")
ARCHIVE_DIR = os.path.join(MEMORY_DIR, "archive")
MANIFEST_PATH = os.path.join(MEMORY_DIR, "MANIFEST.md")
PROMPT_LLAVE_PATH = os.path.join(MEMORY_DIR, "PROMPT_LLAVE.md")

class PegasoMemory:
    def __init__(self):
        for d in [THREADS_DIR, ARCHIVE_DIR]:
            if not os.path.exists(d):
                os.makedirs(d)

    def distill(self, raw_text_path):
        """Lee una charla cruda y extrae puntos clave."""
        if not os.path.exists(raw_text_path):
            print(f"❌ No se encuentra el archivo: {raw_text_path}")
            return

        with open(raw_text_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Lógica simple de extracción de puntos clave (Heuristicas)
        # Podríamos usar una IA para esto, pero buscamos algo local y rápido.
        lines = content.split('\n')
        title = lines[0][:50] if lines else "Conversacion_Sin_Titulo"
        
        # Guardamos el hilo
        self.log_thread(title, content, tags=["distilled"])

    def log_thread(self, title, content, tags=[]):
        safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
        filename = f"{datetime.date.today()}_{safe_title}.md"
        filepath = os.path.join(THREADS_DIR, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n")
            f.write(f"Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Tags: {', '.join(tags)}\n\n")
            f.write("## RESUMEN DE LA CHARLA\n")
            f.write(content[:1000] + "\n... [Resto del hilo guardado en archivo] ...")
        
        print(f"Hilo destilado y guardado: {filename}")
        self.update_all()

    def update_all(self):
        self.update_manifest()
        self.build_master_prompt()

    def update_manifest(self):
        content = "# 🦅 MANIFIESTO DE MEMORIA PEGASO\n\n"
        content += f"Ultima actualizacion: {datetime.datetime.now()}\n\n"
        content += "## HISTORIAL RECIENTE\n"
        
        threads = sorted(os.listdir(THREADS_DIR), reverse=True)[:10]
        for t in threads:
            content += f"- {t}\n"

        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            f.write(content)

    def build_master_prompt(self):
        """Genera el PROMPT_LLAVE.md basado en el estado actual."""
        status_path = os.path.join(MEMORY_DIR, "STATUS.md")
        status_content = ""
        if os.path.exists(status_path):
            with open(status_path, "r", encoding="utf-8") as f:
                status_content = f.read()

        prompt = f"""# PROTOCOLO PEGASO: LLAVE DE ACTIVACION DE MEMORIA

**FECHA DE GENERACION:** {datetime.date.today()}
**ESTADO:** OPERACIONAL

{status_content}

---
## ULTIMOS HILOS DE CONOCIMIENTO
"""
        threads = sorted(os.listdir(THREADS_DIR), reverse=True)[:3]
        for t in threads:
            with open(os.path.join(THREADS_DIR, t), "r", encoding="utf-8") as f:
                content = f.read()
                # Extraemos solo el resumen del hilo (ajustado para mayor robustez)
                match = re.search(r"## RESUMEN DE LA CHARLA\r?\n(.*?)(?:\r?\n---|\r?\n\.\.\.|$)", content, re.DOTALL)
                if match:
                    prompt += f"### {t}\n{match.group(1).strip()}\n\n"

        prompt += "\n--- \n**INSTRUCCION:** Continua desde este punto. No repitas lo ya listado arriba."

        with open(PROMPT_LLAVE_PATH, "w", encoding="utf-8") as f:
            f.write(prompt)
        print(f"PROMPT_LLAVE.md actualizado. Listo para copiar.")
        self.sync_git()

    def check_capacity(self):
        """Verifica la cantidad de archivos y alerta si hay saturacion."""
        try:
            files = [f for f in os.listdir(self.THREADS_DIR) if f.endswith(".md")]
            count = len(files)
            
            if count > 30:
                print(f"\n⚠️ ALERTA DE CAPACIDAD: Tenés {count} hilos de memoria.")
                print("💡 Sugerencia: Ejecutá 'python scripts/pegaso_memory.py archive' para limpiar la mente activa.")
            return count
        except Exception:
            return 0

    def archive_old_threads(self, limit=20):
        """Mueve los hilos mas viejos a la carpeta de archivo."""
        if not os.path.exists(self.ARCHIVE_DIR):
            os.makedirs(self.ARCHIVE_DIR)
            
        files = sorted([f for f in os.listdir(self.THREADS_DIR) if f.endswith(".md")])
        if len(files) > limit:
            to_archive = files[:-limit] # Dejamos los ultimos 'limit'
            for f in to_archive:
                os.rename(os.path.join(self.THREADS_DIR, f), os.path.join(self.ARCHIVE_DIR, f))
            print(f"📦 Se han archivado {len(to_archive)} hilos antiguos.")
            self.sync_git()

    def prune(self, keep_latest=10):
        """Mueve hilos viejos a archive/ para mantener ligero el contexto."""
        all_threads = sorted(os.listdir(THREADS_DIR), reverse=True)
        to_prune = all_threads[keep_latest:]
        
        for t in to_prune:
            src = os.path.join(THREADS_DIR, t)
            dst = os.path.join(ARCHIVE_DIR, t)
            os.rename(src, dst)
            print(f"Archive: {t}")
    def sync_git(self):
        """Agrega los cambios de memoria al repositorio Git."""
        try:
            os.system("git add memory/*")
            # No hacemos commit automatico para evitar spam de commits pequeños
            # pero el 'add' asegura que el usuario lo vea en el proximo commit.
            print("Git: Cambios en carpeta 'memory' indexados.")
        except Exception as e:
            print(f"Error en sync_git: {e}")

if __name__ == "__main__":
    import sys
    pegaso = PegasoMemory()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "distill" and len(sys.argv) > 2:
            pegaso.distill(sys.argv[2])
        elif cmd == "update":
            pegaso.update_all()
        elif cmd == "prune":
            pegaso.prune()
    else:
        print("Pegaso Memory Core")
        print("Usage:")
        print("  python pegaso_memory.py distill <path_to_transcript.txt>")
        print("  python pegaso_memory.py update")
        print("  python pegaso_memory.py prune")
