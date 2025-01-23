import shutil
import os
import time
from datetime import datetime, timedelta

# Ruta del archivo de la base de datos
db_path = 'db.qualities.sqlite3'

# Directorio donde se guardarán los backups
backup_dir = 'backups_qualities'

# Crear el directorio de backups si no existe
os.makedirs(backup_dir, exist_ok=True)

# Generar el nombre del archivo de backup con la fecha y hora actuales
backup_filename = f"db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite3"
backup_path = os.path.join(backup_dir, backup_filename)

# Copiar el archivo de la base de datos al directorio de backups
shutil.copy2(db_path, backup_path)

print(f"Backup realizado con éxito: {backup_path}")

# Eliminar backups más antiguos de 5 días
now = time.time()
backup_retention_days = 5
retention_time = now - (backup_retention_days * 86400)  # 86400 segundos en un día

for filename in os.listdir(backup_dir):
    file_path = os.path.join(backup_dir, filename)
    if os.path.isfile(file_path):
        file_mod_time = os.path.getmtime(file_path)
        if file_mod_time < retention_time:
            os.remove(file_path)
            print(f"Backup antiguo eliminado: {file_path}")
