import numpy as np
# Openness, Cons, Extra, Agree, Neuro
meanVector = np.array([3,3.4,3.08,3.45,2.09])
averageVector = np.array([2.86,3.22,2.9,3.09,2.13])
resilientVector = np.array([3.27,3.53,3.41,3.81,1.96])
overControlledVector = np.array([2.43,2.8,2.34,2.34,2.51])
underControlledVector = np.array([2.61,3.27,2.57,3.68,2.44])


reservedVector = np.array([3.25, 3.25, 2.6, 3.55, 3.25])
excitableVector = np.array([3.8 , 3.5 , 3.75 , 4.1 , 3.7])
wellAdjustedVector = np.array([3.75 , 3.75 , 3.6 , 4.2 , 2.4])
mean2Vector = (reservedVector + excitableVector + wellAdjustedVector) / 3

def printNormalized(arr, mean):
    print(f"{np.round((arr - mean) / np.linalg.norm((arr - mean)), 2)}")

printNormalized(averageVector , meanVector)
printNormalized(resilientVector , meanVector)
printNormalized(overControlledVector , meanVector)
printNormalized(underControlledVector , meanVector)

printNormalized(reservedVector , mean2Vector)
printNormalized(excitableVector , mean2Vector)
printNormalized(wellAdjustedVector , mean2Vector)