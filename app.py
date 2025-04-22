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


# Rutas del dashboard de admin

@app.route('/home-admin')
def home_admin():
    return render_template('admin_dashboard.html')

@app.route('/registrar-libro')
def registrar_libro():
    return render_template('registrar-libro.html')

@app.route('/editar-libros')
def editar_libros():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    books = list(mongo.db.books.find())
    return render_template('editar-libro.html', books=books)


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

def upload_image_to_gcs(file, title, author):
    bucket = client.bucket(bucket_name)
    
    # Renombramos el archivo con el nombre del libro y autor, separados por un guión
    unique_filename = f"{secure_filename(title)}_{secure_filename(author)}.jpg"
    
    blob = bucket.blob(unique_filename)
    blob.upload_from_file(file, content_type=file.content_type)
    blob.make_public()
    
    return blob.public_url



@app.route('/add_book', methods=['POST'])
def add_book():
    if 'username' not in session or session.get('role') != 'admin':
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


#Editar libros

@app.route('/mostrar_libros_admin', methods=['GET'])
def mostrar_libros_admin():  # <-- Este nombre debe ser único
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    books = mongo.db.books.find()
    return render_template('editar-libros.html', books=books)


@app.route('/editar_libro/<book_id>', methods=['GET', 'POST'])
def editar_libro(book_id):
    if 'username' not in session or session.get('role') != 'admin':
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
            return redirect(url_for('editar_libro', book_id=book_id))

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
        return redirect(url_for('editar_libros'))
    
    return render_template('editar-libro-form.html', book=book)

# Eliminar libro 
@app.route('/eliminar_libro/<book_id>', methods=['GET'])
def eliminar_libro(book_id):
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    mongo.db.books.delete_one({'_id': ObjectId(book_id)})
    flash('Libro eliminado correctamente ❌', 'success')
    return redirect(url_for('editar_libros'))


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
