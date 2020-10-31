import data

from app import Teacher
from app import Goal
from app import Timetable
from app import db


def seed():
    for key, value in data.goals.items():
        goal = Goal(
            goal=key,
            goal_rus=value
        )
        db.session.add(goal)
    db.session.flush()

    for teacher1 in data.teachers:
        teacher = Teacher(
            name=teacher1['name'],
            about=teacher1['about'],
            rating=teacher1['rating'],
            picture=teacher1['picture'],
            price=teacher1['price']
        )
        db.session.add(teacher)

        for goal in teacher1['goals']:
            db_goal = db.session.query(Goal).filter(Goal.goal == goal).first()
            teacher.goals.append(db_goal)

        for day, time in teacher1['free'].items():
            for key, value in time.items():
                timetable = Timetable(
                    teacher=teacher,
                    day=day,
                    time=key,
                    free=value
                )
                db.session.add(timetable)
    db.session.commit()


if __name__ == '__main__':
    seed()
