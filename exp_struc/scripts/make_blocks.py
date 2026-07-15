import scipy.stats as stats
import numpy as np
import random
import pickle
import sys

def load_mdp(seed):
    file = open('../pickled_exp_parms/mdps/80_10_10/'+str(seed)+'.pkl','rb')
    data= pickle.load(file)
    all_change_points = data[0]
    all_n_cp = data[1]
    all_next_galaxy = data[2]
    all_counter = data[3]
    file.close()
    return all_change_points, all_n_cp, all_next_galaxy, all_counter

def flatten_list(list):
    new_list = [item for sublist in list for item in sublist]
    return new_list


def sample_init_reward():
    return stats.norm.rvs(loc=100,scale=5,size=1).tolist()[0]

def sample_decay_rate(galaxy):
    if galaxy == 0:
        #decay = np.clip(stats.norm.rvs(loc=0.2,scale=0.05,size=45),0,1).tolist
        #decay = np.clip(stats.beta.rvs(a=29,b=7,size=45),0,1).tolist()
        decay = np.clip(stats.beta.rvs(a=13,b=51,size=45),0,1).tolist()
    elif galaxy == 1:
        #decay = np.clip(stats.norm.rvs(loc=0.5,scale=0.05,size=45),0,1).tolist()
        decay = np.clip(stats.beta.rvs(a=50,b=50,size=45),0,1).tolist()
    elif galaxy == 2:
        #decay = np.clip(stats.norm.rvs(loc=0.8,scale=0.05,size=45),0,1).tolist()
        #decay = np.clip(stats.beta.rvs(a=7.4,b=29,size=45),0,1).tolist()
        decay = np.clip(stats.beta.rvs(a=50,b=12,size=45),0,1).tolist()
    return decay

def galaxy_switch(current_galaxy,next_transition):
    if current_galaxy == 0:
        if next_transition == 0:
            next_galaxy = 1
        else:
            next_galaxy = 2
    elif current_galaxy == 1:
        if next_transition == 0:
            next_galaxy = 0
        else:
            next_galaxy = 2
    elif current_galaxy == 2:
        if next_transition == 0:
            next_galaxy = 0
        else:
            next_galaxy = 1
    return next_galaxy

def make_galaxy_structure(begin_galaxy,transition_stucture):
    block =[begin_galaxy]
    curr_gal = begin_galaxy
    for i in range(len(transition_stucture)):
        next_galaxy = galaxy_switch(curr_gal,transition_stucture[i])
        block.append(next_galaxy)
        curr_gal = next_galaxy
    return block


def make_block(block,block_num,counter):
    block_struc = []
    block_init_r = []
    block_decay = []
    if block_num == 1:
        cp = counter[0] # change points
    elif block_num == 2:
        cp = counter[1]
    elif block_num == 3:
        cp = counter[2]
    elif block_num == 4:
        cp = counter[3]
    elif block_num == 5:
        cp = counter[4]

    for galaxy in range(len(cp)):
        print('galaxy: ' + str(galaxy))
        curr_galaxy_type = block[galaxy]
        curr_galaxy = [curr_galaxy_type]*cp[galaxy]
        block_struc.append(curr_galaxy)
        for planet in range(cp[galaxy]):
            block_init_r.append(sample_init_reward())
            block_decay.append(sample_decay_rate(curr_galaxy_type))
    return block_struc, block_init_r, block_decay

