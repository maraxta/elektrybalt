# -*- coding: utf8




#
#
#
#

str = u'купил замок'
li = str.split(u' ')
#li[0] = 'купил'
#li[1] = 'замок'
# расставили ударения, имеем
# accented = []
# for w in li :
#   accented.extend(setAccent(w))  # setAccent возвращает список вариантов ударений для данного слова
# для "купил" один вариант купи'л
# поэтому result = (безударный слог обозначается 0, ударный 2)

print 'try one'
result = [[0,2]] 

# потом для слова замок два варианта ударения замо'к за'мок
# то есть result должен превратится в матрицу
# [[0,2,0,2], 
#  [0,2,2,0]]

# пытаюсь скопировать список, попытка 1
# 
result.extend(result)
print 'result.extend(result) = ', result
# пока все нормально выглядит
# теперь мне в хвост первого элемента (это тоже список) надо добавить 0,2
result[0].extend([0, 2])
# и вот ерунда, добавляется в оба элемента первого уровня
print 'result[0].extend([0, 2]) = ', result
# !!!!!! а должно получиться [[0,2,0,2], [0,2]] !!!

# попытка 2
print 'try 2'
result = [[0,2]] 
tmp = result
result.extend(tmp)
print 'result.extend(tmp) = ', result
result[0].extend([0, 2])
print 'result[0].extend([0, 2]) = ', result

# попытка 3, читала на SO
print 'try 3'
result = [[0,2]] 
tmp = list(result) # говорят надо использовать явный конструктор ????
result.extend(tmp)
print 'result.extend(tmp) = ',  result
result[0].extend([0, 2])
# и опять неправильно, [0,2] добавилось к каждому элементу первого уровня, а не только к первому
print 'result[0].extend([0, 2]) = ', result

# try 4, копирование в цикле
# в этом примере я пробую скопировать поэлементно,
print 'try 4'
result = [[0,2]] 
tmp = []
for e in result :
  tmp.append(e)
print 'tmp = ', tmp
result.extend(tmp)
print 'result.extend(tmp) = ', result
result[0].extend([0, 2])
# и опять тоже самой
print 'result[0].extend([0, 2]) = ', result

# вопрос
# как по настоящему скопировать список???









