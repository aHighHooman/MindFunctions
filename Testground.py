import Person
import Event
import time
import numpy as np
import matplotlib.pyplot as plt

def TestEvent(numActions = 1):
    conversationLog = []

    Person1 = Person.Person()
    Person2 = Person.Person()
    
    personList = {}
    personList.update({Person1.identity: Person1})
    personList.update({Person2.identity: Person2})
    TestEvent = Event.Event(persons = personList) 
    # Must have a context dictionary, personList, a function to provide the mood offset due to the event
    
    actionPacket = Person1.initializeAction(event = TestEvent, targetID = Person2.identity)
    conversationLog.append(actionPacket)

    for _ in range(2*numActions):
        print(actionPacket)
        for personID in personList.keys():
            if actionPacket[0] == personID:
                continue
            responsePacket = personList[personID].react(event = TestEvent, action = actionPacket)
            #print(f"{Person1.mind.emotionVector}{Person2.mind.emotionVector}")
        
        actionPacket = responsePacket
        conversationLog.append(actionPacket)
    
    Person1.print_summary(Person2.identity)
    Person2.print_summary(Person1.identity)


def measurement(numActions = 1, numConvos = 1):
    measurements = {
        "like" : [],
        "joy"  : []
    }
    likeSum = 0
    joySum = 0
    numFlirt = 0
    trust = [0 for m in range(numActions)]
    like = [0 for m in range(numActions)]
    joy  = [0 for m in range(numActions)]
    envy = [0 for m in range(numActions)]
    wariness = [0 for m in range(numActions)]
    attraction = [0 for m in range(numActions)]
    for k in range (numConvos):
        Person1 = Person.Person()
        Person2 = Person.Person()
        
        personList = {}
        personList.update({Person1.identity: Person1})
        personList.update({Person2.identity: Person2})
        TestEvent = Event.Event(persons = personList) 
        # Must have a context dictionary, personList, a function to provide the mood offset due to the event
        
        actionPacket = Person1.initializeAction(event = TestEvent, targetID = Person2.identity)

        for i in range(2*numActions):
            print(actionPacket)
            for personID in personList.keys():
                if actionPacket[0] == personID:
                    continue
                responsePacket = personList[personID].react(event = TestEvent, action = actionPacket)
                #print(f"{Person1.mind.emotionVector}{Person2.mind.emotionVector}")
            if responsePacket[2].split(".")[0] == "Flirt":
                numFlirt += 1
            if i % 2 == 1:
                trust[i//2] =       1/(k+1)*    (trust[i//2]*k+        0.5*(Person1.connections[Person2.identity]["Trust"] + Person2.connections[Person1.identity]["Trust"]))
                like[i//2] =        1/(k+1)*    (like[i//2]*k+         0.5*(Person1.connections[Person2.identity]["Like"] +  Person2.connections[Person1.identity]["Like"]))
                joy[i//2] =         1/(k+1)*    (joy[i//2]*k+          0.5*(Person1.mind.emotionVector["Joy"] +              Person2.mind.emotionVector["Joy"]))                
                envy[i//2] =        1/(k+1)*    (envy[i//2]*k+         0.5*(Person1.mind.emotionVector["Envy"] +             Person2.mind.emotionVector["Envy"]))               
                wariness[i//2] =    1/(k+1)*    (wariness[i//2]*k+     0.5*(Person1.mind.emotionVector["Wariness"] +         Person2.mind.emotionVector["Wariness"]))
                attraction[i//2] =  1/(k+1)*    (attraction[i//2]*k+   0.5*(Person1.mind.biasVector["Attraction"] +          Person2.mind.biasVector["Attraction"]))
            actionPacket = responsePacket


    return like,trust, joy, envy, wariness , attraction


TestEvent(10)

'''likeMeasure,trustMeasure,joyMeasure,envyMeasure,warinessMeasure,attractionMeasure = measurement(numActions=300,numConvos=1)

plt.plot(trustMeasure, label = "Trust")
plt.plot(likeMeasure, label = "Like")
plt.plot(joyMeasure, label = "Joy")
plt.plot(envyMeasure, label = "Envy")
plt.plot(warinessMeasure, label = "Wariness")
plt.plot(attractionMeasure, label = "Attraction")
plt.legend()
plt.xlabel("Length of Conversation")
plt.show()'''

def run_detailed_simulation(num_steps=10):
    print("\n=== Starting Detailed Simulation ===")
    
    Person1 = Person.Person()
    Person1.name = "Alice"
    Person2 = Person.Person()
    Person2.name = "Bob"
    
    personList = {
        Person1.identity: Person1,
        Person2.identity: Person2
    }
    
    # Initialize an Event (e.g., a Date or Friendly Hangout)
    # Context: 1-to-1, Location: Enjoyment (Coffee Shop)
    TestEvent = Event.Event(persons=personList, event="Enjoyment", locationID="1")
    
    # Initial Action
    actionPacket = Person1.initializeAction(event=TestEvent, targetID=Person2.identity)
    
    history = []
    
    for step in range(num_steps):
        print(f"\n--- Step {step + 1} ---")
        
        # Log the action
        sender_id = actionPacket[0]
        target_id = actionPacket[1]
        action_type = actionPacket[2]
        action_desc = actionPacket[3]
        
        sender_name = Person1.name if sender_id == Person1.identity else Person2.name
        target_name = Person1.name if target_id == Person1.identity else Person2.name
        
        print(f"Action: {sender_name} -> {target_name}: {action_type} ('{action_desc}')")
        
        # Process reaction
        # The target reacts to the action
        target_person = personList[target_id]
        responsePacket = target_person.react(event=TestEvent, action=actionPacket)
        
        # Log Internal States AFTER the interaction
        for p in [Person1, Person2]:
            print(f"  > {p.name} State:")
            print(f"    Mood: {p.revealMood()}")
            print(f"    Emotion Vector: {p.mind.emotionVector}")
            print(f"    Attraction Bias: {p.mind.biasVector}")
            other_id = Person2.identity if p == Person1 else Person1.identity
            if other_id in p.connections:
                conn = p.connections[other_id]
                print(f"    Relationship with {personList[other_id].name}: Trust={conn.get('Trust',0):.1f}, Like={conn.get('Like',0):.1f}, Looks={conn.get('Looks',0):.1f}")
        
        actionPacket = responsePacket
        time.sleep(0.1) # Brief pause for effect if running interactively

    print("\n=== Simulation Complete ===")

if __name__ == "__main__":
    # TestEvent(10)
    run_detailed_simulation(10)
