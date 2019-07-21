#!/usr/bin/env python3

from importlib import import_module
import sys
import argparse

main = import_module('main', '.')
lfc = main.lfc

class ArgNamespace:
    def __init__(self):
        self.input = ''
        self.output = ''
        self.overwrite = False
        self.format = ''
        self.embed = False
        self.adult = False


def get_output_path():
    raw_input = ''
    while True:
        raw_input = input('> ')
        if raw_input == 'EXIT':
            raise KeyboardInterrupt()
        try:
            return main.outputpath_arg(raw_input)
        except argparse.ArgumentTypeError as err:
            print('whoops, something went wrong ({}). Try again.'.format(repr(err)))

def generate_namespace():
    ns = ArgNamespace()
    print('Welcome to the AO3 stylish fic downloader, interactive command prompt version.')
    print('\nFirst, please select the fic you want to download (or type EXIT to exit)\n'+
          "(tip: recommended formats are `https://archiveofourown.org/works/12345678` and `12345678`)")

    raw_input = ''
    while True:
        raw_input = input('> ')
        if raw_input == 'EXIT':
            raise KeyboardInterrupt()
        try:
            ns.input = lfc.url_checker(raw_input)
            break
        except argparse.ArgumentTypeError as err:
            print('whoops, something went wrong ({}). Try again.'.format(repr(err)))


    print('\nNow, please select the output path (or type EXIT to exit)\n'+
          "(tip: it can be either an existing directory, or a full file path)\n"+
          "(tip 2: the file extension should be in ('epub', 'html', 'mobi', 'azw3') )")

    raw_output = get_output_path()
    is_ok = not raw_output[3]
    while not is_ok:
        print('It seems this is the path to an existing file. De you want to overwrite it?')
        ans = input('y/n/EXIT > ')
        if ans.lower() in ('y', 'yes', 'confirm', 'proceed'):
            ns.overwrite = True
            is_ok = True
        elif ans == 'EXIT':
            raise KeyboardInterrupt()
        else:
            print('Please select another output path')
            raw_output = get_output_path()
            is_ok = not raw_output[3]

    ns.output = raw_output

    if ns.output[0]=='FILE' and ns.output[2][-4:] in ('epub', 'html', 'mobi', 'azw3'):
        ns.format = ns.output[2][-4:]
    else:
        print("Please select a format for the output ('epub', 'html', 'mobi', 'azw3'). You can still type EXIT.")
        raw_format = raw_format = input('> ')
        while raw_format not in ('epub', 'html', 'mobi', 'azw3', 'EXIT'):
            print('Whoops. input not recognised. PLease try again.')
            raw_format = input('> ')
        if raw_format == 'EXIT':
            raise KeyboardInterrupt()
        else:
            ns.format = raw_format

    if ns.format != 'html':
        print('Do you want to embed images that could be contained in the fic? (otherwise, seeing them will recquire an internet connection)')
        ans = input('y/n/EXIT > ')
        if ans.lower() in ('y', 'yes', 'confirm', 'proceed'):
            ns.embed = True
        elif ans == 'EXIT':
            raise KeyboardInterrupt()
        else:
            ns.embed=False

    return ns


if __name__=='__main__':
    try:
        main.main(generate_namespace())

    except Exception as err:
        print(repr(err), file=sys.stderr)
        print("\noops, something went wrong. The error is right here ^^^. Press enter for more details", file=sys.stderr)
        input() # show any error that could have happened
        raise
    except KeyboardInterrupt:
        exit(0)
