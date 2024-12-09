<div align="center">

# TR Rename
Rename cryptically named Trade Republic PDFs using their ISIN, order number, date, and more.
</div>

______________________________________________________________________

**TR Rename** is a lightweight offline Python program that can rename cryptically named Trade Republic PDFs by 
extracting the relevant data from the PDFs themselves.

  
Relevant directories should be backed up beforehand. TR Rename should not touch any non-PDFs, but better safe than sorry. 
Also, the old file names are not saved. 


## Supported Files
- Wertpapierabrechnung
- Dividende
- Abrechnung Zinsen
- Abrechnung Cryptogeschaeft
- Steuerliche Optimierung (e.g. "Steuerkorrektur")

Only German files are currently supported.
  
## Requirements
Python (version 3.6 or higher) and the libraries `argparse`, `os`, `re`, and `pdfquery` are required.

While TR Rename should work on any OS, it has only been tested on Linux.

## Usage
No installation needed. Simply run:
```commandline
python3 tr_rename.py [-h] [--dry-run] [paths ...]
```
TR rename recursively searches all provided paths (default is the current working directory) for supported PDF files and renames them.

It is advisable to make a backup of the given files / directories. 

### Examples
To recursively rename all PDF files in the current working directory and its subdirectories:
```commandline
python3 tr_rename.py
```

To rename files within a `dir1` recursively and also `file1` and `file2`:
```commandline
python3 tr_rename.py dir1 file1 file2
```

### Example Output
```commandline
$ python3 tr_rename.py TR/pb0123456789pb0123456789pb012345.pdf 
TR/pb0123456789pb0123456789pb012345.pdf -> TR/TR_Abrechnung_Kauf_US0123456784_Order_1234-5678_abcd-efff_20240428.pdf
```

### Command Line Options
```commandline
-h             Show help
--dry-run      Perform a dry-run, printing the new names without renaming any files
```



## Alternatives
- https://github.com/ArdentEmpiricist/TR_PDF_Rename, written in Rust. It supports other files ("Saveback",
"Sparplan", "Depottransfer" but not e.g. "Zinsen"). Also, the renaming scheme is less unique.

- https://github.com/FabianSer/TradeRepublic-PDF-Renaming
has an even simpler renaming scheme 

- https://github.com/MarcBuch/TR-PDF-Parser seems to have very extensive functionalities, even supporting csv export of data. However, it 
seems not to work right now, because of minor changes in the wording of the PDFs. But it might be easily fixable.

- There are several TR PDF download repositories on GitHub. They *might* include some functionality for generating appropriate filenames.

## Donate
If this has helped you in any way, you can donate to the WWF or any other charity you like: 
https://wwf.panda.org/support_wwf
