# 
# -*- coding: utf8

from collections import namedtuple, defaultdict, Counter
import codecs 
import re
import pymorphy2
from dawg import CompletionDAWG, RecordDAWG


wordParams    = namedtuple('wordParams', ['transcript', 'accent', 'normal', 'morph'])
wordsFname    = "/home/pi/lisa/Pushkinizer/texts/ahmadulina.utf8.txt"
stressFname   = "/home/pi/lisa/Pushkinizer/dict/Rythm.dawg"
morphFname    = "/home/pi/lisa/Pushkinizer/dict/all-forms.utf8.txt"

class PoetryDict() :
   """Dictionary for poetry"""
   vowels = u"еиаоуыюяэё"

   def __init__(self) :
      self.baseDict = defaultdict(list)
      self.baseDict[u'строка'].append(wordParams(u'страка', -1, u'страка', 'NOUN, inan, femn sign, nomn'))
      self.revDict = list()
      self.revDict.append(reverse(u'строка'))
      self.helperDict = list()
      self.stressDict = defaultdict(list)
      self.rhymeDict = None
      
   def __repr__(self) :
      """ печать информации о словаре """
      #return self.baseDict.__repr__()  + self.revDict.__repr__()
      return "Instance of PoetryDict class consists of " + str(len(self.baseDict)) + " wordforms and " + str(len(self.revDict)) + " reverses." 
     
   def prettyPrint(self, fm = 0, to = 10) :
      """ печать нескольких слов (по умолчанию 10), из словаря и их морфологических свойств """
      i = 0;
      for w in self.baseDict : 
         if i >= fm : 
            print w
            for e in self.baseDict[w] :
               print " " + e.__repr__()
         elif i > to :
            return
         i += 1 
      
   def readFromFile(self, fname) :
      """ читаем строки из файла, токенизируем, преобразуем в нижний регистр, автоматически удаляем повторения, сортируем,
          выкидываем всё, что не слова (то есть  4тверка это не слово, но whoisкто - пока что слово) """
      s = set()
      with codecs.open(fname, encoding="utf8") as f :
         for l in f :
            s.update(map(unicode.lower, filter(unicode.isalpha, tokenize(l))))
      self.helperDict = list(s)
      s.clear()
      self.helperDict.sort()
   
   def addMorphInfo(self) :
      """ Добавляем морфологическую информацию к слову из opencorpora """
      ma = pymorphy2.MorphAnalyzer()
      for e in self.helperDict :
         res = ma.parse(e)
         for el in res :
            self.baseDict[e].append(wordParams(u'', 0, el.normal_form, el.tag))

   def readStressFile(self, fname = "") :
      # ERROR: в словаре не проставлены ударения для слов с ё, надо исправить
      self.rhymeDict = CompletionDAWG()
      if fname =="" :
         self.rhymeDict.load(stressFname)
      else  :
         self.rhymeDict.load(fname)
      print 'Done'
         
      # информация для морфологического рабора
      # 6,12,13,14 слов после хэша - существительное
      # 29.32-39 слов - прилагательное
      # 42-178 слов глагол
      # 1 слово - наречие, союз, предлог

   def Stressofizer(self, word) : 
      """ Расставляем ударения, Пользуемся внешним словарем. Возвращаем список вариантов. Тупой перебор"""

      word = word.strip().lower()

      # для каждой гласной буквы слова
      # добавляем после нее знак ударения и ищем слово с словаре рифм (пока что)
      # к сожалению, методом replace для строки воспользоваться не получится
      # так как он заменяет все вхождения
      # в итоге получается немного громоздко

      result = []
      for idx in range(0, len(word)) :
         if word[idx] in self.vowels :
            # добавили после гласной символ ударения. питон не ругается, если индексы выходят за границы строки
            testword = word[0:idx+1] + u"'" + word[idx+1:]   
            print "проверяем вариант ",   testword
            # как всегда, в словаре рифм ищутся перевернутые слова
            if reverse(testword) in self.rhymeDict :
               result.append(testword)
      return result
      
      # Тест : d.Stressofizer(u"замок") -> [u"за'мок", u"зам'ок"]
      # ERROR: для сложносочиненных слов увы не работает так как в словаре у них два ударения: а`виастрои'тель


   def Rhyme(self, word) :
      """ Возвращает список слов, рифмующихся с данным словом. Слово должно быть передано вместе с ударением """
      # важное замечание - рифмовать, конечно, надо траскрипции слов, а не их написание, но подходящего словаря не нашлось
      # Литература: Онуфриев В.В. Словарь разновидностей рифмы
      #             В. Жирмунский. Рифма, её история и теория
      #
      # Наивная (хотя книжки пишут - богатая), рифма.

      # от слова бараба'нщик берем максимальное подслово - бараба'нщик и ищем все слова, оканчивающиеся на
      # данное подслово, получаем (условно) лучшую рифму
      # затем берем подслово араба'нщик и опять ищем все слова, оканчивающиеся на данное подслово
      # так поступаем до подслова а'нщик 
      # функция self.rhymeDict.keys("строка") автоматически ищет в словаре рифм (инверсионный словарь) 
      # все ключи, включающие в себя заданную строку
      
      # данный подход не срабатывает, когда слово оканчивается на ударную гласную, например, для слова пелена'
      # найдено более 7500 якобы рифм. Пока непонятно как постапуть в таких случаях.
      
      # наиболее очевидный способ создания бедной рифмы - модификация исходного слова и поиск рифм для него
      # в функциях ниже YottedRhyme (йотированная рифма) AssonanceRhyme (ассонансная, созвучная рифма) пытаюсь
      # это фоплотить
      
      # приятно, что ищет рифму также к слову, которого нет в словаре 
      
      word = word.strip()
      idx = word.find(u"'") 
      if idx == -1:
         print "Ключевое слово '", word, "' должно быть передано с ударением"
         return
      
      result = []
      for i in range(0, idx) :
         # из слова-перевертыша берем подстроку, начиная с самой длинной и ищем для нее все рифмы
         # получаем список рифм для данного подслова
         s = map(reverse, self.rhymeDict.keys(reverse(word[i:])))
         # добавляем из s в список result только те рифмы, которых там еще нет
         for w in s :
            if not w in result : result.append(w)
         print "Ищем слова, оканчивающиеся на ", word[i:], ", найдено: ", len(s)
         # так у нас получается список, в начале которого стоят лучшие рифмы,
         # осталось удалить из выдачи само слово, которое мы рифмуем
         if word in result : result.remove(word)
      return result
      
   def YottedRhyme(self, word) :
      # самое простое для реализации - йотированная рифма. Нельзя удержаться и не сделать это
      # "равносложная рифма из слов с закрытым и открытым слогом, при этом последний заканчивается на й"
      # "поле - волей, тучи - летучий"
      # 
      word = word.strip() 
      # если слово заканчивается на гласную, добавляем й в конце и ищем рифму
      if word[-1] in u"аеиоуыэ" :
         print "Поиск йотированной рифмы к слову ", word
         return self.Rhyme(word + u'й')
      # если наоборот слово заканчивается на 'й' удалаем ее и ищем рифмы
      if word[-1] in u"й" :
         print "Поиск рифмы к йотированному слову"
         return self.Rhyme(word[0:-1])
      # если слово заканчивается на ёюя ... пока думаю
      # если буква ударная, то надо искать также и среди замен ёюя на оуа
      # кстати и для ударной е,
   
   def AssonanceRhyme(self, word) :
      # совпадает гласный ударный звук, но несовпадают согласные
      return word
   
   def ConsonanceRhyme(self, word) :
      # рифма с совпадение согласных звуков и неточным совпадением гласных
      # в частности редукция заударных а<->о, в меньшей степени е<->и, еще меньше и<->ы, и почти никогда для у
      
      # каламбурная рифма: теперь я - те перья, до канала - доканала, по калачу - поколочу
      # мультирифма: центральная базовая рифма с одним послеударным согласным звуком
      # день - тень, дым - летим (о, тут редукция гласной), рок - звонок
      # удвоенная согласная может выкидиваться
      
      # усеченная рифма, частным случаем которой является йотированная рифма,
      # то есть есть лишний согласный звук в одном из рифмующихся слов
      # друг - звук, крик - миг, веторок - мог
      return word
      
