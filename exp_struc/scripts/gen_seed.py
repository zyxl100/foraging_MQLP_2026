import random
import os

def main():
    rand_num=random.choices(range(8),k=9)
    rand_string=sum([rand_num[i]*(10**(8-i)) for i in range(9)])
    print(rand_string)
    os.system("python3 generate_mdp.py " + str(rand_string))
    os.system("python3 make_blocks.py " + str(rand_string))
    os.system("python3 eval_mdp.py " + str(rand_string))

if __name__ == "__main__":
    main()
