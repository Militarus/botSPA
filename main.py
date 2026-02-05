from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

# Настройка приложения
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Модель таблицы
class EquipmentRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    place = db.Column(db.String(100))
    equipment = db.Column(db.String(100))
    part = db.Column(db.String(100))
    key = db.Column(db.String(100), unique=True)
    description = db.Column(db.Text())

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/add', methods=['GET', 'POST'])
def add_record():
    if request.method == 'POST':
        new_record = EquipmentRecord(
            place=request.form.get('place'),
            equipment=request.form.get('equipment'),
            part=request.form.get('part'),
            key=request.form.get('key'),
            description=request.form.get('description')
        )
        try:
            db.session.add(new_record)
            db.session.commit()
            return redirect(url_for('view_records'))
        except Exception as e:
            print(e)
            return "Ошибка при добавлении записи."
    else:
        return render_template('add_record.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_record(id):
    record = EquipmentRecord.query.get_or_404(id)
    if request.method == 'POST':
        record.place = request.form.get('place')
        record.equipment = request.form.get('equipment')
        record.part = request.form.get('part')
        record.key = request.form.get('key')
        record.description = request.form.get('description')
        try:
            db.session.commit()
            return redirect(url_for('view_records'))
        except Exception as e:
            print(e)
            return "Ошибка при обновлении записи."
    else:
        return render_template('edit_record.html', record=record)

@app.route('/delete/<int:id>')
def delete_record(id):
    record_to_delete = EquipmentRecord.query.get_or_404(id)
    try:
        db.session.delete(record_to_delete)
        db.session.commit()
        return redirect(url_for('view_records'))
    except Exception as e:
        print(e)
        return "Ошибка при удалении записи."

@app.route('/records')
def view_records():
    records = EquipmentRecord.query.all()
    return render_template('view_records.html', records=records)

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Создать базу данных перед первым запуском
    app.run(debug=True)