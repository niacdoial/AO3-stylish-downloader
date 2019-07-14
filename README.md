## 'archive restyler' by niacdoial
This python script's purpose is to download a fic from AO3 (fic URL and destination have to be provided), but unlike the vanilla on-site downloader, it keeps the author's style.

**Warning** : when downloading a fic from ao3, the author's style is *deliberately missing* because it might look broken on some reading devices.
When using this script, please acknowledge the fact that *you are bypassing compatibility measures* put in place by ao3.


Also, this script comes with NO GUARANTY WHATSOEVER, like pretty much every open source software.

---


#### How to install and use (windows)
- Make sure you have installed python (version 3, ideally 3.5 or more)
  To do so, just see if the command `py -3` starts the python environnement, when you type it in the command line (to get out of it, type "exit()" and enter.)
  If you don't have python, grab it from python.org

- Install (or just download) Calibre (calibre-ebook.com), and edit ebook-convert.bat so that the path points to Calibre's `ebook-convert.exe`


From there you have several options to launch the program.

- **command line**:
  Open a console in the folder where `main.py` is located, and type `py .\main.py -h` to get a help text. Then, do that again, but replace `-h` by the arguments you want (example: `archiveofourown.org/works/12345678  .\output.epub`).

- **fully interactive command line**
  Open a console where `main.py` is located, and launch `py .\interact.py`. You will be guided through the entire process. You should also be able to simply double click on `./interact.py` from the file explorer instead of launching it from the command line.

- **Graphical interface**
  To be implemented


  #### How to install and use (linux)
  - Make sure you have installed python (version 3, ideally 3.5 or more)
    To do so, just see if the command `python3` starts the python environnement, when you type it in the command line (to get out of it, enter Ctrl-D.)
    If you don't have python, grab it from you package manager (usually under the name 'python3')

  - also make sure ou have calibre (calibre-ebook.com), which is also probably in your package manager.
  - make sure `main.py` and `interact.py` are executable (use the 'properties' dialog of your file explorer if you don't know how to do this)


  From there you have several options to launch the program.

  - **command line**:
    Open a console in the folder where `main.py` is located, and type `./main.py -h` to get a help text. Then, do that again, but replace `-h` by the arguments you want (example: `archiveofourown.org/works/12345678  .\output.epub`).

  - **fully interactive command line**
    Open a console where `main.py` is located, and launch `./interact.py`. You will be guided through the entire process. Depending on the file explorer, you should also be able to simply double click on `./interact.py`.

  - **Graphical interface**
    To be implemented

---

Lastly, please note that some updates on ao3's side might break this script.
