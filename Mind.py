import numpy as np
import random 
import Util
import pandas as pd

# Set of all Actions
# I have been thinking of classifying the action structure into 4 types; I'll use a 2 digit binary system (Speaker , Listener)
'''
- 01 : To affect/elicit an action from the listener
    - Remark
    - Joke (?)
    - Gift
    - Prank
    - Insult
    - Compliment
    - Flirt (?)
- 10 : To affect/fulfill a need of the speaker
    - Monologue
- 11 : To affect/fulfill need of both the speaker and listener
    - Converse
    - Spend Time    
'''

# Add something about poetic talking
ALL_ACTIONS = {
            "Remark" : {
                "Remark" : ["Remark1"]
                },
            "Converse" : {
                "Formal" : ["Formal1"],
                "Friendly" : ["Friendly1"],
                "Casual" : ["Casual1"],
                "Deep" : ["Deep1"]
            },
            "Joke" : {
                "Dark" : ["Dark1"],
                "Dirty": ["Dirty1"],
                "Self Deprecating" : ["Self Deprecating1"],
                "Pun" : ["Pun1"],
                "Sarcastic" : ["Sarcastic1"]
            },
            "Gift" : {
                "Gift" : ["Gift1"]
            },
            "Prank": {
                "Prank" : ["Prank1"]
            },
            "Insult": {
                "Insult":["Insult1"]
            },
            "Spend Time": {
                "Spend Time": ["Spend Time1"]
            },
            "Compliment": {
                "Appearance": ["Appearance1"],
                "Character": ["Character1"],
                "Skills": ["Skills1"]
            },
            "Monologue": {
                "Vent" : ["Vent1"],
                "Storytelling" : ["Storytelling1"],
                "Gossip" : ["Gossip1"]
            },
            "Flirt": {
                "Subtle Actions": ["Subtle Actions1"],
                "Subtle Talk" : ["Subtle Talk1"]
            },
        }

# Emotion Vector : <Joy, Envy, Wariness>
MOOD_PRESETS = {
        "Excited"   : np.array([87.5,0,0]),
        "Joyful"    : np.array([62.5,0,0]),
        "Happy"     : np.array([37.5,0,0]),
        "Irritated" : np.array([-37.5,0,0]),
        "Frustrated": np.array([-62.5,0,0]),
        "Angry"     : np.array([-87.5,0,0]),
        "Furious"   : np.array([-87.5,0,-75]),
        "Resentful"   : np.array([0,87.5,0]),
        "Envious"     : np.array([0,62.5,0]),
        "Greedy"      : np.array([0,62.5,-75]),
        "Discontent"  : np.array([0,37.5,0]),
        "Content"     : np.array([0,-37.5,0]),
        "Satisfied"   : np.array([0,-62.5,0]),
        "Fulfilled"   : np.array([0,-87.5,0]),
        "Hyper Vigilant" : np.array([0,0,87.5]),
        "Cautious"       : np.array([0,0,62.5]),
        "Observant"      : np.array([0,0,37.5]),
        "Bold"           : np.array([0,0,-37.5]),
        "Reckless"       : np.array([0,0,-62.5]),
        "Impulsive"      : np.array([0,0,-87.5])
    }
POSITIVE_MOODS = ["Excited","Joyful","Happy","Content","Satisfied","Fulfilled"]
MAXIMUM_MOOD_DISTANCE2 = 25**2 # If any preset mood is further than this then it doesn't count

# Sets of all relationships
ALL_RELATIONSHIPS = {
                     "Enemy","Nemesis","Bad Acquaintance",
                     "Stranger","Familiar",
                     "Date", "Friend", "Best Friend",
                     "Father" , "Mother" , "Brother" , "Sister" , "Son" , "Daughter",
                     "Lover" , "Wife" , "Husband"
                     }
BAD_RELATIONSHIPS = {"Enemy","Nemesis","Bad Acquaintance"}
NEUTRAL_RELATIONSHIPS = {"Stranger","Familiar" "Date"}
GOOD_RELATIONSHIPS = {"Date", "Friend", "Best Friend"}
ROMANTIC_RELATIONSHIPS = {"Lover"}
EMOTIONAL_RELATIONSHIPS = {"Father" , "Mother" , "Brother" , "Sister" , "Son" , "Daughter"}

