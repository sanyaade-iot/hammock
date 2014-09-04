#
# The MIT License (MIT)
#
# Copyright (c) 2014 SIMPLETHINGS, INC
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
import xml.etree.ElementTree as ET
import sys
import re
import os

class ToC:
    # List of (keyword, hyperlink) pairs
    # For example: "(Get Company Information", "docs/company_resource.html#get_company_information")
    # The list is sorted by keyword length (longest first), so that "Update a
    # Device" will always be made a hyperlink before "Device", for example.
    autolinks = []
    _elems = []

    _html = ""
    _script = ""

    def __init__(self, elem, pagemode="single"):
        self.gen(elem)

    def gen(self, elem):
        out = "<div class='hammock-toc-outer'>"
        out += "<div class='hammock-toc-title'>Contents</div>"
        out += self._toc_parse_element(elem)
        out += "</div>"
        self._html = out
        self.autolinks = sorted(self.autolinks, key=lambda x: -len(x[0]))
        return out

    def script(self):
        out = """
<script>
function get_scroll_y() {
    return window.pageYOffset || document.body.scrollTop || document.html.scrollTop;
}
function get_element_scroll_y(id) {
    return document.getElementById(id).offsetTop;
}

function update_scroll() {
    var y = get_scroll_y();

        """
        for elem in self._elems:
            out += "document.getElementById('" + self._toc_id(elem) + "').style.fontWeight = '';";
            out += "document.getElementById('" + self._toc_id(elem) + "').style.backgroundColor = '';";

        out += """
    if (0) {
    }
    """

        for elem in reversed(self._elems):
            out += """
            else if (y + 32 > get_element_scroll_y('""" + self._id(elem) + """')) {
                document.getElementById('""" + self._toc_id(elem) + """').style.fontWeight = "bold";
                document.getElementById('""" + self._toc_id(elem) + """').style.backgroundColor = "#d0d0d0";
            }
            """

        out += """
}
window.onload = function() {
    window.addEventListener("scroll", update_scroll);
}
</script>
"""
        return out


    def html(self):
        return self._html

    def _href(self, elem):
        if elem.tag == "chapter" or elem.tag == "section":
            return "#" + file_namify(elem.attrib["title"])

    def _id(self, elem):
        if elem.tag == "chapter" or elem.tag == "section":
            return file_namify(elem.attrib["title"])

    def _toc_id(self, elem):
        if elem.tag == "chapter" or elem.tag == "section":
            return "toc_" + file_namify(elem.attrib["title"])

    def _toc_parse_element(self, elem):
        out = ""
        if elem.tag == "chapter":
            out += "<div id='" + self._toc_id(elem) + "' class='hammock-toc-chapter'><a href='" + self._href(elem) + "'>" + elem.attrib["title"] + "</a></div>"
            self.autolinks.append((elem.attrib["title"], self._href(elem)))
            self._elems.append(elem)
            if "autolinks" in elem.attrib:
                keywords = elem.attrib["autolinks"].split(",")
                for keyword in keywords:
                    self.autolinks.append((keyword, self._href(elem)))
        elif elem.tag == "section":
            out += "<div id='" + self._toc_id(elem) + "' class='hammock-toc-section'><a href='" + self._href(elem) + "'>" + elem.attrib["title"] + "</a></div>"
            self.autolinks.append((elem.attrib["title"], self._href(elem)))
            self._elems.append(elem)
            if "autolinks" in elem.attrib:
                keywords = elem.attrib["autolinks"].split(",")
                for keyword in keywords:
                    self.autolinks.append((keyword, self._href(elem)))
        elif elem.tag == "subsection":
            out += ""
        
        for child in elem:
            out += self._toc_parse_element(child)

        return out
        

    def _toc_parse_children(self, elem):
        out = ""
        for child in elem:
            out += self._parse_element(toc, child)
            if child.tail != None:
                out += child.tail
        return out


    # Replaces the names of chapters & sections anywhere in <text> with a
    # hyperlink to the documentation for that chapter or section.
    #
    # Returns the modified string.
    def autolink(self, text):
        out = text
        for (needle, link) in self.autolinks:
            polluted = ""
            for char in needle:
                polluted = polluted + char + "<!---->"
            out = out.replace(needle, "<a href=" + link + ">" + polluted + "</a>")
        return out

#
# Convert <s> to a string that can be used as a filename.
#
# >>> file_namify("List Users")
# list_users
#
def file_namify(s):
    s = re.sub(r'\s', "_", s)
    s = s.lower()
    return s

def _gen_chapter_page(toc, elem):
    html = ""
    with open('out.html', "w") as f:
        f.write(html)

def fixup_text(text, toc):
    text = escape(text)
    text = toc.autolink(text)
    return text;

def escape(text):
    # replace "<" with "&lt;"
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text;

def fixup_code(text):
    out = ""

    # Determine indentation of first non-blank line.  Then subtract that much
    # indentation from each line.
    lines = escape(text).split("\n")
    for line in lines:
        if line.strip() != "":
            shift = len(line) - len(line.lstrip())
            break
            
    for line in lines:
        out += line[shift:] + "\n"

    return out.strip()


def parse_doc(toc, elem):
    return """
<html>
    <head>
        <link href='hammock-custom.css' rel='stylesheet' type='text/css'>
        """ + toc.script() + """
    </head>
    <body>
        """ + toc.html() + """
        <div class=hammock-doc-outer>
            <div class=hammock-doc-header>
                <img src='""" + elem.attrib['logo'] + """'></img>""" + elem.attrib['title'] + """<br>
            </div>
            """ + _parse_inner_xml(toc, elem) + """
        </div>
        <br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>
    </body>
<html>"""

