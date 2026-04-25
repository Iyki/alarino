from datetime import date, datetime
from sqlalchemy import Index, func
from sqlalchemy import text as sql_text

from alarino_backend.flask_extensions import db

class Word(db.Model):
    __tablename__ = 'words'

    w_id = db.Column(db.Integer, primary_key=True)
    language = db.Column(db.String(3), nullable=False)
    word = db.Column(db.String(200), nullable=False)  ##todo: rename to text
    part_of_speech = db.Column(db.String(20))
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
        server_default=func.now(),
    )

    __table_args__ = (
        db.UniqueConstraint('language', 'word', name='unique_language_word'),
        db.CheckConstraint(
            "language IN ('en', 'yo')",
            name='ck_words_language_valid',
        ),
    )

    def __repr__(self):
        return f"<Word {self.language}:{self.word}>"


class Translation(db.Model):
    __tablename__ = 'translations'

    t_id = db.Column(db.Integer, primary_key=True)
    source_word_id = db.Column(db.Integer, db.ForeignKey('words.w_id', ondelete='CASCADE'), nullable=False)
    target_word_id = db.Column(db.Integer, db.ForeignKey('words.w_id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
        server_default=func.now(),
    )

    source_word = db.relationship('Word', foreign_keys=[source_word_id], backref='translations_from')
    target_word = db.relationship('Word', foreign_keys=[target_word_id], backref='translations_to')

    __table_args__ = (
        db.UniqueConstraint('source_word_id', 'target_word_id', name='unique_translation_pair'),
        # target_word_id index supports reverse-direction joins; source_word_id
        # is already covered by the unique_translation_pair constraint prefix.
        Index('idx_translations_target_word_id', 'target_word_id'),
    )

    def __repr__(self):
        return f"<Translation {self.source_word.word} -> {self.target_word.word}>"


class DailyWord(db.Model):
    __tablename__ = "daily_words"

    dw_id = db.Column(db.Integer, primary_key=True)
    word_id = db.Column(db.Integer, db.ForeignKey("words.w_id"), nullable=False)
    en_word_id = db.Column(db.Integer, db.ForeignKey("words.w_id"), nullable=False)
    date = db.Column(db.Date, default=date.today, unique=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
        server_default=func.now(),
    )

    word = db.relationship("Word", foreign_keys=[word_id])
    en_word = db.relationship("Word", foreign_keys=[en_word_id])

    __table_args__ = (
        # Add index on date for faster lookups of daily words
        Index('idx_daily_words_date', 'date'),
    )

    def __repr__(self):
        return f"<DailyWord {self.word.word} for {self.date}>"


class MissingTranslation(db.Model):
    __tablename__ = 'missing_translations'

    m_id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    source_language = db.Column(db.String(3), nullable=False)
    target_language = db.Column(db.String(3), nullable=False)
    user_agent = db.Column(db.Text)
    hit_count = db.Column(
        db.Integer,
        nullable=False,
        default=1,
        server_default=sql_text("1"),
    )
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
        server_default=func.now(),
    )

    __table_args__ = (
        db.UniqueConstraint('text', 'source_language', 'target_language', name='unique_missing_translation'),
        db.CheckConstraint(
            "source_language IN ('en', 'yo')",
            name='ck_missing_translations_source_language_valid',
        ),
        db.CheckConstraint(
            "target_language IN ('en', 'yo')",
            name='ck_missing_translations_target_language_valid',
        ),
        # Add index on hit_count to quickly find most requested missing translations
        Index('idx_missing_hit_count', 'hit_count', postgresql_ops={'hit_count': 'DESC'}),
    )

    def __repr__(self):
        return f"<Missing '{self.text}' from {self.source_language} to {self.target_language}>"


class Example(db.Model):
    __tablename__ = 'examples'

    e_id = db.Column(db.Integer, primary_key=True)
    translation_id = db.Column(db.Integer, db.ForeignKey('translations.t_id', ondelete='CASCADE'), nullable=False)
    example_source = db.Column(db.Text, nullable=False)
    example_target = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
        server_default=func.now(),
    )

    translation = db.relationship('Translation', backref='examples')

    __table_args__ = (
        db.UniqueConstraint(
            'translation_id',
            'example_source',
            'example_target',
            name='unique_example_per_translation',
        ),
    )

    def __repr__(self):
        return f"<Example for Translation {self.translation_id}>"


class Proverb(db.Model):
    __tablename__ = 'proverbs'

    p_id = db.Column(db.Integer, primary_key=True)
    yoruba_text = db.Column(db.Text, nullable=False)
    english_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
        server_default=func.now(),
    )

    __table_args__ = (
        db.UniqueConstraint('yoruba_text', 'english_text', name='unique_proverb_pair'),
    )

    def __repr__(self):
        return f"<Proverb Yoruba: '{self.yoruba_text}' English: '{self.english_text}'>"


class ProverbWord(db.Model):
    __tablename__ = 'proverb_words'

    proverb_id = db.Column(
        db.Integer,
        db.ForeignKey('proverbs.p_id', ondelete='CASCADE'),
        primary_key=True,
    )
    word_id = db.Column(
        db.Integer,
        db.ForeignKey('words.w_id', ondelete='CASCADE'),
        primary_key=True,
    )
    language = db.Column(db.String(3), primary_key=True)
    # position is the 0-indexed order of the word within its language sequence
    # in the proverb. Repeated occurrences of the same word get distinct
    # position values so the composite PK stays unique.
    position = db.Column(db.Integer, primary_key=True)

    proverb = db.relationship('Proverb', backref='proverb_words')
    word = db.relationship('Word')

    __table_args__ = (
        db.CheckConstraint(
            "language IN ('en', 'yo')",
            name='ck_proverb_words_language_valid',
        ),
        Index('idx_proverb_words_word_id', 'word_id'),
    )

    def __repr__(self):
        return (
            f"<ProverbWord proverb={self.proverb_id} word={self.word_id} "
            f"lang={self.language} pos={self.position}>"
        )
