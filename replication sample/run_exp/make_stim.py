from PIL import Image, ImageFont, ImageDraw
import numpy as np
import math


def resize_img(img,basewidth):
    """ This function resizes this image to a width specified
        and height proportional to new width
        https://stackoverflow.com/questions/273946/how-do-i-resize-an-image-using-pil-and-maintain-its-aspect-ratio"""
    wpercent = (basewidth/float(img.size[0]))
    hsize = int((float(img.size[1])*float(wpercent)))
    img = img.resize((basewidth,hsize), Image.ANTIALIAS)
    return img

def place_gem(num_gems,x_1,y_1,width,height,max_col_len,gem_im,folder,padding=0):
    back_im = Image.open('static/images/task_images/land.png')
    gem_w, gem_h = gem_im.size # 254,337
    # split num_gems into integer and decimal
    split = math.modf(num_gems)
    integer = int(split[1])
    dec = round(split[0],1)

    for i in range(integer):
        x_pos = int(x_1+(gem_w+padding)*(i%max_col_len))
        y_pos = int(y_1+(gem_h*math.floor((i/max_col_len))))
        back_im.paste(gem_im, (x_pos,y_pos),mask=gem_im)

    crop_gem = gem_im.crop((0,0,int(gem_w*dec),gem_h))

    x_pos = int(x_1+(gem_w+padding)*(integer%max_col_len))
    y_pos = int(y_1+(gem_h*(integer>=max_col_len)))

    back_im.paste(crop_gem, (x_pos,y_pos),mask=crop_gem)

    # now write text to image
    draw = ImageDraw.Draw(back_im)
    font = ImageFont.truetype("/Library/Fonts/Arial.ttf", 300)
    draw.text((width/4 + 100,height/4),"You mined " + str(integer) + " gems!",font=font)
    draw.text((width/4 + 100+ 300,height/4 + 300), str(integer*num_cents_gem) + " cents",font=font)

    #back_im.save('img_foraging/'+folder+'/'+str(integer)+'_'+str(dec)+'.png')
    back_im = back_im.convert('RGB')
    back_im.save('static/images/task_images/'+folder+'/'+str(integer)+'.png')
    return

def place_pile_of_gems(num_gems,gem_img,width,height,folder,padding=0):
    back_im = Image.open('static/images/task_images/land.png')

    x_pos = 2500
    y_pos = 1900

    back_im.paste(gem_img, (x_pos,y_pos),mask=gem_img)

    # now write text to image
    draw = ImageDraw.Draw(back_im)
    font = ImageFont.truetype("/Library/Fonts/Arial.ttf", 300)
    draw.text((width/4 + 100,height/4),"You mined " + str(num_gems) + " gems!",font=font)
    draw.text((width/4 + 750,height/4 + 300), '%.3f' % (num_gems*num_cents_gem) + " cents",font=font)

    #back_im.save('img_foraging/'+folder+'/'+str(integer)+'_'+str(dec)+'.png')
    back_im = back_im.convert('RGB')
    back_im.save('static/images/task_images/'+folder+'/'+str(num_gems)+'.png')
    return

def get_gem_img(gem_amount):
    if  1 <= gem_amount < 6:
        gem_img = Image.open('static/images/task_images/gems/piles_of_gems-11.png')
    elif 6 <= gem_amount < 12:
        gem_img = Image.open('static/images/task_images/gems/piles_of_gems-10.png')
    elif 12 <= gem_amount < 24:
        gem_img = Image.open('static/images/task_images/gems/piles_of_gems-09.png')
    elif 24<=gem_amount<36:
        gem_img = Image.open('static/images/task_images/gems/piles_of_gems-08.png')
    elif 36<=gem_amount<48:
        gem_img = Image.open('static/images/task_images/gems/piles_of_gems-07.png')
    elif 48<=gem_amount<60:
        gem_img = Image.open('static/images/task_images/gems/piles_of_gems-06.png')
    elif 60<=gem_amount<72:
        gem_img = Image.open('static/images/task_images/gems/piles_of_gems-05.png')
    elif 72<=gem_amount<84:
        gem_img = Image.open('static/images/task_images/gems/piles_of_gems-04.png')
    elif 84<=gem_amount<96:
        gem_img = Image.open('static/images/task_images/gems/piles_of_gems-03.png')
    elif 96<=gem_amount<108:
        gem_img = Image.open('static/images/task_images/gems/piles_of_gems-02.png')
    elif gem_amount >= 108:
        gem_img = Image.open('static/images/task_images/gems/piles_of_gems-01.png')
    else:
        gem_img = Image.open('static/images/task_images/gems/empty.png')
    return gem_img

