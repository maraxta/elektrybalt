# 
# -*- coding: utf8

from collections import namedtuple, defaultdict, Counter
import codecs 
import re
import pymorphy2
from dawg import CompletionDAWG, RecordDAWG


# вау, чтобы работало автодополнение по нажатию Tab
# надо только поискать вопрос на SO: How do i add tab completion to python shell
#
import rlcompleter
import readline
readline.parse_and_bind("tab: complete")

wordParams      = namedtuple('wordParams', ['transcript', 'accent', 'normal', 'morph'])
wordsFname      = ".home/pi/lisa/Pushkinizer/texts/ahmadulina.utf8.txt"
accentDictFname = "dict/union1.dawg"
inputFname      = "/home/pi/lisa/Pushkinizer/dict/all-forms.utf8.txt"

#гласные
vowels    = u"еиаоуыюяэё"
alphabet  = u"абвгдеёжзийклмнопрстуфхцчшщъыьэюя"

# словарь замен заударных глухих и звонких согласных
consonantsReplaces = {u"к":u"г",u"г":u"к",u"ф":u"в",u"в":u"ф",u"ж":u"ш",u"ш":u"ж",u"ч":u"щ",u"щ":u"ч",u"д":u"т",u"т":u"д"}


class Poet() :
   """eletric poet, nothing special"""

   def __init__(self) :
      self.baseDict = defaultdict(list)
      self.baseDict[u'строка'].append(wordParams(u'страка', -1, u'страка', 'NOUN, inan, femn sign, nomn'))
      self.revDict = list()
      self.revDict.append(reverse(u'строка'))
      self.helperDict = list()
      # self.accentDict - словарь из библиотеки DAWG, инициализируется объектом типа CompletionDAWG, в функции read...FromFile()
      self.accentDict = CompletionDAWG()
      self.compReplaces = self.accentDict.compile_replaces(replaces)

      
   def __repr__(self) :
      """ печать информации о словаре """
      #return self.baseDict.__repr__()  + self.revDict.__repr__()
      return "Instance of Poet class consists of " + str(len(self.accentDict)) + " wordforms and " + str(len(self.revDict)) + " reverses." 
     
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

   def loadAccentDict(self, fname = accentDictFname) :
      self.accentDict.load(fname)
      print 'Done'
         
   def setAccent(self, word) : 
      """ Расставляем ударения, Пользуемся внешним словарем. Возвращаем список вариантов. Тупой перебор"""

      word = word.strip().lower()

      if u"'" in word :
         return [word]

      # после каждой гласной буквы добавляем знак ударения и ищем слово с словаре accentDict (пока что)
      # к сожалению, методом replace для строки воспользоваться не получится, так как он заменяет все вхождения.
      # в итоге получается немного громоздко

      result = []
      for i in range(len(word)) :
         if word[i] in vowels :
            # добавили после гласной символ ударения. питон не ругается, если индексы выходят за границы строки в слайсе
            testword = word[0:i+1] + u"'" + word[i+1:]   
            # print "проверяем вариант ",   testword
            # как всегда, в словаре рифм ищутся перевернутые слова
            if reverse(testword) in self.accentDict :
               result.append(testword)
      if len(result) == 0 :
         print u"Не найдено ни одного варианта ударения слова <<" + word + u">>"

      return result
      
      # Тест : d.setAccent(u"замок") -> [u"за'мок", u"зам'ок"]
      # ERROR: для сложносочиненных слов увы не работает так как в словаре у них два ударения: а`виастрои'тель
      #        а символ (`) называется гравис, или знак побочного ударения

   def formatVerse(self, text) :
      """ Печатает переданный текст, вместе с ритмическим рисунком под каждой из строк, например, под
          Мой дядя самых честных правил
           '   ' _  ' _   '   _    ' _  A(''_'_'_'_)
          Когда не в шутку занемог
           _  '  '    '  _  _ _ '       b(_'''___')
          Он уважать себя заставил
          '  _ _ '    _ '  _  ' _       A('__'_'_'_)
          И лучше выдумать не мог
          '  '  _  ' _ _    '  '        b(''_'__'') """
         
      endwords = []
      scheme = []
      # текст разбили на строки, из каждой строки взяли только последнее слово
      for l in text.split(u"\n") :
         endwords.append(tokenize(l)[-1])   
               
      # расттавили ударения, взяли только первый вариант пока что
      # см. SO How to change element of list in for in loop
      endwords[:] = [self.setAccent(x)[0] for x in endwords]