# Relationship mood offsets
RELATIONSHIP_DELTAS = {
    "Family":           { "joy":  20,  "envy":  0,  "wariness":   0,  "attraction":  10 },
    "Lover":            { "joy":  30,  "envy":  0,  "wariness":   0,  "attraction":  25 },
    "Best Friend":      { "joy":  50,  "envy":  0,  "wariness":   0,  "attraction": -10 },
    "Friend":           { "joy":  30,  "envy":  0,  "wariness":   0,  "attraction":   0 },
    "Date":             { "joy":   0,  "envy":  0,  "wariness":  15,  "attraction":  15 },
    "Obsession":        { "joy":  50,  "envy":  0,  "wariness": -50,  "attraction":  25 },
    "Bad Acquaintance": { "joy": -20,  "envy":  0,  "wariness":  10,  "attraction":   0 },
    "Enemy":            { "joy": -30,  "envy":  0,  "wariness":  20,  "attraction":   0 },
    "Nemesis":          { "joy": -50,  "envy":  0,  "wariness":  50,  "attraction":   0 },
    "Stranger":         { "joy":   0,  "envy":  0,  "wariness":  10,  "attraction":   0 },
    "N/A":              { "joy":   0,  "envy":  0,  "wariness":   0,  "attraction":   0 },
}

# Attraction Thresholds
THRESHOLD_MATRIX = pd.DataFrame({
    "Attraction":   {"Low": 42, "Medium": 56, "High": 70},
    "Like":         {"Low": 42, "Medium": 56, "High": 80},
    "Trust":        {"Low": 42, "Medium": 56, "High": 70},
    "Joy":          {"Low": 37.5, "Medium": 62.5, "High": 87.5},
    "Envy":         {"Low": 37.5, "Medium": 62.5, "High": 87.5},
    "Wariness":     {"Low": 37.5, "Medium": 62.5, "High": 87.5}
})
LOW_ATTRACTION_THRESHOLD = 42
MED_ATTRACTION_THRESHOLD = 56
HIGH_ATTRACTION_THRESHOLD = 70

# Reaction Failure Probabilities
VARIANCE_MATRIX = pd.Series({
   "Remark" :       0.25,
   "Converse" :     0.25,
   "Monologue" :    0.25,
   "Spend Time" :   0.25,
   "Compliment" :   0.25,
   "Joke" :         0.25,
   "Flirt" :        0.35,
})

# Reaction Means
REACTION_MATRIX = pd.DataFrame(
    {
    "Remark" :    {
                    "Joy":          0,
                    "Envy":         0,
                    "Wariness":     0,
                    "Attraction":   0,  
                    "Like" :        0, 
                    "Trust" :       0
                    },
    "Converse" :    {
                    "Joy":          0.3,
                    "Envy":         0,
                    "Wariness":     0,
                    "Attraction":   0,  
                    "Like" :        0.05, 
                    "Trust" :       0.1
                    },
    "Monologue" :   {
                    "Joy":          0,
                    "Envy":         0,
                    "Wariness":     0,
                    "Attraction":   0,  
                    "Like" :        0.05, 
                    "Trust" :       0.1
                    },
    "Spend Time" :  {
                    "Joy":          0.3,
                    "Envy":         0,
                    "Wariness":     0,
                    "Attraction":   0,  
                    "Like" :        0.2, 
                    "Trust" :       0.1
                    },
    "Compliment" :  {
                    "Joy":          0.3,
                    "Envy":         0,
                    "Wariness":     0,
                    "Attraction":   0,  
                    "Like" :        0.1, 
                    "Trust" :       0
                    },
    "Joke" :        {
                    "Joy":          0.2,
                    "Envy":         0,
                    "Wariness":     0,
                    "Attraction":   0,  
                    "Like" :        0.1, 
                    "Trust" :       0
                    },
    "Flirt":        {
                    "Joy":          0.2,
                    "Envy":         0,
                    "Wariness":     0.1,
                    "Attraction":   0.3,  
                    "Like" :        0.2, 
                    "Trust" :       0
                    },
})

