# 
# -*- coding: utf8

import dawg, codecs
from wd import reverse

inputFname      = "/home/pi/lisa/Pushkinizer/dict/all-forms.utf8.txt"

def unionDAWGS(inDawg, inText, outFName) :
   """ Объединение , базового акцентурированного словаря (имя inDawg) и 
   файла с вручную проставленными ударениями, (имя inText)
   создание нового файла dawg (имя outDawg"""
   d = dawg.CompletionDAWG()
   
   print "Read base dawg from file " + inDawg
   try : 
      d.load(inDawg)
   except ValueError :
      d = None
      print "Value Error while loading dawg from file:" +  inFName1
      return

   print "Read additional accents from file " + inText

   # читаем текстовый файл в список
   newWords = []
   with codecs.open(inText, encoding="utf8") as f:
      for l in f :
         s = l.strip()
         if len(s) != 0 :
            if u"'" in s :
               newWords.append(reverse(s))
      
   # записываем первый словарь в список, туда же второй словарь, 
   # из того что получилось, создаем словарь d3
   print "Concatenate 1 and 2"
   oldWords = d.keys()
   oldWords.extend(newWords)
   
   newDawg = dawg.CompletionDAWG(oldWords)
   
   # сохраняем его
   print "Save united dawg to file " + outFName   
   newDawg.save(outFName)
   d = None
   oldWords = None
   newWords = None
   print "Done"


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
         # а есть ли слова с двумя ё?
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

