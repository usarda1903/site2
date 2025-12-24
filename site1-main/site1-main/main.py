from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime,timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
import uuid
import random
import smtplib
import time

app = Flask(__name__)
app.secret_key = "your-secret-key-here-change-this"

# -------------------------------------------------
# FILE UPLOAD CONFIGURATION
# -------------------------------------------------
UPLOAD_FOLDER = 'static/uploads/products'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -------------------------------------------------
# FILE PATHS
# -------------------------------------------------
USER_DATA_FILE = "user_purchases.json"
COMMENTS_FILE = "comments.json"
USERS_FILE = "users.json"
PRODUCTS_FILE = "products.json"
SUPPORT_FILE = "support.json"
BANK_ACCOUNTS_FILE = "bank_accounts.json"
ADMIN_SECRET_KEY = "123"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = "seninmail@gmail.com"
SMTP_PASSWORD = "bttq sgop dkki yxya"
AVATAR_FOLDER = "static/uploads/avatars"
ALLOWED_AVATAR_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
CHALLENGE_QUESTIONS = "challenge_questions.json"
CHALLENGE_SCORES = "challenge_scores.json"

os.makedirs(AVATAR_FOLDER, exist_ok=True)


# -------------------------------------------------
# BANK ACCOUNT HELPERS
# -------------------------------------------------
def load_bank_accounts():
    if os.path.exists(BANK_ACCOUNTS_FILE):
        with open(BANK_ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_bank_accounts(data):
    with open(BANK_ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def mask_card_number(card_number):
    """Mask credit card number (show only last 4 digits)"""
    if not card_number or len(card_number) < 4:
        return "****"
    return "**** **** **** " + card_number[-4:]

# -------------------------------------------------
# JSON HELPERS
# -------------------------------------------------


def load_products():
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # Default products
    return {
    "1": {"id": "1", "name": "Mystical Spell Book", "price": 49.99, "category": "books", "emoji": "📖",
          "description": "2000 yıl öncesinen büyüler",
          "yorumlar": ["Mükemmel bir kitap", "Ben okuyamadım", "Bu kitabı aldım ve bütün hayatım değişti"]},
    "2": {"id": "2", "name": "Carnivorous Plant", "price": 29.99, "category": "plants", "emoji": "🌿"},
    "3": {"id": "3", "name": "Ancient Grimoire", "price": 79.99, "category": "books", "emoji": "📚"},
    "4": {"id": "4", "name": "Enchanted Succulent", "price": 19.99, "category": "plants", "emoji": "🪴"},
    "5": {"id": "5", "name": "Potion Making Kit", "price": 59.99, "category": "accessories", "emoji": "🧪"},
    "6": {"id": "6", "name": "Crystal Ball", "price": 89.99, "category": "accessories", "emoji": "🔮"},
    "7": {"id": "7", "name": "Magic Wand", "price": 39.99, "category": "accessories", "emoji": "🪄"},
    "8": {"id": "8", "name": "Venus Flytrap", "price": 24.99, "category": "plants", "emoji": "🌺"},
    "9": {"id": "9", "name": "Görünmezlik İksiri", "price": 99.99, "category": "potions", "emoji": "⚗️"},
    "10": {"id": "10", "name": "Ayışığı Tozu", "price": 4.99, "category": "potions", "emoji": "🌙"},
    "11": {"id": "11", "name": "Ejderha Yumurtası", "price": 149.99, "category": "pets", "emoji": "🐲"},
    "12": {"id": "12", "name": "Sihirli Elf Şapkası", "price": 109.99, "category": "accessories", "emoji": "🧑‍🎄"},
    "13": {"id": "13", "name": "Ateş Kılıcı", "price": 190.00, "category": "silah", "emoji": "🔥"},
    "14": {"id": "14", "name": "5x Hız", "price": 199.99, "category": "ozel guc", "emoji": "⚡"},
    "15": {"id": "15", "name": "Büyü Bombası", "price": 399.99, "category": "silah", "emoji": "💣"},
    "16": {"id": "16", "name": "Kalkan", "price": 12.99, "category": "koruma", "emoji": "🛡️"},
    "17": {"id": "17", "name": "Harita", "price": 119.99, "category": "accessories", "emoji": "🗺️"},
    "18": {"id": "18", "name": "ucma", "price": 99.99, "category": "ozel guc", "emoji": "🦅",
           "description": "kuş gibi uçacaksın",
           "yorumlar": ["kus gibi his ediyorum", "🌟🌟🌟🌟🌟 cok iyi"]}
    }

def check_user_access():
    if "username" not in session:
        return False, redirect(url_for("login"))

    users = load_users()
    user = users.get(session["username"])

    if not user:
        session.clear()
        return False, redirect(url_for("login"))

    if user.get("banned", False) or not user.get("active", True):
        session.clear()
        return False, ("Hesabınız devre dışı.", 403)

    return True, None

def allowed_avatar(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_AVATAR_EXTENSIONS

def load_support():
    if os.path.exists(SUPPORT_FILE):
        with open(SUPPORT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_support(data):
    with open(SUPPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def mask_username(username):
    if len(username) <= 2:
        return username
    return username[0] + "*" * (len(username) - 2) + username[-1]

app.jinja_env.globals.update(mask_username=mask_username)
app.jinja_env.globals.update(mask_card_number=mask_card_number)


def save_products(data):
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_comments():
    if os.path.exists(COMMENTS_FILE):
        with open(COMMENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_comments(data):
    with open(COMMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_account(user_id):
    if not os.path.exists(BANK_ACCOUNTS_FILE):
        with open(BANK_ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

    with open(BANK_ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if user_id not in data:
        data[user_id] = {
            "balance": 0.0,
            "transactions": []
        }
        with open(BANK_ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    return data[user_id]


def save_account(user_id, account):
    with open(BANK_ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    data[user_id] = account

    with open(BANK_ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)



def load_challenge_questions():
    with open(CHALLENGE_QUESTIONS, "r", encoding="utf-8") as f:
        return json.load(f)

def load_challenge_scores():
    if os.path.exists(CHALLENGE_SCORES):
        with open(CHALLENGE_SCORES, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_challenge_scores(data):
    with open(CHALLENGE_SCORES, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_time_until_midnight():
    now = datetime.now()
    tomorrow = now.date() + timedelta(days=1)
    midnight = datetime.combine(tomorrow, datetime.min.time())

    remaining = midnight - now

    hours, remainder = divmod(int(remaining.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)

    return hours, minutes, seconds

# -------------------------------------------------
# AI RECOMMENDATION
# -------------------------------------------------
def get_ai_recommendations(user_id):
    user_data = load_user_data()
    purchases = user_data.get(user_id, {}).get("purchases", [])
    products = load_products()

    if not purchases:
        return list(products.values())[:3]

    category_count = {}
    for p in purchases:
        pid = p["product_id"]
        if pid in products:
            cat = products[pid]["category"]
            category_count[cat] = category_count.get(cat, 0) + 1

    scored = []
    for product in products.values():
        score = category_count.get(product["category"], 0)
        scored.append((score, product))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [p for _, p in scored[:3]]

def send_verification_email(to_email, token):
    link = f"http://127.0.0.1:5000/verify/{token}"

    msg = MIMEMultipart()
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email
    msg["Subject"] = "Hesap Doğrulama"

    body = f"""
Merhaba,

Hesabını doğrulamak için aşağıdaki linke tıkla:

{link}

Eğer bu işlemi sen yapmadıysan maili yok sayabilirsin.
"""
    msg.attach(MIMEText(body, "plain"))

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SMTP_EMAIL, SMTP_PASSWORD)
    server.send_message(msg)
    server.quit()


# -------------------------------------------------
# BANK ROUTES
# -------------------------------------------------
@app.route("/bank", methods=["GET", "POST"]) 
def bank():
    allowed, response = check_user_access()
    if not allowed:
        return response

    username = session["username"]
    bank_accounts = load_bank_accounts()
    
    # Initialize user's bank account if doesn't exist
    if username not in bank_accounts:
        bank_accounts[username] = {
            "balance": 1000.00,  # Starting balance
            "cards": [],
            "transactions": []
        }
        save_bank_accounts(bank_accounts)
    
    user_account = bank_accounts[username]
    message = request.args.get("message")
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "add_card":
            card_number = request.form.get("card_number", "").replace(" ", "")
            card_holder = request.form.get("card_holder", "")
            expiry = request.form.get("expiry", "")
            cvv = request.form.get("cvv", "")
            
            # Basic validation
            if len(card_number) == 16 and len(cvv) == 3:
                new_card = {
                    "id": str(uuid.uuid4()),
                    "number": card_number,
                    "holder": card_holder,
                    "expiry": expiry,
                    "cvv": cvv,
                    "added_date": datetime.now().strftime("%d.%m.%Y %H:%M")
                }
                user_account["cards"].append(new_card)
                save_bank_accounts(bank_accounts)
                return redirect(url_for("bank", message="Kart başarıyla eklendi!"))
            else:
                return redirect(url_for("bank", message="Geçersiz kart bilgileri!"))
        
        elif action == "delete_card":
            card_id = request.form.get("card_id")
            user_account["cards"] = [c for c in user_account["cards"] if c["id"] != card_id]
            save_bank_accounts(bank_accounts)
            return redirect(url_for("bank", message="Kart silindi!"))
        
        elif action == "deposit":
            amount = float(request.form.get("amount", 0))
            if amount > 0:
                user_account["balance"] += amount
                user_account["transactions"].append({
                    "type": "deposit",
                    "amount": amount,
                    "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
                    "description": "Para Yatırma"
                })
                save_bank_accounts(bank_accounts)
                return redirect(url_for("bank", message=f"{amount} 🪙 yatırıldı!"))
    
    return render_template(
        "bank.html",
        username=username,
        account=user_account,
        message=message
    )


# -------------------------------------------------
# ROUTES
# -------------------------------------------------
@app.route("/")
def index():
    return render_template(
        "index.html",
        username=session.get("username"),
        role=session.get("role")
    )


@app.route("/magaza")
def magaza():
    # Kullanıcı oturumu için geçici ID (AI önerileri için gerekli)
    if "user_id" not in session:
        session["user_id"] = os.urandom(16).hex()

    # Ürünleri ve önerileri yükle
    products = load_products()
    recommendations = get_ai_recommendations(session["user_id"])
    message = request.args.get("message")
    
    current_username = session.get("username")
    current_role = session.get("role")
    
    # ---------------------------------------------------------
    # 1. SAAT BAZLI İNDİRİM MANTIĞI (ELIF BLOKLARI)
    # ---------------------------------------------------------
    zaman = int(datetime.now().strftime("%H"))
    indirim_kategorisi = ""
    oran = 0

    if 20 <= zaman <= 21: 
        indirim_kategorisi = "books"
        oran = 0.50  # %50 İndirim
    elif 18 <= zaman < 20: 
        indirim_kategorisi = "plants"
        oran = 0.30  # %30 İndirim
    elif 16 <= zaman < 18: 
        indirim_kategorisi = "accessories"
        oran = 0.25  # %25 İndirim
    elif 14 <= zaman < 16: 
        indirim_kategorisi = "potions"
        oran = 0.40  # %40 İndirim
    elif 12 <= zaman < 14: 
        indirim_kategorisi = "pets"
        oran = 0.20  # %20 İndirim
    elif 10 <= zaman < 12: 
        indirim_kategorisi = "silah"
        oran = 0.15  # %15 İndirim
    elif 8 <= zaman < 10: 
        indirim_kategorisi = "ozel guc"
        oran = 0.10  # %10 İndirim
    elif 6 <= zaman < 8: 
        indirim_kategorisi = "koruma"
        oran = 0.35  # %35 İndirim

    # ---------------------------------------------------------
    # 2. ÜRÜNLERİ DÖNÜŞTÜRME VE FİYAT GÜNCELLEME
    # ---------------------------------------------------------
    discounted_products = []
    
    for pid, p in products.items():
        # Orijinal veriyi korumak için kopyalıyoruz
        p_info = p.copy()
        p_info['old_price'] = p['price']  # Çizilecek orijinal fiyat
        
        # Eğer ürünün kategorisi şu an indirimdeyse fiyatı düşür
        if p.get('category') == indirim_kategorisi:
            p_info['price'] = round(p['price'] * (1 - oran), 2)
            p_info['has_discount'] = True
            p_info['discount_rate'] = int(oran * 100)
        else:
            p_info['has_discount'] = False
            
        discounted_products.append(p_info)

    # ---------------------------------------------------------
    # 3. TEMPLATE'E GÖNDERME
    # ---------------------------------------------------------
    return render_template(
        "magaza.html",
        products=discounted_products,
        recommendations=recommendations,
        message=message,
        username=current_username,
        role=current_role,
        indirim=indirim_kategorisi, # Banner'da görünecek kategori ismi
        indirim_orani=int(oran * 100) # Banner'da görünecek oran
    )

def get_remaining_time_for_challenge():
    now = datetime.now()

    tomorrow = now.date() + timedelta(days=1)
    reset_time = datetime.combine(tomorrow, datetime.min.time())

    remaining = reset_time - now
    total_seconds = int(remaining.total_seconds())

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return hours, minutes, seconds

@app.route("/challenge", methods=["GET", "POST"])
def challenge():
    allowed, response = check_user_access()
    if not allowed:
        return response

    user_id = session["user_id"]
    username = session["username"]
    today = datetime.now().strftime("%Y-%m-%d")

    scores = load_challenge_scores()

    # 🔒 GÜNDE 1 KEZ KONTROL
    if user_id in scores and scores[user_id]["last_play"] == today:
        hours, minutes, seconds = get_remaining_time_for_challenge()

        return render_template(
            "challenge_blocked.html",
            hours=hours,
            minutes=minutes,
            seconds=seconds
        )

    questions = random.sample(load_challenge_questions(), 5)

    if request.method == "POST":
        correct = 0
        for q in questions:
            if request.form.get(str(q["id"])) == q["answer"]:
                correct += 1

        scores.setdefault(user_id, {
            "username": username,
            "weekly_score": 0,
            "last_play": ""
        })

        scores[user_id]["weekly_score"] += correct
        scores[user_id]["last_play"] = today
        save_challenge_scores(scores)

        # 💰 +50 BANKA ÖDÜLÜ
        account = load_account(user_id)
        account["balance"] += 50
        account["transactions"].append({
            "amount": 50,
            "description": "Challenge Oyunu Ödülü",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_account(user_id, account)

        return redirect(url_for("challenge_result", score=correct))

    return render_template("challenge.html", questions=questions)


@app.route("/challenge/finish", methods=["POST"])
def challenge_finish():
    if "user_id" not in session:
        return redirect(url_for("login"))

    # 🔑 Kullanıcı ID
    user_id = session["user_id"]

    # 🏦 Banka hesabını yükle
    account = load_account(user_id)

    # 🎁 HER OYUN SONU BONUS (50)
    account["balance"] += 50
    account["transactions"].append({
        "amount": 50,
        "description": "Challenge oyun ödülü",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    # 💾 KAYDET (EN ÖNEMLİ SATIR)
    save_account(user_id, account)

    return redirect(url_for("challenge"))


@app.route("/challenge/result")
def challenge_result():
    score = request.args.get("score")
    return render_template("challenge_result.html", score=score)

@app.route("/challenge/leaderboard")
def challenge_leaderboard():
    scores = load_challenge_scores()
    leaderboard = sorted(
        scores.items(),
        key=lambda x: x[1]["weekly_score"],
        reverse=True
    )
    return render_template("challenge_leaderboard.html", leaderboard=leaderboard)

def distribute_weekly_challenge_prizes(sorted_users):
    prizes = [1000, 500, 250]  # 1., 2., 3. ödülleri

    for i in range(min(3, len(sorted_users))):
        username, info = sorted_users[i]

        # 🔑 USER ID (ÇOK ÖNEMLİ)
        user_id = info["user_id"]

        # 🏦 Banka hesabını yükle
        account = load_account(user_id)

        # 💰 Ödülü ekle
        account["balance"] += prizes[i]
        account["transactions"].append({
            "amount": prizes[i],
            "description": f"Challenge haftalık {i + 1}.lik ödülü",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # 💾 Kaydet
        save_account(user_id, account)


@app.route("/destek", methods=["GET", "POST"])
def destek():
    allowed, response = check_user_access()
    if not allowed:
        return response

    if "username" not in session:
        return redirect(url_for("login"))

    support = load_support()
    username = session["username"]

    support.setdefault(username, [])

    bildirim_var = any(
        m.get("from") == "admin" and not m.get("read", False)
        for m in support.get(username, [])
    )

    if request.method == "POST":
        mesaj = request.form.get("mesaj")
        if mesaj:
            support[username].append({
                "id": str(uuid.uuid4()),
                "from": "user",
                "text": mesaj,
                "time": datetime.now().strftime("%d.%m.%Y %H:%M"),
                "read": True
            })
            save_support(support)

        return redirect(url_for("destek"))

    for m in support.get(username, []):
        if m.get("from") == "admin":
            m["read"] = True

    save_support(support)

    return render_template(
        "destek.html",
        messages=support[username],
        bildirim=bildirim_var,
        username=username
    )



@app.route("/destek_admin", methods=["GET", "POST"])
def destek_admin():
    if session.get("role") != "admin":
        return redirect(url_for("index"))

    support = load_support()

    if request.method == "POST":
        user = request.form.get("user")
        cevap = request.form.get("cevap")

        if user and cevap:
            support[user].append({
                "from": "admin",
                "text": cevap,
                "time": datetime.now().strftime("%d.%m.%Y %H:%M")
            })
            save_support(support)

    return render_template(
        "destek_admin.html",
        support=support,
        username=session.get("username"),
        role=session.get("role")
    )


@app.route("/admin/users", methods=["GET", "POST"])
def admin_users():

    if "username" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        return "Bu sayfaya erişim yetkin yok.", 403

    users = load_users()

    if request.method == "POST":
        username = request.form.get("username")
        action = request.form.get("action")

        if username == session["username"]:
            return "Kendin üzerinde işlem yapamazsın.", 400

        if username in users:

            if action == "ban":
                users[username]["banned"] = True

            elif action == "unban":
                users[username]["banned"] = False

            elif action == "make_admin":
                users[username]["role"] = "admin"

            elif action == "remove_admin":
                users[username]["role"] = "user"

            elif action == "deactivate":
                users[username]["active"] = False

            elif action == "activate":
                users[username]["active"] = True

            save_users(users)

    return render_template("admin_users.html", users=users)



@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    allowed, response = check_user_access()
    if not allowed:
         return response

    if "username" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        name = request.form.get("name")
        price = request.form.get("price")
        category = request.form.get("category")
        emoji = request.form.get("emoji", "📦")
        description = request.form.get("description", "")
        
        if not name or not price or not category:
            return render_template("add_product.html", 
                                 username=session.get("username"),
                                 message="Lütfen tüm alanları doldurun!")
        
        try:
            price = float(price)
        except ValueError:
            return render_template("add_product.html", 
                                 username=session.get("username"),
                                 message="Geçersiz fiyat!")
        
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                image_filename = f"{uuid.uuid4().hex}.{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        
        products = load_products()
        product_id = str(len(products) + 1)
        
        while product_id in products:
            product_id = str(int(product_id) + 1)
        
        new_product = {
            "id": product_id,
            "name": name,
            "price": price,
            "category": category,
            "emoji": emoji,
            "description": description,
            "image": image_filename,
            "yorumlar": [],
            "seller": session["username"]
        }
        
        products[product_id] = new_product
        save_products(products)
        
        return redirect(url_for("magaza", message=f"{name} başarıyla eklendi!"))
    
    return render_template("add_product.html", username=session.get("username"))

@app.context_processor
def inject_user():
    return {
        "username": session.get("username"),
        "role": session.get("role")
    }

@app.route("/my_products")
def my_products():
    if "username" not in session:
        return redirect(url_for("login"))
    
    products = load_products()
    username = session["username"]
    is_admin = session.get("role") == "admin"
    
    if is_admin:
        user_products = list(products.values())
    else:
        user_products = [p for p in products.values() if p.get("seller") == username]
    
    return render_template(
        "my_products.html",
        products=user_products,
        username=username,
        is_admin=is_admin
    )

@app.route("/delete_product/<product_id>")
def delete_product(product_id):
    allowed, response = check_user_access()
    if not allowed:
        return response

    if "username" not in session:
        return redirect(url_for("login"))
    
    products = load_products()
    
    if product_id not in products:
        return redirect(url_for("magaza", message="Ürün bulunamadı"))
    
    product = products[product_id]
    current_user = session["username"]
    is_admin = session.get("role") == "admin"
    
    if product.get("seller") == current_user or is_admin:
        if product.get("image"):
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], product["image"])
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except:
                    pass
        
        comments = load_comments()
        if product_id in comments:
            del comments[product_id]
            save_comments(comments)
        
        product_name = product["name"]
        del products[product_id]
        save_products(products)
        
        return redirect(url_for("magaza", message=f"'{product_name}' başarıyla silindi"))
    else:
        return redirect(url_for("magaza", message="Bu ürünü silme yetkiniz yok!"))

@app.route("/purchase/<product_id>")
def purchase(product_id):
    allowed, response = check_user_access()
    if not allowed:
        return response

    if "user_id" not in session:
        return redirect(url_for("login"))

    products = load_products()
    product = products.get(product_id)

    if not product:
        return redirect(url_for("magaza", message="Ürün bulunamadı"))

    user_id = session["user_id"]
    account = load_account(user_id)

    price = float(product["price"])

    # ❗ BAKİYE KONTROLÜ
    if account["balance"] < price:
        return redirect(url_for(
            "magaza",
            message="❌ Banka bakiyen yetersiz"
        ))

    # ✅ PARAYI DÜŞ
    account["balance"] = round(account["balance"] - price, 2)

    account["transactions"].append({
        "amount": -price,
        "description": f"{product['name']} satın alındı",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    save_account(user_id, account)

    # 🧾 SATIN ALMA KAYDI
    user_data = load_user_data()
    user_data.setdefault(user_id, {"purchases": []})
    user_data[user_id]["purchases"].append({
        "product_id": product_id,
        "product_name": product["name"],
        "timestamp": datetime.now().isoformat()
    })
    save_user_data(user_data)

    return redirect(url_for(
        "magaza",
        message=f"✅ {product['name']} satın alındı"
    ))


@app.route("/purchase_history")
def purchase_history():
    allowed, response = check_user_access()
    if not allowed:
        return response

    user_id = session.get("user_id")
    purchases = []

    if user_id:
        user_data = load_user_data()
        raw_purchases = user_data.get(user_id, {}).get("purchases", [])

        # 🔒 SADECE timestamp'li kayıtları al
        purchases = [
            p for p in raw_purchases
            if isinstance(p, dict) and "timestamp" in p
        ]

    return render_template(
        "history.html",
        purchases=purchases,
        username=session.get("username")
    )

@app.route("/esya/<id>")
def esyalar(id):
    products = load_products()
    if id not in products:
        return redirect(url_for("magaza"))
    
    current_user = session.get("username")
    is_admin = session.get("role") == "admin"
    product = products[id]
    
    can_delete = (product.get("seller") == current_user) or is_admin
    
    return render_template(
        "urun_sayfasi.html", 
        product=product, 
        username=current_user,
        can_delete=can_delete
    )

@app.route("/urun_penceresi/<product_id>")
def urun_penceresi(product_id):

    if "username" not in session:
        return redirect(url_for("login"))

    products = load_products()

    if product_id not in products:
        return redirect(url_for("magaza"))

    product = products[product_id].copy()  # 🔴 KOPYA (ÇOK ÖNEMLİ)

    # ---------------------------------------------------------
    # 1. SAAT BAZLI İNDİRİM MANTIĞI (MAĞAZA İLE AYNI)
    # ---------------------------------------------------------
    zaman = int(datetime.now().strftime("%H"))
    indirim_kategorisi = ""
    oran = 0

    if 20 <= zaman <= 21:
        indirim_kategorisi = "books"
        oran = 0.50
    elif 18 <= zaman < 20:
        indirim_kategorisi = "plants"
        oran = 0.30
    elif 16 <= zaman < 18:
        indirim_kategorisi = "accessories"
        oran = 0.25
    elif 14 <= zaman < 16:
        indirim_kategorisi = "potions"
        oran = 0.40
    elif 12 <= zaman < 14:
        indirim_kategorisi = "pets"
        oran = 0.20
    elif 10 <= zaman < 12:
        indirim_kategorisi = "silah"
        oran = 0.15
    elif 8 <= zaman < 10:
        indirim_kategorisi = "ozel guc"
        oran = 0.10
    elif 6 <= zaman < 8:
        indirim_kategorisi = "koruma"
        oran = 0.35

    # ---------------------------------------------------------
    # 2. ÜRÜNE İNDİRİM UYGULAMA
    # ---------------------------------------------------------
    product["old_price"] = product["price"]
    product["has_discount"] = False

    if product.get("category") == indirim_kategorisi:
        product["price"] = round(product["price"] * (1 - oran), 2)
        product["has_discount"] = True
        product["discount_rate"] = int(oran * 100)

    # ---------------------------------------------------------
    # 3. YETKİLER
    # ---------------------------------------------------------
    can_delete = (
        session.get("role") == "admin"
        or product.get("seller") == session.get("username")
    )

    return render_template(
        "urun_penceresi.html",
        product=product,
        can_delete=can_delete,
        role=session.get("role")
    )



@app.route("/yorumlar/<product_id>", methods=["GET", "POST"])
def yorumlar(product_id):
    allowed, response = check_user_access()
    if not allowed:
          return response

    products = load_products()
    if product_id not in products:
        return redirect(url_for("magaza"))

    comments = load_comments()
    comments.setdefault(product_id, [])

    if request.method == "POST":
        if "username" not in session:
            return redirect(url_for("login"))

        yorum = request.form.get("yorum")
        if yorum:
            comments[product_id].append({
                "id": str(uuid.uuid4()),
                "user": session["username"],
                "text": yorum,
                "time": datetime.now().strftime("%d.%m.%Y %H:%M")
            })
            save_comments(comments)

    return render_template(
        "yorumlar.html",
        product=products[product_id],
        comments=comments[product_id],
        username=session.get("username")
    )

@app.route("/yorum_sil/<product_id>/<comment_id>")
def yorum_sil(product_id, comment_id):
    if "username" not in session:
        return redirect(url_for("login"))

    comments = load_comments()
    if product_id in comments:
        comments[product_id] = [
            c for c in comments[product_id]
            if not (c["id"] == comment_id and c["user"] == session["username"])
        ]
        save_comments(comments)

    return redirect(url_for("yorumlar", product_id=product_id))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            return "Kullanıcı adı ve şifre zorunlu", 400

        users = load_users()

        # Kullanıcı zaten var mı
        if username in users:
            return "Bu kullanıcı adı zaten kayıtlı", 400

        # Yeni kullanıcı oluştur
        users[username] = {
            "password": generate_password_hash(password),
            "role": "user",
            "banned": False,
            "active": True,
            "created_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "avatar": None
        }

        save_users(users)

        # Otomatik giriş (istersen kaldırabilirsin)
        session["username"] = username
        session["role"] = "user"
        session["user_id"] = str(uuid.uuid4())

        return redirect(url_for("index"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        users = load_users()
        user = users.get(username)

        if not user or not check_password_hash(user["password"], password):
            return "Kullanıcı adı veya şifre yanlış", 401

        if user.get("banned", False):
            return "Hesabınız banlanmıştır.", 403

        if not user.get("active", True):
            return "Hesabınız pasif durumdadır.", 403
        
        # GİRİŞ BAŞARILI OLDUKTAN SONRA
        if "user_id" not in session:
           session["user_id"] = os.urandom(16).hex()


        session["username"] = username
        session["role"] = user.get("role", "user")

        return redirect(url_for("index"))

    return render_template("login.html")

@app.route("/profil")
def profil():
    allowed, response = check_user_access()
    if not allowed:
        return response

    users = load_users()
    support = load_support()
    user_data = load_user_data()

    username = session["username"]
    user = users.get(username)

    user_id = session.get("user_id")
    purchase_count = len(
        user_data.get(user_id, {}).get("purchases", [])
    ) if user_id else 0

    support_count = len(support.get(username, []))

    return render_template(
        "profil.html",
        username=username,
        avatar=user.get("avatar"),
        role=user.get("role"),
        banned=user.get("banned"),
        active=user.get("active"),
        created_at=user.get("created_at"),
        purchase_count=purchase_count,
        support_count=support_count
    )

@app.route("/profil/avatar", methods=["POST"])
def upload_avatar():
    allowed, response = check_user_access()
    if not allowed:
        return response

    if "avatar" not in request.files:
        return redirect(url_for("profil"))

    file = request.files["avatar"]
    if file.filename == "":
        return redirect(url_for("profil"))

    if not allowed_avatar(file.filename):
        return "Geçersiz dosya türü", 400

    filename = secure_filename(file.filename)
    ext = filename.rsplit(".", 1)[1].lower()
    new_filename = f"{uuid.uuid4().hex}.{ext}"

    save_path = os.path.join(AVATAR_FOLDER, new_filename)
    file.save(save_path)

    users = load_users()
    users[session["username"]]["avatar"] = new_filename
    save_users(users)

    return redirect(url_for("profil"))


@app.route("/product_detail/<product_id>")
def product_detail(product_id):
    return render_template("urun_penceresi.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/add_to_cart/<product_id>")
def add_to_cart(product_id):
    allowed, response = check_user_access()
    if not allowed:
        return response

    products = load_products()  # dict geliyor

    if product_id not in products:
        return "Ürün bulunamadı", 404

    product = products[product_id]

    if "cart" not in session:
        session["cart"] = {}

    cart = session["cart"]

    if product_id in cart:
        cart[product_id]["quantity"] += 1
    else:
        cart[product_id] = {
            "id": product_id,
            "name": product["name"],
            "price": product["price"],
            "quantity": 1
        }

    session["cart"] = cart

    return redirect(url_for("cart"))


from datetime import datetime

def get_discount_info():
    """Saat bazlı indirim kategorisini ve oranını döndürür."""
    zaman = int(datetime.now().strftime("%H"))
    if 20 <= zaman <= 21: return "books", 0.50
    elif 18 <= zaman < 20: return "plants", 0.30
    elif 16 <= zaman < 18: return "accessories", 0.25
    elif 14 <= zaman < 16: return "potions", 0.40
    elif 12 <= zaman < 14: return "pets", 0.20
    elif 10 <= zaman < 12: return "silah", 0.15
    elif 8 <= zaman < 10:  return "ozel guc", 0.10
    elif 6 <= zaman < 8:   return "koruma", 0.35
    return None, 0

@app.route("/cart")
def cart():
    allowed, response = check_user_access()
    if not allowed:
        return response

    cart = session.get("cart", {})
    products = load_products()
    indirim_kat, oran = get_discount_info()

    cart_items = []
    total_price = 0

    for product_id, item_data in cart.items():
        product = products.get(product_id)
        if not product:
            continue

        # Güncel indirimli fiyat hesaplama
        current_price = product["price"]
        is_disc = False
        if product.get("category") == indirim_kat:
            current_price = round(product["price"] * (1 - oran), 2)
            is_disc = True

        item_total = current_price * item_data["quantity"]
        total_price += item_total

        cart_items.append({
            "id": product_id,
            "name": product["name"],
            "price": current_price,
            "old_price": product["price"],
            "is_discounted": is_disc,
            "discount_rate": int(oran * 100),
            "quantity": item_data["quantity"],
            "total": item_total
        })

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total_price=total_price
    )

@app.route("/remove_from_cart/<product_id>")
def remove_from_cart(product_id):
    cart = session.get("cart", {})
    cart.pop(product_id, None)
    session["cart"] = cart
    return redirect(url_for("cart"))

@app.route("/clear_cart")
def clear_cart():
    session.pop("cart", None)
    return redirect(url_for("cart"))

@app.route("/checkout", methods=["POST"])
def checkout():
    allowed, response = check_user_access()
    if not allowed:
        return response

    cart = session.get("cart", {})
    if not cart:
        return redirect(url_for("cart"))

    products = load_products()
    indirim_kat, oran = get_discount_info()
    
    total_price = 0
    for product_id, item in cart.items():
        product = products.get(product_id)
        if not product:
            continue
        
        # Ödeme anındaki gerçek fiyatı tekrar hesapla (Güvenlik için)
        price = product["price"]
        if product.get("category") == indirim_kat:
            price = round(product["price"] * (1 - oran), 2)
            
        total_price += price * item["quantity"]

    account = load_account(session["username"])
    if account["balance"] < total_price:
        # Hata mesajını url parametresi olarak gönderiyoruz
        return redirect(url_for("cart", message="Yetersiz bakiye!"))

    # Bakiyeden düş ve sepeti sıfırla
    account["balance"] -= total_price
    # İşlem geçmişine (opsiyonel) ekle
    if "transactions" not in account: account["transactions"] = []
    account["transactions"].append({
        "type": "Alışveriş",
        "amount": -total_price,
        "date": datetime.now().strftime("%d.%m.%Y %H:%M")
    })
    
    save_account(session["username"], account)
    session.pop("cart", None)

    return redirect(url_for("magaza", message="Satın alma başarılı!"))

    # 💸 Para düş
    account["balance"] -= total_price
    account["transactions"].append({
        "amount": -total_price,
        "description": "Sepet Satın Alımı",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    save_account(user_id, account)

    # 🧹 Sepeti temizle
    session["cart"] = {}

    return redirect("/purchase_history")


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)