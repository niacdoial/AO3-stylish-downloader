from tempfile import TemporaryDirectory as TDir
import tempfile
from zipfile import ZipFile
import sys, os   # for os.stat and sys.platform
import re
from shutil import copyfile
from subprocess import run

def filedump(a, b):
    """dumps fontent of readable a into writable b, by chunks of 2048 bytes for memory efficience"""
    buffer = a.read(2048)
    while buffer:
        b.write(buffer)
        buffer = a.read(2048)

class OpenedZip:
    """a class to edit zip files, by dumping its contents into a temporary directory"""
    def __init__(self, name):
        """a basic (inexpensive) setup"""
        self.filename = name
        self.ifile = ZipFile(name, 'r', 8)
        self.tdir_obj = TDir()
        self.tdir = self.tdir_obj.name
        self.files = self.ifile.namelist()

    def extract(self):
        """extract the contents of the zip file in a temp directory (EXPENSIVE)"""
        self.ifile.extractall(self.tdir)

    def getfile(self, name, mode):
        """the equivalent of open() for files from the zip archive"""
        if 'w' in mode.lower() and name not in self.files:
            self.files.append(name)
        return open(self.tdir + os.path.sep +name, mode)
    def getfilepath(self, name):
        return self.tdir + os.path.sep +name

    def zipback(self, zerooffname='mimetype'):
        """creates a new zip file from the temp directory:
           - very expensive
           - can make sure a specific file is at the lowest offset in the resulting archive
           - tweaked for epub files"""

        if '/' in zerooffname or '\\' in zerooffname:
            raise ValueError('cannot zero_offset a buried file (yet)')
        if zerooffname not in self.files:
            zerooffname=''

        self.ifile.close()
        ofile = ZipFile(self.filename[:-5]+'_neu.epub', 'w', 8)

        if zerooffname:
            ofile.write(self.tdir + '\\'+zerooffname,
                            zerooffname)

        for name in self.files:
            if name != zerooffname:
                ofile.write(self.tdir + '\\'+name, name)

        ofile.close()

def makeseekable(file):
    newfile = tempfile.TemporaryFile()
    filedump(file, newfile)
    file.close()
    newfile.seek(0)
    return newfile


def localconvert(namea, nameb, finalstylefile=''):
    if sys.platform=='linux':
        program = 'ebook-convert'
    elif sys.platform[:3].lower=='win':
        program = '.\\ebook-convert.bat'
    else:
        raise RuntimeError('platform not supported. sorry.')

    args = [program, namea, nameb,
    '--chapter', "//*[name()='div' and @class = 'meta group']"]
    if nameb[-4:] == 'epub':
        args.append('--preserve-cover-aspect-ratio')
    if finalstylefile:
        args += ['--extra-css', finalstylefile]
    run(args)
