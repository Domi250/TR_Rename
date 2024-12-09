# todo
# clean up
# Readme with install + usage

import argparse
import os
from pdfquery import PDFQuery
import re

# Commandline options
dry_run = False


# Print an error message and exit
def err(abort, msg, filename, pdf=None):
    print(f"Error for {filename}: {msg}")
    if pdf: pdf.file.close()
    if abort != 0: exit(1)


# Prints all text elements from TextLines and TextBoxes. Helps with locating objects
def print_all(pdf):
    text_elements = pdf.pq('LTTextLineHorizontal').extend(pdf.pq('LTTextBoxHorizontal'))
    for t in text_elements: print(t.text)


# Formats a date having the format *dd.mm.yyyy*
def format_date(string):
    date = string.split(".")
    dd = date[0][-2:]
    mm = date[1]
    yyyy = date[2][0:4]
    return yyyy, mm, dd


# Finds the only TextLine or TextBox containing "string". Error, if there are no or multiple matches.
def find_string(pdf, filename, string):
    text_elements = pdf.pq('LTTextLineHorizontal').extend(pdf.pq('LTTextBoxHorizontal'))
    matches = [t.text for t in text_elements if string in t.text]
    if len(matches) < 1:
        err(1, f"No matches found for \"{string}\".", filename, pdf)
    elif len(matches) > 1:
        err(1, "fToo many matches found for \"{string}\".", filename, pdf)
    return matches[0]


# Determine order type by matching for "Kauf"/"Verkauf"
def find_order_type(pdf, filename):
    kauf = pdf.pq('LTTextLineHorizontal:contains("Kauf")')
    verkauf = pdf.pq('LTTextLineHorizontal:contains("Verkauf")')

    order_type = ""
    if kauf and verkauf:
        err(1, "Cannot determine order_type (both \"Kauf\"and \"Verkauf\" found)", filename, pdf)
    elif kauf:
        order_type = "Kauf"
    elif verkauf:
        order_type = "Verkauf"
    else:
        err(1, "No \"Kauf\" or \"Verkauf\" found", filename, pdf)
    return order_type


# Extracts Order and Ausfuehrung from the top right of the document
def find_order_ausfuehrung(pdf, filename):
    text_elements = pdf.pq('LTTextLineHorizontal').extend(pdf.pq('LTTextBoxHorizontal'))

    for i in range(len(text_elements)):
        match = re.match(r"1 von [0-9]", text_elements[i].text)

        if match and (i + 3) < len(text_elements):
            # yyyy,mm,dd = format_date(text_elements[i+1].text) # pdf creation date, usually not interesting
            order_nr = text_elements[i + 2].text.strip()
            ausfuehrung = text_elements[i + 3].text.strip()

            return order_nr, ausfuehrung

    err(1, "find_order_ausfuehrung() couldn't match its search pattern", filename, pdf)


# Extracts stock/cryptocurrency name, looking for the first occurrence of "POSITION".
# Use carefully, since "POSITION" usually occurs multiple times.
def find_product_name(pdf, filename):
    text_elements = pdf.pq('LTTextLineHorizontal').extend(pdf.pq('LTTextBoxHorizontal'))

    for i in range(len(text_elements)):
        t = text_elements[i]
        match = re.match(r"POSITION", t.text)
        # print(t.text)
        if match and (i + 1) < len(text_elements):
            name = text_elements[i + 1].text.strip()
            name = name.replace(' ', '_')
            return name

    err(1, "find_product_name() couldn't match its search pattern", filename, pdf)


# Find any string matching the ISIN structure and having the correct check digit
def find_isin_match(pdf, filename):
    text_elements = pdf.pq('LTTextLineHorizontal').extend(pdf.pq('LTTextBoxHorizontal'))

    # Search for unique regex matches matching an ISIN
    matches = []
    for t in text_elements:
        match = re.search(r"(?<![a-zA-Z])[A-Z]{2}[0-9A-Z]{9}[0-9](?![0-9])", t.text)
        if match and match.group() not in matches and check_isin(match.group()):
            matches.append(match.group())

    if len(matches) < 1:
        err(1, "No ISIN string matches found.", filename, pdf)
    elif len(matches) > 1:
        err(1, "Too many ISIN string matches found.", filename, pdf)
    return matches[0]


# Verify the ISIN check digit
def check_isin(isin):
    if len(isin) != 12:
        return False

    isi = isin[0:-1]
    check_digit = int(isin[-1])

    # Transform ISIN to list of digits
    l = []
    for i, c in enumerate(isi):
        if c.isdigit():
            l.append(ord(c) - ord('0'))
        else:
            l += divmod(ord(c) - ord('A') + 10, 10)

    # Double every second digit and calculate sum
    digit_sum = 0
    for i, d in enumerate(reversed(l)):
        if i % 2 == 1:
            digit_sum += d
        else:
            digit_sum += 2 * d - 9 if 2 * d > 9 else 2 * d

    return check_digit + digit_sum % 10 == 10


