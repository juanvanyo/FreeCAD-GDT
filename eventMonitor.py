import FreeCADGui, FreeCAD, Part
from pivy.coin import *

class EventMonitor:
  '''
     Easy method to bind a callback to slot events.
     Usage:
     monitor = Monitor()
     fn = lambda data: function(data[0], data[1]) #and so on...
     monitor.append(Monitorized_object_name, monitoring_object_name, fn, (self, important_data))
     .....
     monitor.remove(monitoring_object_name)
  '''
  #SUPPORTED_EVENTS = ['all', 'object', 'document', 'deleted_object' 'changed_object', 'created_object', 'activate_document', 'relabel_document', 'delete_document', 'create_document']
  
  def __init__(self):
    FreeCAD.Console.PrintMessage('Starting ' + self.__class__.__name__ + '\n')
    self.lines = {}

  def append(self, objName, callerName, fn, data=None ):#, events='all'
    '''
       Run fn(data) whenever objName is deleted (by now)
       if no data, fs() is called
       if the object 'callerName' is deleted, this listener stop listening for it but it remains working for all other callers
    '''
    # TODO: generate a list for each kind of event
    #events = events if type(events) is list else [events]
    if not objName in self.lines:
      self.lines[objName] = []
    self.lines[objName].append((fn,data,callerName))
    FreeCAD.addDocumentObserver(self)

  def hasCaller(self, callerName):
    for line, data in self.lines.items():
       if len([x for x in data if x[2] == callerName]) > 0:
         return True
    return False

  def remove(self, callerName):
    '''
       Stops listening events FOR callerName
       If callerName isn't in the 'listening for' list, it has no effect
    '''
    for line, data in self.lines.items():
       for s in [x for x in data if x[2] == callerName]:
         self.lines[line].remove(s)
         if len(self.lines[line]) == 0:
           self.pop(line)

  def pop(self, objName):
    '''
       Stops listening events of object objName
       If objName isn't in listening list, it has no effect
    '''
    self.lines.pop(objName,None)
    if len(self.lines) == 0:
      FreeCAD.removeDocumentObserver(self)

  def fire(self, objName):
    '''
       Runs callbacks linked to objName if any
    '''
    for fn,data,caller in self.lines.get(objName,[]):
      fn(data) if data else fn()


  def slotCreatedDocument(self, doc):
    '''
       Do nothing by now
    '''
    FreeCAD.Console.PrintMessage('slotCreatedDoc\n')

  def slotDeletedDocument(self, doc):
    '''
       Do nothing by now
    '''
    FreeCAD.Console.PrintMessage('slotDeletedDoc\n')

  def slotRelabelDocument(self, doc):
    '''
       Do nothing by now
    '''
    FreeCAD.Console.PrintMessage('slotRelabelDoc\n')

  def slotActivateDocument(self, doc):
    '''
       Do nothing by now
    '''
    FreeCAD.Console.PrintMessage('slotActivateDoc\n')

  def slotCreatedObject(self, obj):
    '''
       Do nothing by now
    '''
    FreeCAD.Console.PrintMessage('slotCreatedObject\n')

  def slotDeletedObject(self, obj):
    '''
       Delete event
    '''
    FreeCAD.Console.PrintMessage('slotDeletedObject' + ' ev: ' + obj.Name + '\n')
    #FreeCAD.Console.PrintMessage('listening to ' + ','.join(self.lines.keys()) + '\n')

    self.fire(obj.Name) # Run callbacks
    self.remove(obj.Name) # stop listening for this object (if it vas listening for)
    self.pop(obj.Name) # remove from listening this deleted object (if it was listening to)

  def slotChangedObject(self, obj, prop):
    '''
       Do nothing by now
    '''
    FreeCAD.Console.PrintMessage('slotChangedObject' + ' ev: ' + obj.Name + ':' + prop + '\n')
