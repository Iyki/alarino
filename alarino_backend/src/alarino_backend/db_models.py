from datetime import date, datetime
from sqlalchemy import Index, String, Text, func
from sqlalchemy import text as sql_text
from sqlalchemy.types import TypeDecorator

from alarino_backend.flask_extensions import db
from alarino_backend.normalization import normalize_text, normalize_word_text


class NFCWord(TypeDecorator):
    """Word-level canonical text column. Mirrors normalize_word_text():
    strip outer whitespace + punctuation, lowercase, then NFC. Applied at
    SQLAlchemy bind time so every ORM write *and* every parameterized query
    against this column normalizes the value, regardless of whether the
    call site remembered to. Defense against a class of drift bugs we
    repeatedly hit during the schema evolution work."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return normalize_word_text(value)


class NFCText(TypeDecorator):
    """Sentence/proverb-level canonical text column. Mirrors normalize_text():
    strip leading and trailing whitespace then NFC. Case and inner punctuation
    preserved. Same bind-time normalization guarantee as NFCWord."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return normalize_text(value)

class Word(db.Model):
    __tablename__ = 'words'

    w_id = db.Column(db.Integer, primary_key=True)
    language = db.Column(db.String(3), nullable=False)
    word = db.Column(NFCWord(200), nullable=False)  ##todo: rename to text
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
    # Phase 6a additions: senses are between Word and Translation. These FKs
    # are nullable in 6a (backfilled from one-sense-per-word during the
    # migration) and become NOT NULL in 6d after the cutover. Read paths in
    # 6c will use these to group polysemous matches; write paths in 6b will
    # require them on every new Translation.
    source_sense_id = db.Column(
        db.Integer,
        db.ForeignKey('senses.sense_id', name='fk_translations_source_sense_id', ondelete='CASCADE'),
        nullable=True,
    )
    target_sense_id = db.Column(
        db.Integer,
        db.ForeignKey('senses.sense_id', name='fk_translations_target_sense_id', ondelete='CASCADE'),
        nullable=True,
    )
    note = db.Column(db.Text, nullable=True)
    confidence = db.Column(db.Float, nullable=True)
    provenance = db.Column(db.String(40), nullable=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
        server_default=func.now(),
    )

    source_word = db.relationship('Word', foreign_keys=[source_word_id], backref='translations_from')
    target_word = db.relationship('Word', foreign_keys=[target_word_id], backref='translations_to')
    source_sense = db.relationship('Sense', foreign_keys=[source_sense_id])
    target_sense = db.relationship('Sense', foreign_keys=[target_sense_id])

    __table_args__ = (
        db.UniqueConstraint('source_word_id', 'target_word_id', name='unique_translation_pair'),
        # target_word_id index supports reverse-direction joins; source_word_id
        # is already covered by the unique_translation_pair constraint prefix.
        Index('idx_translations_target_word_id', 'target_word_id'),
    )

    def __repr__(self):
        return f"<Translation {self.source_word.word} -> {self.target_word.word}>"


class Sense(db.Model):
    __tablename__ = 'senses'

    sense_id = db.Column(db.Integer, primary_key=True)
    word_id = db.Column(
        db.Integer,
        db.ForeignKey('words.w_id', ondelete='CASCADE'),
        nullable=False,
    )
    # part_of_speech is duplicated on Word during Phases 6a-6c (read paths still
    # use Word.part_of_speech). The Word column is dropped in Phase 6d once the
    # sense layer is fully load-bearing.
    part_of_speech = db.Column(db.String(20), nullable=True)
    sense_label = db.Column(db.String(80), nullable=True)
    definition = db.Column(db.Text, nullable=True)
    register = db.Column(db.String(40), nullable=True)
    domain = db.Column(db.String(80), nullable=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
        server_default=func.now(),
    )

    word = db.relationship('Word', backref='senses')

    __table_args__ = (
        Index('idx_senses_word_id', 'word_id'),
    )

    def __repr__(self):
        return f"<Sense {self.sense_id} for word {self.word_id} label={self.sense_label!r}>"


class DailyWord(db.Model):
    __tablename__ = "daily_words"

    dw_id = db.Column(db.Integer, primary_key=True)
    # Phase 5: replaces word_id + en_word_id with a single FK to the translation
    # pair. Makes "daily word is a translation pair" a structural fact instead
    # of a conventional pairing of two unrelated word_id columns. Read paths
    # derive the Yoruba and English sides by joining Word and inspecting
    # Word.language — never by assuming a column position.
    translation_id = db.Column(
        db.Integer,
        db.ForeignKey('translations.t_id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
    )
    date = db.Column(db.Date, default=date.today, unique=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
        server_default=func.now(),
    )

    translation = db.relationship("Translation")

    __table_args__ = (
        # Add index on date for faster lookups of daily words
        Index('idx_daily_words_date', 'date'),
    )

    def __repr__(self):
        return f"<DailyWord translation_id={self.translation_id} for {self.date}>"


class MissingTranslation(db.Model):
    __tablename__ = 'missing_translations'

    m_id = db.Column(db.Integer, primary_key=True)
    text = db.Column(NFCWord(200), nullable=False)
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
    # Phase 6b additions: examples are sense-scoped, not just translation-scoped
    # (an example for "bank — financial institution" shouldn't appear under
    # "bank — riverbank"). Nullable here in 6b so the backfill can run
    # incrementally; tightened in 6d. translation_id is intentionally kept
    # until 6d so the existing relationship and read path keep working.
    source_sense_id = db.Column(
        db.Integer,
        db.ForeignKey('senses.sense_id', name='fk_examples_source_sense_id', ondelete='CASCADE'),
        nullable=True,
    )
    target_sense_id = db.Column(
        db.Integer,
        db.ForeignKey('senses.sense_id', name='fk_examples_target_sense_id', ondelete='CASCADE'),
        nullable=True,
    )
    example_source = db.Column(db.Text, nullable=False)
    example_target = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
        server_default=func.now(),
    )

    translation = db.relationship('Translation', backref='examples')
    source_sense = db.relationship('Sense', foreign_keys=[source_sense_id])
    target_sense = db.relationship('Sense', foreign_keys=[target_sense_id])

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
    yoruba_text = db.Column(NFCText, nullable=False)
    english_text = db.Column(NFCText, nullable=False)
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