#      endwords2 = []
#      for x in endword :
#         endwords2.append(self.setAccent(x)[0])
#      for i in range(len(endwords)) :
#         enwords[i] = self.setAccent(endwords[i])[0]
      
      
      scheme[:] = [u'' for x in endwords]  
      
      curletter = u'A'

      for i in range(len(endwords)) :
         # если рифма для строки не установлена, маркируем строку буквой curletter
         if scheme[i] == u'' : 
            scheme[i] = curletter 
            curletter = unichr(ord(curletter) + 1)  # строим следующую букву
            currentRhyme = self.simpleRhyme(endwords[i])
            # проверяем строки, следующие после данной на наличие их в списке рифм 
            # если строка в списке, то устанавливаем одинаковую букву
            for j in range(i+1, len(endwords)) :    #
               if endwords[j] in currentRhyme : scheme[j] = scheme[i]
      
   
      return (endwords, scheme)


   
   def lineStyle(self, text) :
      # разбили на слова
      words = tokenize(text.lower())
      # расставили ударения
      words[:] = [self.setAccent(w)[0] for w in words]

      result = []
      # в каждом слове согласные удаляются, безударные гласные заменяются на o, ударные на O
      for w in words :
         style = ""
         for i in range(len(w)) :
            if w[i] in vowels :
               if w[i+1:i+2] == u"'" or w[i+1:i+2] == u"`" :
                  style += u"Я"
               else :
                  style += u"я"
         result.append(style)
      return ("".join(result), words)


   def simpleRhyme(self, word) :
      """ Возвращает список слов, рифмующихся с данным словом. Слово должно быть передано вместе с ударением """
      # важное замечание - рифмовать, конечно, надо траскрипции слов, а не их написание, но подходящего словаря не нашлось
      # Лит-ра: Онуфриев В.В. Словарь разновидностей рифмы
      #         В. Жирмунский. Рифма, её история и теория
      #
      # Наивная (хотя книжки пишут - богатая), рифма.

      # от слова бараба'нщик берем максимальное подслово - бараба'нщик и ищем все слова, оканчивающиеся на
      # данное подслово, получаем (условно) лучшую рифму
      # затем берем подслово араба'нщик и опять ищем все слова, оканчивающиеся на данное подслово
      # так поступаем до подслова а'нщик 
      # функция self.accentDict.keys("строка") автоматически ищет в словаре рифм (инверсионный словарь) 
      # все ключи, включающие в себя заданную строку
      
      # данный подход не срабатывает, когда слово оканчивается на ударную гласную, например, для слова пелена'
      # найдено более 7500 якобы рифм. Пока непонятно как постапуть в таких случаях.
      
      # наиболее очевидный способ создания бедной рифмы - модификация исходного слова и поиск рифм для него
      # в функциях ниже yottedRhyme (йотированная рифма) assonanceRhyme (ассонансная, созвучная рифма) пытаюсь
      # это воплотить
      
      # этот не комент, а цитата, но источник потерялся, но это важно
      # в стихах некоторые односложные слова могут быть безударными, боллее того
      # это часть общего правила, что ударный звук помжно поставить на место безударного,
      # но обратное категорически недопустимо
      
      # Бонус: ищет рифму также к слову, которого нет в словаре 
      
      word = word.strip()
      idx = word.find(u"'") 
      if idx == -1:
         print "Ключевое слово '", word, "' должно быть передано с ударением"
         return []
   
      result = []
      for i in range(idx) :
         # из слова-перевертыша берем подстроку, начиная с самой длинной и ищем для нее все рифмы
         # получаем список рифм для данного подслова
         s = map(reverse, self.accentDict.keys(reverse(word[i:])))
         # добавляем из s в список result только те рифмы, которых там еще нет
         for w in s :
            if not w in result : result.append(w)
         print "Ищем слова, оканчивающиеся на ", word[i:], ", найдено: ", len(s)
         # так у нас получается список, в начале которого стоят лучшие рифмы,
         # осталось удалить из выдачи само слово, которое мы рифмуем
         if word in result : result.remove(word)
      return result
      
   def yottedRhyme(self, word) :
      # самое простое для реализации - йотированная рифма. Нельзя удержаться и не сделать это
      # "равносложная рифма из слов с открытым и закрытым слогом, при этом последний заканчивается на й"
      # "поле - волей, тучи - летучий"
      # 
      word = word.strip() 
      # если слово заканчивается на гласную, добавляем й в конце и ищем рифму
      if word[-1] in u"аеиоуыэ" :
         print "Поиск йотированной рифмы к слову ", word
         return self.simpleRhyme(word + u'й')
      # если наоборот слово заканчивается на 'й' удалаем ее и ищем рифмы
      if word[-1] in u"й" :
         print "Поиск рифмы к йотированному слову"
         return self.simpleRhyme(word[0:-1])
      # если слово заканчивается на ёюя ... пока думаю
      # если буква ударная, то надо искать также и среди замен еёюя на эоуа
   
   def assonanceRhyme(self, word) :
      # совпадает гласный ударный звук, но несовпадают заударные согласные
      # рог - ветерок
      # брага - шняга..... чёрт

      word = word.strip() 
      result = []

      idx = word.find(u"'")
      if idx == -1:
         print "Ключевое слово '", word, "' должно быть передано с ударением"
         return result
      # то, что от начала слова, до ударной гласной вкл.- голова
      whead = word[:idx]
      # остальное хвост, в котором мы меняем пары букв и получаем список возможных хвостов
      wtail = word[idx:]
      # замечательная функция similar_keys объекта DAWG вернет нам только список хвостов, которые есть в словаре
      # НЕТ, увы, не вернет
      
      # надо построить из данного хвоста другие варианты, заменив безуударные согласные на
      tails = self.accentDict.similar_keys(reverse(wtail), self.compReplaces)
      prettyPrint(reverse(tails))
      
      for t in tails :
         # 
         # из слова-перевертыша берем подстроку, начиная с самой длинной и ищем для нее все рифмы
         # получаем список рифм для данного подслова
         s = map(reverse, self.accentDict.keys(t))
         # добавляем из s в список result только те рифмы, которых там еще нет
         for w in s :
            if not w in result : result.append(w)
         print "Ищем слова, оканчивающиеся на ", word[i:], ", найдено: ", len(s)
         # так у нас получается список, в начале которого стоят лучшие рифмы,
         # осталось удалить из выдачи само слово, которое мы рифмуем
         if word in result : result.remove(word)

      return result


         
   def consonanceRhyme(self, word) :
      # рифма с совпадение согласных звуков и неточным совпадением гласных
      # в частности редукция заударных а<->о, в меньшей степени е<->и, еще меньше и<->ы, и почти никогда для у
      
      # каламбурная рифма: теперь я - те перья, до канала - доканала, по калачу - поколочу
      # мультирифма: центральная базовая рифма с одним послеударным согласным звуком
      # день - тень, дым - летим (о, тут редукция гласной), рок - звонок
      # удвоенная согласная может выкидиваться
      
      # усеченная рифма, частным случаем которой является йотированная рифма,
      # то есть есть лишний согласный звук в одном из рифмующихся слов
      # ERROR: примеру не те почему-то
      # друг - звук, крик - миг, веторок - мог
      return word
   
   def poetize(self, seed) :    # versify ?
      # seed - случайная велечина
      # структура данных - список списков слов 
      #
      #
      #
      return seed

