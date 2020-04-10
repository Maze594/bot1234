from sqlalchemy import and_, Column, create_engine, Integer, String, ForeignKey
from sqlalchemy import and_, Column, create_engine, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql.expression import func
import os

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    viber_id = Column(String, nullable=False)
    last_answer_timestamp = Column(Integer)
    answers = relationship('Answer')

    def __repr__(self):
        return f'User({self.id}, {self.viber_id}, {self.last_answer_timestamp}, {self.answers})'


class Word(Base):
    __tablename__ = 'words'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    word = Column(String, nullable=False, unique=True)
    translation = Column(String, nullable=False)
    examples = relationship('Example')
    answers = relationship('Answer')

    def __repr__(self):
        return f'Word({self.id}, {self.word}, {self.translation}, {self.examples}, {self.answers})'


class Example(Base):
    __tablename__ = 'examples'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    word_id = Column(Integer, ForeignKey('words.id'), nullable=False)
    example = Column(String, nullable=False)

    def __repr__(self):
        return f'Example({self.id}, {self.word_id}, {self.example})'


class Answer(Base):
    __tablename__ = 'answers'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    word_id = Column(Integer, ForeignKey('words.id'), nullable=False)
    answers_count = Column(Integer, nullable=False)
    right_answers_count = Column(Integer, nullable=False)
    last_answer_timestamp = Column(Integer)

    def __repr__(self):
        return f'Answer({self.id}, {self.user_id}, {self.word_id}, {self.answers_count}, {self.right_answers_count}, ' \
               f'{self.last_answer_timestamp})'


class Settings(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    interval = Column(Integer, nullable=False, default=1)
    right_answer_count = Column(Integer, nullable=False, default=10)
    test_length = Column(Integer, nullable=False, default=10)


class Database:
    def __init__(self, connection=None):
        if connection is None:
            self.engine = create_engine(os.getenv('DATABASE_URL'))
        else:
            self.engine = create_engine(connection)
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine, autoflush=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, Exception):
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()
        self.engine.dispose()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def get_settings(self):
        if self.session.query(Settings).count() == 0:
            self.session.add(Settings())
        return self.session.query(Settings).first()

    def get_words(self):
        return self.session.query(Word)

    def fill_words_and_examples(self, words):
        for el in words:
            word = el['word']
            word_from_db = self.session.query(Word).filter(Word.word == word).first()
            if word_from_db is None:
                self.session.add(Word(word=word, translation=el['translation']))
                word_id = self.session.query(Word).filter(Word.word == word).first().id
                for ex in el['examples']:
                    self.session.add(Example(word_id=word_id, example=ex))

    def get_examples(self, word_id=None):
        if word_id is None:
            return self.session.query(Example).all()
        else:
            return self.session.query(Example).filter(Example.word_id == word_id).all()

    def get_answer(self, user_id, word_id):
        return self.session.query(Answer).filter(and_(Answer.word_id == word_id, Answer.user_id == user_id)).one()

    def get_word(self, word_id):
        return self.session.query(Word).filter(Word.id == word_id).first()

    def get_words_indices(self):
        return self.session.query(Word.id).all()

    def get_user(self, viber_id=None, user_id=None):
        if viber_id is not None:
            return self.session.query(User).filter(User.viber_id == viber_id).first()
        elif user_id is not None:
            return self.session.query(User).filter(User.id == user_id).one()

    def add_user(self, viber_id):
        self.session.add(User(viber_id=viber_id))

    def update_user_last_answer_timestamp(self, user_id, timestamp):
        self.session.query(User).filter(User.id == user_id).update(
            {'last_answer_timestamp': timestamp})

    def update_answers_increment_count(self, user_id, word_id, timestamp, answers_count=0, right_answer_count=0):
        self.session.query(Answer).filter(and_(Answer.user_id == user_id, Answer.word_id == word_id)).update(
            {'answers_count': (Answer.answers_count + answers_count),
             'right_answers_count': (Answer.right_answers_count + right_answer_count),
             'last_answer_timestamp': timestamp}
        )

    def create_all_answers(self, user_id):
        for idx in self.get_words_indices():
            self.session.add(Answer(word_id=idx.id, user_id=user_id, answers_count=0, right_answers_count=0))

    def get_answers(self, user_id):
        return self.session.query(Answer).filter(Answer.user_id == user_id).all()

    def get_words_for_question(self, user_id, right_answers_count):
        return self.session.query(Word).join(Answer).filter(
            and_(Answer.user_id == user_id, Answer.right_answers_count < right_answers_count)).all()

    def get_words_for_keyboard_random_limit(self, word_id, limit):
        return self.session.query(Word).filter(Word.id != word_id).order_by(func.random()).limit(limit)

    def get_words_for_keyboard(self, word_id):
        return self.session.query(Word).filter(Word.id != word_id).all()

    def count_right_answers(self, user_id, right_answers_count):
        return self.session.query(Answer).filter(
            and_(Answer.user_id == user_id, Answer.right_answers_count >= right_answers_count)).count()

    def count_words(self):
        return self.session.query(Word).count()

    def get_users_to_notify(self, timestamp, interval_seconds, timed_job_interval):
        return self.session.query(User)\
            .filter(and_(interval_seconds < timestamp - User.last_answer_timestamp,
                         timestamp - User.last_answer_timestamp <= interval_seconds + timed_job_interval))\
            .all()
