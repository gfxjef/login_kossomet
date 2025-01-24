from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os
import bcrypt
import logging
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

app = Flask(__name__)
CORS(app, resources={
    r"/login": {
        "origins": os.getenv('ALLOWED_ORIGINS', 'https://kossodo.estilovisual.com'),
        "methods": ["POST"],
        "allow_headers": ["Content-Type"]
    }
})

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración original de la base de datos (sin cambios)
DB_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'port': int(os.getenv('DB_PORT', 3306))
}

def get_db_connection():
    """Establece y retorna conexión a la base de datos"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        logger.info("Conexión a DB exitosa")
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Error de conexión: {err}")
        return None

@app.route('/login', methods=['POST'])
def handle_login():
    # Validación de campos ORIGINALES
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Se requiere JSON'}), 400
    
    data = request.get_json()
    
    if 'usuario' not in data or 'pass' not in data:
        return jsonify({'success': False, 'message': 'Faltan usuario o pass'}), 400

    usuario = data['usuario'].strip()
    pass_input = data['pass'].encode('utf-8')  # Campo se llama 'pass'

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Error de conexión a BD'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        # Consulta ORIGINAL (columna pass)
        cursor.execute(
            "SELECT id, usuario, nombre, cargo, pass FROM usuarios WHERE usuario = %s",
            (usuario,)
        )
        user = cursor.fetchone()

        if not user:
            logger.warning(f"Intento fallido: Usuario {usuario} no existe")
            return jsonify({'success': False, 'message': 'Credenciales inválidas'}), 401

        # Verificar contraseña con bcrypt (columna pass)
        if bcrypt.checkpw(pass_input, user['pass'].encode('utf-8')):
            logger.info(f"Login exitoso: {usuario}")
            return jsonify({
                'success': True,
                'user': {
                    'id': user['id'],
                    'usuario': user['usuario'],
                    'nombre': user['nombre'],
                    'cargo': user['cargo']
                }
            })
        else:
            logger.warning(f"Pass incorrecta para: {usuario}")
            return jsonify({'success': False, 'message': 'Credenciales inválidas'}), 401

    except mysql.connector.Error as err:
        logger.error(f"Error BD: {err}")
        return jsonify({'success': False, 'message': 'Error interno'}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    )