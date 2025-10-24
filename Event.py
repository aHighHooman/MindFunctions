# The Event is a class you can consider an external input to the blackbox, modification is expected and maybe even encouraged,
# I will consider making the blackbox more capable of working with it
class Event:
    
    def __init__(self, persons = [], context = "1-to-1", event = "Enjoyment", locationID = "-1"):
        self.context = {
            "Situation": "1-to-1",
            "Severity" : 0,
            "Risk"     : 0
            }
        self.persons = persons
        
        # Syntax: LocationType.Event.LocationID
        # The first 2 are necessary
        self.location = event + "." + f"{locationID}"

        return

    # What type of emotions can be inflicted
    '''
    - Panic (Wariness -= 2)
    - Fear (Wariness += 1)
    - Joy (Joy += 1)
    - Despair ()
    - Comfort (Like += 1 ; Love += 1)
    '''
    def emotionOffset(self):
        joy = 0
        envy = 0
        wariness = 0
        location = self.location

        match location.split(".")[0]:
            case "Emergency":     # Inflict Panic or Fear
                wariness += 50
            case "Work":          # Inflict Stress
                wariness *= 1.2
                joy -= 10
            case "Relaxation":    # Inflict Destress 
                joy += 10
                wariness *= 0.8
            case "Enjoyment":     # Inflict Joy
                joy += 20
            case "Home":          # Inflict Comfort
                wariness *= 0.5
            case "Shop":          # Inflict Focus
                wariness += 10
            case _:
                location = "N/A"
        
        assert location != "N/A", "event location failure (emotionOffset)"
        return {"Joy": joy, "Envy": envy, "Wariness": wariness}
        
    def broadcast(self,action):
        #print(action)
        self.actionCount += 1
        
        if self.actionCount < 10:
            for person in self.persons.values():
                person.processBroadcast(action,event = self)
        return

    def provideSource(self,resource):
        locationID = int(self.location.split(".")[2])
        return Location.provideSource(locationID = locationID, resource = resource)
        
''' 
- Location Parameters:
    - Type: 
        - Emergency 
            - Battlefield
            - Fire
            - Raid
        - Work
            - Work Cafe
            - Roof
            - Meeting Room 
        - Relaxation
            - Work Library
            - Public Library 
            - Book Cafe
            - Gym
        - Home
        - Shop
            - Weapon Smith
            - Armor Smith
            - Clothing Store
            - Farmer's Market
        - Enjoyment
            - Theatre
            - Coffee Shop
            - Dine in Restaurant 
            - Fast Food Restaurant
            - Party
            - Pub 
        - Misc
            - Field
            - Road/Path
            - Funeral 
            - Marriage
- Context Parameters:
    - Persons: []
    - Situation Type: 
        - Conversation(1-to-1)
        - Council(1-to-Many)
        - Duel(1-to-1)
        - Battle(Many-to-Many) 
        - Neutral(1-to-None)
    - Severity (Level of Mental Impact):
        - Formal
        - Casual
        - Thoughful
        - Deep
        - Serious
    - Risk (Difficulty):
        - Easy        ( No risk         +       No Difficulty          )
        - Stimulating ( No risk         +       Decent Difficulty      )
        - Focus       ( Low-Decent risk +       Low-Decent Difficulty  )
        - Risky       ( High risk       +       Low-Decent Difficulty  ) ////// Maybe remove
        - Hard        ( Low-Decent risk +       High Difficulty        )
        - Dangerous   ( High risk       +       High Difficulty        )
        - Sacrifice   ( Extreme risk    +       High Difficulty        )
        - Ultimatum   ( Extreme risk    +       Extreme Difficulty     )

Event = {
        "Visual": [],
        "Auditory": [],
        "Olfactory": [],
        "Tactile": [],
        "Taste": [],
        "Emotion": [],
        "Logic": [], 
        "Location": [], # Bedroom, Shop, Meeting Room
        "Context": [], # Planning, Partying, War etc
        } 
'''



class Location:        
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
    

'''home0 = Location("Home", archetype="Home")
print(home0.furniture)

event0 = Event(locationID = home0.ID)
print(event0.location)
print(event0.provideSource("Clean"))'''