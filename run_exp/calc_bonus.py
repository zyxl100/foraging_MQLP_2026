import math
# Calculate bonus for workers
# Decay rates are sample from a gaussian with params, mu = 0.88, sd = 0.07,
# Initial reward is 100 at every planet
# Experiment lasts 15 minutes without instructions
# travel time is 9 seconds
# harvest time is 2.5  seconds
len_exp = 15*60 # in seconds, 15 minutes
decay_rate_mu = 0.88
initial_reward = 100
travel_time = 9
harvest_time = 2

V_leave = initial_reward/travel_time # always stays the same
V_stay = initial_reward/harvest_time # to begin
rewards = [initial_reward]
PRT = 1

while V_stay >= V_leave:
    PRT += 1
    reward = rewards[-1]*0.88
    rewards.append(reward)
    V_stay = reward/harvest_time

print("This is the optimal PRT on average: " + str(PRT))
print("This is the last reward received if left at optimal PRT: " + str(rewards[-1]))

# How many planets would you visit if you left at the optimal time on average?
one_trial_time = PRT*harvest_time + travel_time
num_planets_visit = math.ceil(len_exp/one_trial_time)
print("This is the optimal num planets to visit: " + str(num_planets_visit))

# Based on the number of planets we would expect to visit and how much reward they would receive
# Calculate bonus
opt_space_treasure = sum(rewards)*num_planets_visit
print("This is the amount of space treasure expect to collect using MVT optimal strategy: " + str(opt_space_treasure))


# Let's now calculate the lower bound for rewards
rewards = [initial_reward]
PRT = 1
while reward > 1:
    PRT += 1
    reward = rewards[-1]*0.88
    rewards.append(reward)
    V_stay = reward/harvest_time

print("This is the PRT on average if exhausted patches: " + str(PRT))
one_trial_time = PRT*harvest_time + travel_time
num_planets_visit = math.ceil(len_exp/one_trial_time)
print("This is the num planets visited if exhausted ever : " + str(num_planets_visit))

exhaust_space_treasure = sum(rewards)*num_planets_visit
print("This is the amount of space treasure expect to collect using exhaustion strategy: " + str(exhaust_space_treasure))
