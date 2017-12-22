# 
# -*- coding: utf8


# Приветствие и инструкция находжятся в конце файла
# Запуск python -i wd.py


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


# надо определить из какой директории запускается наш модуль
# чтобы потом находить файлы словарей
import os
module_dir = os.path.dirname(os.path.abspath(__file__))
print 'Dir is ', module_dir

accentDictFname = module_dir + "/dict/union5.dawg"
accentErrorsFname = module_dir + "/dict/accentErrors.txt"
 
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

      
   def loadAccentDict(self, fname = accentDictFname) :
      try :
         self.accentDict.load(fname)
         print 'accent dictionary loaded from file: ' + fname
      except :
         print 'accent dictionary NOT loaded, file is: ' + fname
         
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
               
      #   if len(result) != 0 :
      #      print u"Слово <<" + testword + u">> найдено при замене Е на Ё"
            
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
         # если ударения не найдено, то возвращается неизменное слово
         result.append(word)
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
   
   def rhythmVectors(self, text) :
      """ ритмическая характеристика слова или строки (одной!!! не более). 
      Бу'ря мгло'ю не'бо кро'ет -> 20202020
      вихри снежные кружа       -> 2020002
      то как зверь она завоет   -> 11101020
      то заплачет как дитя      -> 1020102
      возможно ударные (слабоударные) слоги обозначим 1, ударные - 2, безударные 0 """
      
      # вылетаем если получили более одной строки
      assert u'\n' not in text, "rhythmVectors needs single line at input"

      # result - это список возможных ритмических векторов фразы (то есть матрица), 
      # каждый ритмический вектор - это список чисел от 0 до 2
      # чаще всего это будет матрица из одной строки - Ой не зарекайся. Редко получается одна строка. Много омонимов
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
      # если удареный слог не найден, то считаем все слово слабоударным
      if not u"'" in accentedWord :
         for i in range(len(result)) :
            result[i] = 1
      return result

      
   def rhythmError(self, rhythmVector, template) :
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
      
      if len(rhythmVector) != len(template) :
         print u"Размерности вектора и шаблона не равны, такого не должно быть!!!"
         return 1000
      
      error = 0
      for i in range(len(rhythmVector)) :
         e = rhythmVector[i] - template[i]
         if     e ==  2 : e = 50
         elif   e == -2 : e = 2
         elif   e == -1 : e = 1
         error += e
      return error


   def verseDetectBestTemplate(self, str) :
      """Определяет наиболее подходящий шаблон для ритмических векторов одной строки
      возвращаем кортеж из числа слогов, значение 
      ошибки, копию лучшего шаблона, копию лучшего вектора"""
      # вылетаем если получили более одной строки
      assert not u"\n" in str , "Function needs single line at input"
      
      # число слогов в строке
      sl = syllables(str)
      
      # возможные ритмические вектора строки
      vectors = self.rhythmVectors(str)
      
      error = 100000
      # индекс наиболее подходящего вектора и наиболее подходящего шаблона
      vidx   = 1000
      tidx   = 1000
      
      # для каждого ритмического вектора 
      for v in range(len(vectors)) :
         for t in range(len(self.Templates[sl])) :
            e = self.rhythmError(vectors[v], self.Templates[sl][t][0])
            # если ошибка меньше текущей,
            if e <= error : 
               error = e
               vidx  = v
               tidx  = t 
               
      return (sl, error, deepcopy(self.Templates[sl][tidx]), deepcopy(vectors[vidx]))

      
   def verseDetector(self, text) :
      result = []
      for li in text.strip().split('\n') :
         (sl, e, t, v) = self.verseDetectBestTemplate(li)
         # теперь определив лучшие вектора и шаблон, мы можем расставить ударения, сняв омонимию
         # кроме того, расставим акценты на тех слабоударных слогах, где шаблоном предписано ударение
         
         tmp = []
         i = 0 
         for l in li.lower().replace(u"'", u"") :
            tmp.append(l)
            if l in vowels :
               # если позиция слога в векторе ударная, то ставим ударение
               # print "v[",i,"] = ", v[i]
               if v[i] == 2 : 
                  #print "v[",i,"]", v[i]
                  tmp.append(u"'")
               # если позиция слога в векторе слабоударная, но шаблон предписывает ставить здесь ударения, 
               # то ставим
               elif v[i] == 1 and t[0][i] == 2 :  
                  #print "v[",i,"]", v[i]
                  tmp.append(u"'")
               i = i + 1

         accentedLine = u"".join(tmp)
         
         # result это список списков
         # [[0-исходня строка, 1-строка с ударениями, 2-число слогов, 3-ошибка, 4-шаблон, 5-вектор, 6-тип рифмы]]
         result.append([li, accentedLine, sl, e, t, v, u' '])  

      # теперь лучшие вектора и строки собраны, надо определить рифмованные строки
      endwords = []
      scheme = []   
      for e in result :
         endwords.append(tokenize(e[1])[-1].lower())  # последнее слово в строке, причем с ударением
         scheme.append(u"")                   # сколько строк такова и длина списков endwords, scheme
      
      curletter = u'a'
         
      for i in range(len(endwords)) :
         # если рифма для строки не установлена, маркируем строку буквой curletter
         if scheme[i] == u'' : 
            scheme[i] = curletter 
            curletter = unichr(ord(curletter) + 1)  # строим следующую букву
            # print " Рифма к ", "i = " , i, "endwords[i] = ", endwords[i] 
            currentRhyme = self.simpleRhyme(endwords[i])
            
            # проверяем строки, следующие после данной на наличие их последних слов в списке рифм 
            # если слово в списке, то устанавливаем одинаковую букву
            for j in range(i+1, len(endwords)) :    #
               if endwords[j] in currentRhyme : 
                  scheme[j] = scheme[i]
      # рифмы найдены, осталось занести их в result, предварительно поделив на мужскую (a) женскую (A) дактилическую (_A)
      for i in range(len(endwords)) :
         # проверяем что написано в описании шаблона
         if u"женская" in result[i][4][2] :
            scheme[i] = scheme[i].upper()
            result[i][6] = scheme[i].upper()
         elif u"дакт"  in result[i][4][2] :
            scheme[i] = u"_" + scheme[i].upper()
            result[i][6] = u"_" + scheme[i].upper()
         else  : # мужская
            result[i][6] = scheme[i]
      
      # пробуем красиво напечатать result
      print u'Введенный текст'
      print '-----------------------------------'
      print text
      print '-----------------------------------'
      sumError = 0
      for e in result :
         print e[1].ljust(40), 'vec = ', e[5], ', error = ', e[3]
         print u''. ljust(40), 'temp= ', e[4][0]
         sumError += e[3]  # суммарная ошибка по всем строкам
      print '-----------------------------------'
      print u'Рифма   ', "".join(scheme)
      print u'Размер  ', result[0][4][3], u'-x стопный ', result[0][4][1]
      print u'Суммарная ошибка: ', sumError
      print '-----------------------------------'      
      
      return


   
   def simpleRhyme(self, word) :
      """ Возвращает список слов, рифмующихся с данным словом. Слово должно быть передано вместе с ударением """
      # важное замечание - рифмовать, конечно, надо траскрипции слов, а не их написание, но подходящего словаря не нашлось
      # Лит-ра: Онуфриев В.В. Словарь разновидностей рифмы
      #         В. Жирмунский. Рифма, её история и теория
      #
      # Наивная (хотя книжки пишут - богатая), рифма.
      # наконец-то появилась ясность с богатой рифмой. кроме заударных звуков должен совпадать и предударный согласный
      # то есть правил-заставил небогатая рифма, а сталь-деталь - богатая

      # от слова бараба'нщик берем подслово - а'нщик и ищем все слова, оканчивающиеся на
      # данное подслово, получаем рифму
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
      # из слова-перевертыша берем подстроку с конца, включая ударную гласную, ищем для нее все рифмы
      # переворачиваем рифмы
      s = map(reverse, self.accentDict.keys(reverse(word[idx-1:])))
      # добавляем из s в список result только те рифмы, которых там еще нет
      for w in s :
         if not w in result : result.append(w)
      # print "Ищем слова, оканчивающиеся на ", word[idx-1:], ", найдено: ", len(s)
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
   
   def generateRhythmTemplates(self) :
      """ создаем шаблоны идеальных ритмов, то есть вектора цифр вида 0202, 02020 - двустопные ямбы мужской и женский и тд
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
      ],
      # 13 слогов
      [
      [[0,2,0,2,0,2,0,2,0,2,0,2,0], Ja, Rf, 6],
      [[2,0,2,0,2,0,2,0,2,0,2,0,2], Ch, Rm, 7],
      [[2,0,0,2,0,0,2,0,0,2,0,0,2], Dt, Rm, 5],
      [[0,2,0,0,2,0,0,2,0,0,2,0,0], Am, Rd, 4],
      [[0,0,2,0,0,2,0,0,2,0,0,2,0], An, Rf, 4]
      ],
      # 14 слогов
      [
      [[0,2,0,2,0,2,0,2,0,2,0,2,0,2], Ja, Rm, 7],
      [[2,0,2,0,2,0,2,0,2,0,2,0,2,0], Ch, Rf, 7],
      [[2,0,0,2,0,0,2,0,0,2,0,0,2,0], Dt, Rf, 5],
      [[0,2,0,0,2,0,0,2,0,0,2,0,0,2], Am, Rm, 5],
      [[0,0,2,0,0,2,0,0,2,0,0,2,0,0], An, Rd, 4]
      ]

      ]
      print u"Шаблоны размеров созданы"
      return templates

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






p=Poet()  # создали экземпляр распознавателя

if __name__ == '__main__':
   print u"""--------------------------------------------------------------------------------------------
Программа распознавания стихотворного размера и рифмы, Поэтический фильтр

Запустить программу можно так: python -i wd.py

затем введите какой-нибудь стих в строку, например, введем стихотворение Афанасия Фета
"""
   text = u"""Свежеет ветер, меркнет ночь
А море злей и злей бурлит
И пена плещет на гранит
То прянет, то отхлынет прочь"""

   print 'text =u"""', text, u'"""'

   print u"""Или создайте файл с расширением .py, в который поместите один или несколько стихов.
Затем импортируйте его директивой import имя_файла (без расширения)

Несколько таких файлов уже создано: eo.py - фрагменты поэмы Евгений Онегин, mishka.py - разные стихи разных стилей
Теперь Вы можете определять стихотворные размеры и рифмы любых стихов, вызвав функцию
p.verseDetector(text)

Например, распознаем четверостишие Фета
p.verseDetector(text)
"""
   p.verseDetector(text)

   print u"""или распознать фрагмент из Онегина, для чего наберите
   import eo
   p.verseDetector(str1)"""

   print u"""Удачного распознавания! Завершить работу можно набрав команду quit()
--------------------------------------------------------------------------------------------"""