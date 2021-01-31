image_magick_convert = r"C:\Program Files\ImageMagick-7.0.10-Q16-HDRI\convert.exe"
import os
import subprocess

IMAGEMAGICK_ROOT = r"C:\Program Files\ImageMagick-7.0.10-Q16-HDRI"
IMAGEMAGICK_CONVERT = os.path.join( IMAGEMAGICK_ROOT, 'convert.exe')  # Path to ImageMagick convert.exe


def combine_rgba_channels(r_channel_tif_path='', g_channel_tif_path='', b_channel_tif_path='', a_channel_tif_path='',
                          dest_path='', ):
    '''
    combines 3 single-channel images into an RGB tif.
    returns the path to the finished image.
    '''
    if r_channel_tif_path == '':
        r_channel_tif_path = '-size 64x64 canvas: black'
    if g_channel_tif_path == '':
        g_channel_tif_path = '-size 64x64 canvas: black'
    if b_channel_tif_path == '':
        b_channel_tif_path = '-size 64x64 canvas: black'

    # combines three images that are each 1 color channel
    combine_channels_str = '{Image_Magick_Root} {r_channel_tif} {g_channel_tif} {b_channel_tif} -combine -set colorspace sRGB {dest_path}'.format(
        Image_Magick_Root=IMAGEMAGICK_CONVERT,
        r_channel_tif=r_channel_tif_path,
        g_channel_tif=g_channel_tif_path,
        b_channel_tif=b_channel_tif_path,
        dest_path=dest_path
    )
    create_alpha_str = '{Image_Magick_Root} {dest_path} -alpha on {dest_path}'.format(
        Image_Magick_Root=IMAGEMAGICK_CONVERT,
        dest_path=dest_path
    )

    p = subprocess.Popen(combine_channels_str, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.wait()

    if len(a_channel_tif_path):
        add_opacity_str = '{Image_Magick_Root} {rgb_packed_image} {alpha_grayscale_image} -alpha off -compose CopyOpacity -composite {dest_path}'.format(
            Image_Magick_Root=IMAGEMAGICK_CONVERT,
            rgb_packed_image=dest_path,
            alpha_grayscale_image=a_channel_tif_path,
            dest_path=dest_path
        )
        p = subprocess.Popen(add_opacity_str, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.wait()

    return dest_path


def split_image_channels(source_tif, r=False, g=False, b=False, a=False):
    '''
    get a r, g, b channel from the input tif and save each one as a tif in the same dir.
    Returns the filepaths to the new images in a dict with a key for any arg set to True
    '''
    root, file_name = os.path.split(source_tif)
    file_name, _ = os.path.splitext(file_name)
    output_results = {}
    if r or g or b or a:
        os.chdir(IMAGEMAGICK_ROOT)
    if r:
        r_dest = os.path.join(root, file_name + '_r.tif')
        # saves out an image of just 1 channel from an image.
        r_channel = '{Image_Magick_Root} {source} -channel {channel_var} -separate {dest}'.format(
            Image_Magick_Root=IMAGEMAGICK_CONVERT,
            source=source_tif,
            channel_var='r',
            dest=r_dest)
        p = subprocess.Popen(r_channel, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.wait()
        output_results['r'] = r_dest

    if g:
        g_dest = os.path.join(root, file_name + '_g.tif')
        g_channel = '{Image_Magick_Root} {source} -channel {channel_var} -separate {dest}'.format(
            Image_Magick_Root=IMAGEMAGICK_CONVERT,
            source=source_tif,
            channel_var='G',
            dest=g_dest)

        p = subprocess.Popen(g_channel, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.wait()
        output_results['g'] = g_dest

    if b:
        b_dest = os.path.join(root, file_name + '_b.tif')
        b_channel = '{Image_Magick_Root} {source} -channel {channel_var} -separate {dest}'.format(
            Image_Magick_Root=IMAGEMAGICK_CONVERT,
            source=source_tif,
            channel_var='B',
            dest=b_dest)

        p = subprocess.Popen(b_channel, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.wait()
        output_results['b'] = b_dest

    if a:
        a_dest = os.path.join(root, file_name + '_a.tif')
        a_channel = '{Image_Magick_Root} {source} -channel {channel_var} -separate {dest}'.format(
            Image_Magick_Root=IMAGEMAGICK_CONVERT,
            source=source_tif,
            channel_var='A',
            dest=a_dest)

        p = subprocess.Popen(a_channel, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.wait()
        output_results['a'] = a_dest

    return output_results


def repack_textures(source_tifs=[], channel_maps=[], dest_tif=''):
    '''
    Puts the specified channels (up to 4) for each source image (up to 4 individual images, 1 channel from each)
    into the specified channel for a single final output .tif

    source_tifs[list]: a list of filepaths to tifs which have at least 1 channel you want to re-pack
    channel_maps[list]: a list of dicts where each dict represents 1 source_tif, and each key:value pair is source_channel:dest_channel
    '''
    # ensure input data is proper format.
    if len(source_tifs) != len(channel_maps):
        raise ValueError("The length of source_tifs does not match the length of channel_maps.")
    dest_channel_occupancy = [0, 0, 0, 0]
    for mapping in channel_maps:
        for key, value in mapping.items():
            if not key in ['r', 'g', 'b', 'a']:
                raise ValueError(
                    "the input channel of {} does not exist. Please only use 'r', 'g', 'b', 'a'".format(key))
            if value == 'r':
                dest_channel_occupancy[0] += 1
            elif value == 'g':
                dest_channel_occupancy[1] += 1
            elif value == 'b':
                dest_channel_occupancy[2] += 1
            elif value == 'a':
                dest_channel_occupancy[3] += 1
            else:
                raise ValueError(
                    "the output channel of {} does not exist. Please only use 'r', 'g', 'b', 'a'".format(value))

    if all(i > 1 for i in dest_channel_occupancy):
        raise ValueError(
            "multiple input channels are mapped to the same output channel. Ensure only 1 input channel is assigned to each output channel.")
    for image in source_tifs:
        if not os.path.exists(image):
            raise ValueError("This image_path does not exist: {}".format(image))

    else:
        # repack maps
        red_channel_tif = ''
        green_channel_tif = ''
        blue_channel_tif = ''
        alpha_channel_tif = ''
        temp_files = []
        for index, source_tif in enumerate(source_tifs):
            channel_map = channel_maps[index]  # dict of input_channel:output_channel
            desired_maps = [key for key in channel_map.keys()]  # get list of just the desired maps from this texture.
            r = 'r' in desired_maps
            g = 'g' in desired_maps
            b = 'b' in desired_maps
            a = 'a' in desired_maps
            print("Channels to Pull: r={1}")
            # split this image and only return the channels needed.
            channels_needed_from_tif = split_image_channels(source_tif, r=r, g=g, b=b, a=a)
            for key, value in channels_needed_from_tif.items():
                temp_files.append(value)
            # assign each separated channel to it's dest channel.
            for input_channel_needed, output_channel in channel_map.items():  #
                if output_channel == 'r':
                    red_channel_tif = channels_needed_from_tif[input_channel_needed]
                elif output_channel == 'g':
                    green_channel_tif = channels_needed_from_tif[input_channel_needed]
                elif output_channel == 'b':
                    blue_channel_tif = channels_needed_from_tif[input_channel_needed]
                elif output_channel == 'a':
                    alpha_channel_tif = channels_needed_from_tif[input_channel_needed]

        # when finished with all input images, use the new mappings to create a new image.
        combine_rgba_channels(r_channel_tif_path=red_channel_tif,
                              g_channel_tif_path=green_channel_tif,
                              b_channel_tif_path=blue_channel_tif,
                              a_channel_tif_path=alpha_channel_tif,
                              dest_path=dest_tif
                              )

        # delete the temp files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    return dest_tif

if __name__ == '__main__':
    # example Usage
    source_tifs = [r"C:\Users\zoeys\Downloads\mask_test_bitmap.tif", r"C:\Users\zoeys\Downloads\test_image_2.tif" ]
    channel_maps = [
        {'r':'b', 'a':'g'}, # the r channel of image 1 goes to the b channel, and the a channel goes to g
        {'g':'a', 'b':'r'}
    ]
    dest_tif = r"C:\Users\zoeys\Downloads\result.tif"
    repack_textures(source_tifs, channel_maps, dest_tif)
