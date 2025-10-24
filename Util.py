import random
from scipy.stats import norm
# There are 2 Prereqs for this function
# - The data inside each entry of the dictionary must be numbers
def addDictionaries(*args, keySet = "equal"):
    if len(args) == 1:
        return args
    else:
        keySubset = set(args[0].keys())
        keySuperset = set(args[0].keys())
        for arg in args: 
            keySubset = keySubset.intersection(set(arg.keys()))
            keySuperset = keySuperset.union(set(arg.keys()))

        # To make sure all dictionaries are the "same"
        if keySubset != keySuperset and keySet == "equal":
            print(f"Different keyLists: \nSuperset:{keySuperset} \nSubset:{keySubset}")
            return


        sumDic = {}
        for key in keySuperset:
            sumDic.update({key : 0})
        
        for arg in args:
            for key in keySuperset:
                sumDic[key] += arg.get(key, 0)

        if keySet == "union" or "equal":
            return sumDic
        elif keySet == "intersection":
            intersectionDic = {}
            for key in sumDic.keys():
                if key in keySubset:
                    intersectionDic.update({key : sumDic[key]})
            return intersectionDic
        else:
            return None

def mapLinear(input, minIn = 0, maxIn = 100, maxOut = 100, minOut = 0):
    return minOut + max((input - minIn) * (maxOut - minOut)/(maxIn - minIn),0)

def Norm(mu = 0, sigma = 1, minimum = 0, maximum = 100, ndigits = 0):
    return round(min(maximum, max(minimum, random.gauss(mu, sigma))), ndigits = ndigits)

def distance2(vec1, vec2):
    diff = vec1 - vec2
    return diff.dot(diff)

def magnitude(array):
    sum = 0
    for i in range(len(array)):
        sum += array[i]**2
    return sum**0.5


def PtoZ(p):
    return norm.ppf(p)

#print(PtoZ(0.25))