def get_early_blocks(condition,transition_structure):
    if condition == 'poor_graded':
        #block_1 = make_galaxy_structure(0,transition_structure[0])
        #block_2 = make_galaxy_structure(0,transition_structure[1])
        block_1 = [0,1,2,1,0,1,0,2,1,2,0,1,2,1]
        block_2 = [0,1,2,0,1,2,0,1,2,1,2,1,0,1]
    elif condition == 'poor_extreme':
        #block_1 = make_galaxy_structure(0,transition_structure[0])
        #block_2 = make_galaxy_structure(0,transition_structure[1])
        block_1 = [0,2,0,1,0,2,0,1,2,0,1,2,0,1]
        block_2 = [0,2,0,1,0,2,1,0,2,1,0,2,0,1]
    elif condition == 'rich_graded':
        #block_1 = make_galaxy_structure(2,transition_structure[0])
        #block_2 = make_galaxy_structure(2,transition_structure[1])
        block_1 = [2,1,0,1,2,1,2,0,1,0,2,1,0,1]
        block_2 = [2,1,0,2,1,0,2,1,2,1,0,1,2,1]
    elif condition == 'rich_extreme':
        #block_1 = make_galaxy_structure(2,transition_structure[0])
        #block_2 = make_galaxy_structure(2,transition_structure[1])
        block_1 = [2,0,2,1,2,0,2,1,0,2,1,0,2,1]
        block_2 = [2,0,2,1,2,0,1,2,0,1,2,0,2,1]
    return block_1, block_2

def get_late_blocks(transition_structure):
    #block_3 = [2,1,0,2,1,0,1,2,0,2,1,2,0,1] # 13
    #block_4 = [2,0,2,1,0,1,2,1,0,2,0,1,2] # 12
    #block_5 = [2,1,0,2,1,0,1,2] # 7

    #block_3 = [2,1,2,0,1,2,1,0,2,0,1,2,1,0] # 13
    #block_4 = [0,2,1,0,1,0,2,1,0,2,0,1,0] #12
    #block_5 = [2,1,2,0,1,2,1,0,2,0,1,2,1,0] #7
    if len(transition_structure[2]) > len(transition_structure[4]):
        large_struc = transition_structure[2]
    else:
        large_struc = transition_structure[4]
    block_3 = make_galaxy_structure(1,large_struc)
    block_4 = make_galaxy_structure(0,transition_structure[3])
    block_5 = make_galaxy_structure(1,large_struc)
    return block_3, block_4, block_5

def make_late_blocks(transition_structure,counter):
    late_blocks = get_late_blocks(transition_structure)
    exp_struc = []
    all_r_0 = []
    all_decay = []
    for block in range(3):
        block_struc, block_init_r, block_decay = make_block(late_blocks[block],block+3,counter)

        exp_struc.append(block_struc)
        all_r_0.append(block_init_r)
        all_decay.append(block_decay)
    lb={}
    lb['exp_struc'] = exp_struc
    lb['r0'] = all_r_0
    lb['k'] = all_decay
    return lb


def get_blocks_old(transition_structure):
    galaxy = random.choices(range(3),k=5)
    if len(transition_structure[2]) > len(transition_structure[4]):
        large_struc = transition_structure[2]
    else:
        large_struc = transition_structure[4]

    block_1 = make_galaxy_structure(galaxy[0],transition_structure[0])
    block_2 = make_galaxy_structure(galaxy[1],transition_structure[1])
    block_3 = make_galaxy_structure(galaxy[2],large_struc)
    block_4 = make_galaxy_structure(galaxy[3],transition_structure[3])
    block_5 = make_galaxy_structure(galaxy[2],large_struc)

    return block_1, block_2, block_3, block_4, block_5


def get_blocks(transition_structure):
    galaxy = [0,0,1,0,1]
    if len(transition_structure[2]) > len(transition_structure[4]):
        large_struc = transition_structure[2]
    else:
        large_struc = transition_structure[4]

    block_1 = make_galaxy_structure(galaxy[0],transition_structure[0])
    block_2 = make_galaxy_structure(galaxy[1],transition_structure[1])
    block_3 = make_galaxy_structure(galaxy[2],large_struc)
    block_4 = make_galaxy_structure(galaxy[3],transition_structure[3])
    block_5 = make_galaxy_structure(galaxy[2],large_struc)

    return block_1, block_2, block_3, block_4, block_5


def make_blocks(transition_structure,counter):
    blocks = get_blocks(transition_structure)
    exp_struc = []
    all_r_0 = []
    all_decay = []
    for block in range(5):
        block_struc, block_init_r, block_decay = make_block(blocks[block],block+1,counter)

        exp_struc.append(block_struc)
        all_r_0.append(block_init_r)
        all_decay.append(block_decay)
    b={}
    b['exp_struc'] = exp_struc
    b['r0'] = all_r_0
    b['k'] = all_decay

    return b

