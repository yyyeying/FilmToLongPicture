# Film To Long Picture
# by YYYeYing
# weibo: @夜莺夜影XWB
# twitter: 高坂琉璃 @Kousaka_Rurii

import ffmpy3
import os
import sys
import gc
from PIL import Image
from PIL import ImageFilter
import numpy as np


def KeyFrame(path, dest_path):
    # Get key frames of the film, using FFMPEG.
    # path: Path of the video
    # dest_path: The directory where you want to save the key frames.
    dest_path += '%04d.jpg'
    video = ffmpy3.FFmpeg(executable="ffmpeg.exe",
                          inputs={path: '-hwaccel dxva2'},
                          outputs={dest_path: '-vf select=\'eq(pict_type\,I)\' -vsync 2 -b:v 5M -s 1920*1080 -f image2'}
                          )
    print(video.cmd)
    video.run()
    return


def FrameConnection(source_path, dest_path, dest_name='num', split=100, width=5000, mode="col"):
    # connect the key frames to a long picture.
    # source_path: the directory of key frames.
    # dest_path: the directory of the long picture.
    # dest_name: the name of the long picture, an optional argument in main program.
    # spilt: frames per picture, an optional argument in main program.
    # width: the width of the long picture, an optional argument in main program.
    # mode: the treatment of frames.
    modes = {'norm': MedianFilter, 'row': PicAvgRow, 'col': PicAvgCol, 'max': PicMaxColor, 'non': DoNothing}
    # the options in argument [mode]: 'norm', 'row', 'col', 'max', 'non'
    images = []
    for root, dirs, files in os.walk(source_path):
        for f in sorted(files):
            images.append(f)
    pic_num = len(images)
    print("There are "+str(pic_num)+" images.")
    example = Image.open(source_path + '\\' + images[0])

    # unit_width = example.size[0]
    unit_width = int(width / split)
    target_height = example.size[1]
    target_width = split * unit_width
    seg_num = int(pic_num / split)
    print("Frames will be connect into "+str(seg_num)+" segments.")
    print("Target Segment Size: " + str(target_width) + " × " + str(target_height)+'\n')
    quality_value = 100
    for i in range(seg_num):
        new_left = 0
        print('connecting segment ' + str(i+1) + ' of ' + str(seg_num) + '...')
        target = Image.new(mode=example.mode, size=(target_width, target_height))
        for j in range(0, split):
            print("Segment "+str(i+1)+" of "+str(seg_num)+", Picture "+str(j+1)+" of "+str(split))
            # print(str('%.2f' % (((i*split + j) / pic_num)*100)) + ' % ...')
            this_image = Image.open(source_path + '\\' + images[i * split + j])
            # this_image = modes.get(mode)(this_image)
            re_image = this_image.resize((unit_width, target_height), Image.ANTIALIAS)
            re_image = modes.get(mode)(re_image)
            target.paste(re_image, (new_left, 0))  # paste resized-image into target
            new_left += unit_width
            del this_image
            del re_image
            gc.collect()
        target = target.filter(ImageFilter.GaussianBlur(1))
        # target = target.filter(ImageFilter.SMOOTH_MORE)
        target = MedianFilter(target)
        if dest_name == 'num':
            target.save(dest_path + str('%04d' % i) + '.jpg', quality=quality_value)
        else:
            target.save(dest_path + dest_name + '.jpg', quality=quality_value)
        del target
        gc.collect()
    print("picture connected.")
    return seg_num


def PicMaxColor(image):
    # if you choose 'max' in the argument [mode]
    # set the picture to the most frequent color.
    image = image.convert('RGB')
    colors = image.getcolors(image.size[0]*image.size[1])
    max_color = 0
    max_color_t = 0
    for i in range(len(colors)):
        if colors[i][0] > max_color_t:
            max_color_t = colors[i][0]
            max_color = colors[i][1]
    target = Image.new(mode="RGB", size=image.size, color=max_color)
    return target


def PicAvgRow(image):
    # if you choose 'row' in the argument [mode]
    # set every row to the mean color of this row.
    image = image.convert('RGB')
    width = image.size[0]
    height = image.size[1]
    color = np.array(image)
    # print(color.flags)
    color.setflags(write=True)
    for i in range(height):
        r = color[i, :, 0]
        g = color[i, :, 1]
        b = color[i, :, 2]
        avg_r = [int(np.mean(r))]*width
        avg_g = [int(np.mean(g))]*width
        avg_b = [int(np.mean(b))]*width
        color[i, :, 0] = avg_r
        color[i, :, 1] = avg_g
        color[i, :, 2] = avg_b
    result = Image.fromarray(color)
    return result


def PicAvgCol(image):
    # if you choose 'col' in the argument [mode]
    # set every column to the mean color of this column.
    image = image.convert('RGB')
    width = image.size[0]
    height = image.size[1]
    color = np.asarray(image)
    color.flags.writeable = True
    # print(color[:, 0, 0])
    for j in range(width):
        r = color[:, j, 0]
        g = color[:, j, 1]
        b = color[:, j, 2]
        avg_r = [int(np.mean(r))]*height
        avg_g = [int(np.mean(g))]*height
        avg_b = [int(np.mean(b))]*height
        color[:, j, 0] = avg_r
        color[:, j, 1] = avg_g
        color[:, j, 2] = avg_b
    result = Image.fromarray(color)
    return result


def MedianFilter(image):
    # if you choose 'norm' in the argument [mode]
    # use a median filter on the image.
    image = image.filter(ImageFilter.MedianFilter(5))
    return image


def DoNothing(image):
    # if you choose 'non' in the argument [mode]
    # do nothing with the picture.
    return image


if __name__ == "__main__":
    sys_path = sys.path[0]
    key_frame_path = sys_path + '/KeyFrames/'
    key_frame_path = key_frame_path.replace('\\', '/')
    myVideo = KeyFrame("test.mkv", key_frame_path)
    # get key frames
    print("Key frames selected and saved in " + str(key_frame_path))
    connection_path = sys_path + '\\connection\\'
    con_num = FrameConnection(source_path=key_frame_path, dest_path=connection_path, mode="row")
    # connect key frames to many segments, 100 frames in each segment.
    # Why not connect all the key frames in once? Due to the limitation of width in JPEG.
    # con_num = FrameConnection(source_path=key_frame_path, dest_path=connection_path, mode="col")
    result_path = sys_path + '\\result\\'
    FrameConnection(source_path=connection_path, dest_path=result_path, split=con_num, mode="norm",
                    dest_name="Your Name")
    # connect the segments to a complete picture.
    print("Result picture is in " + result_path)
