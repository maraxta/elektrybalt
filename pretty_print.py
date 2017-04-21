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
