from datetime import datetime
from alarino_backend import db

class Word(db.Model):
    __tablename__ = 'words'

    w_id = db.Column(db.Integer, primary_key=True)
    language = db.Column(db.String(3), nullable=False)
    word = db.Column(db.String(200), nullable=False)
    part_of_speech = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.now())

    __table_args__ = (
        db.UniqueConstraint('language', 'word', name='unique_language_word'),
    )

    def __repr__(self):
        return f"<Word {self.language}:{self.word}>"


class Translation(db.Model):
    __tablename__ = 'translations'

    t_id = db.Column(db.Integer, primary_key=True)
    source_word_id = db.Column(db.Integer, db.ForeignKey('words.w_id', ondelete='CASCADE'), nullable=False)
    target_word_id = db.Column(db.Integer, db.ForeignKey('words.w_id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    source_word = db.relationship('Word', foreign_keys=[source_word_id], backref='translations_from')
    target_word = db.relationship('Word', foreign_keys=[target_word_id], backref='translations_to')

    __table_args__ = (
        db.UniqueConstraint('source_word_id', 'target_word_id', name='unique_translation_pair'),
    )

    def __repr__(self):
        return f"<Translation {self.source_word.word} -> {self.target_word.word}>"


class Example(db.Model):
    __tablename__ = 'examples'

    e_id = db.Column(db.Integer, primary_key=True)
    translation_id = db.Column(db.Integer, db.ForeignKey('translations.t_id', ondelete='CASCADE'), nullable=False)
    example_source = db.Column(db.Text, nullable=False)
    example_target = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    translation = db.relationship('Translation', backref='examples')

    def __repr__(self):
        return f"<Example for Translation {self.translation_id}>"


class MissingTranslation(db.Model):
    __tablename__ = 'missing_translations'

    m_id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    source_language = db.Column(db.String(3), nullable=False)
    target_language = db.Column(db.String(3), nullable=False)
    user_ip = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    hit_count = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint('text', 'source_language', 'target_language', name='unique_missing_translation'),
    )

    def __repr__(self):
        return f"<Missing '{self.text}' from {self.source_language} to {self.target_language}>"
