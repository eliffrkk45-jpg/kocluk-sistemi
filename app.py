from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fatih_hoca_gizli_anahtar_45'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'ogretmen_giris'

class Ogretmen(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

class Veli(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)

class OgrenciDosyasi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ogrenci_adi = db.Column(db.String(100), nullable=False)
    sinif_duzeyi = db.Column(db.String(20), nullable=False)
    bolum = db.Column(db.String(10), nullable=False)
    ders_ismi = db.Column(db.String(50), nullable=False)
    konular = db.Column(db.Text, nullable=False)
    deneme_takip = db.Column(db.Text, nullable=False)
    okudugu_kitap = db.Column(db.String(150), nullable=False)
    hoca_yorumu = db.Column(db.Text, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    if user_id.startswith('ogretmen_'):
        return Ogretmen.query.get(int(user_id.split('_')[1]))
    elif user_id.startswith('veli_'):
        return Veli.query.get(int(user_id.split('_')[1]))
    return None

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/ogretmen-giris', methods=['GET', 'POST'])
def ogretmen_giris():
    if request.method == 'POST':
        k_adi = request.form.get('username')
        sifre = request.form.get('password')
        if k_adi == 'fatihhoca' and sifre == 'fatih45':
            ogretmen = Ogretmen.query.filter_by(username='fatihhoca').first()
            if not ogretmen:
                ogretmen = Ogretmen(username='fatihhoca', password='fatih45')
                db.session.add(ogretmen)
                db.session.commit()
            login_user(ogretmen, id='ogretmen_' + str(ogretmen.id))
            return redirect(url_for('ogretmen_panel'))
        else:
            flash('Hatalı kullanıcı adı veya şifre!', 'danger')
    return render_template('ogretmen_giris.html')

@app.route('/veli-giris', methods=['GET', 'POST'])
def veli_giris():
    if request.method == 'POST':
        veli_adi = request.form.get('veli_adi')
        veli_email = request.form.get('veli_email')
        
        veli = Veli.query.filter_by(email=veli_email).first()
        if not veli:
            veli = Veli(name=veli_adi, email=veli_email)
            db.session.add(veli)
            db.session.commit()
            
        class VeliSession(UserMixin):
            def __init__(self, id, name, email):
                self.id = f"veli_{id}"
                self.name = name
                self.email = email
        
        v_user = VeliSession(veli.id, veli.name, veli.email)
        login_user(v_user)
        return redirect(url_for('veli_panel'))
    return render_template('veli_giris.html')

@app.route('/ogretmen-panel', methods=['GET', 'POST'])
@login_required
def ogretmen_panel():
    if not current_user.get_id().startswith('ogretmen_'):
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        yeni_dosya = OgrenciDosyasi(
            ogrenci_adi=request.form.get('ogrenci_adi').strip(),
            sinif_duzeyi=request.form.get('sinif_duzeyi'),
            bolum=request.form.get('bolum'),
            ders_ismi=request.form.get('ders_ismi'),
            konular=request.form.get('konular'),
            deneme_takip=request.form.get('deneme_takip'),
            okudugu_kitap=request.form.get('okudugu_kitap'),
            hoca_yorumu=request.form.get('hoca_yorumu')
        )
        db.session.add(yeni_dosya)
        db.session.commit()
        flash('Öğrenci dosyası başarıyla kaydedildi!', 'success')
        return redirect(url_for('ogretmen_panel'))
        
    ogrenciler = OgrenciDosyasi.query.all()
    return render_template('ogretmen_panel.html', ogrenciler=ogrenciler)

@app.route('/ogrenci-duzenle/<int:id>', methods=['GET', 'POST'])
@login_required
def ogrenci_duzenle(id):
    if not current_user.get_id().startswith('ogretmen_'):
        return redirect(url_for('index'))
    
    dosya = OgrenciDosyasi.query.get_or_404(id)
    if request.method == 'POST':
        dosya.ogrenci_adi = request.form.get('ogrenci_adi').strip()
        dosya.sinif_duzeyi = request.form.get('sinif_duzeyi')
        dosya.bolum = request.form.get('bolum')
        dosya.ders_ismi = request.form.get('ders_ismi')
        dosya.konular = request.form.get('konular')
        dosya.deneme_takip = request.form.get('deneme_takip')
        dosya.okudugu_kitap = request.form.get('okudugu_kitap')
        dosya.hoca_yorumu = request.form.get('hoca_yorumu')
        
        db.session.commit()
        flash('Öğrenci dosyası güncellendi.', 'success')
        return redirect(url_for('ogretmen_panel'))
        
    return render_template('ogretmen_panel', ogrenci=dosya, ogrenciler=OgrenciDosyasi.query.all())

@app.route('/veli-panel', methods=['GET', 'POST'])
@login_required
def veli_panel():
    if not current_user.get_id().startswith('veli_'):
        return redirect(url_for('index'))
        
    raporlar = None
    aranan_isim = None
    if request.method == 'POST':
        aranan_isim = request.form.get('ogrenci_adi', '').strip()
        if aranan_isim:
            raporlar = OgrenciDosyasi.query.filter(OgrenciDosyasi.ogrenci_adi.ilike(f"%{aranan_isim}%")).all()
            if not raporlar:
                flash('Bu isimle kayıtlı öğrenci raporu bulunamadı.', 'warning')
                
    return render_template('veli_panel.html', raporlar=raporlar, aranan_isim=aranan_isim)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
