import yaml

def loadParameters(name):
        return yaml.load(open('parameters.yaml'))['Environment'][name]

# Class to Serve as Communication Medium for the NPCs
class Environment:
    actionLimit = loadParameters('actionLimit')
    
    def __init__(self, persons = []):
        self.persons= persons
        self.actionMessages = []
        self.actionCount = 0
        return            
    
    def broadcast(self , actionMessage):
        #print(action)
        self.actionMessages.append(actionMessage)
        self.actionCount += 1
        
        if self.actionCount < Environment.actionLimit:
            for person in self.persons.values():
                person.processBroadcast(actionMessage, event=self)
        return

        


'''class Location:        
    locationID = 0
    locationList = ["N/A"]

    def provideSource(locationID,resource):
        sourceList = []
        location = Location.locationList[locationID]

        match (resource):
            case "Rest":                
                for item in location.furniture:
                    if "Rest" in item.split("."):
                        sourceList.append(item.split(".")[0])
                
            case "Drink":
                for item in location.furniture:
                    if "Drink" in item.split("."):
                            sourceList.append(item.split(".")[0])
                    
            case "Eat":
                for item in location.furniture:
                    if "Eat" in item.split("."):
                            sourceList.append(item.split(".")[0])

            case "Excrete":
                for item in location.furniture:
                    if "Excrete" in item.split("."):
                            sourceList.append(item.split(".")[0])
                    
            case "Clean":
                for item in location.furniture:
                    if "Clean" in item.split("."):
                            sourceList.append(item.split(".")[0])
        
        sourceList.append("Elsewhere")
        return sourceList
    
    
    def __init__(self, locationType, furniture = [], archetype= "N/A"):
        self.locationType = locationType
        self.furniture = furniture.copy()
        Location.locationID += 1
        self.ID = Location.locationID
        Location.locationList.append(self)
        
        if archetype == "N/A":
            return
        else:
            match (archetype):
                case "Home":
                    if not("Bed.Rest" in self.furniture): self.furniture.append("Bed.Rest")
                    if not("Stove.Cook" in self.furniture): self.furniture.append("Stove.Cook")
                    if not("Table.Eat" in self.furniture): self.furniture.append("Table.Eat")
                    #if not("Chair" in self.furniture): self.furniture.append("Chair")
                    if not("Toilet.Excrete" in self.furniture): self.furniture.append("Toilet.Excrete")
                    if not("Shower.Clean" in self.furniture): self.furniture.append("Shower.Clean")
                    if not("Sink.Drink" in self.furniture): self.furniture.append("Sink.Drink.Clean")

        return
'''    

'''home0 = Location("Home", archetype="Home")
print(home0.furniture)

event0 = Event(locationID = home0.ID)
print(event0.location)
print(event0.provideSource("Clean"))'''