def reverse(str) :
   """ Возвращает строку задом наперед """
   return str[::-1]
   # return "".join(reversed(s))
   

GROUPING_SPACE_REGEX = re.compile('([^\w_-]|[+])', re.U)

# слово должно начинаться с буквы, может содержать дефис или акцент' или слабый акцент` (увы не только 1), заканчиваться буквой или акцентом
TOKEN_REGEX = re.compile(u"[a-zA-Zа-яёЁА-Я][a-zA-Zа-яёЁА-Я'-]+[a-zA-Zа-яёЁА-Я']", re.UNICODE)

def tokenize(text):
   """ Разделяем текст на токены (недослова). не делим красное-прекрасное по черточке, но делим красное - прекрасное по тире 
       уродцы типа то4ка делятся на [то, ка]. Возвращаем список недослов """
   #return [t for t in GROUPING_SPACE_REGEX.split(text)
   #        if t and not t.isspace()]
   return re.findall(TOKEN_REGEX, text)


def createStressDictionary(self, fname) :
      """ читаем строки из файла, слово до хештега становиться ключем словаря, все остальное - строка в словаре при данном ключе,
          так как слово до хэштега может иметь омонимы, то эта строка еще и элемент списка
          то есть мы не токенизируем словарную статью
      """
      # Используемого словарь
      # "Полная акцентуированная парадигма по А.А.Зализняку"
      # www.speakrus.ru/dict/all_forms.rar
      #
      # ФОРМАТ такой
      # беляши#беляши',беляше'й,беляша'м,беляши',беляша'ми,беляша'х
      # слова, содержащие ё, не акцентуированы,
      # сложные слова, например а`виаба'за,а`виаба'зы, акцентуированы по каждой из частей.
      # предварительно словарь переведен в кодировку utf-8
      # слова с ё не размечены
      # предлоги не размечены
      
      with codecs.open(fname, encoding="utf8") as f :
         lc = 0
         for l in f :
            # надо символы перевода строки убрать, перевести все маленькие буквы, затем разделить строку на две по символу #
            wl = l.strip().lower().split('#')
            # делаем все буквы ё ударными, ищем все ё, заменяем на ё'
            # ERROR: я не знаю, есть ли слова с двумя ё
            wl[0].replace(u"ё", u"ё'")
            # записываем строку в словарь, ключ которого - нормальная форма слова, значение - строка словоформ
            self.stressDict[wl[0]].append(wl[1])
            lc = lc+1
         print lc, " lines read from ", stressFname
         
      # подсчет статистики словоформ для каждой нормальной формы
      stat = Counter()
      for l in self.stressDict.itervalues() :
         for s in l :
            wc = len(s.split(u','))
            stat[wc] += 1
      print stat
      
      # разбиваем файл словаря на несколько подсловарей, в каждом из которых 
      # н-ное количество словоформ
      # это пока не актуально, так как морфемы для рифм не помечены
