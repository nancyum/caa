#!/usr/bin/python3

# Simbao

import requests
import re
import sys
from bs4 import BeautifulSoup

# The <p> element that is used for a dissertation may have nested elements for
# formatting.  This function flattens it.  It also checks that the nested
# elements are only for formatting.
def flatten_paragraph(e, level):
    if e.string is not None:
        return e.string
    else:
        # One entry had a stray <br> element. Also, <p> element only allowed at
        # the top level.
        if e.name in ["i", "br"] or (e.name == "p" and level == 0):
            return ''.join([flatten_paragraph(child, level + 1) for child in e.contents])
        else:
            print("Paragraph child element not a formatting element: {}.".format(e.name))
            sys.exit(1)

# This function extracts the dissertation information out of a URL for a page
# with dissertations.  The argument is an <a> element that links to the page.
def extract_dissertations_subject(a_elem):

    # Deep in the subject page, it looks like this.
    #
    #      <div class="center-panel">
    #       <h1>
    #        African Art (sub-Saharan)
    #        <br/>
    #        <span style="font-weight:normal">
    #         Dissertations Completed by Subject, 2002
    #        </span>
    #       </h1>
    #       <div class="content">
    #        <!-- This is the first paragraph. -->
    #        <p>
    #         <a href="/dissertations/178/in_progress">
    #          Show in progress dissertations
    #         </a>
    #        </p>
    #        <p>
    #         Adams, Sarah, “Hand to Hand: Uli Body and Wall Painting and Artistic Identity in Southeastern Nigeria” (Yale, R. Thompson)
    #        </p>

    # print(a_elem.string)
    url = "http://www.caareviews.org" + a_elem['href']
    #print(url)
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html5lib")
    #print(soup.prettify())

    # The disseration <p> elements are within an element that matches below.

    # First find the <div class="center-panel"> element.
    elems = soup.find_all('div', class_="center-panel")
    # Check that there is exactly one such element.
    if len(elems) != 1:
        print("Number of div elements with class='center-panel' was not one.")
        sys.exit(1)
    center_panel_elem = elems[0]

    # Next find the <div class="content"> element.  The dissertation paragraphs
    # are within this element.
    elems = center_panel_elem.find_all('div', class_="content")
    if len(elems) != 1:
        print("Number of div elements with class='content' was not one.")
        sys.exit(1)
    content_elem = elems[0]
    #print(content_elem)

    # This element has mixed content, strings and child elements, so we need to
    # do a find_all() on it to get only the paragraph elements.
    content_elem_paragraphs = content_elem.find_all("p")
    # print("Content element paragraphs: ", content_elem_paragraphs)

    # Verify that the first paragraph is as expected and is therefore NOT a
    # dissertation, and is safe to skip.  The checks here are somewhat
    # stringent, to make sure that we don't accidentally miss a dissertation
    # due to unexpected changes to the HTML.
    first_paragraph = content_elem_paragraphs[0]
    # print(first_paragraph)
    if len(first_paragraph.contents) != 1:
        print("First paragraph does not exactly one child.")
        sys.exit(1)
    # The first paragraph should contain an anchor to show the in-progress disserations,
    # so verify that.
    in_progress_anchor = first_paragraph.contents[0]
    if in_progress_anchor.name != "a":
        print("In progress element is not an <a> element.")
        sys.exit(1)
    if len(in_progress_anchor.contents) != 1:
        print("In progress anchor does not have exactly one child.")
        sys.exit(1)
    # Verify that the in-progress URL is as expected.
    in_progress_url = in_progress_anchor['href']
    #print("URL: ", in_progress_anchor['href'])
    if in_progress_url != a_elem['href'].replace('completed', 'in_progress'):
        print("In progress URL not has expected.")
        sys.exit(1)

    # All paragraphs after the first are expected to contain dissserations.
    dissertation_paragraphs = content_elem_paragraphs[1:]
    # print("Dissertation paragraphs:")
    # The dissertation paragraph looks like below.
    #<p>Amor, Joe, Jr., “Defying Structures: Gego and the Crisis of Geometric Abstraction in the Americas” (CUNY, A. Chave) </p>
    # We extract out the components with a regular expression.

    extract_re = re.compile(r"""
     \s*
     ([^,]+), # Last name.
     \s*
     # First name and maybe middle initial.  Note that we include the comma and
     # white space, and strip off later.  This is due to complications like
     # Jr., one entry forgot the comma, etc.
     ([^“]+)
     \s*
     # Title.  Sometimes the directional double quotes are used, other times
     # the straight ones are used.  We try to be lenient, because there seems
     # to be lots of typos.  Hopefully, we are not too lenient.
     # [“"«]([^”"]+)[”"»“«]
     [“”«»"](.+)[“”«»"]
     \s*
     \(([^,]+), # Institution
     \s*
     # Advisor.  Often the last parentheses is missing.
     ([^)]+)\)?
     \s*
     \Z
     """,
     re.VERBOSE|re.DOTALL)
    entries = []
    parse_failed = []
    for child in dissertation_paragraphs:
        # print("    Child element: ", child)
        # print("    Child tag: '{}'".format(child.name))
        s = flatten_paragraph(child, 0)
        # print("        Child string: ", s)
        # There are some empty paragraphs, so make sure that it isn't just white space.
        if not re.match(r"\s*\Z", s):
            m = extract_re.match(s)
            if not m or len(m.groups()) != 5:
                # print("Match failed, on entry: ", s)
                parse_failed.append(s)
            else:
                last_name, first_name, title, institution, advisor = m.groups()
                # Do additional cleanup on first name.  Strip off possible trailing
                # white space and/or comma.
                first_name = re.sub(r"\s*,?\s*$", "", first_name)
                # print("    Last: ", last_name)
                # print("    First: ", first_name)
                # print("    Title: ", title)
                # print("    Institution: ", institution)
                # print("    Advisor: ", advisor)
                # Cleanup all white space, since sometimes there are random newlines, etc.
                result = [re.sub(r'\s+', ' ', s) for s in (last_name, first_name, title, institution, advisor)]
                entries.append(tuple(result))

    return (entries, parse_failed)

