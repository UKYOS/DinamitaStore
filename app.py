from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from bson.objectid import ObjectId  
from google.cloud import storage
from google.oauth2 import service_account
from werkzeug.utils import secure_filename
import json
import os
from functools import wraps

# Cargar variables del archivo .env (solo aplica en entorno local)
load_dotenv()

# Obtener variables de entorno
credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
project_id = os.getenv('GCP_PROJECT_ID')
bucket_name = os.getenv('GCP_BUCKET_NAME')

# Determinar método de autenticación
if credentials_path:
    # ✅ Local: con archivo JSON
    credentials = service_account.Credentials.from_service_account_file(credentials_path)
else:
    # ✅ Render: con variable de entorno JSON
    credentials_info = json.loads(os.getenv('GCP_CREDENTIALS_JSON'))
    credentials = service_account.Credentials.from_service_account_info(credentials_info)

# Crear el cliente de almacenamiento
client = storage.Client(credentials=credentials, project=project_id)

# Crear la app y configurar la base de datos
app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# Iniciar las extensiones
mongo = PyMongo(app)
bcrypt = Bcrypt(app)

# Decorador para rutas protegidas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:  # Si no está en sesión
            return redirect(url_for('home'))  # Redirigir a la página principal (login)
        return f(*args, **kwargs)
    return decorated_function

# Ruta de inicio y login
@app.route('/')
def home():
    if 'username' in session:
        if session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif session['role'] == 'user':
            return redirect(url_for('user_dashboard'))
    return render_template('login.html')

# Rutas de comprobación de login
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
    

# Rutas de comprobación del registro
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
@login_required
def admin_dashboard():
    if session['role'] != 'admin':
        return redirect(url_for('home'))
    return render_template('admin_dashboard.html')

@app.route('/home-admin')
@login_required
def home_admin():
    return render_template('admin_dashboard.html')

@app.route('/registrar-libro')
@login_required
def registrar_libro():
    return render_template('registrar-libro.html')

@app.route('/editar-libros')
@login_required
def editar_libros():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    books = list(mongo.db.books.find())
    return render_template('editar-libro.html', books=books)


# Ruta del dashboard de usuario
@app.route('/user_dashboard')
@login_required
def user_dashboard():
    if session['role'] != 'user':
        return redirect(url_for('home'))

    books = list(mongo.db.books.find())
    borrowed_books = list(mongo.db.books.find({'borrowed_by': session['username']}))

    return render_template('user_dashboard.html', books=books, borrowed_books=borrowed_books)


# Cerrar sesión
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  # Borra todos los datos de la sesión
    flash('Sesión cerrada exitosamente', 'info')
    return redirect(url_for('home'))


# Subir imagen a Google Cloud Storage
def upload_image_to_gcs(file, title, author):
    bucket = client.bucket(bucket_name)
    
    # Renombramos el archivo con el nombre del libro y autor, separados por un guión
    unique_filename = f"{secure_filename(title)}_{secure_filename(author)}.jpg"
    
    blob = bucket.blob(unique_filename)
    blob.upload_from_file(file, content_type=file.content_type)
    blob.make_public()
    
    return blob.public_url

# Agregar libro
@app.route('/add_book', methods=['POST'])
@login_required
def add_book():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    title = request.form.get('title')
    author = request.form.get('author')
    genre = request.form.get('genre')
    stock = int(request.form.get('stock'))

    # Verificar si ya existe un libro con el mismo título y autor
    existing_book = mongo.db.books.find_one({'title': title, 'author': author})
    if existing_book:
        flash('Ya existe un libro con ese título y autor 📚', 'error')
        books = list(mongo.db.books.find())
        return render_template('registrar-libro.html', books=books)

    image = request.files.get('image')
    if image and image.filename != '':
        filename = secure_filename(image.filename)
        image_url = upload_image_to_gcs(image, title, author)  # Ahora se pasa title y author

        mongo.db.books.insert_one({
            'title': title,
            'author': author,
            'genre': genre,
            'stock': stock,
            'status': 'available',
            'borrowed_by': None,
            'image_url': image_url
        })

        flash('Libro registrado con éxito 🎉', 'success')
    else:
        flash('Por favor, sube una imagen válida del libro', 'error')

    books = list(mongo.db.books.find())
    return render_template('registrar-libro.html', books=books)


# Editar libros
@app.route('/mostrar_libros_admin', methods=['GET'])
def mostrar_libros_admin():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    books = mongo.db.books.find()
    return render_template('editar-libro.html', books=books)

@app.route('/editar_libro/<book_id>', methods=['GET', 'POST'])
@login_required
def editar_libro(book_id):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    book = mongo.db.books.find_one({'_id': ObjectId(book_id)})

    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        genre = request.form.get('genre')
        stock = int(request.form.get('stock'))
        
        # Verificar si el libro con el mismo título y autor ya existe
        existing_book = mongo.db.books.find_one({'title': title, 'author': author})
        if existing_book and str(existing_book['_id']) != book_id:
            flash('Ya existe un libro con ese título y autor 📚', 'error')
            return redirect(url_for('editar_libro', book_id=book_id))  # Redirigir al formulario para mostrar el error

        # Actualización de los datos del libro
        mongo.db.books.update_one(
            {'_id': ObjectId(book_id)},
            {'$set': {
                'title': title,
                'author': author,
                'genre': genre,
                'stock': stock
            }}
        )

        flash('Libro actualizado con éxito 🎉', 'success')
        return redirect(url_for('mostrar_libros_admin'))  # Redirigir a la vista de libros admin
    
    return render_template('form-edit-book.html', book=book)


# Eliminar libro 
@app.route('/eliminar_libro/<book_id>', methods=['GET'])
def eliminar_libro(book_id):
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    mongo.db.books.delete_one({'_id': ObjectId(book_id)})
    flash('Libro eliminado correctamente ❌', 'success')
    return redirect(url_for('editar_libros'))


# Iniciar la aplicación
if __name__ == '__main__':
    app.run(debug=True)