#      
#      files = stat
#      path  = '/home/pi/lisa/Pushkinizer/'
#
#      for k in stat :
#         files[k] = codecs.open(path + str(k) + ".txt", mode="w", encoding="utf8")
#
#      for (kee,l) in self.stressDict.iteritems() :
#         for s in l :
#            wc = len(s.split(u','))
#            files[wc].write(kee + "#" + s)
#
#      for k in stat :
#         files[k].close()
#
#      print 'Stresses dictionary splitted to ', str(len(stat)), ' parts'
      
      # пробуем сделать словарь рифм, просто создав список ударных слов, записанных задом наперед
      # инверсионный словарь
      self.rhymeList = [];
      for l in self.stressDict.itervalues() :
         for s in l :
            # получили строку слов, разделенных запятыми, надо превратить ее в список слов,
            # затем отфильтровать его от пустых слов, затем переписать его задом наперед

            self.rhymeList.extend(filter(lambda x : len(x) > 0,map(unicode.strip, map(reverse, s.split(u',')))))

      print 'rhymeList created, size = ' + str(len(self.rhymeList))
      #self.rhymeList.sort()
      print 'Из списка рифм создаем словарь с возможностью автодополнения' 
      tmpDict = CompletionDAWG(rhymeList)
      print 'Сохраняем файл rhyme.dawg'
      tmpDict.save('rhyme.dawg')
      print 'DONE'

   