def reverse(str) :
   """ Возвращает строку задом наперед, версия 100500, решение на SOO """
   return str[::-1]
   # return "".join(reversed(s))

 
def syllables(word) :
   """ Возращает количество слогов в слове """
   v = 0
   for idx in range(len(word)) :
      if word[idx] in vowels :
         v += 1 
   return v


GROUPING_SPACE_REGEX = re.compile('([^\w_-]|[+])', re.U)

# слово должно начинаться с буквы, может содержать дефис или акцент' или слабый акцент` (не только 1), заканчиваться буквой или акцентом
TOKEN_REGEX = re.compile(u"[a-zA-Zа-яёЁА-Я][a-zA-Zа-яёЁА-Я`'-]*", re.UNICODE)

def tokenize(text):
   """ Разделяем текст на токены (недослова). не делим красное-прекрасное по черточке, но делим красное - прекрасное по тире 
       уродцы типа то4ка делятся на [то, ка]. Возвращаем список недослов """
   #return [t for t in GROUPING_SPACE_REGEX.split(text)
   #        if t and not t.isspace()]
   return re.findall(TOKEN_REGEX, text)


import urllib2

# не работает
def askSelebrex(word) :
   """ поиск семантически связанных слов на serelex...."""
   serelex = u'http://www.serelex.org/find/ru-skipgram-librusec/'
   url = serelex + word.strip();
   ans = urllib2.urlopen(url).read()
   return ans