def make_exp_old(condition,late_blocks,transition_structure,counter):
    all_blocks = get_early_blocks(condition,transition_structure)
    exp_struc = []
    all_r_0 = []
    all_decay = []
    for block in range(2):
        block_struc, block_init_r, block_decay = make_block(all_blocks[block],block+1,counter)

        exp_struc.append(block_struc)
        all_r_0.append(block_init_r)
        all_decay.append(block_decay)
    for block in range(3):
        exp_struc.append(late_blocks['exp_struc'][block])
        all_r_0.append(late_blocks['r0'][block])
        all_decay.append(late_blocks['k'][block])

    return exp_struc, all_r_0, all_decay

def make_exp(transition_structure,counter):
    all_blocks = make_blocks(transition_structure,counter)
    exp_struc = []
    all_r_0 = []
    all_decay = []
    for block in range(5):
        exp_struc.append(all_blocks['exp_struc'][block])
        all_r_0.append(all_blocks['r0'][block])
        all_decay.append(all_blocks['k'][block])

    return exp_struc, all_r_0, all_decay

def pickle_data_old(seed,condition,exp_struc,all_r_0,all_decay):
    with open('../pickled_exp_parms/condition_'+condition+'_'+str(seed)+'.pkl', 'wb') as f_out:
         pickle.dump([exp_struc,all_r_0,all_decay],f_out)
    return

def write_to_js_old(seed,condition,exp_struc,all_r_0,all_decay):
    f = open( '../js_files/condition_'+condition+'_'+str(seed)+'.js', 'w' )
    f.write( 'var ' +condition +'_r_0 = ' + repr(all_r_0) + ';\n' + 'var '+condition +'_decay = ' +  repr(all_decay) + '\n')
    f.close()
    return

def pickle_data(seed,exp_struc,all_r_0,all_decay):
    with open('../pickled_exp_parms/blocks/'+str(seed)+'_best.pkl', 'wb') as f_out:
         pickle.dump([exp_struc,all_r_0,all_decay],f_out)
    return

def write_to_js(seed,exp_struc,all_r_0,all_decay):
    flat_exp_struc = [flatten_list(exp_struc[i]) for i in range(5)]
    f = open( '../js_files/'+str(seed)+'_best.js', 'w' )
    f.write( 'var r_0 = ' + repr(all_r_0) + ';\n' + 'var decay = ' +  repr(all_decay) + ';\n' + 'var struc = ' +  repr(flat_exp_struc)+ '\n')
    f.close()
    return


def save_to_files(seed,exp_struc,all_r_0,all_decay):
    pickle_data(seed,exp_struc,all_r_0,all_decay)
    write_to_js(seed,exp_struc,all_r_0,all_decay)
    return

def save_to_files_old(seed,exp_struc,all_r_0,all_decay):
    pickle_data(seed,condition,exp_struc,all_r_0,all_decay)
    write_to_js(seed,condition,exp_struc,all_r_0,all_decay)
    return

def main_old():
    seed = int(sys.argv[1])
    np.random.seed(seed=seed)
    __, __, transition_structure, counter = load_mdp(seed)
    late_blocks = make_late_blocks(transition_structure,counter)
    all_conditions = ['poor_graded','poor_extreme','rich_graded','rich_extreme']
    for condition in all_conditions:
        exp_struc, all_r_0, all_decay = make_exp(condition,late_blocks,transition_structure,counter)
        save_to_files(seed,condition,exp_struc,all_r_0,all_decay)

def main():
    seed = int(sys.argv[1])
    np.random.seed(seed=seed)
    __, __, transition_structure, counter = load_mdp(seed)
    exp_struc, all_r_0, all_decay = make_exp(transition_structure,counter)
    save_to_files(seed,exp_struc,all_r_0,all_decay)


if __name__ == "__main__":
    main()
