from flask import Flask, redirect, url_for, render_template, request, session
import requests
import firebase_admin
from firebase_admin import credentials, auth
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from firebase_admin import auth
import pyrebase
import os
import requests
from firebase_admin import credentials, auth


# Firebase Ayarları
cred = credentials.Certificate(r"C:\Users\feyza\Documents\filmapi.json")  
firebase_admin.initialize_app(cred)

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["SESSION_TYPE"] = "filesystem"

# Flask-WTF Kullanıcı Formları
class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Sign Up")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


# Firebase yapılandırma
config = {
    "apiKey": "AIzaSyDLmm9y8_c4_IbWUIpVq2yF1yqKKsCl5kY",
    "authDomain": "filmapi-9f933.firebaseapp.com",
    "projectId": "filmapi-9f933",
    "storageBucket": "filmapi-9f933.firebasestorage.app",
    "messagingSenderId": "37197178307",
    "appId": "1:37197178307:web:f3d0cecf5f41aa05f6c976",
    "measurementId": "G-HXQ8STR714",
    "databaseURL": "https://filmapi-9f933.firebaseio.com"  # DÜZELTİLDİ!
}

firebase = pyrebase.initialize_app(config)
auth_pyrebase = firebase.auth()  # Pyrebase ile auth nesnesini farklı adlandır!

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    error = None
    
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        try:
            user = auth.create_user(email=email, password=password)
            return redirect(url_for("login"))
        except Exception as e:
            error = f"Böyle bir hesap mevcut!"
    
    return render_template("register.html", form=form, error=error)

import firebase_admin
from firebase_admin import auth

@app.route("/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    error = None

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        try:
            # Firebase Admin ile kullanıcıyı doğrula
            user = auth.get_user_by_email(email)  # Kullanıcıyı email ile bul
            try:
                # Kullanıcıyı pyrebase ile giriş yapmaya çalış (şifre doğrulaması için)
                user = auth_pyrebase.sign_in_with_email_and_password(email, password)

                # Firebase ID Token al (Kimlik doğrulama için önemli!)
                user_info = auth_pyrebase.get_account_info(user['idToken'])

                if user_info:
                    session["user"] = user["email"]  # idToken yerine email saklanıyor!
                    return redirect(url_for("anasayfa"))
                else:
                    error = "Hatalı giriş!"
            except Exception as e:
                error = "Kullanıcı adı veya şifre hatalı!"
                
        except auth.UserNotFoundError:
            error = "Böyle bir hesap yok!"  # Kayıtlı olmayan kullanıcı

    return render_template("login.html", form=form, error=error)


# Çıkış Yapma
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


# API Ayarları
BASE_URL = "https://api.themoviedb.org/3/movie/popular"
TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjMjU3MDA3MmY1MmUyYzgwZDU4ZTU1OTA4NTBiM2ViYiIsIm5iZiI6MTczOTk2NzYzNy45MDgsInN1YiI6IjY3YjVjYzk1ZDI4ZTg3ZTBlNWUzYzViYiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.Gm0lNlwENOflI0FEu5MqMGU6V29QuALTFM4cq6DWPno"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}
response = requests.get(BASE_URL, headers=headers)
data = response.json()

favori_films = []

@app.route("/anasayfa", methods=["POST", "GET"])
def anasayfa():
    return render_template("anasayfa.html", movies=data['results'])

@app.route("/ekle", methods=["POST", "GET"])
def ekle():
    title = request.form.get('title')
    poster_path = request.form.get('poster_path')
    release_date = request.form.get('release_date')

    film = {
        "title": title,
        "poster_path": poster_path,
        "release_date": release_date
    }

    if title and film not in favori_films:
        favori_films.append(film)
    return redirect(url_for('anasayfa'))

@app.route("/sil", methods=["POST"])
def sil():
    title = request.form.get('title')

    global favori_films
    favori_films = [film for film in favori_films if film['title'] != title]
    return redirect(url_for('favoriler'))

@app.route("/favoriler", methods=["POST", "GET"])
def favoriler():
    return render_template("favoriler.html", favori_films=favori_films)

@app.route("/film_detay/<int:film_id>", methods=["GET", "POST"])
def film_detay(film_id):
    film = next((item for item in data['results'] if item["id"] == film_id), None)
    if film:
        return render_template("read.html", film=film)
    else:
        return "Film bulunamadı", 404

if __name__ == "__main__":
    app.run(debug=True, port=5000)
