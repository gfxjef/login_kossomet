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

# Configuración de la base de datos desde variables de entorno
DB_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

def get_db_connection():
    """Establece y retorna una conexión segura a la base de datos"""
    try:
        conn = mysql.connector.connect(
            **DB_CONFIG,
            ssl_disabled=False,  # Habilitar SSL si está disponible
            connection_timeout=10
        )
        logger.info("Conexión a DB establecida exitosamente")
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Error de conexión a DB: {err}")
        return None

@app.route('/login', methods=['POST'])
def handle_login():
    """Endpoint para autenticación de usuarios"""
    # Validación básica de entrada
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Content-Type must be application/json'}), 400
    
    data = request.get_json()
    
    required_fields = ['usuario', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Faltan campos requeridos'}), 400

    usuario = data['usuario'].strip().lower()
    password = data['password'].encode('utf-8')

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Error de conexión con el servidor'}), 500

    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT id, usuario, nombre, cargo, password_hash FROM usuarios WHERE usuario = %s",
                (usuario,)
            )
            user = cursor.fetchone()

        if not user:
            logger.warning(f"Intento de login fallido para usuario: {usuario}")
            return jsonify({'success': False, 'message': 'Credenciales inválidas'}), 401

        # Verificar contraseña con bcrypt
        if bcrypt.checkpw(password, user['password_hash'].encode('utf-8')):
            logger.info(f"Login exitoso para usuario: {usuario}")
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
            logger.warning(f"Contraseña incorrecta para usuario: {usuario}")
            return jsonify({'success': False, 'message': 'Credenciales inválidas'}), 401

    except mysql.connector.Error as err:
        logger.error(f"Error de base de datos: {err}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'}), 500

    finally:
        if conn.is_connected():
            conn.close()

if __name__ == '__main__':
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    )