# This function scrapes the disseration page for a given year.  Within it, it
# looks like:
#
# <div class="content">
# 
#     <div><a href="/dissertations/485/completed">1500 BCE to 500 BCE</a></div>
# 
#     <div><a href="/dissertations/424/completed">500 BCE to 500 CE</a></div>
# 
#     <div><a href="/dissertations/426/completed">Africa</a></div>
def extract_dissertations_year(year):
    url_format = "http://www.caareviews.org/dissertations/year/{}/completed"
    url = url_format.format(year)
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html5lib")
    #print(soup.prettify())
    # Find all <a> elements where the href matches the pattern.
    elems = soup.find_all('a', href=re.compile("/dissertations/[0-9]+/completed$"))
    rows = []
    failed = []
    for e in elems:
        subject = e.string
        # print("    Subject: ", subject)
        # Extract the dissertations for that subject.
        dissertation_entries, failed_extract = extract_dissertations_subject(e)
        for de in dissertation_entries:
            # Now need to add subject and year to the row.
            last_name, first_name, title, institution, advisor = de
            rows.append((last_name, first_name, title, institution, advisor, subject, year))
        for e in failed_extract:
            failed.append((year, subject, e))
            
    return (rows, failed)

import csv

rows = []
failed = []
# Python ranges are half-open.
for y in range(2004, 2019):
    # print("Year: ", y)
    r, f = extract_dissertations_year(y)
    rows.extend(r)
    failed.extend(f)

print("Dissertations that were unable to be parsed:")
for d in failed:
    print("    ", d)

# Excel will only open the CSV as UTF-8 if the BOM is present.  Using
# encoding='utf-8-sig' will cause the BOM to written.
with open('caa.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
    # Write header.
    writer.writerow([
     "Last Name",
     "First Name",
     "Title",
     "Institution",
     "Advisor",
     "Subject",
     "Year"])
    writer.writerows(rows)

# vim: set ai ts=4 sw=4 et:
