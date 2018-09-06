#!/usr/bin/env python2


# noinspection PyUnusedLocal
# https://stackoverflow.com/a/392258/365408
import multiprocessing
import subprocess
import time
from optparse import OptionParser

from colorama import init
from pymobileproduct.utils.make.shared import mkdir_p, cd, MakeException, set_env_vars, WARN, TITLE, SUCCESS
from pymobileproduct.utils.make.build import create_standalone_toolchain

POSSIBLE_PLATFORMS = ["all", "linux", "android", "clean"]
POSSIBLE_RUNTESTS = ["none", "short", "long"]
POSSIBLE_BUILD_TYPES = ["debug", "release"]

# Colorama
init(autoreset=True)



def split_list(option, opt, value, parser):
    setattr(parser.values, option.dest, value.split(','))


def parse_options():
    parser = OptionParser(usage="%prog <platform> [options]")
    parser.add_option('-t', '--target',
                      dest="platform",
                      default="linux")
    parser.add_option('-r', '--build_targets',
                      dest="build_targets",
                      default=["all"],
                      type='string',
                      action='callback',
                      callback=split_list)
    parser.add_option('-b', '--buildtype',
                      dest="buildtype",
                      default="release")
    options, args = parser.parse_args()
    if args:
        options.platform = args[0]

    if options.platform == "all":
        options.platform = ["android", "linux"]
    else:
        options.platform = [options.platform]
    return options


def validate_options(options):
    success = True
    if options.platform[0] not in POSSIBLE_PLATFORMS:
        print(WARN + "platform can only be: {}".format(POSSIBLE_PLATFORMS))
        print("./make.py -b <{}>".format("/".join(POSSIBLE_PLATFORMS)))
        success = False
    if options.buildtype not in POSSIBLE_BUILD_TYPES:
        print(WARN + "configuration can only be: {}".format(POSSIBLE_BUILD_TYPES))
        print("./make.py -b <{}>".format("/".join(POSSIBLE_BUILD_TYPES)))
        success = False
    if not success:
        raise MakeException("Invalid option")

def build_platforms(options):
    for platform in options.platform:
        build_dir = "build_" + platform + '_' + options.buildtype
        mkdir_p(build_dir)
        with cd(build_dir):
            my_env = set_env_vars(CC="/usr/bin/clang", CXX="/usr/bin/clang++")

            try:
                print(TITLE + " * CMake")

                # The following is for computers that find the wrong python library.
                # subprocess.check_call(
                #     "/opt/cmake/bin/cmake -DPYTHON_LIBRARY=/usr/lib/x86_64-linux-gnu/libpython2.7.so .. {}-DCMAKE_BUILD_TYPE={}".format("-DMY_BUILD_ANDROID=TRUE " if platform == "android" else "-DMY_BUILD_ANDROID=FALSE ",
                #                                                              options.buildtype.capitalize()).split(" "), env=my_env)

                # The weird spaces in the format string are important, doesn't work without them
                subprocess.check_call(
                    "/opt/cmake/bin/cmake .. {}-DCMAKE_BUILD_TYPE={}".format("-DMY_BUILD_ANDROID=TRUE " if platform == "android" else "-DMY_BUILD_ANDROID=FALSE ",
                                                                             options.buildtype.capitalize()).split(" "), env=my_env)

                print(TITLE + " * Building")
                start_time = time.time()
                for target in options.build_targets:
                    print(TITLE + "Building " + target)
                    subprocess.check_call("make {} -j{}".format(target, multiprocessing.cpu_count()).split(" "), stderr=subprocess.STDOUT)
                print(SUCCESS + " * Compilation took {:.2f} seconds".format(time.time() - start_time))
            except subprocess.CalledProcessError:
                raise MakeException(" * Compilation failed :(")

def main():
    options = parse_options()
    validate_options(options)
    create_standalone_toolchain(options.platform)
    build_platforms(options)


if __name__ == "__main__":
    main()
