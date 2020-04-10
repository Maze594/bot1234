class UserContext:
    def __init__(self, words_ids):
        self.words_ids = words_ids
        self.testing = False
        self.test_num = 0
        self.counter = 0
        self.keyboard = None
