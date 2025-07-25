from datetime import date, datetime
from main import db
from sqlalchemy import Index

class Word(db.Model):
    __tablename__ = 'words'

    w_id = db.Column(db.Integer, primary_key=True)
    language = db.Column(db.String(3), nullable=False)
    word = db.Column(db.String(200), nullable=False)  ##todo: rename to text
    part_of_speech = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.now())

    __table_args__ = (
        db.UniqueConstraint('language', 'word', name='unique_language_word'),
        # Add index on language and word for faster lookups
        Index('idx_words_language_word', 'language', 'word'),
        # Add index on just language for filtering words by language
        Index('idx_words_language', 'language'),
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
        # Add indexes for faster joins and lookups
        Index('idx_translations_source_word_id', 'source_word_id'),
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
    created_at = db.Column(db.DateTime, default=datetime.now)

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
    user_ip = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    hit_count = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint('text', 'source_language', 'target_language', name='unique_missing_translation'),
        # Add composite index for faster lookups
        Index('idx_missing_text_source_target', 'text', 'source_language', 'target_language'),
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
    created_at = db.Column(db.DateTime, default=datetime.now)

    translation = db.relationship('Translation', backref='examples')

    def __repr__(self):
        return f"<Example for Translation {self.translation_id}>"


class Proverb(db.Model):
    __tablename__ = 'proverbs'

    p_id = db.Column(db.Integer, primary_key=True)
    yoruba_text = db.Column(db.Text, nullable=False)
    english_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint('yoruba_text', 'english_text', name='unique_proverb_pair'),
        Index('idx_proverbs_yoruba_text', 'yoruba_text'),
    )

    def __repr__(self):
        return f"<Proverb Yoruba: '{self.yoruba_text}' English: '{self.english_text}'>"