# Data Structures
## Relationships
- Classification Parameters: 
    - Like
    - Trust
    - Attraction
    - Unique Tag (Family , Spouse)

### Like Class (This is sufficient for all non-romantic connections)
- Nemesis       (Full Hostile Action Set Open)
- Hostile
- Stranger      (Minimum Action Set)
- Acquintance
- Friend        (Full Basic Action Set Open) 

### Trust Class 
- Stranger
- ...
- Close 

### Unique Tags (These are tags which require specific preconditions and cannot be acquired simply with like or trust class)
- Love (Special Tag requiring family or ceremony (marriage))
- Confidant (Only One; for top class trust)
- Best Friend (Only One; for top class like)
- Romantic Interest (Only One; for top class attraction)


## Personality Types (Unimplemented)
### Base Personalities
- For Game Design and Balancing Purposes each basis will have a pro and con
    - If a basis is stronger then I won't make it weaker I'll just make it occur more rarely

- **Neuroticism** 
    - Pro: Higher Work Speed / Higher Accuracy (Better Results)
    - Con: Higher sensitivity to stress (multiply incoming stress probably)
- **Agreeableness**
    - Pro: Higher Kindness, Higher Morals, Higher Cooperative Affinity
    - Con: Higher mood cost for immorality, cruelty, and suffering. 
- **Extraversion**
    - Pro: Higher Social Skill, Higher Expressiveness
    - Con: Higher Social Bar/desire
- **Conscientiousness**
    - Pro: Higher Work Quality / Higher Precision (Consisent Results)
    - Con: Higher costs with uncertain parameters (More)
- **Openness** 
    - Pro: Higher learning speed for new skills 
    - Con: Higher cost for gaining expertise

### Conversation Effects
- Type 01 : To affect/elicit an action from the listener
    - Prank
    - Insult
- Type 10 : To affect/fulfill a need of the speaker
    - Monologue
- Type 11 : To affect/fulfill need of both the speaker and listener
    - Converse
    - Spend Time 

- **Neurotic**
    - Less trust given universally
    - Less affected by attraction 
    - More likely to do type 10 actions
    - More perceptive
    - Stronger negative reactions
- **Agreeable**
    - Less likely to prank / insult 
    - Less affected by attraction
    - More like given and gained universally
    - More trust given and gained universally
    - Weaker negative reactions
- **Extraverted**
    - More likely to flirt
    - More likely to do type 01 or 10 actions 
    - More likely to be the one speaking
    - More perceptive 
    - Stronger reactions 
- **Conscientious**
    - More likely to do type 11 actions
    - More likely to converse based on logic than emotion
    - Less responsive to pranks/jokes/insults/flirts
- **Open**
    - More trusting of strangers
    - More likely to use jokes
    - Less likely to react negatively to anything


# Overview
## Person Class
## Mind Class
## Body Class


# Rough Work
If I want to design a normal distribution with mean $\mu$ and a given probability of failure (P(X < 0)), lets call it p. What should the SD or Var be.

Assuming SD = S
The Z score of 0 in such a distribution would be $\frac{0 - \mu}{S} = \frac{-\mu}{S}$
This means that P(X < 0) = P(Z < $\frac{-\mu}{S}$)

I have to find the Z score of which fulfills the condition let's call is Zp. 
From this I can deduce that $\frac{-\mu}{S} = Zp => S = \frac{\mu}{Zp}$