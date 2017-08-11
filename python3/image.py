import os
import libtcodpy as libtcod


def count_img(path):

    img_count = 0

    if not os.path.exists(path):
        img_count = 0
    else:
        for f in os.listdir(path):
            if os.path.isfile(os.path.join(path, f)):
                img_count += 1

    return img_count


def take_screenshot(f_path, img_path, rn_path, tmp_path):

    img_count = count_img(f_path)

    new_ss = libtcod.image_from_console(0)

    if not os.path.exists(f_path):
        os.makedirs(f_path)

    if os.path.exists(img_path):
        libtcod.image_save(new_ss, tmp_path)
        os.rename(tmp_path, rn_path % img_count)
    else:
        libtcod.image_save(new_ss, img_path)

    if os.path.exists(tmp_path):
        os.remove(tmp_path)
