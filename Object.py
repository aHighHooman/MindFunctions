import yaml

def loadParameters(name):
        return yaml.load(open('parameters.yaml'))['Object'][name]

# The difference between the object and person class strictly speaking is that 
# The object's action block will not be considerate of action choices.

class Object:
    durability = loadParameters('durability')
    def __init__(self):
        self.stateVectors = []
        self.actionChoices = []
        return 

    def processBroadcast(self,actionMessage,event):
        self.discretizeState(self.stateVectors,event)
        return

    def discretizeState(self,stateVectors,event):
        discretizedStates = []
        self.action(discretizedStates,event)
        return

    def action(self,discretizedStates,event):
        actionMessage = [self.identity, None, ]
        event.broadcast(actionMessage)
        return

