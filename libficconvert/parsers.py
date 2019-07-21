import argparse
import re
from sys import argv, stderr
from subprocess import run
import os
from .connection import download_to_file

# ## utilities

def io_insert(file, text, buffsize=2048):
    """a utility to write into a BufferedRandomIO file interface, without overwriting some contents"""
    if len(text)>=buffsize:
        buffsize = len(text)
    fsize = os.fstat(file.fileno()).st_size

    # begin actual 'insertion', by copy-pasting buffers at the right place
    cur = file.tell()
    orig_pos = cur
    buff1 = file.read(buffsize)
    file.seek(cur)
    file.write(text)

    while cur < fsize-buffsize:
        # at this point, all text before cur+len(text) has been fixed
        # first, extend buffer,
        file.seek(cur + buffsize)
        buff2 = file.read(buffsize)

        # then, paste first buffer part
        file.seek(cur + len(text))
        file.write(buff1)

        # and adjust for next step
        buff1 = buff2
        cur += buffsize

    # now, there is only less than one buffer size left.
    file.seek(cur + len(text))
    file.write(buff1)

    file.seek(orig_pos + len(text))

def io_erase(file, size, buffsize=2048):
    """a utility to write into a BufferedRandomIO file interface, without overwriting some contents"""
    if size>=buffsize:
        buffsize = size
    elif size == 0:
        return
    elif size < 0:
        raise ValueError('io_erase: cannot erase a negative amount of bytes')
    fsize = os.fstat(file.fileno()).st_size

    # begin actual 'deletion', by copy-pasting the contents just afterwards
    orig_pos = cur = file.tell()

    while cur < fsize-buffsize:
        # at this point, all text before cur has been fixed
        # first, look up the contents that should be here
        file.seek(cur+size)
        buff1 = file.read(buffsize)
        # then, paste on the right spot
        file.seek(cur)
        file.write(buff1)
        # and adjust `cur` for next step
        cur = file.tell()

    # now, there is only less than one buffer size left.
    # but is it before or after the new end of file?
    if cur < fsize-size:
        file.seek(cur+size)
        buff1 = file.read(buffsize)
        file.seek(cur)
        file.write(buff1)
    else:
        file.seek(fsize-size)

    # and adjust the file size
    file.truncate()
    file.seek(orig_pos)


# ## read-only parsers (state-machine optimized)

def scanforagebarrier(page):
    """will scan a page to tell if it is a "please confirm you want to see this" page."""
    correct_line = b"This work could have adult content. If you proceed you have agreed that you are willing to see such content."
    line = b' '

    while line:
        if correct_line in line:
            return True
        line = page.readline()
    else:
        # if it didn't return yet, EOF happened.
        return False


def getdownloadurl(page):
    """scans web page for the link to the HTML download of the fic."""
    correct_line = re.compile(r'.*?<li><a href="(?P<url>/downloads/[0-9]+/.*?\.html\?updated_at\=[0-9]+)">HTML</a></li>.*\n?')
    state='out'
    line = ' '

    while line:
        if state=='out':
            if '<li class="download"' in line:
                state='in_dl'
        elif state == 'in_dl':
            temp = correct_line.fullmatch(line)
            if temp:
                return temp.group('url')

        line = page.readline().decode()
    else:
        # if it didn't return yet, EOF happened.
        print('sorry, this page doesn\'t seem to have a download link. Please make sure this is an existing and publicly available fic.', file=stderr)
        raise ValueError('getdownloadurl: unexpected EOF (current state: {:s})'.format(state))


def getmetafrompage(page):
    """scans web page for some metadata (title, author name)"""

    auth_re_matcher = re.compile(r'.*?\<a rel\="author" href\="[\w/\%]+?"\>(?P<name>[\w\%]+?)\</a\>.*\n?')
    state='out'  # out, in_title
    line = ' '

    title_out = ''
    author_out = ''

    while line:
        if state=='out':
            if '<h2 class="title heading">' in line:
                state='in_title'
            elif '<a rel="author"' in line:
                # no state change necessary. all processing is done in the same line.
                temp = auth_re_matcher.fullmatch(line)
                if temp is None:
                    print(line)
                    raise ValueError('invalid page formatting. There doesn\'t seem to be an author in the designated field')
                author_out = temp.group('name')
        elif state == 'in_title':
            title_out =  line.strip()  # the line with the title is the one after the heading
            state = 'out'

        line = page.readline().decode()

        if title_out and author_out:
            return title_out, author_out
    else:
        raise ValueError('Couldn\'t retrieve metadata (title, author) from page.')