# это надо перенести в utils
def createAccentDictionary(inputFName, outputFName = "new.dawg") :
      """ читаем строки из файла, слова с проставленными ударениями добавляем в хороший список, с непроставленными - в плохой,
          в плохом списке пробуем расставить ударения сами, если не получилось 
          Первоначально используется словарь "Полная акцентуированная парадигма по А.А.Зализняку"
          www.speakrus.ru/dict/all_forms.rar
      
          ФОРМАТ которого такой:
          беляши#беляши',беляше'й,беляша'м,беляши',беляша'ми,беляша'х
          слова, содержащие ё, не акцентуированы,
          сложные слова, например а`виаба'за,а`виаба'зы, акцентуированы по каждой из частей.
          предварительно словарь переведен в кодировку utf-8
          * слова с ё не размечены
          * предлоги не размечены
          * наречия не размечены почему-то 
          
          Плохой список сохраняется в файле "doitbyhands.txt", из хорошего списка создается структура данных dawg,
          которая сохраняется в файле с именем outputFName
          
          
          """
      
      # в итоге, несмотря на название =Полная акцентуированная=, - масса слов в этот словарь, увы, не входит.
      # тест на акцентуирование ЕО не проходит чуть ли не в каждой строфе
      
      
      #просто список слов в перевернутом порядке - инверсионный словарь
      accentList = [];
      # список слов, где ударение не проставлено
      noAccentList = [];
      
      with codecs.open(inputFName, encoding="utf8") as f :
         lc = 0 # счетчик строк
         for l in f :
            # надо символы перевода строки убрать, перевести все в маленькие буквы, затем разделить строку на две по символу #
            wl = l.strip().lower().split('#')
            # если все нормально, то получим двухэлементный список
            # нулевой элемент нам не нужен, первый - строка разделенными запятыми словоформ с ударениями.
            # делим ее по запятой, получаем список слов... там все еще могут быть лишние пробелы
            # strip их уберет, а filter выкинет пустые строки
            words = filter(lambda x : len(x) > 0,map(unicode.strip, wl[1].split(u',')))
            # но words все еще содержит слова без ударений, фильтруем его по отсутствию символа '
            for w in words :
               # ударённые слова переворачиваем и добавляем в нормальный спиок
               if u"'" in w : accentList.append(reverse(w))
               # если найдены слова без ударений, добавляем их в список ошибок, который попробуем обработать позже
               else         : noAccentList.append(w)
            lc = lc+1
         print lc, " lines read from ", stressFname
         
      # все слова с ударениями в accentList. теперь пробуем проставить ударения там, где их нет
      # если в слове есть ё, делаем её ударноё, заменяем на ё', если слово односложное, ставим ударение на гласную
      
      # следующий цикл тяжело дался... Дело в том, что если написать for w in List, а затем
      # внутри for менять w, то элемент списка не меняется, а если менять List[i], то вполне меняется...
      # объяснение на stackoverflow (SO) вопрос "How to modify list entries during for in loop", возможно
      # проще еще один список завести для слов где не удалось поставить ударение
      
      doItByHands = []   # тут слова, где никак ударение не ставится
      
      for w in noAccentList :
         if u"ё" in w : 
            accentList.append(reverse(w.replace(u"ё", u"ё'")))
         # односложное слова
         elif syllables(w) == 1:
            for j in range(0, len(w)) :
               if w[j] in vowels :
                  # добавили после гласной символ ударения, сразу сохранили в списке хороших слов
                  accentList.append(reverse(w[0:j+1] + u"'" + w[j+1:]))
         else :
         # последнее прибежище
            doItByHands.append(w)
      
      print 'accentList created, size = ' + str(len(accentList))
      print "Сохраняем слова, ударения в которых не расставлены, в файле doitbyhands.txt"
      with codecs.open("doitbyhands.txt", mode = "wb", encoding = "utf8") as f :
         for w in doItByHands :
            if len(w) > 0  : f.write(w + u"\n")
            
      #self.accentList.sort()
      print 'Из списка словоформ с ударениями создаем DAWG словарь с возможностью автодополнения... это может быть ДООООЛГО' 
      tmpDict = CompletionDAWG(accentList)
      print 'Сохраняем файл ', outputFName 
      tmpDict.save(outputFName)
      print 'DONE'