# Steady State Conversation Parameters
SS = pd.Series({"Joy":          THRESHOLD_MATRIX["Joy"]["High"], 
                "Envy":         THRESHOLD_MATRIX["Envy"]["Low"], 
                "Wariness":     THRESHOLD_MATRIX["Wariness"]["Low"],
                "Like":         THRESHOLD_MATRIX["Like"]["High"], 
                "Trust":        THRESHOLD_MATRIX["Trust"]["Medium"], 
                "Attraction":   THRESHOLD_MATRIX["Attraction"]["Medium"]})

class LogicBlock:
    def __init__(self, parentMind):
        self.myMind = parentMind

        self.getRelationship = self.myMind.getRelationship
        return

    def think(self, event, personID,): 
        context = event.context

        if context["Situation"] == "1-to-1":
            choices = self.figureOptions(event,personID)
            actionPacket = self.decideAndAct(targetIdentity=personID,choices=choices)
            #event.broadcast(self.decideAndAct(targetIdentity=personID,choices=choices))
            return actionPacket
        return
    
    def thinkReaction(self, reaction, targetID):
        if reaction:
            print(f"Person {self.myMind.identity} reacted positively to Person {targetID}")
        else:
            print(f"Person {self.myMind.identity} reacted negatively to Person {targetID}")
        return

    # f(self,person,context) = possible Actions
    def figureOptions(self,event,personID):

        # Which factors would go into considering what is possible? 
        # - Relationship with person (Captures Connection)
        # - Attraction to the person (Captures Appearance)
        # - Personality Traits       (Captures Constant Internal State)
        # - Current Mood             (Captures Dynamic Internal State)
        # - Person's Gender          (Captures Romantic/Sexual Alignment)

        # Relationship Stage ---------------------------
        relationship = self.getRelationship(personID = personID)
        attraction = self.myMind.biasVector["Attraction"]
        preferredChoices = []
        
        badRelationship = relationship in BAD_RELATIONSHIPS
        neutralRelationship = relationship in NEUTRAL_RELATIONSHIPS
        goodRelationship = relationship in GOOD_RELATIONSHIPS 
        emotionalRelationship = relationship in EMOTIONAL_RELATIONSHIPS
        
        # Attraction Stage --------------------------------
        slightlyAttracted = attraction in range(THRESHOLD_MATRIX["Attraction"]["Low"],THRESHOLD_MATRIX["Attraction"]["Medium"])
        attracted =         attraction in range(THRESHOLD_MATRIX["Attraction"]["Medium"],THRESHOLD_MATRIX["Attraction"]["High"])
        veryAttracted =     attraction > THRESHOLD_MATRIX["Attraction"]["High"]
  
        # Personality Stage -------------------------------
        # Mood Stage --------------------------------------
        # Gender Stage (?) --------------------------------

        # Choosing Stage -------------------------
        if badRelationship: 
            preferredChoices = []
        if neutralRelationship:
            preferredChoices.append("Remark")
            if slightlyAttracted:
                preferredChoices.append("Compliment")
            if attracted or (slightlyAttracted and "Enjoyment" in event.location):
                preferredChoices.append("Flirt")
        if goodRelationship:
            preferredChoices.append("Joke")
            preferredChoices.append("Converse")
            preferredChoices.append("Monologue")
            preferredChoices.append("Compliment")  
            if veryAttracted or attracted or (slightlyAttracted and "Enjoyment" in event.location):
                preferredChoices.append("Flirt") 
        if emotionalRelationship:
            preferredChoices.append("Joke")
            preferredChoices.append("Converse")
            preferredChoices.append("Monologue")
            preferredChoices.append("Compliment")
        '''else:
            print(f"Relationship Error: Relationship:{relationship}; Mind.figureOptions")'''
        
        return preferredChoices
    
    # f(self,person,actionChoice) = Action
    def decideAndAct(self,targetIdentity = None,choices = []):
        assert targetIdentity is not None, "Target Identity Undefined (decideAndAct)"

        # Temp
        if choices == []:
            choices = list(ALL_ACTIONS.keys())

        predictabilityThreshold = 1 # An element of randomness
        num = random.random()
        type = ""
        
        if num < predictabilityThreshold:
            action = random.choice(choices)
            description = ALL_ACTIONS[action]
            type = f"{random.choice(list(ALL_ACTIONS[action]))}"
            description = description[type]
            return [self.myMind.identity,targetIdentity,f"{action}.{type}",description]
        else: 
            action = random.choice(ALL_ACTIONS.keys)
            type = f"{random.choice(ALL_ACTIONS[action].keys)}"
            description = description[type]
            return [self.myMind.identity,targetIdentity,f"{action}.{type}",description]