def parse_chapter(toc, elem, multipage=False):
    if multipage:
        contents = ""
    else:
        return """
            <div class=hammock-chapter-outer>
                <a id=""" + file_namify(elem.attrib["title"]) + """ name=""" + file_namify(elem.attrib["title"]) + """></a>
                <div class=hammock-chapter-title>
                    """ + elem.attrib["title"] + """
                </div>
                <div class=hammock-chapter-contents>
                    """ + _parse_inner_xml(toc, elem) + """
                </div>
            </div>"""

def parse_section(toc, elem):
    return """
        <div class=hammock-section-outer>
            <a id=""" + file_namify(elem.attrib["title"]) + """ name=""" + file_namify(elem.attrib["title"]) + """></a>
            <div class=hammock-section-title>
                """ + elem.attrib["title"] + """
            </div>
            <div class=hammock-section-contents>
                """ + _parse_inner_xml(toc, elem) + """
            </div>
        </div>"""

def parse_subsection(toc, elem):
    return """
        <div class=hammock-subsection-outer>
            <div class=hammock-subsection-title>
                """ + elem.attrib["title"] + """
            </div>
            <div class=hammock-subsection-contents>
                """ + _parse_inner_xml(toc, elem) + """
            </div>
        </div>"""

def parse_subsubsection(toc, elem):
    return """
        <div class=hammock-subsubsection-outer>
            <div class=hammock-subsubsection-title>
                """ + elem.attrib["title"] + """
            </div>
            <div class=hammock-subsubsection-contents>
                """ + _parse_inner_xml(toc, elem) + """
            </div>
        </div>"""

def parse_b(toc, elem):
    return "<b>" + fixup_code(elem.text + _parse_children(toc, elem)) + "</b>"


def parse_icode(toc, elem):
    return "<span class=hammock-icode>" + fixup_code(elem.text + _parse_children(toc, elem)) + "</span>"

def parse_code(toc, elem):
    return "<div class=hammock-code>" + fixup_code(elem.text + _parse_children(toc, elem)) + "</div>"

def parse_i(toc, elem):
    out = "<i>"
    out += _parse_inner_xml(toc, elem)
    out += "</i>"
    return out

def parse_ul(toc, elem):
    out = "<ul>"
    out += _parse_children(toc, elem)
    out += "</ul>"
    return out

def parse_li(toc, elem):
    out = "<li>"
    out += _parse_inner_xml(toc, elem)
    out += "</li>"
    return out

def parse_tbl(toc, elem):
    template = "default"
    if "template" in elem.attrib:
        template = elem.attrib["template"]

    out = ""
    if template == "get_fields":
        out += "<table cellspacing=0 cellpadding=0 border=0 class=hammock-tbl>"
        out += "     <tr>"
        out += "         <td class=hammock-tbl-header>Field</td>"
        out += "         <td class=hammock-tbl-header>Datatype</td>"
        out += "         <td class=hammock-tbl-header>Description</td>"
        out += "     </tr>"
        out += _parse_inner_xml(toc, elem)
        out += "</table>"
    elif template == "query_params":
        out += "<table cellspacing=0 cellpadding=0 border=0 class=hammock-tbl>"
        out += "     <tr>"
        out += "         <td class=hammock-tbl-header>Parameter</td>"
        out += "         <td class=hammock-tbl-header>Required?</td>"
        out += "         <td class=hammock-tbl-header>Datatype and Validation</td>"
        out += "         <td class=hammock-tbl-header>Description</td>"
        out += "     </tr>"
        out += _parse_inner_xml(toc, elem)
        out += "</table>"
    else:
        out += "<table cellspacing=0 cellpadding=0 border=0 class=hammock-tbl>"
        out += _parse_inner_xml(toc, elem)
        out += "</table>"

    return out

def parse_row(toc, elem):
    out = "<tr>"
    out += _parse_inner_xml(toc, elem)
    out += "</tr>"
    return out

def parse_cell(toc, elem):
    nowrap = ""
    if "nowrap" in elem.attrib:
        nowrap = "nowrap"
    if "header" in elem.attrib:
        out = "<td " + nowrap + " class=hammock-tbl-header>"
    else:
        out = "<td " + nowrap + ">"
    out += _parse_inner_xml(toc, elem)
    out += "</td>"
    return out

def _parse_element(toc, elem):
    funcname = "parse_" + elem.tag
    if funcname in globals():
        return globals()["parse_" + elem.tag](toc, elem)
    else:
        return "<span class=hammock-interpret-error>&lt;" + elem.tag + "&gt;</span>"
        

def _parse_children(toc, elem):
    out = ""
    for child in elem:
        out += _parse_element(toc, child)
        if child.tail != None:
            out += child.tail
    return out

def _parse_inner_xml(toc, elem):
    out = ""
    if elem.text != None:
        out += fixup_text(elem.text, toc)
    for child in elem:
        out += _parse_element(toc, child)
        if child.tail != None:
            out += fixup_text(child.tail, toc)
    return out

def create_output_directory(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)

def gen_single_page(toc, elem):
    dirname = "out/"
    create_output_directory(dirname)
    destfile = open(dirname + "single_page.html", "w")
    if not destfile:
        print "FATAL: Could not open " + dirname + "single_page.html for write."
        return

    contents = _parse_element(toc, elem)
    destfile.write(contents)
    destfile.close()


def main():
    pageMode = "single" # | "chapters" | "sections"
    tree = ET.parse(sys.argv[1])
    root = tree.getroot()
    toc = ToC(root)
    gen_single_page(toc, root)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "usage: python hammock.py <xmlfilename>"
        sys.exit(0)
    main()
