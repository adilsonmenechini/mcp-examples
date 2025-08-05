from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
import bcrypt
import os
from datetime import timedelta
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração do Flask
app = Flask(__name__)

# Configuração do banco de dados SQLite
# O arquivo do banco de dados será "database.db"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuração do JWT
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')  # Altere para uma chave mais segura em produção
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1) # Token expira em 1 hora
jwt = JWTManager(app)

db = SQLAlchemy(app)

# --- Definição das tabelas do banco de dados ---

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# --- Rotas da API ---

@app.route('/register', methods=['POST'])
def register():
    """Rota para registrar um novo usuário."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    # Verifica se o usuário já existe
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'User already exists'}), 409

    # Cria o hash da senha
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Cria e salva o novo usuário no banco de dados
    new_user = User(username=username, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    """Rota para fazer login e gerar um token."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    # Verifica se o usuário existe e se a senha está correta
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'message': 'Invalid username or password'}), 401

    # Cria o token de acesso
    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token), 200

@app.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    """Rota protegida que exige um token de acesso."""
    # `get_jwt_identity()` retorna o que foi passado para 'identity' no create_access_token
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
        
    return jsonify(
        message=f'Welcome, {user.username}! This is a protected resource.',
        user_id=user.id
    ), 200

if __name__ == '__main__':
    # Garante que o arquivo do banco de dados seja criado antes de rodar
    with app.app_context():
        # Apenas cria as tabelas se elas não existirem
        db.create_all()

    app.run(debug=True)