def unionAccentDictionares(inFName1, inFName2, outFName) :
   """ Объединение двух словарей """
   d1 = CompletionDAWG()
   d2 = CompletionDAWG()
   
   print "Read first dawg from file " + inFName1
   try : 
      d1.load(inFName1)
   except ValueError :
      d1 = None
      print "Value Error while loading dawg from file:" +  inFName1
      return

   print "Read second dawg from file " + inFName2
   try :
      d2.load(inFName2)
   except ValueError : 
      d1 = None
      d2 = None
      print "Value Error while loading dawg from file:" +  inFName2
      return
      
   # записываем первый словарь в список, туда же второй словарь, 
   # из того что получилось, создаем словарь d3
   print "Concatenate 1 and 2"
   li = d1.keys()
   li.extend(d2.keys())
   d3 = CompletionDAWG(li)
   
   # сохраняем его
   print "Save united dawg to file " + outFName   
   try : 
      d3.save(outFName)
   except ValueError : 
      print "Value Error while loading dawg from file:" +  inFName2
      d1 = None
      d2 = None
      li = None
      return
   print "Done"


# попытка исправить питонью особенность печатать строки в формате unicode кодами символов
# 
def prettyPrint(x) :
   if isinstance(x, (str, unicode, int, float)) :
      print x
   elif isinstance(x, tuple) :
      for e in x : print e,
      else : print
   else:
      try :
         for e in x :         
            prettyPrint(e)
      except TypeError :
         print 'TypeError', x



# подсчет статистики словоформ для каждой нормальной формы
#      stat = Counter()
#      for l in stressDict.itervalues() :
#         for s in l :
#            wc = len(s.split(u','))
#            stat[wc] += 1
#      print stat
#      # сохраним статистику для интереса
#      with codecs.open("Counter.txt", mode ="w", encoding="utf8") as f :
#         f.write(stat.__repr__())
      
      # разбиваем файл словаря на несколько подсловарей, в каждом из которых 
      # н-ное количество словоформ
      # это пока не актуально, так как морфемы для рифм не помечены
#      
#      files = stat
#      path  = '/home/lisa/elektrybalt/'
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


