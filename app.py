from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from bson.objectid import ObjectId  
import os

# Cargar variables de entorno
load_dotenv()



# Crear la app y configurar la base de datos
app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# Iniciar las extensiones
mongo = PyMongo(app)
bcrypt = Bcrypt(app)

# Ruta de inicio y login
@app.route('/')
def home():
    return render_template('login.html')

#Rutas de comprobacion de login
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Buscar el usuario en la base de datos
    user = mongo.db.users.find_one({'username': username})
    
    if user:
        # Si el usuario existe, verificar la contraseña
        if bcrypt.check_password_hash(user['password'], password):
            session['username'] = user['username']
            session['role'] = user['role']  # 'admin' o 'user'
            
            # Redirigir según el rol del usuario
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Contraseña incorrecta, por favor intente de nuevo', 'error')
            return redirect(url_for('home'))
    else:
        # Si el usuario no existe, mostrar un mensaje de error
        flash('El nombre de usuario no existe', 'error')
        return redirect(url_for('home'))
    

#Rutas de comprobacion del registro
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    # Verificar que los campos no estén vacíos
    if not username or not email or not password:
        flash('Por favor, complete todos los campos.', 'error')
        return redirect(url_for('home'))

    # Verifica si el nombre de usuario ya existe
    if mongo.db.users.find_one({'username': username}):
        flash('El nombre de usuario ya está en uso', 'error')
        return redirect(url_for('home'))

    # Verifica si el correo ya está registrado
    if mongo.db.users.find_one({'email': email}):
        flash('El correo electrónico ya está registrado', 'error')
        return redirect(url_for('home'))

    # Hashea la contraseña antes de guardarla
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Crea el nuevo usuario como usuario común
    new_user = {
        'username': username,
        'email': email,
        'password': hashed_password,
        'role': 'user'
    }
    mongo.db.users.insert_one(new_user)

    flash('Usuario registrado exitosamente. Ya puedes iniciar sesión.', 'success')
    return redirect(url_for('home'))



# Ruta del dashboard de admin
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('home'))
    return render_template('admin_dashboard.html')

# Ruta del dashboard de usuario
@app.route('/user_dashboard')
def user_dashboard():
    if 'username' not in session or session['role'] != 'user':
        return redirect(url_for('home'))

    books = list(mongo.db.books.find())
    borrowed_books = list(mongo.db.books.find({'borrowed_by': session['username']}))

    return render_template('user_dashboard.html', books=books, borrowed_books=borrowed_books)

# Cerrar sesión
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('Sesión cerrada exitosamente', 'info')
    return redirect(url_for('home'))

# Agregar libro (admin)
@app.route('/add_book', methods=['POST'])
def add_book():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('home'))

    title = request.form.get('title')
    author = request.form.get('author')
    genre = request.form.get('genre')

    # Insertar el libro en la base de datos
    mongo.db.books.insert_one({
        'title': title,
        'author': author,
        'genre': genre,
        'status': 'available',
        'borrowed_by': None
    })

    flash('Libro agregado con éxito', 'success')
    return redirect(url_for('admin_dashboard'))

# Eliminar libro (admin)
@app.route('/delete_book/<book_id>', methods=['POST'])
def delete_book(book_id):
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('home'))

    mongo.db.books.delete_one({'_id': ObjectId(book_id)})  
    flash('Libro eliminado con éxito', 'success')
    return redirect(url_for('admin_dashboard'))

# Alquilar libro (usuario)
@app.route('/borrow_book/<book_id>', methods=['POST'])
def borrow_book(book_id):
    if 'username' not in session or session['role'] != 'user':
        return redirect(url_for('home'))

    user = mongo.db.users.find_one({'username': session['username']})
    book = mongo.db.books.find_one({'_id': ObjectId(book_id)})  

    # Lógica para alquilar el libro
    if book and user:
        mongo.db.books.update_one(
            {'_id': ObjectId(book_id)},
            {'$set': {'status': 'borrowed', 'borrowed_by': user['username']}}
        )
        flash('Libro alquilado con éxito', 'success')

    return redirect(url_for('user_dashboard'))

# Ejecutar la app
if __name__ == "__main__":
    app.run(debug=True)
