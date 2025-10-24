import Mind
import Util 
import numpy as np
import random



'''
- Looks: (Attraction is 70% Looks, 30% Actions, 20% Character)
    - Apparel:              (Changeable; -20 to 20)
        - Beauty
        - Clothes
        - Jewellery
        - Scars / Makeup    // Fuck this for the sake of my sanity
    - Fitness               (Changeable; -40 to 20)
    - Body Type             (Changeable; -10 to 10)
        - Buff          (Strong Body , Low Dex) : <3,1>
        - Balanced      (Medium Body , Medium Dex) : <2,2>
        - Dextrous      (Weak Body , High Dex) : <1,3>
    - Face                  (Fixed; -30 to 30)
        - Beauty
        - Masculine to Feminine  (Scale)
        - Eyes  
    - Hair                  (Changeable; -5 to 5)
        - Beauty
        - Style
        - Color
    - Height                (Fixed; -15 to 15)

'''



'''
Long Term Motivations
    - Authority
    - Influence
    - Growth
    - Stability

Short Term Motivations:
    - Survival

Interaction Directives:
    - Maintain Relationship
    - Improve Relationship
    
    - Spend Time (Fulfill Desire for social interaction?)
    - Destress
    
    - Improve Partner's mood
    - Reduce Partner's bad mood
 
Interaction Traits:
    - Moody (Acts mostly based on mood)
    - Observant (Better at discerning mood/directives)
    - Considerate (Better at eliciting positive reactions)
    - Sympathetic (Better at improving moods)
    - Comedic (Jokes more often, they trigger stronger reactions)
'''



'''
I want the person module to be a blackbox. With the following probes to be intereacted or understood with
- Speak (Say something probably a representative of mental state/mood)
- giveMood (Provide the current discrete mood)
- revealIntent (Show the directive or goal of any action, if there is no directive then mood + physical state are the bases)
'''
class Person:
    ID = 0
    BODYTYPE = {
        "Buff" : np.array([3,1]),
        "Balanced" : np.array([2,2]),
        "Dextrous" : np.array([1,3])
    }
    '''InteractionTraits = ["Moody","Observant","Considerate","Sympathetic","Comedic"]
    InteractionDirectives = {
        "Relationship": ["Maintain","Improve"],
        "Self": ["Destress","Socialize"],
        "Partner": ["Improve Mood", "Reduce Stress"]
    }'''

    def __init__(self):
        self.identity = Person.ID
        Person.ID += 1
        
        self.name = ""
        
        self.moralAlignment = ""
        self.personality = {
            "Neu": 0,
            "Agr": 0,
            "Ext": 0,
            "Con": 0,
            "Opn": 0
        }
        
        self.affiliation = ""
        self.job = ""

        self.weapon = ""
        self.armor = {
            "Head" : "",
            "Body" : "",
            "Leg"  : "",
            "Shoes": ""
        }
        self.artifacts = []

        self.fitness = Util.Norm(mu = 80, 
                            sigma = 20, 
                            ndigits = 1)           # 0 to 100
        self.appearance = {
            "Apparel" : {
                "Beauty" : Util.Norm(mu = 70, 
                                sigma = 30, 
                                ndigits = 1
                                ),       # 0 to 100
                "Clothes" : [],
                "Jewellery" : [],
            },
            "Body Type" : np.array([round(random.uniform(0,4), 2),round(random.uniform(0,4),2)]),       
            "Face" : {
                "Beauty" : Util.Norm(mu = 70, 
                                sigma = 30, 
                                ndigits = 1
                                ),       # 0 to 100   
                "Structure" : 0,    # -100 to 100
                "Eyes" : ""
            },
            "Hair" : [],
            "Height" : Util.Norm(mu = 50, 
                            sigma = 10,
                            ndigits=1
                            )       # 0 to 100; 0 extremely short and 100 extremely tall, 50 is the average
        }

 
        # This accounts for 70% of the looks
        # f(apparel,face,fitness) = objectiveBeauty 
        self.objectiveBeauty = self.appearance["Apparel"]["Beauty"] * 0.2 + self.appearance["Face"]["Beauty"] * 0.3
        if self.fitness <= 40:
            self.objectiveBeauty += (self.fitness - 40)         # (-40to0)      
        else:
            self.objectiveBeauty += (self.fitness - 40) / 3     # (1to60) / 3
        
        self.objectiveBeauty = round(self.objectiveBeauty)
        
        # [Name, Relationship, Looks, LoveVal, TrustVal, LikeVal]
        self.connections = {}

        # This is where I'll preset a person's preferences or tastes for looks to become the subjective
        # part of the beauty metric. This will account for the remaining 30% of looks
        self.heightPreference = self.appearance["Height"]
        self.bodyTypePreference = self.appearance["Body Type"]
        # self.hairPreference 

        
        self.mind = Mind.Mind(self)

        return
    
    # Intrinsic Functions, these are functional and *backend* functions of sorts
    def processBroadcast(self,action,event):
        target = action[1]
        if target != self.identity:
            return
        else: 
            self.react(action = action,event = event)
        return

    def getPerson(self,event, targetID):
        if "1-to-1" in event.context["Situation"]:
            return event.persons[targetID]
        else: 
            return event.persons

    def getRelationship(self,location, person):
        assert person.identity != self.identity, "Self Reference Error (getRelationship)"    
        
        relationship = "N/A"
        if self.connections.get(person.identity,"Stranger") == "Stranger":
            relationship = "Stranger"
            self.connections.update({person.identity : {
                "Name" : "N/A",
                "Relationship" : "Stranger", 
                "Looks" : 0, 
                "Like" : 0, 
                "Love" : 0, 
                "Trust" : 0
            }})   
        else:
            relationship = self.connections[person.identity]["Relationship"]
        
        if "Date" in location and self.connections[person.identity]["Relationship"] == "Stranger":
            self.connections[person.identity]["Relationship"] = "Date"
            relationship = "Date"

            
        assert relationship != "N/A", "getRelationship Function Failure"
        return relationship

    def react(self,event,action):
        context = event.context
        if context["Situation"] == "1-to-1":
            self.mind.perceivedAction[:] = action
            self.mind.reactFlag = True
            actionPacket = self.mind.process(event,reason = "React", targetID=action[0])
            
        assert actionPacket, "The Action Packet is Empty (Person.react)"
        return actionPacket  

    def initializeAction(self,event, targetID):
        #actionPacket = self.mind.emotionBlock(event, targetID=targetID)
        actionPacket = self.mind.process(event=event, targetID=targetID)
        return actionPacket

    # Probing Functions, use these functions to control or check a character's state
    def speak(self):
        return self.mind.decideAndAct()
    
    def revealIntention(self):
        return
    
    def revealMood(self):
        return self.mind.getMood()
    
    def print_summary(self, targetPersonID=None):
        print(f"\n--- Summary for Person {self.identity} ---")
        print(f"  Objective Beauty: {self.objectiveBeauty}")
        print(f"  Mood: {self.revealMood()}")
        print(f"  Emotion Vsector: {self.mind.emotionVector}")
        print(f"  Attraction Bias: {self.mind.biasVector}")
        if targetPersonID is not None:
            print(f"  Connections: {self.connections[targetPersonID]}")
        
