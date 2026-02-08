
import os
import sys

# Motor de buceo en el archivo de memoria
current_dir = os.getcwd()
THREADS_DIR = os.path.join(current_dir, "memory", "threads")
ARCHIVE_DIR = os.path.join(current_dir, "memory", "archive")

def bucear(keyword):
    print(f"🔎 Buceando en los archivos de la mente por: '{keyword}'...")
    
    if not os.path.exists(ARCHIVE_DIR):
        print("📭 El archivo esta vacio todavia.")
        return

    encontrados = []
    
    # Buscamos en el archivo
    for f in os.listdir(ARCHIVE_DIR):
        if f.endswith(".md"):
            with open(os.path.join(ARCHIVE_DIR, f), "r", encoding="utf-8") as file:
                content = file.read()
                if keyword.lower() in content.lower():
                    encontrados.append(f)
    
    if not encontrados:
        print(f"❌ No encontre nada en el archivo sobre '{keyword}'.")
        return

    print(f"✅ Encontre {len(encontrados)} hilos relacionados:")
    for i, f in enumerate(encontrados):
        print(f"  [{i}] {f}")
    
    opcion = input("\n¿Quieres traer estos hilos a la mente ACTIVA? (s/n): ")
    if opcion.lower() == 's':
        for f in encontrados:
            os.rename(os.path.join(ARCHIVE_DIR, f), os.path.join(THREADS_DIR, f))
        print(f"🧠 {len(encontrados)} hilos han sido restaurados a la memoria activa.")
        # Sincronizamos
        os.system("git add memory/* && git commit -m 'Memoria: Restauracion de hilos' && git push")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        keyword = input("¿Que quieres buscar en la memoria profunda?: ")
    else:
        keyword = sys.argv[1]
    bucear(keyword)
