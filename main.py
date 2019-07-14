#!/usr/bin/env python3
import argparse
import os, sys
import libficconvert as lfc

# ## command line argument management:
def outputpath_arg(string):
    """output path. format: (`DIR or FILE`, directory, file (if provided), overwrite warning(bool) )"""
    if os.path.isdir(string):
        return ("DIR" , os.path.abspath(string), '', False)
    elif os.path.isdir(os.path.split(string)[0]):
        path, file = os.path.split(os.path.abspath(string))
        ovrw_warning = os.path.isfile(string)
        return ("FILE", path, file, ovrw_warning)
    else:
        raise argparse.ArgumentTypeError("invalid output path. must be a existing dir or a proper file")

def ext_format(string):
    if string.lower() in ('epub', 'html', 'mobi', 'azw3'):
        return string.lower()
    else:
        raise argparse.ArgumentTypeError("invalid extension. must be 'epub', 'html', 'mobi' or 'azw3'")



def parse():
    parser = argparse.ArgumentParser()  # prog='myprogram'
    parser.add_argument('input', type=lfc.url_checker, help="the url of the original AO3 fic"
                        "(tip: recommended formats are `https://archiveofourown.org/works/12345678` and `12345678`)")
    parser.add_argument('output', type=outputpath_arg, help="output path. Can be either an existing directory or a full file path"
                        "(within an existing directory). The file name will be generated automatically if it is the former.")
    parser.add_argument('-W', '--overwrite', help="do allow overwriting output file", default=False, action='store_true')
    parser.add_argument('-f', '--format', type=ext_format, help="choose the output format (overridden by a possible extension in the output filepath)", default='epub')
    parser.add_argument('-e', '--embed',  help="choose to embed images into the final document", default=False, action='store_true')
    parser.add_argument('-A', '--adult', help='do confirm you are an adult now. if you don\'t, you might be prompted to do so later.', default=False, action='store_true')
    #parser.add_argument('-f', '--filling', type=int, help="filling for file numbering", default=5)
    #parser.add_argument('-d', '--directory', help="diretory where files shall be created", default='./TEST')
    args = parser.parse_args()

    if args.output[0]=='FILE' and args.output[2][-4:] in ('epub', 'html', 'mobi', 'azw3'):
        args.format = args.output[2][-4:]
    elif args.output[0]=='FILE':
        args.output[2] += '.' + args.format
        args.output[3] = os.path.isfile( os.path.join( args.output[1], args.output[2] ) )

    if (not args.overwrite) and args.output[3]:
        print("Error: file \"" + os.path.join(*args.output[1:3]) + "\" already exists and overwriting is disabled. Use -W to enable.", file=sys.stderr)
        exit(1)

    print(args)
    return args


def main(args):
    address, page = lfc.getwebpage(args.input)
    tempdir_obj = lfc.TDir()
    tempdir = tempdir_obj.name
    page = lfc.makeseekable(page)

    # if the work contains adult content, be sure of user consent
    if lfc.scanforagebarrier(page):
        page.close()
        if not args.adult:
            print('This work could have adult content. If you proceed you have agreed that you are willing to see such content.', file=sys.stderr)
            try:
                adult = input('proceed? (y/n) > ')
                if adult.lower() in ('y', 'yes', 'confirm', 'proceed'):
                    pass
                else:
                    raise KeyboardInterrupt()
            except KeyboardInterrupt:
                return
        address, page = lfc.getwebpage(address, '?view_adult=true')
        page = lfc.makeseekable(page)



    down_url = lfc.getdownloadurl(page)
    _, down_page = lfc.getwebpage(down_url, base_site='download.archiveofourown.org')

    page.seek(0)
    style = lfc.getstylefrompage(page)
    style = lfc.style_parser(style)

    if not args.output[2]:  # if no filename was provided
        temp_title, temp_author = lfc.getmetafrompage(page)
        args.output[2] = '{}-{}_by_{}.{}'.format(args.input[7:], temp_title, temp_author, args.format)

    if args.format == 'html':
        mainfile_path = os.path.join(args.output[1], args.output[2])
    else:
        mainfile_path = os.path.join(tempdir, 'main.html')

    pagedump = open(mainfile_path, 'bw')
    lfc.filedump(down_page, pagedump)
    page.close()
    pagedump.close()
    mainfile = open(mainfile_path, 'r+b')  # use binary because io_insert has a problem with text files

    # todo: include images if asked



    if args.format == 'html':
        lfc.add_style_to_final_html(mainfile, style)
        mainfile.close()
    else:
        lfc.add_chapter_boundaries(mainfile)
        mainfile.close()
        lfc.localconvert(mainfile_path, os.path.join(args.output[1], args.output[2]), style)


if __name__=='__main__':
    try:
        main(parse())

    except Exception as err:
        print(repr(err), file=sys.stderr)
        print("\noops, something went wrong. The error is right here ^^^. Press enter for more details", file=sys.stderr)
        input() # show any error that could have happened
        raise

"""
try: # TODO: options?
    #raise ValueError('fbpsr')
    # argv: [pyfile, ...] in every case
    print(sys.argv)
    if len(sys.argv)==1:
        print(__doc__)
    else:
        if argv[1][-4:] == 'html':
            fix_html(argv[1])
        elif argv[1][-4:] == 'epub':
            fix_epub(argv[1])
        else:
            print(__doc__)
    input('[Press enter to close]')
except Exception as err:
    print(repr(err))
    print("\noops, something went wrong. The error is right here ^^^. Press enter for more details")
    input() # show any error that could have happened
    raise
"""
