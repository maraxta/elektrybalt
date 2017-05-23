# 
# -*- coding: utf8

from collections import namedtuple, defaultdict, Counter
import codecs 
import re
from dawg import CompletionDAWG, RecordDAWG
from copy import deepcopy

# вау, чтобы работало автодополнение по нажатию Tab
# надо только поискать вопрос на SO: How do i add tab completion to python shell
#
import rlcompleter
import readline
readline.parse_and_bind("tab: complete")

wordParams      = namedtuple('wordParams', ['transcript', 'accent', 'normal', 'morph'])
accentDictFname = "dict/union1.dawg"
inputFname      = "/home/pi/lisa/Pushkinizer/dict/all-forms.utf8.txt"
accentErrorsFname = "dict/accentErrors.txt"

#гласные
vowels    = u"еиаоуыюяэё"
alphabet  = u"абвгдеёжзийклмнопрстуфхцчшщъыьэюя"

# словарь замен заударных глухих и звонких согласных
consonantReplaces = {u"к":u"г",u"г":u"к",u"ф":u"в",u"в":u"ф",u"ж":u"ш",u"ш":u"ж",u"ч":u"щ",u"щ":u"ч",u"д":u"т",u"т":u"д"}



class Poet() :
   """eletric poet, nothing special"""

   def __init__(self) :
      # self.accentDict - словарь из библиотеки DAWG, инициализируется объектом типа CompletionDAWG
      self.accentDict = CompletionDAWG()
      # загружаем словарь
      self.loadAccentDict()
      # замены для поиска слов (ключей) где вместо Ё стоит Е
      self.yoReplaces = self.accentDict.compile_replaces({u'е':u'ё'})
      # список шаблонов стихотворных размеров
      self.Templates  = self.generateRhythmTemplates()

      
   def __repr__(self) :
      """ печать информации о словаре """
      #return self.baseDict.__repr__()  + self.revDict.__repr__()
      return "Instance of Poet class consists of " + str(len(self.accentDict)) + " wordforms and " + str(len(self.revDict)) + " reverses." 
     
      
   def loadAccentDict(self, fname = accentDictFname) :
      self.accentDict.load(fname)
      print 'accent dictionary loaded from file: ' + fname
         
   def setAccent(self, word) : 
      """ Расставляем ударения, Пользуемся словарем. Возвращаем список вариантов. Тупой перебор"""

      word = word.strip().lower()

      if u"'" in word : return [word]

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

      # словарный поиск неудачен, попытаемся искать слово, предположив, что вместо е где-то стоят ё
      # используем метод similar_keys класса CompletionDAWG
      if len(result) == 0 :
         for i in range(len(word)) :
            if word[i] in u"е" :    # ударение добавляет только после е. остальное аналогично
               testword = word[0:i+1] + u"'" + word[i+1:]   
               # print "проверяем вариант ",   testword
               # как всегда, в словаре рифм ищутся перевернутые слова, и на выходе имеем перевернутые слова
               yoList = self.accentDict.similar_keys(reverse(testword), self.yoReplaces) 
               result.extend(map(reverse, yoList))
               
         if len(result) != 0 :
            print u"Слово <<" + testword + u">> найдено при замене Е на Ё"
            
      # если словарный поиск не удачен, пытаемся поставить ударение алгоритмически
      if len(result) == 0 :
         result = self.setAlgoAccent(word)
      
      # увы не повезло
      if len(result) == 0 :
         print u"Не найдено ни одного варианта ударения слова <<" + word + u">>"
         print u"Слово добавлено в файл: ", accentErrorsFname
         
         # открываю файл в режиме append, with закроет его автоматически
         with codecs.open(accentErrorsFname, mode="a", encoding="utf8") as f :
            f.write(word + u"\n")
      return result

      # Тест : d.setAccent(u"замок") -> [u"за'мок", u"зам'ок"]
      # ERROR: для сложносочиненных слов увы не работает так как в словаре у них два ударения: а`виастрои'тель
      #        а символ (`) называется гравис, или знак побочного ударения


   def setAlgoAccent(self, word) : 
      # !!! надо переписать, но нет идей
      # в нульсложных словах ударений нет
      if syllables(word) == 0 :
         return [word]
      # если односложное слово - ставим ударение сами
      if syllables(word) == 1 :
         for i in range(0, len(word)) :
            if word[i] in vowels :   # добавили после гласной символ ударения, вернули слово
               return [word[0:i+1] + u"'" + word[i+1:]]
      # если в слове есть ё - ставим ударение сами
      if u"ё" in word : 
         return [word.replace(u"ё", u"ё'")]
      # ERROR - это неправда, !!! если слова заканчивается на -ать, -ять, то там и ударение, 
      # но пусть будет пока
      if word.endswith((u"ать", u"ять")) :
         return [word[:-2] + u"'" + word[-2:]]
      # и'вый - также кроме милостиливый и юродивый
      if word.endswith(u"ивый") :
         return [word[:-3] + u"'" + word[-3:]]
      
      return [] 
   
   def rhythmVector(self, text) :
      """ ритмическая характеристика слова или строки (одной!!! не более). 
      Бу'ря мгло'ю не'бо кро'ет -> 20202020
      вихри снежные кружа       -> 2020002
      то как зверь она завоет   -> 11101020
      то заплачет как дитя      -> 1020102
      возможно ударные (слабоударные) слоги обозначим 1, ударные - 2, безударные 0 """
      
      # вылетаем если получили более одной строки
      assert u'\n' not in text, "rhythmVector needs single string at input"

      # result - это список возможных ритмических векторов фразы (то есть матрица), 
      # каждый ритмический вектор - это список чисел от 0 до 2
      # чаще всего это будет матрица из одной строки
      result = [[]] 

      for w in tokenize(text.strip().lower()) :
         # для каждого слова расставляем ударения, 
         # может быть несколько вариантов для слова, это все ООООчень усложняет
         accented = self.setAccent(w)
         
         # то есть если в стихе два варианта ударения одного слова, число возможных ритмических векторов удваивается
         # если три - то утраивается и т.д.
         if len(accented) > 1 :  
            # объяснение почему копировать так на SO "how to clone a list"
            tmp = deepcopy(result)       # tmp - копия матрицы, куда еще не добавлен ритм текущего слова 
         else :                          # tmp = result  писать нельзя, это будут просто 2 разных слова, ссылающиеся на одну структуру
            tmp = []
         # print "w= ", w

         for i in range(len(accented)) :
            vec = self.wordRhytmVector(accented[i]) 
            fm = 0                 # добавлять ритм текущего слова надо ко всем векторам
            if i > 0 :
               fm = len(result)    # добавлять ритм текущего слова надо только в конец вновь созданных векторов
               result.extend(tmp)  #
            #   print "extending result with", tmp
            # print "len result" , len(result) , "fm = ", fm , "vec =", vec
            # тут тонкое и опасное место, 
            # да тут все опасно и непонятно
             
            for j in range(fm, len(result)) :
               # print "len result" , len(result) , "fm = ", fm , "vec =", vec, "i=", i, "j =", j, "accented =" , accented[i], "tmp =", tmp
               # добавляем в хвост НЕ каждого вектора ритм текущего слова
               result[j].extend(vec)
               # print "result " , result
      return result
      
   def wordRhytmVector(self, accentedWord) :
      """ заменяем ударные слоги единственного слова на 2, неударные на 0 """
      result = []
      for l in accentedWord :
         if l in vowels :
            result.append(0)
         if l == u"'" :
            result[-1] = 2
      # если слово односложное, считаем его слабоударным
      if len(result) == 1 :
         result[0] = 1
      return result

      
   def rhythmError(self, rhythmVector, rhythmTemplate) :
      """ арифметика ритмов """
      # безударный на ударном месте должен давать небольшую ошибку
      # если:  vec    =   вихри снежные кружа       -> 2 0 2 0 0 0 2
      #    template   = (хорей 4 стопы)                2 0 2 0 2 0 2 
      # то rhytmError = (отнимаем поразрядно)          0 0 0 0-2 0 0 = -2
      # САМОЕ ГЛАВНОЕ ударный слог не должен стоять на безударном месте
      # но если rvec  = глупый пингви'н робко прячет   2 0 0 2 2 0 2 0
      # а rtemplate   = (опять хорей, пять стоп)       2 0 2 0 2 0 2 0
      # то rhytmError =                                0 0 0 2 0 0 0 0   должна превращаться во что то вроде 50
      # слабоударный слог может стоять на любом месте с небольшой ошибкой
      #        vec    = то как зверь она завоет   ->   1 1 1 0 1 0 2 0
      #      template =                                2 0 2 0 2 0 2 0
      #   rhythmError =                        sum    -1 1-1 0-1 0 0 0
      # в итоге, получается такая арифметика:
      # vec template error
      # (1, 0)      == 1
      # (1, 2)      == 1
      # (0, 2)      == 2
      # (2, 0)      == 50
      # (x, x)      == 0
      # а затем суммируем по всем членам списка
      
      if len(rhythmVector) != len(rhythmTemplate) :
         print u"Размерности вектора и шаблона не равны"
         return 1000
      
      error = 0
      for i in range(len(rhythmVector)) :
         e = rhythmVector[i] - rhythmTemplate[i]
         if     e ==  2 : e = 50
         elif   e == -2 : e = 2
         elif   e == -1 : e = 1
         error += e
      return error

   def generateRhythmTemplates(self) :
      """ генерируем шаблоны идеальных ритмов, то есть вектора цифр вида 0202, 02020 - двустопные ямбы мужской и женский и тд
          списки длиной от 0 до 12, чтобы гарантированно охватить все популярные размеры
          каждому шаблону должна предшествовать описывающея его строка"""
      # функция вызывается один раз при создании объекта.
      # допустим у нас в строке 5 слогов, тогда Templates[5] - это список шаблонов с описаниями
      # Templates[5][0] ... Templates[5][что-то] - один пятислоговый шаблон с описанием
      # Templates[5][что-то][0] - сам шаблон
      # Templates[5][что-то][1] - ямб, хорей и т.п.
      # Templates[5][что-то][2] - мужская женская дактилическая рифма
      # Templates[5][что-то][3] - число стоп, ударных слогов
      #
      # тогда, чтобы найти подходящий шаблон для строки со значением vec мы перебираем все пятислоговые так
      # for el in Templates[5] :
      #    if self.rhythmError(vec, t[0]) < error :
      #       делаем что-то полезное

      # Стихотворные размеры (foot): ямб, хорей, дактиль, амфибрахий, анапест Ja, Ch, Dt, Am, An
      # надо перенести их в глобальные чтобы не создавать заново
      Ja = u"ямб"           #[0,2]
      Ch = u"хорей"         #[2,0]
      Dt = u"дактиль"       #[2,0,0]
      Am = u"амфибрахий"    #[0,2,0]
      An = u"анапест"       #[0,0,2]
      # Рифмы: Мужская, Женская, Дактилическая (число безударных слогов в конце строки)
      Rm = u"мужская рифма" #0
      Rf = u"женская рифма" #1
      Rd = u"дактилическая рифма" #2


      templates = [  
      # 0 сложные размеры
      [
      [[],  u"Ошибка",u"",0]
      ],
      # односложные размеры
      [
      [[2],         Ch,Rm,1]
      ],
      # двусложные размеры
      [
      [[0,2],       Ja,Rm,1],
      [[2,0],       Ch,Rf,1]
      ],
      # трехсложные
      [
      [[2,0,2],     Ch,Rm,2],
      [[2,0,0],     Dt,Rd,1],
      [[0,2,0],     Am,Rf,1],
      [[0,0,2],     An,Rm,1]
      ],
      # 4 слога
      [
      [[0,2,0,2],   Ja,Rf,2],
      [[2,0,2,0],   Ch,Rm,2],
      [[2,0,0,2],   Dt,Rm,2],
      [[0,0,2,0],   An,Rf,2]
      ],
      # 5 слогов
      [
      [[0,2,0,2,0], Ja,Rf,2],
      [[2,0,2,0,2], Ch,Rm,3],
      [[2,0,0,2,0], Dt,Rf,2],
      [[0,2,0,0,2], Am,Rm,2],
      [[0,0,2,0,0], An,Rd,1]
      ],
      # 6 слогов
      [
      [[0,2,0,2,0,2], Ja,Rm,3],
      [[2,0,2,0,2,0], Ch,Rf,3],
      [[2,0,0,2,0,0], Dt,Rd,2],
      [[0,2,0,0,2,0], Am,Rf,2],
      [[0,0,2,0,0,2], An,Rm,2]
      ],
      # 7 слогов
      [
      [[0,2,0,2,0,2,0], Ja,Rf,3],
      [[2,0,2,0,2,0,2], Ch,Rm,4],
      [[2,0,0,2,0,0,2], Dt,Rm,3],
      [[0,2,0,0,2,0,0], Am,Rd,2],
      [[0,0,2,0,0,2,0], An,Rf,2]
      ],
      # 8 слогов
      [
      [[0,2,0,2,0,2,0,2], Ja, Rm, 4],
      [[2,0,2,0,2,0,2,0], Ch, Rf, 4],
      [[2,0,0,2,0,0,2,0], Dt, Rf, 3],
      [[0,2,0,0,2,0,0,2], Am, Rm, 3],
      [[0,0,2,0,0,2,0,0], An, Rd, 2]
      ],
      # 9 слогов
      [
      [[0,2,0,2,0,2,0,2,0], Ja, Rf, 4],
      [[2,0,2,0,2,0,2,0,2], Ch, Rm, 5],
      [[2,0,0,2,0,0,2,0,0], Dt, Rd, 3],
      [[0,2,0,0,2,0,0,2,0], Am, Rf, 3],
      [[0,0,2,0,0,2,0,0,2], An, Rm, 3]
      ],
      # 10 слогов
      [
      [[0,2,0,2,0,2,0,2,0,2], Ja, Rm, 5],
      [[2,0,2,0,2,0,2,0,2,0], Ch, Rf, 5],
      [[2,0,0,2,0,0,2,0,0,2], Dt, Rm, 4],
      [[0,2,0,0,2,0,0,2,0,0], Am, Rd, 3],
      [[0,0,2,0,0,2,0,0,2,0], An, Rf, 3]
      ],
      # 11 слогов
      [
      [[0,2,0,2,0,2,0,2,0,2,0], Ja, Rf, 5],
      [[2,0,2,0,2,0,2,0,2,0,2], Ch, Rm, 6],
      [[2,0,0,2,0,0,2,0,0,2,0], Dt, Rf, 4],
      [[0,2,0,0,2,0,0,2,0,0,2], Am, Rm, 4],
      [[0,0,2,0,0,2,0,0,2,0,0], An, Rd, 3]
      ],
      # 12 слогов
      [
      [[0,2,0,2,0,2,0,2,0,2,0,2], Ja, Rm, 6],
      [[2,0,2,0,2,0,2,0,2,0,2,0], Ch, Rf, 6],
      [[2,0,0,2,0,0,2,0,0,2,0,0], Dt, Rd, 4],
      [[0,2,0,0,2,0,0,2,0,0,2,0], Am, Rf, 4],
      [[0,0,2,0,0,2,0,0,2,0,0,2], An, Rm, 4]
      ]
      ]
      print u"Шаблоны размеров созданы"
      return templates

   def verseDetector(self, text) :
      # первая задача оперделить стихотворный размер переданных (foot)  строк
      # для этого считаем сколько слогов в строке, затем строим вектора метров, которые подходят по числу слогов
      # например, если в строке 9 слогов - возможно это 4 стопный ямб с женской рифмой
      # или пятистопный хорей с мужской рифмой 
      # или любой из 3-х стопных размеров
      # затем выбираем наиболее подходящий размер по наименьшему значению ошибки rhythmError
      
     

      # 
      # foots = [ (Название, число стоп, рифма, число слогов, [ритмический вектор]) ]
      # Наша задача, зная длину вектора текущей строки, сгенерировать шаблон такой же длины.
      # то есть если в строке 8 слогов, то надо сгенерировать шаблон четырехстопного ямба Ja4m с мужской рифмой
      # и четырехстопного хорея Ch4f с женской 
      # 
      return



   def formatVerse(self, text) :
      """ Печатает переданный текст, вместе с ритмическим рисунком каждой строки, например
          Мо'й дя'дя са'мых че'стных пра'вил    120202020-A
          Когда' не' в шу'тку занемо'г          02120002-b
          О'н уважа'ть себя' заста'вил          100202020-A
          И' лу'чше вы'думать не' мо'г          12020011-b 
      """


      endwords = []
      scheme = []
      
      # разбили текст на строки
      verse = []
      for l in text.split(u"\n") :
         # получили список слов строки, добавили весь список очередным элементом verse
         # type(verse[0]) -> list
         verse.append(tokenize(l))
     
      # имеем список списков слов, теперь каждое слово надо заменить на список его ударных вариантов
      # так работать не будет но закомментированный код поможет создать verse 
      # способом list comprehension
      #for l in verse : 
      #   for w in l :
      #      w = self.setAccent(w)
            
      verse[:] = [[self.setAccent(w) for w in l] for l in verse]
      
      # появившиеся варианты ударений одного слова очень усложняют работу
      # мo'й дя'дя ca'мыx чe'cтныx  πpa'вил
      #                   чecтны'x  πpaви'л
      # имеем 4 варианта
      return verse

      
      # текст разбили на строки, из каждой строки взяли только последнее слово
      for l in text.split(u"\n") :
         endwords.append(tokenize(l)[-1])   
               
      # расттавили ударения, взяли только первый вариант пока что
      # см. SO How to change element of list in for in loop
      # endwords[:] = [self.setAccent(x)[0] for x in endwords]
      #

      
      # схема стиха - пока список из пустых строк такой же длины как список endwords
      scheme[:] = [u'' for x in endwords]  
      
      curletter = u'A'

      prettyPrint(endwords)
      
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

   
   def simpleRhyme(self, word) :
      """ Возвращает список слов, рифмующихся с данным словом. Слово должно быть передано вместе с ударением """
      # важное замечание - рифмовать, конечно, надо траскрипции слов, а не их написание, но подходящего словаря не нашлось
      # Лит-ра: Онуфриев В.В. Словарь разновидностей рифмы
      #         В. Жирмунский. Рифма, её история и теория
      #
      # Наивная (хотя книжки пишут - богатая), рифма.
      # наконец-то появилась ясность с богатой рифмой. кроме заударных звуков должен совпадать и предударный согласный
      # то есть правил-заставил небогатая рифма, а сталь-деталь - богатая

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
      # созвучная рифма
      # совпадает гласный ударный звук, но несовпадают заударные согласные
      # рог - ветерок  друг - звук, крик - миг, 
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
      # tails = self.accentDict.similar_keys(reverse(wtail), self.compReplaces)
      # prettyPrint(reverse(tails))
      
      # строим из данного хвоста другие, заменив безуударные согласные на их.... на дуальные им, короче на те,
      # что перечислены в consonantsReplaces
      
      tails = [wtail]
      
      
      for t in tails :
         # 
         # из слова-перевертыша берем подстроку, начиная с самой длинной и ищем для нее все рифмы
         # получаем список рифм для данного подслова
         s = map(reverse, self.accentDict.keys(t))
         # добавляем из s в список result только те рифмы, которых там еще нет
         for w in s :
            if not w in result : result.append(w)
         print "Ищем слова, оканчивающиеся на ", word[idx:], ", найдено: ", len(s)
         # так у нас получается список, в начале которого стоят лучшие рифмы,
         # осталось удалить из выдачи само слово, которое мы рифмуем
         if word in result : result.remove(word)

      return result


         
   def consonanceRhyme(self, word) :
      # согласная рифма
      # рифма с совпадение согласных звуков и неточным совпадением гласных
      # в частности редукция заударных а<->о, в меньшей степени е<->и, еще меньше и<->ы, и почти никогда для у
      
      # каламбурная рифма: теперь я - те перья, до канала - доканала, по калачу - поколочу
      # мультирифма: центральная базовая рифма с одним послеударным согласным звуком
      # день - тень, дым - летим (о, тут редукция гласной), рок - звонок
      # удвоенная согласная может выкидиваться
      
      # усеченная рифма, частным случаем которой является йотированная рифма,
      # то есть есть лишний согласный звук в одном из рифмующихся слов
      # ERROR: примеру не те почему-то

      return word
   
   def phoneticExpand(self, word, have_forms, model) :
      # все предыдущие функции поиска рифмы (cons... ans.. yotted, etc) основывались на том, что поиск 
      # простой рифмы выполнялся не для исходного, а для модифицированного слова (например, в исходном слове
      # редуцировалась гласная)
      # Причем способы модификации, в общем, были нехитрыми, заменить что-то на что-то
      # 
      result = []
      return result
   
   def poetize(self, seed) :    # versify ?
      # seed - случайная велечина
      # структура данных - список списков слов 
      #
      #
      #
      return seed

def reverse(str) :
   """ Возвращает строку задом наперед, версия 100500, решение на SO """
   return str[::-1]
   # return "".join(reversed(list(str)))

 
def syllables(word) :
   """ Возращает количество слогов в слове или фразе """
   v = 0
   for idx in range(len(word)) :
      if word[idx].lower() in vowels :
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



# попытка исправить питонью особенность печатать строки в формате unicode кодами символов
# 
def prettyPrint(x) :
   if isinstance(x, (str, unicode, int, float)) :
      print x
   elif isinstance(x, tuple) :
      for e in x : prettyPrint(e) ,
      else : print
   else:
      try :
         for e in x :         
            prettyPrint(e)
      except TypeError :
         print 'TypeError', x

