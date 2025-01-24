from flask import Flask, request, jsonify
import mysql.connector
from flask_cors import CORS  # <-- Añade esta línea

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://kossodo.estilovisual.com"}})  # <-- Configuración CORS

DB_CONFIG = {
    'user': 'atusalud_atusalud',
    'password': 'kmachin1',
    'host': 'atusaludlicoreria.com',
    'database': 'atusalud_kossomet',
    'port': 3306
}

@app.route('/', methods=['POST'])
def login():
    # Obtener datos JSON
    data = request.get_json()
    if not data or 'usuario' not in data or 'pass' not in data:
        return jsonify({'success': False, 'message': 'Faltan usuario o contraseña'}), 400

    usuario = data['usuario']
    contraseña = data['pass']

    try:
        # Conectar a la base de datos
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Buscar usuario en la base de datos
        cursor.execute(
            "SELECT id, usuario, nombre, cargo FROM usuarios WHERE usuario = %s AND pass = %s",
            (usuario, contraseña)
        )
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()

        if user:
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
            return jsonify({'success': False, 'message': 'Credenciales inválidas'}), 401

    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Error de base de datos: {err}'}), 500

if __name__ == '__main__':
    app.run(debug=True)