# 💥 DinamitaStore

DinamitaStore es una tienda virtual construida con Flask y MongoDB, donde los usuarios pueden registrarse, ver libros disponibles y comprarlos. Además, cuenta con un panel de administración que permite a los administradores gestionar libros .

🔗 Proyecto desplegado: https://dinamitastore.onrender.com/

---

## 🚀 Tecnologías utilizadas

- Backend: Python (Flask)  
- Base de Datos: MongoDB (usando pymongo)  
- Frontend: HTML, CSS, Bootstrap, JavaScript  
- Almacenamiento de imágenes: Google Cloud Storage  

---

## 📁 Estructura del proyecto

├── static/                # Archivos estáticos (CSS, JS, imágenes)  
├── templates/             # Plantillas HTML para las vistas  
├── .gitignore             # Archivos ignorados por Git  
├── README.md              # Documentación del proyecto  
├── app.py                 # Lógica principal de la aplicación Flask  
├── requirements.txt       # Dependencias necesarias del proyecto  

---

## ⚙️ Requisitos previos

- Python 3.7 o superior  
- Cuenta en MongoDB Atlas  
- Proyecto y bucket configurado en Google Cloud Storage  
- Crear un archivo `.env` o configurar variables de entorno con:

MONGO_URI=mongodb+srv://<usuario>:<password>@cluster.mongodb.net/<db>?retryWrites=true&w=majority  
GCS_BUCKET_NAME=nombre_del_bucket  
GCS_CREDENTIALS_JSON=archivo_credenciales.json  
SECRET_KEY=clave_secreta_para_flask  

---

## 🛠️ Instalación y ejecución local

1. Clona el repositorio:

git clone https://github.com/UKYOS/DinamitaStore.git  
cd DinamitaStore  

2. Crea un entorno virtual:

python -m venv venv  
source venv/bin/activate     # En Windows: venv\Scripts\activate  

3. Instala las dependencias:

pip install -r requirements.txt  

4. Configura tus variables de entorno como se indica arriba.

5. Ejecuta la aplicación localmente:

flask run  

---

## ✨ Funcionalidades principales

- 🔐 Registro e inicio de sesión con validación  
- 📚 Catálogo de libros con opción de alquiler  
- 🛠️ Panel de administración para:  
  - Agregar, editar y eliminar libros  
 - ☁️ Subida de imágenes de libros a Google Cloud Storage  
- 💡 Interfaz responsive y amigable  

---

## 📌 Notas importantes

> Este proyecto requiere credenciales externas (MongoDB Atlas y Google Cloud Storage)  
> para funcionar correctamente. Estas no se incluyen por motivos de seguridad.  

---

## 🤝 Contribuciones

¿Tienes ideas para mejorar DinamitaStore?  
¡Las contribuciones son bienvenidas!  
Abre un issue o haz un pull request.

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT – puedes usarlo, modificarlo y compartirlo libremente.

---

## 👤 Autores

UKYOS

Thefernan122

JOSHxMAYKOL


https://github.com/UKYOS
