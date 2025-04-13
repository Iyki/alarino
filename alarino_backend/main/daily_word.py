from datetime import date
from db_models import Word, DailyWord

def get_word_of_the_day(db, _daily_word_cache):
    today = date.today()

    # Check the in-memory cache first
    if today in _daily_word_cache:
        return _daily_word_cache[today]

    # Check if already selected today in the DB
    existing = DailyWord.query.filter_by(date=today).first()
    if existing:
        _daily_word_cache[today] = existing.word
        return existing.word

    # Get list of previously used word IDs
    used_word_ids = db.session.query(DailyWord.word_id).all()
    used_ids_set = set(word_id for (word_id,) in used_word_ids)

    # Filter Yoruba words that are single-word and not used
    selected_word = (
        Word.query
        .filter(Word.language == 'yo')
        .filter(~Word.word.contains(" "))
        .filter(~Word.id.in_(used_ids_set))
        .order_by(db.func.random())
        .first()
    )

    if not selected_word:
        raise Exception("No unused Yoruba words remaining!")

    # Save to daily_words
    daily = DailyWord(word=selected_word)
    db.session.add(daily)
    db.session.commit()

    # Cache it
    _daily_word_cache[today] = selected_word

    return selected_word
