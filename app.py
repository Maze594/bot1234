from src.main import app
import os

if __name__ == '__main__':
    from src.database import Database
    from src.words import all_words
    with Database() as database:
        database.fill_words_and_examples(all_words)
        database.commit()
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
