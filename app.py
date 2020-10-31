import os

from flask import Flask
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import FlaskForm

from wtforms import StringField
from wtforms import HiddenField
from wtforms import SubmitField
from wtforms import RadioField
from wtforms.validators import InputRequired


app = Flask(__name__)
# Настраиваем приложение
app.config["DEBUG"] = False
# - URL доступа к БД берем из переменной окружения DATABASE_URL
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "randomstring777"

# Создаем подключение к БД
db = SQLAlchemy(app)
# Создаем объект поддержки миграций
migrate = Migrate(app, db)


teachers_goals_association = db.Table(
    "teachers_goals",
    db.Column("teacher_id", db.Integer, db.ForeignKey("teachers.id"), nullable=False),
    db.Column("goal_id", db.Integer, db.ForeignKey("goals.id"), nullable=False)
)


class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    about = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Float)
    picture = db.Column(db.String)
    price = db.Column(db.Integer, nullable=False)
    goals = db.relationship('Goal', secondary=teachers_goals_association, back_populates='teachers')
    timetables = db.relationship('Timetable', back_populates='teacher')
    bookings = db.relationship('Booking', back_populates='teacher')


class Goal(db.Model):
    __tablename__ = 'goals'
    id = db.Column(db.Integer, primary_key=True)
    goal = db.Column(db.String, nullable=False)
    goal_rus = db.Column(db.String, nullable=False)
    teachers = db.relationship('Teacher', secondary=teachers_goals_association, back_populates='goals')


class Timetable(db.Model):
    __tablename__ = 'timetables'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"))
    teacher = db.relationship('Teacher', back_populates='timetables')
    day = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)
    free = db.Column(db.Boolean, nullable=False)


class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=False)
    day = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"))
    teacher = db.relationship("Teacher", back_populates="bookings")


class Request(db.Model):
    __tablename__ = 'requests'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=False)
    goal = db.Column(db.String, nullable=False)
    weektime = db.Column(db.String, nullable=False)


# Задаем словарики для удобства вывода в шаблонах

days = {'mon': 'Понедельник', 'tue': 'Вторник', 'wed': 'Среда', 'thu': 'Четверг', 'fri': 'Пятница', 'sat': 'Суббота',
        'sun': 'Воскресенье'}
pics = {'travel': '⛱', 'study': '🏫', 'work': '🏢', 'relocate': '🚜', 'programming': '✌'}

# Определяем классы под две формы бронирования (Booking) и запроса (Request)


class BookingForm(FlaskForm):
    clientName = StringField("Вас зовут", [InputRequired()])
    clientPhone = StringField("Ваш телефон", [InputRequired()])
    clientWeekday = HiddenField()
    clientTime = HiddenField()
    clientTeacher = HiddenField()
    submit = SubmitField('Записаться на пробный урок')


class RequestForm(FlaskForm):
    clientGoal = RadioField('Цель', choices=[('Для путешествий', 'Для путешествий'), ('Для учебы', 'Для учебы'),
                                             ('Для работы', 'Для работы'), ('Для переезда', 'Для переезда'),
                                             ('Для программирования', 'Для программирования')],
                            default='Для путешествий')
    clientWeektime = RadioField('Время', choices=[('1-2 часа в неделю', '1-2 часа в неделю'),
                                                  ('3-5 часов в неделю', '3-5 часов в неделю'),
                                                  ('5-7 часов в неделю', '5-7 часов в неделю'),
                                                  ('7-10 часов в неделю', '7-10 часов в неделю')],
                                default='1-2 часа в неделю')
    clientName = StringField("Вас зовут", [InputRequired()])
    clientPhone = StringField("Ваш телефон", [InputRequired()])
    submit = SubmitField('Найдите мне преподавателя')


@app.route('/')
def re_main():
    r_teachers = []
    goals = Goal.query.all()
    teachers = Teacher.query.order_by(db.func.random()).all()
    for teacher in teachers:
        if len(r_teachers) < 6:
            r_teachers.append(teacher)
    return render_template('index.html', r_teachers=r_teachers, goals=goals, pics=pics)


@app.route('/goals/<goal>/')
def re_goals(goal):
    db_goal = db.session.query(Goal).filter(Goal.goal == goal).first()
    return render_template('goal.html', db_goal=db_goal, pics=pics)


@app.route('/profiles/<int:id_teacher>/')
def re_profiles(id_teacher):
    teacher = db.session.query(Teacher).get_or_404(id_teacher)
    # Отлавливаем полностью занятые дни у преподавателя
    full = []
    for day in days:
        flag = 0
        for timetable in teacher.timetables:
            if timetable.day == day:
                if timetable.free:
                    flag = 1
                    break
        if flag == 0:
            full.append(day)
    return render_template('profile.html', teacher=teacher, days=days, full=full)


@app.route('/request/', methods=["GET", "POST"])
def re_request():
    # Отправляем/получаем форму запроса на преподавателя через валидацию
    form = RequestForm()
    if form.validate_on_submit():
        clientGoal = form.clientGoal.data
        clientWeektime = form.clientWeektime.data
        clientName = form.clientName.data
        clientPhone = form.clientPhone.data
        # Заносим запрос в таблицу requests БД
        request = Request(
            name=clientName,
            phone=clientPhone,
            goal=clientGoal,
            weektime=clientWeektime
        )
        db.session.add(request)
        db.session.commit()

        return render_template('request_done.html', request=request)
    return render_template('request.html', form=form)


@app.route('/booking/<int:id_teacher>/<day>/<time>/', methods=["GET", "POST"])
def re_booking(id_teacher, day, time):
    # Отправляем/получаем форму бронирования преподавателя через валидацию
    form = BookingForm()
    if form.validate_on_submit():
        clientName = form.clientName.data
        clientPhone = form.clientPhone.data
        clientWeekday = form.clientWeekday.data
        clientTime = form.clientTime.data
        clientTeacher = int(form.clientTeacher.data)
        # Фиксируем бронь у преподавателя
        free_st = db.session.query(Timetable).filter(
            db.and_(Timetable.teacher_id == clientTeacher, Timetable.day == clientWeekday, Timetable.time == clientTime)
        ).first()
        free_st.free = False
        # Заносим бронирование в таблицу bookings БД
        booking = Booking(
            name=clientName,
            phone=clientPhone,
            day=clientWeekday,
            time=clientTime,
            teacher_id=clientTeacher
        )
        db.session.add(booking)
        db.session.commit()

        return render_template('booking_done.html', booking=booking, days=days)

    teacher = db.session.query(Teacher).get_or_404(id_teacher)
    return render_template('booking.html', teacher=teacher, day=day, time=time, days=days, form=form)


@app.route('/all/')
def re_all():
    # Фильтр всех преподователей из базы по убыванию рейтинга
    goals = db.session.query(Goal).all()
    teachers = db.session.query(Teacher).order_by(Teacher.rating.desc()).all()
    return render_template('all.html', pics=pics, goals=goals, teachers=teachers)


if __name__ == '__main__':
    app.run()
