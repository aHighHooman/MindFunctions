import random
import matplotlib.pyplot as plt

cost = 0
numberOfEvents = 0


p = 0.5
hyperParameter = 3

finalBudgets = []

for j in range(1000):
    budget = 0
    for i in range(100):
        budget += 1
        if budget > hyperParameter * 1/p:
            budget -= 1/p
            numberOfEvents += 1

        if random.random() < p:
            if budget > 0:
                budget -= 1/p
                numberOfEvents += 1
    finalBudgets.append(budget)

plt.hist(finalBudgets)
print(numberOfEvents / 100000)
plt.show()