def process_abrechnung_zinsen(pdf, filename):
    date_string = find_string(pdf, filename, "zum ")
    yyyy, mm, dd = format_date(date_string)
    new_name = f"TR_Zinsen_{yyyy}{mm}{dd}.pdf"
    return new_name


def process_abrechnung_cryptogeschaft(pdf, filename):
    order_type = find_order_type(pdf, filename)

    cryptocurrency = find_product_name(pdf, filename)
    order_nr, ausfuehrung = find_order_ausfuehrung(pdf, filename)

    # Find "Kauf/Verkauf am " to extract the date
    date_string = find_string(pdf, filename, "auf am ")
    yyyy, mm, dd = format_date(date_string)

    new_name = f"TR_Abrechnung_Cryptogeschaeft_{order_type}_{cryptocurrency}_Order_{order_nr}_{ausfuehrung}_{yyyy}{mm}{dd}.pdf"
    return new_name


def process_wertpapierabrechnung(pdf, filename):
    order_type = find_order_type(pdf, filename)

    isin_match = find_string(pdf, filename, "ISIN: ")
    isin = isin_match.split()[1].strip()
    order_nr, ausfuehrung = find_order_ausfuehrung(pdf, filename)

    # Find "Kauf/Verkauf am " to extract the date
    date_string = find_string(pdf, filename, "auf am ")
    yyyy, mm, dd = format_date(date_string)

    new_name = f"TR_Abrechnung_{order_type}_{isin}_Order_{order_nr}_{ausfuehrung}_{yyyy}{mm}{dd}.pdf"
    return new_name


def process_dividende(pdf, filename):
    date_string = find_string(pdf, filename, "mit Ex-Datum")
    yyyy, mm, dd = format_date(date_string)

    isin = find_isin_match(pdf, filename)
    new_name = f"TR_Dividende_{isin}_{yyyy}{mm}{dd}.pdf"
    return new_name


def process_steuerliche_optimierung(pdf, filename):
    date_string = find_string(pdf, filename, "Steuerliche Optimierung am ")
    yyyy, mm, dd = format_date(date_string)
    new_name = f"TR_Steuerliche_Optimierung_{yyyy}{mm}{dd}.pdf"
    return new_name


def process_pdf(dirpath, file):
    pdf_path = os.path.join(dirpath, file)
    pdf = PDFQuery(pdf_path)
    pdf.load()

    # if debug : pdf.tree.write("tree", pretty_print=True)

    if not pdf.pq(f'LTTextLineHorizontal:contains("TRADE REPUBLIC")'):
        err(0, "Does not seem to be a Trade Republic file. Skipping.", file, pdf)
        return

    # Old name is the default name. Only needed to suppress warnings.
    # new_name = str(os.path.join(dirpath, file))

    if pdf.pq(f'LTTextLineHorizontal:contains("ABRECHNUNG ZINSEN")'):
        new_name = process_abrechnung_zinsen(pdf, file)
    elif pdf.pq(f'LTTextLineHorizontal:contains("WERTPAPIERABRECHNUNG")'):
        new_name = process_wertpapierabrechnung(pdf, file)
    elif pdf.pq(f'LTTextLineHorizontal:contains("DIVIDENDE")'):
        new_name = process_dividende(pdf, file)
    elif pdf.pq(f'LTTextLineHorizontal:contains("ABRECHNUNG CRYPTOGESCHÄFT")'):
        new_name = process_abrechnung_cryptogeschaft(pdf, file)
    elif pdf.pq(f'LTTextLineHorizontal:contains("STEUERLICHE OPTIMIERUNG")'):
        new_name = process_steuerliche_optimierung(pdf, file)
    # elif pdf.pq(f'LTTextLineHorizontal:contains("")'):
    # new_name = process_
    else:
        err(0, "PDF file could not be matched to any known document type.", pdf_path, pdf)
        return

    full_name = os.path.join(dirpath, new_name)
    if os.path.isfile(full_name):
        err(0, "File already exists. Skipping.", full_name, pdf)
        return

    if not dry_run:
        os.rename(os.path.join(dirpath, file), os.path.join(dirpath, new_name))
    print(os.path.join(dirpath, file) + " -> " + os.path.join(dirpath, new_name))

    pdf.file.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", default=[os.getcwd()], help="Path to directory or PDF-file")
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without renaming files')
    args = parser.parse_args()

    global dry_run
    if args.dry_run:
        dry_run = True
        print("Performing dry-run. No files will be renamed.")

    for path in args.paths:
        if os.path.isdir(path):
            for dirpath, _, files in os.walk(path):
                for file in files:
                    if file.endswith(".pdf"):
                        process_pdf(dirpath, file)
        elif os.path.isfile(path):
            dirpath, file = os.path.split(path)
            process_pdf(dirpath, file)
        else:
            err(1, "Error with given path.", path)


if __name__ == "__main__":
    main()
