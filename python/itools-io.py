#!/usr/bin/env python3

"""itools-io.py module description.

Generic I/O functions.
"""


import cv2
import os.path
import importlib

itools_common = importlib.import_module("itools-common")
itools_exiftool = importlib.import_module("itools-exiftool")
itools_heif = importlib.import_module("itools-heif")
itools_rgb = importlib.import_module("itools-rgb")
itools_y4m = importlib.import_module("itools-y4m")
itools_yuv = importlib.import_module("itools-yuv")


def read_image_file(
    infile,
    config_dict,
    flags=None,
    return_type=itools_common.ProcColor.bgr,
    iinfo=None,
    debug=0,
):
    outyvu = None
    outbgr = None
    status = {}
    if os.path.splitext(infile)[1] == ".y4m":
        outyvu, _, _, status = itools_y4m.read_y4m(
            infile, colorrange="full", debug=debug
        )
        if status is not None and status.get("broken", False):
            print(f"error: file {infile} is broken")

    elif os.path.splitext(infile)[1] in (".yuv", ".YUV420NV12"):
        outyvu = itools_yuv.read_yuv(infile, iinfo)

    elif os.path.splitext(infile)[1] == ".rgba":
        outbgr = itools_rgb.read_rgba(infile, iinfo)

    elif os.path.splitext(infile)[1] in (".heic", ".avif", ".hif"):
        outyvu, status = itools_heif.read_heif(infile, config_dict, debug)

    else:
        outbgr = cv2.imread(cv2.samples.findFile(infile, flags))
        # use exiftool to get the metadata
        status = itools_exiftool.get_exiftool(
            infile, short=True, config_dict=config_dict, debug=debug
        )

    read_image_components = config_dict.get("read_image_components")
    if return_type == itools_common.ProcColor.yvu:
        if outyvu is None and read_image_components:
            outyvu = cv2.cvtColor(outbgr, cv2.COLOR_BGR2YCrCb)
            return outyvu, status
        else:
            return outyvu, status

    elif return_type == itools_common.ProcColor.bgr:
        if outbgr is None and read_image_components:
            outbgr = cv2.cvtColor(outyvu, cv2.COLOR_YCrCb2BGR)
            return outbgr, status
        else:
            return outbgr, status

    else:  # if return_type == itools_common.ProcColor.both:
        if outyvu is None and read_image_components:
            outyvu = cv2.cvtColor(outbgr, cv2.COLOR_BGR2YCrCb)
        elif outbgr is None and read_image_components:
            outbgr = cv2.cvtColor(outyvu, cv2.COLOR_YCrCb2BGR)
        return outbgr, outyvu, status


def read_metadata(infile, debug):
    config_dict = {
        "read_image_components": True,
        "qpextract_bin": False,
        "h265nal_parser": True,
        "isobmff_parser": True,
    }
    _, status = read_image_file(infile, config_dict=config_dict, debug=debug)
    return status


def read_colorrange(infile, debug):
    status = read_metadata(infile, debug)
    if os.path.splitext(infile)[1] == ".y4m":
        return status["y4m:colorrange"].upper()


def write_image_file(
    outfile, outimg, return_type=itools_common.ProcColor.bgr, **kwargs
):
    if os.path.splitext(outfile)[1] == ".y4m":
        # y4m writer requires YVU
        if return_type == itools_common.ProcColor.yvu:
            outyvu = outimg
        elif return_type == itools_common.ProcColor.bgr:
            outyvu = cv2.cvtColor(outimg, cv2.COLOR_BGR2YCrCb)
        colorspace = "420"
        colorrange_id = kwargs.get("hevc:fr", 1)
        colorrange = "FULL" if colorrange_id == 1 else "LIMITED"
        itools_y4m.write_y4m(outfile, outyvu, colorspace, colorrange)
    else:
        # cv2 writer requires BGR
        if return_type == itools_common.ProcColor.yvu:
            outbgr = cv2.cvtColor(outimg, cv2.COLOR_YCrCb2BGR)
        elif return_type == itools_common.ProcColor.bgr:
            outbgr = outimg
        cv2.imwrite(outfile, outbgr)
