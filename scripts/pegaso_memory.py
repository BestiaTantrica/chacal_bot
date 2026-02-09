
import os
import json
import datetime
import re

# El motor ahora busca 'memory' en la carpeta donde estas parado
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
            print(f"No se encuentra: {raw_text_path}")
            return
        with open(raw_text_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.log_thread(raw_text_path, content, tags=["distilled"])

    def log_thread(self, title, content, tags=[]):
        safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
        filename = f"{datetime.date.today()}_{safe_title}.md"
        filepath = os.path.join(THREADS_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n")
            f.write(f"Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Tags: {', '.join(tags)}\n\n")
            f.write("## RESUMEN DE LA CHARLA\n")
            f.write(content + "\n")
        self.update_all()

    def update_all(self):
        self.update_manifest()
        self.build_master_prompt()
        self.sync_git()

    def update_manifest(self):
        content = "# 🦅 MANIFIESTO DE MEMORIA PEGASO\n\n"
        content += f"Ultima actualizacion: {datetime.datetime.now()}\n\n"
        threads = sorted(os.listdir(THREADS_DIR), reverse=True)[:10]
        for t in threads:
            content += f"- {t}\n"
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            f.write(content)

    def build_master_prompt(self):
        # Buscamos el estado en la Bitácora unificada
        bitacora_path = os.path.join(THREADS_DIR, "BITACORA_CHACAL_V4.md")
        status_content = ""
        if os.path.exists(bitacora_path):
            with open(bitacora_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Extraemos la sección de Estado Actual
                match = re.search(r"(## 📊 ESTADO ACTUAL:.*?)---", content, re.DOTALL)
                if match:
                    status_content = match.group(1).strip()

        prompt = f"# PROTOCOLO PEGASO: LLAVE DE ACTIVACION DE MEMORIA\n\n"
        prompt += f"**FECHA:** {datetime.date.today()}\n\n"
        prompt += status_content + "\n\n"
        prompt += "---\n## ULTIMOS HILOS\n"
        
        threads = sorted(os.listdir(THREADS_DIR), reverse=True)[:3]
        for t in threads:
            with open(os.path.join(THREADS_DIR, t), "r", encoding="utf-8") as f:
                content = f.read()
                resumen_match = re.search(r"## RESUMEN DE LA CHARLA\r?\n+(.*)", content, re.DOTALL)
                if resumen_match:
                    texto = resumen_match.group(1).strip()
                    texto = re.split(r"\r?\n---|\r?\n\.\.\.", texto)[0].strip()
                    prompt += f"### {t}\n{texto[:500]}\n\n"

        prompt += "\n---\n**INSTRUCCION:** Continua desde aqui."
        with open(PROMPT_LLAVE_PATH, "w", encoding="utf-8") as f:
            f.write(prompt)

    def sync_git(self):
        try:
            os.system(f"git -C {current_dir} add memory/*")
        except: pass

if __name__ == "__main__":
    import sys
    peg = PegasoMemory()
    if len(sys.argv) > 1 and sys.argv[1] == "update":
        peg.update_all()