def get_alien_img(alien_num):
    if alien_num < 10:
        alien_img = Image.open('../../alien_images/alien-0'+str(alien_num)+'.png')
    else:
        alien_img = Image.open('../../alien_images/alien-'+str(alien_num)+'.png')
    return alien_img

def make_harvest_img(lower_bound,upper_bound):
    for i in range(lower_bound,upper_bound):
        #place_gem(num_gems[i], x_1, y_1, width, height,max_col_len,gem_im,'gems')
        #place_gem(num_gems[i],x_1,y_1,width,height,pink_gem_im,'pink_gems',padding=50)
        gem_img = get_gem_img(i)
        place_pile_of_gems(i,gem_img,width,height,'gems',padding=0)
    return

def make_space_barrel_img():
    barrel_im = Image.open('static/images/task_images/barrel.png')
    draw = ImageDraw.Draw(barrel_im)
    font = ImageFont.truetype("/Library/Fonts/Arial.ttf", 300)
    draw.text((width/4 - 300,height/4),"You found space treasure!",font=font)
    draw.text((width/4 + 750,height/4 + 300), '%.3f' % 0 + " cents",font=font)
    barrel_im.save('static/images/task_images/barrel_text.png')
    return

def make_catch_trial(back_im):
    draw = ImageDraw.Draw(back_im)
    font = ImageFont.truetype("/Library/Fonts/Arial.ttf", 200)
    draw.text((width/4-500,height/4),"Please press the letter Z on your keyboard",font=font)
    back_im.save('../../experiment1b/run_exp/static/images/task_images/catch.png')
    return

def make_alien_img(back_im,alien_num,width,height):
    alien_im = get_alien_img(alien_num)
    alien_im = resize_img(alien_im,2200)
    back_im.paste(alien_im, (3400,1800),mask=alien_im)
    font = ImageFont.truetype("/Library/Fonts/Arial.ttf", 300)
    draw = ImageDraw.Draw(back_im)
    draw.text((width/4 - 100,height/4),"Welcome to my planet!",font=font)
    back_im.save('../../alien_images/alien_planet-' + str(alien_num) +'.png')
    return

def make_alien_img_bye(back_im,alien_num,width,height):
    alien_im = get_alien_img(alien_num)
    alien_im = resize_img(alien_im,2200)
    back_im.paste(alien_im, (3400,1800),mask=alien_im)
    font = ImageFont.truetype("/Library/Fonts/Arial.ttf", 300)
    draw = ImageDraw.Draw(back_im)
    draw.text((width/4 + 300,height/4),"Thanks for visiting!",font=font)
    back_im.save('../../alien_images/pngs/alien_planet_bye-' + str(alien_num) +'.png')
    return

def make_alien_welcome():
    for i in range(64,125):
        back_im = Image.open('../../alien_images/lone_planet.png')
        width, height = back_im.size
        make_alien_img(back_im,i,width,height)
    return

def make_alien_goodbye():
    for i in range(58,65):
        back_im = Image.open('../../alien_images/old_old_aliens/lone_planet.png')
        width, height = back_im.size
        make_alien_img_bye(back_im,i,width,height)
    return

def make_planet_alien_icon(planet_im,alien_num,width,height):
    alien_im = get_alien_img(alien_num)
    alien_im = resize_img(alien_im,1500)
    planet_im.paste(alien_im, (int(width/5),int(height/20)),mask=alien_im)
    planet_im.save('../../alien_images/icon_alien_planet-' + str(alien_num) +'.png')
    return


#back_im = Image.open('static/images/task_images/land.png') # background image, astronaut with shovel
#back_im = Image.open('static/images/task_images/pngs/land.png')
#planet_im = Image.open('../../alien_images/mars 5-03.png')
#width, height = back_im.size

#make_catch_trial(back_im)
make_alien_welcome()