class EmotionBlock:
    def __init__(self, parentMind):
        self.myMind = parentMind

        self.getPerson = self.myMind.getPerson
        self.getRelationship = self.myMind.getRelationship
        self.getMood = self.myMind.getMood
        return    

    # Provides Initial Parameters/Offsets
    def feel(self, event, targetID = None, cues = [], reason = "Greet"):
        assert targetID is not None, "No Target Individual (emotionBlock)"
        eventContext = event.context
        person = self.getPerson(event, ID = targetID) # will have to adjust for multiple people later
        
        # f(event.location) = emotionValue
        eventOffset = event.emotionOffset()
        self.myMind.emotionVector = Util.addDictionaries(self.myMind.emotionVector, eventOffset)

        if eventContext["Situation"] == "1-to-1":
            self.evaluateRelationship(personID=targetID)
            self.evaluateLooks(person=person)        
        return 

    # Updates Internal Parameters of NPC
    def feelReaction(self):
        sender = self.myMind.perceivedAction[0]
        action = self.myMind.perceivedAction[2].split(".")[0]
        trust = self.myMind.connections[sender]["Trust"] 
        like = self.myMind.connections[sender]["Like"] 
        joy = self.myMind.emotionVector["Joy"] 
        envy = self.myMind.emotionVector["Envy"] 
        wariness = self.myMind.emotionVector["Wariness"]
        attraction = self.myMind.biasVector["Attraction"] 

        currentVals = pd.Series({"Joy" : joy, "Envy" : envy, 'Wariness': wariness,
                                 "Trust": trust, "Like": like, "Attraction": attraction})

        # Attraction Stage
        attractionMultiplier = 1

        # Mood Stage
        moodMultiplier = 1

        # Randomness Stage
        threshold = Util.PtoZ(attractionMultiplier * moodMultiplier * VARIANCE_MATRIX[action])
        reactionDeltas = REACTION_MATRIX[action].apply(lambda x: random.gauss(mu=x , sigma=0.1 + x/threshold))
        
        # Evaluation Stage
        currentVals += (SS - currentVals) * reactionDeltas
        currentVals = currentVals.apply(lambda x: round(x, 1))
        currentVals = currentVals.apply(lambda x: max(0, x))


        self.myMind.connections[sender]["Trust"] =  currentVals["Trust"]
        self.myMind.connections[sender]["Like"] =   currentVals["Like"]
        self.myMind.emotionVector["Joy"] =          currentVals["Joy"]
        self.myMind.emotionVector["Envy"] =         currentVals["Envy"]
        self.myMind.emotionVector["Wariness"] =     currentVals["Wariness"]
        self.myMind.biasVector["Attraction"] =      currentVals["Attraction"]
        '''print(f"Trust: {self.connections[sender]['Trust']},Like: {self.connections[sender]['Like']}")
        print(f"{self.emotionVector}")
        print(f"{self.biasVector}")'''
        return True

        # f(person, self) = attraction; in general people like those more similar to themselves
    
    def evaluateLooks(self,person):
        assert person.identity != self.myMind.identity, "Self Reference Error (evaluateRelationship)"          

        # Objective Looks 
        looks = person.objectiveBeauty

        # Height Stage
        heightDelta = abs(self.myMind.heightPreference - person.appearance["Height"])
        if heightDelta <= 10:
            looks += (10 - heightDelta)             # <0,10>          
        else:
            looks -= (heightDelta - 10) * 10 / 79   # <-10,0>
        
        # Body Type Stage
        bodyTypeDelta = (self.myMind.bodyTypePreference.dot(person.appearance["Body Type"])) / (Util.magnitude(self.myMind.bodyTypePreference) * Util.magnitude(person.appearance["Body Type"]))
        looks += -10 + 20 * bodyTypeDelta           # -10 + 20 * <0to1>
        looks = round(looks)



        # Attraction Evaluation 
        if looks >= 70:
            attraction = Util.mapLinear(looks, minIn = 70, maxIn = 100, minOut = 49, maxOut = 70)
        elif looks >= 30 and looks <= 69:
            attraction = Util.mapLinear(looks, minIn = 30, maxIn = 69, minOut = 0, maxOut = 49)
        else:
            attraction = 0

        self.myMind.connections[person.identity]["Looks"] = looks
        self.myMind.biasVector["Attraction"] = round(attraction,1) 
        return

        # See if you can get something better than just arbitrarily assigning the deltas
    # f(person, self) = emotion due to relationship
    def evaluateRelationship(self,personID):
        assert personID != self.myMind.identity, "Self Reference Error (evaluateRelationship)"          
        
        relationship = self.getRelationship(personID = personID)
        deltas = RELATIONSHIP_DELTAS.get(relationship, "N/A")
        
        joyDelta = deltas["joy"]
        envyDelta = deltas["envy"]
        warinessDelta = deltas["wariness"]
        attractionDelta = deltas["attraction"]

        self.myMind.biasVector["Attraction"] += attractionDelta
        self.myMind.emotionVector["Envy"] += envyDelta 
        self.myMind.emotionVector["Joy"] += joyDelta
        self.myMind.emotionVector["Wariness"] += warinessDelta 



