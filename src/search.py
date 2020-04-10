# from typing import List
# import nltk.data
#
#
# def search_entries(word: str, count: int) -> List[str]:
#     word = word.lower()
#     count = max(0, count)
#     if count == 0:
#         return []
#
#     with open(r'../texts/01 - The Fellowship Of The Ring.txt', 'r', encoding='cp1252') as f:
#         result = []
#         paragraph = []
#         counted = False
#         for line in f:
#             paragraph.append(line)
#
#             # paragraph
#             if line.strip() == '':
#                 if counted:
#                     result.append(''.join(paragraph))
#                     count -= 1
#                     counted = False
#                 paragraph.clear()
#                 if count == 0:
#                     break
#
#             if not counted and word in line.lower():
#                 counted = True
#         if counted:
#             result.append(''.join(paragraph))
#
#         return result
#
#
# def search_entries_sentences(word: str, count: int) -> List[str]:
#     word = word.lower()
#     count = max(0, count)
#     if count == 0:
#         return []
#
#     import nltk.data
#
#     result = []
#     text = open(r'../texts/01 - The Fellowship Of The Ring.txt', 'r', encoding='cp1252').read()
#     sent_tokenize = nltk.data.load(r'../nltk_data/tokenizers/punkt/english.pickle')
#     for sentence in sent_tokenize.tokenize(text.strip()):
#         if word in sentence.lower().split():
#             result.append(sentence)
#             count -= 1
#             if count == 0:
#                 break
#     return result
#
#
# # Текст разбитый на предложения
# full_text = open(r'../texts/01 - The Fellowship Of The Ring.txt', 'r', encoding='cp1252').read()
# tokenize = nltk.data.load(r'../nltk_data/tokenizers/punkt/english.pickle')
# sentences = tokenize.tokenize(full_text.strip())
# del full_text
# del tokenize
#
#
# def search_entries_idx(word: str, count: int, offset: int = 0) -> List[int]:
#     word = word.lower()
#     count = max(0, min(10, count))  # Не больше 10 вхождений слов за 1 раз
#     assert offset >= 0
#
#     result = []
#     while count > 0 and offset < len(sentences):
#         if word in sentences[offset].lower().split():
#             result.append(offset)
#             count -= 1
#         offset += 1
#     return result
#
#
# def join_sentences(indexes: List[int], s: str = '\n') -> str:
#     return s.join((sentences[i] for i in indexes))
