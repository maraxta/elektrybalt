# -*- coding: utf8

import time, wd


def test1():
   d = wd.PoetryDict()
   d.readStressFile()

   testAnswer = d.YottedRhyme(u"краси'вей")
   totalRequests = 0

   t0 = time.time()

   for c in range(0, 99) :
      for w in testAnswer :
         ll = d.Rhyme(w)
      totalRequests += len(testAnswer)
   t1 = time.time()

   print str(totalRequests) + " at " + str(t1-t0) + " seconds"