#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Imports
import argparse
import logging
import subprocess
import sys

# PDF Specific Library Imports
import PyPDF2

# File MetaData
__author__ = "Dhairya Jain"
__copyright__ = "Copyright 2022, The Resume-Editor Project"
__credits__ = ["Dhairya Jain"]
__license__ = "GPL"
__version__ = "1.0.1"
__maintainer__ = "Dhairya Jain"
__email__ = "jaindhairya2001@gmail.com"
__status__ = "Development"

class constants:
    logger_name = "Resume-Editor"
    logfile = "resume_editor_logfile.log"
    version = "1.0.1"
    header_size = lambda pages, pad=0: 150 + 30*min(pages-1,1) + pad
    default_padding = 5


############################ Set Up Logging ###########################
logger = logging.getLogger(constants.logger_name)
logger.setLevel(logging.DEBUG)

# console stream handler
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(module)s - %(message)s')

log_handler = logging.FileHandler(constants.logfile, mode='w')
log_handler.setLevel(logging.DEBUG)
log_handler.setFormatter(formatter)

console.setFormatter(formatter)

logger.addHandler(log_handler)

########################### Set Up Argument Parser ###################
def parse_args():
    """Parses the commandline arguments with argparse"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog='IITB-ResumeEditor',
        description='''
            IITB-ResumeEditor is a tool to anytyme change the header of
            resume file; hence allowing students to change it with time
        ''')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help="Silences the output to the terminal;"
                        "Useful when logging behaviour unnecessary")
    
    # sys.version gives more information than we care to print
    py_ver = sys.version.replace('\n', '').split('[')[0]
    parser.add_argument('-v', '--version', action='version',
                        version="{ver_str}\n   python version = {py_v}".format(
                            ver_str=constants.version, py_v=py_ver))
    subparsers = parser.add_subparsers(help='Subcommands', dest='sub')

    # subparser for extract-header
    parser_extract = subparsers.add_parser('extract-header',
                                          help="Extract header from a previous resume"
                                          " Run 'extract-header -h' for"
                                          " header input specifications.")
    parser_extract.add_argument('resume',action='store',
                               help="Resume that contains the header")
    parser_extract.add_argument('pages', action='store',
                               type=int, default=1,
                               help="Number of pages in the passed pdf")
    parser_extract.add_argument('-o', '--output-file', default=None,
                               metavar='FILE',
                               help="Write the report to a file. "
                               "If no file is given the report will be "
                               "printed to a default file name")

    # subparser for merge-resume
    parser_merge = subparsers.add_parser('merge-resume',
                                        help="Create an annotated Dockerfile"
                                        " that will pin the information "
                                        "it finds. Use this option to help "
                                        "achieve a more repeatable "
                                        "container image build.")
    parser_merge.add_argument('header',action='store',
                               help="File that contains the header")
    parser_merge.add_argument('resume',action='store',
                               help="File that contains the resume-content and no header")
    parser_merge.add_argument('pages', action='store',
                               type=int, default=1,
                               help="Number of pages in the passed pdf")
    parser_merge.add_argument('-o', '--output-file', default=None,
                               metavar='FILE',
                               help="Write the report to a file. "
                               "If no file is given the report will be "
                               "printed to a default file name")

    args = parser.parse_args()
    return args

########################### Main Functions ###########################
def makeHead(header_resume, pages, output_header_name):
    ######################## Step 1 ###########################
    # Open a resume already containing the header in it
    headerFile = PyPDF2.PdfFileReader(open(header_resume, "rb"))
    # Select the page of resume file (1st page) that contains the header
    header = headerFile.getPage(0)
    heightPage = header.cropBox.upperRight[1]
    widthPage = header.cropBox.upperRight[0]
    # Crop the header and add it to the writer
    newLowerLeftY = heightPage - constants.header_size(pages)
    header.cropBox.lowerLeft = (0, newLowerLeftY)
    header.mediaBox.lowerRight = (widthPage, 0)

    # Add the page to pdfwriter
    Writer = PyPDF2.PdfFileWriter()
    Writer.addPage(header)
    with open(f"{output_header_name}.pdf", "wb") as headFile:
        # This will print just a cropped header
        Writer.write(headFile)
        logger.info(f"Printed {output_header_name}.pdf")
    ######################## Step 2 ###########################
    # Re-Print it to a temporary file
    cmd = ["pdftocairo", "-nocenter", "-paper", "A4", "-expand", "-pdf",
     f"{output_header_name}.pdf", f"{output_header_name}_temp.pdf"]
    # Now this will print expanded header but towards the bottom of the page
    subprocess.call(cmd)
    logger.info(f"Re-Printed {output_header_name}_temp.pdf")

    ######################## Step 3 ###########################
    # Reopen the re-printed file and tweak it and reprint it
    pg1 = PyPDF2.PdfFileReader(open(f"{output_header_name}_temp.pdf", "rb")).getPage(0)
    pg1.mediaBox.upperLeft = (0, constants.header_size(pages) + 30)
    pg1.mediaBox.lowerRight = (pg1.mediaBox.lowerRight[0], constants.header_size(pages)-heightPage)
    
    pg1.cropBox = pg1.bleedBox = pg1.artBox = pg1.trimBox = pg1.mediaBox
    Writer = PyPDF2.PdfFileWriter()
    Writer.addPage(pg1)
    with open(f"{output_header_name}.pdf", "wb") as headFile:
        # This will print just a cropped header
        Writer.write(headFile)
        logger.info(f"Re-Re-Printed {output_header_name}.pdf")
    ######################## Step 4 ###########################
    # Clean temporary files
    subprocess.call(["rm", f"{output_header_name}_temp.pdf"])
    logger.info(f"Cleaned {output_header_name}_temp.pdf")
    return f"{output_header_name}.pdf"

def editTemplate(resume_header, resume_template, resume_pages, resume_target, header_scaleBy=0.78, *args):
    # Open the template resume file
    templateFile = PyPDF2.PdfFileReader(open(resume_template, "rb"))
    pg1:PyPDF2.pdf.PageObject = templateFile.getPage(0)
    header_pg:PyPDF2.pdf.PageObject = PyPDF2.PdfFileReader(open(resume_header, "rb")).getPage(0)
    header_pg.scaleBy(header_scaleBy)
    heightPage = pg1.cropBox.upperRight[1]
    translateY = constants.header_size(resume_pages,0)-heightPage
    header_pg.mergeRotatedScaledTranslatedPage(pg1,*args,expand=True)
    header_pg.mediaBox.lowerLeft = (header_pg.mediaBox.lowerLeft[0], header_pg.mediaBox.lowerLeft[1]-400) 
    NewWriter = PyPDF2.PdfFileWriter()
    NewWriter.addPage(header_pg)
    if resume_pages==2:
        NewWriter.addPage(templateFile.getPage(1))
    headFile = open(f"{resume_target}.pdf", "wb")
    NewWriter.write(headFile) 
    headFile.close()

def extract_header(args):
    _extract_header = makeHead
    if args.output_file is None:
        output_file = f"header_{args.pages}_{args.resume}"[:-4]
    else:
        output_file = args.output_file if args.output_file[-3:] not in ["pdf", "PDF"] else args.output_file[:-4]
    output_header_file = _extract_header(args.resume, args.pages, output_file)
    return output_header_file

def merge_resume(args):
    _merge_resume = editTemplate
    if args.output_file is None:
        output_file = f"output_{args.pages}_{args.resume}"[:-4]
    else:
        output_file = args.output_file if args.output_file[-3:] not in ['pdf', 'PDF'] else args.output_file[:-4]
    output_resume_file = _merge_resume(args.header, args.resume, args.pages, output_file)
    return output_resume_file

########################### Driver Code ##############################
def main():
    args = parse_args()
    if args.sub == 'extract-header':
         output_header_file = extract_header(args)
    elif args.sub == 'merge-resume':
        output_resume_file = merge_resume(args)
    elif args.sub == 'complete':
        pass
        # output_header_file = extract_header(args)
        # output_resume_file = merge_resume(args)
    else:
        logger.error(f"{args.sub} is not a valid command")

if __name__=="__main__":
    main()