def getstylefrompage(page):
    """returns the embedded css code in a specific web page"""

    # now get the style(s)
    # (state machine reading the page one line at a time, to prevent memory issues)
    styles = ''
    buffer = b''  # incrementially filled to contain a style block
    line = b' '

    is_in = False  # state automaton: needs to know if
                   # the 'read head' is inside a <style> block

    while line:
        # TODO: case for multiple style block tags in single line (</style><style>)
        if not is_in:
            # detect possible <style> block entered
            if b'<style type="text/css">' in line:
                buffer = b''  # reset cached style block when entering a new one
                is_in = True
        if is_in:  # not elif because begin and end might be on the same lone
            # buffer += line.replace(b'\n',b'<LINE>')  # removes the '\n's to make the regex work
            buffer += line
            if b'</style>' in line:
                # the buffer contains an entire block, extract its contents
                style = re.match('.*<style type="text/css">(?P<styl>.*)</style>',
                                 buffer.decode(), re.S).group('styl')
                styles += '\n' + style #.replace('<LINE>', '\n')
                is_in = False

        line = page.readline()

    return styles

# parser options:
add_lisibility = True
adapt_black_bg = False  # not yet implemented


# let's suppose that no comments happen
def style_parser(style_str):
    """parse css style and adapts it"""
    # it "consumes" the previous style
    new_style = ''
    while style_str:  # while non-zero
        # identifier(s!) time
        no_more_ids = False
        while not no_more_ids:
            style_str = style_str.lstrip()
            if style_str[:9] == '#workskin':
                new_style += '.workskin'
                style_str = style_str[9:]
            if ',' in style_str:
                begin_index = min(style_str.index('{'), style_str.index(','))
            else:
                begin_index = style_str.index('{')
            new_style += style_str[: begin_index].rstrip()
            if style_str[begin_index]==',':
                if add_lisibility:
                    new_style += ', '
                else:
                    new_style += ','
            else:
                if add_lisibility:
                    new_style += ' {\n'
                else:
                    new_style += '{'
                no_more_ids = True
            style_str = style_str[begin_index +1 :]

        end_index = style_str.index('}')
        # 'header' done: time to get the properties

        sep_index = 0
        # while the newt preperty is inside the block:
        while ':' in style_str: # do not crash when last property is done
            # preperty
            sep_index = style_str.index(':')
            if sep_index > end_index:
                break
            else:
                new_style += style_str[:sep_index].strip()+':'
                style_str = style_str[sep_index +1 :]
                end_index -= (sep_index +1)
                if add_lisibility:
                    new_style += ' '

            # value (assume it is inside the block)
            if ';' in style_str:
                sep_index = min(style_str.index(';'), end_index)
            else:
                sep_index = end_index
            # for the last parameter in the block, ';' is replaced by ';'
            new_style += style_str[:sep_index].strip()
            style_str = style_str[sep_index +1 :]
            if sep_index == end_index:
                new_style += '}'
            else:
                new_style += ';'
            end_index -= (sep_index +1)  # if the end is reached, end_index=1.
                                         # next iteration will hit 'break'
            if add_lisibility:
                new_style += '\n'
        # closing '}' has been processed
    return new_style


# vvv rendered useless vvv
def extracturl(file):
    """gets original fic url from 'preface' file"""
    # (read file line by line)
    line = ' '
    while line:
        # detect the corresponding generated pattern on the exported xhtml files in the epub archive
        if '<p class="message">Posted originally on the' in line:
            buffer = line.strip() + file.readline().strip()  # strip the '\n's to not crash the regex
            print(buffer)
            return re.match(r'.*?<a.*?>.*?</a>.*?<a href="(?P<url>.*?)">', buffer).group('url')
        line = file.readline()




# ## functions for files to be written
def add_style_to_head(file, styleheader=b''):
    """navigates after the head section of a html file,
    and puts a link to the style sheet in said head section"""

    #get end of head section
    pos = 0
    line = ' '
    while line:
        line = file.readline()
        if line.strip()[:7] == b'</head>':
            break
        else:
            pos = file.tell()
    else:
        # didn't break: eof
        raise ValueError('unexpected EOF in add_style_to_head')

    # then add the stylesheet
    file.seek(pos)
    io_insert(file, styleheader)

    # get to beginning of actual work
    file.seek(pos)
    file.readlines(2)