class MemoryBlock: 
    def __init__(self,):
        return



class Mind:
    def __init__(self, parentPerson):   
        # Inheritance ------------------------------------
        self.me = parentPerson
        
        self.identity = self.me.identity
        self.connections = self.me.connections
        self.heightPreference = self.me.heightPreference
        self.bodyTypePreference = self.me.bodyTypePreference

        # Core Variables ---------------------------------
        self.perceivedAction = []
        self.emotionVector = {
            "Joy" : 0,
            "Envy" : 0,
            "Wariness" : 0,
        }
        self.biasVector = {
            "Attraction" : 0
        }
        self.evaluatedFlag = False
        self.reactFlag = False

        # Children ----------------------------------------
        self.LogicBlock = LogicBlock(self)
        self.EmotionBlock = EmotionBlock(self)
        
        return
    
    def process(self, event, targetID = None, cues = [], reason = "Greet"):
        if not self.evaluatedFlag:
            self.EmotionBlock.feel(event=event, targetID=targetID, cues=cues, reason=reason)
            self.evaluatedFlag = True
        if self.reactFlag:
            reaction = self.EmotionBlock.feelReaction()
            #self.LogicBlock.thinkReaction(reaction=reaction, targetID=targetID)
            self.reactFlag = False
        
        actionPacket = self.LogicBlock.think(event=event, personID=targetID)

        return actionPacket

    # f(Event, PersonID) = Person Object
    def getPerson(self,event, ID = None):
        assert ID != self.identity, "Self Reference Error (Mind.getPerson)"    
        assert ID is not None, "No Target ID (Mind.getPerson)"

        if "1-to-1" in event.context["Situation"]:
            if not ID:
                return event.persons[0]
            else:
                return event.persons[ID]
        else: 
            return event.persons

    def getMood(self, numMoods = 3):
        emotionVector = np.array([
            self.emotionVector["Joy"],
            self.emotionVector["Envy"],
            self.emotionVector["Wariness"]
            ])
        
        distances = {}
        for emotion in MOOD_PRESETS:
            emotionPreset =  MOOD_PRESETS[f"{emotion}"]
            distances.update({emotion : Util.distance2(emotionPreset,emotionVector)})
        
        #sortedDistances = dict(sorted(distances.items(), key=lambda item: item[1]))
        
        moods = []
        
        for i in range(numMoods):
            nearestMood = min(distances,key = distances.get)
            
            if distances[nearestMood] > MAXIMUM_MOOD_DISTANCE2:
                moods.append("Normal")
                return moods
            
            moods.append(nearestMood)
            del distances[nearestMood]
        
        return moods

    # f(person, self) = Relationship
    def getRelationship(self, personID):
        assert personID != self.identity, "Self Reference Error (getRelationship)"    
        
        # Check if you recognize this person otherwise return Stranger, 
        identity = self.connections.get(personID,"Unknown")

        if identity == "Unknown":
            relationship = "Date"
            self.connections.update({personID : {
                "Name"          : "N/A",
                "Relationship"  : relationship, 
                "Looks"         : 0, 
                "Like"          : 0, 
                "Love"          : 0, 
                "Trust"         : 0,
                "Tag"           : "N/A"
            }})   
        else:
            relationship = self.connections[personID]["Relationship"]
            
        return relationship