def adapt_chapter(file):
    """finds the borders of a chapter and puts the `workskin` class on it.
    returns wether or not it succeeded (if False, assume EOF)"""

    line = ' '
    while line:
        line = file.readline()
        if line.strip() == b'<!--chapter content-->':
            break
        else:
            pos = file.tell()
    else:  # no break: eof
        return False

    # insert style division beginning
    file.seek(pos)
    file.readline()
    io_insert(file, b'<div class="workskin">\n')


    # get to end of chapter
    file.seek(pos)

    line = ' '
    while line:
        line = file.readline()
        if line.strip() == b'<!--/chapter content-->':
            break
        else:
            pos = file.tell()
    else:  # eof
        raise ValueError('unexpected mid-chapter EOF')

    # insert style division end
    file.seek(pos)
    io_insert(file, b'</div>\n')

    return True

"""
def adapt_entire_file(file, type='EPUB', actualstyle=''):
    \"\"\"adapts a full file, wether an epub chapter file or a full html file (EPUB/HTML)\"\"\"
    if type=='EPUB':
        styleheader = b'  <link rel="stylesheet" href="user_style.css" />\n'
    elif type=='HTML':
        styleheader = '  <style type=text/css>\n{:s}\n  </style>\n'.format(actualstyle).encode('utf-8')
    else:
        raise ValueError('invalid type for adapt_entire_file')
    file.seek(0)
    add_style_to_head(file, styleheader)
    while adapt_chapter(file):
        pass
"""

def add_chapter_boundaries(file):
    while adapt_chapter(file):
        pass

def add_style_to_final_html(file, actualstyle=''):
    styleheader = '  <style type=text/css>\n{:s}\n  </style>\n'.format(actualstyle).encode('utf-8')
    file.seek(0)
    add_style_to_head(file, styleheader)
    while adapt_chapter(file):
        pass


def parse_images(file, tempdir):
    """finds the image tags in a html file and changes them into local images"""
# <img src="https://66.media.tumblr.com/d8aabb041f3082e89fe4f3cc2b535889/tumblr_ptmhg0FVwz1wfpfh6_1280.jpg" alt="" width="286" height="293" data-pagespeed-url-hash="1369688483" onload="pagespeed.CriticalImages.checkImageForCriticality(this);"/>
    parser = re.compile(b'(?P<all>(?P<pre>.*?)\\<img(?P<first>( *[\\w]+=".*?")*) src="(?P<url>.*?)"(?P<rest>( *[\\w]+=".*?")*) */ *\\>).*\\n?')
    basename = os.path.split(file.name)[1] + '_image{:04d}'

    line = b' '
    counter = 0
    pos = 0
    while line:
        # if the current line contains image tags, get ready to overwrite them.,
        line_dirty = False  # if the file cursor scrolled back to be beginning of the line
        if b'<img' in line:
            file.seek(pos)
            line_dirty = True

        while b'<img' in line:
            # beginning of while: file cursor is just before the contents contained in `line`

            # first, get file and write to temp directory, and create new image tag
            res = parser.fullmatch(line)
            newname = os.path.split(
                download_to_file(res.group('url').decode(), os.path.join(tempdir, basename.format(counter)))
            )[1]
            newstring = '{:s}<img{:s} src="./{:s}"{:s} />'.format(
              res.group('pre').decode(),
              res.group('first').decode(),
              newname,
              res.group('rest').decode()
            ).encode()

            # then write changes to file.

            delta_l = len(res.group('all')) - len(newstring)
            if delta_l < 0:  # need to insert
                file.write(
                    newstring[ :len(res.group('all'))  ]
                )
                io_insert(file,
                    newstring[  len(res.group('all')): ]
                )
            else:  # need to erase ?
                file.write(newstring)
                io_erase(file, delta_l)

            # loop maintenance:
            counter +=1
            line = line[len(res.group('all')):]  # remove the processed image from

        # end while: somehting might still be on the line, but no more images.
        # or me might already be on the next line
        if line_dirty:
            _ = file.readline()

        pos = file.tell()
        line = file.readline()
    # end of "while line"
