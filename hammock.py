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
        if elem.tag == "doc":
            toc_title = "Contents"
            if "toc_title" in elem.attrib:
                toc_title = elem.attrib["toc_title"]
            out += "<div class='hammock-toc-title'>" + toc_title + "</div>"
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

def fixup_code(toc, text):
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

    out = toc.autolink(out)
    return out.strip()


# Returns tuple:
#   (HEAD_HTML, TOC_HTML, CONTENTS_HTML)
def parse_doc(toc, elem):
    return (
        "<link href='hammock-custom.css' rel='stylesheet' type='text/css'>" + toc.script(),
        toc.html(),
        "<div class=hammock-doc-outer>" + _parse_inner_xml(toc, elem) + "</div>"
    )

def parse_chapter(toc, elem, multipage=False):
    if multipage:
        contents = ""
    else:
        return """
            <div class=hammock-chapter-outer>
                <a class=hammock-a-name id=""" + file_namify(elem.attrib["title"]) + """ name=""" + file_namify(elem.attrib["title"]) + """></a>
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
            <a class=hammock-a-name id=""" + file_namify(elem.attrib["title"]) + """ name=""" + file_namify(elem.attrib["title"]) + """></a>
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

def parse_a(toc, elem):
    text = elem.text
    if text == None:
        text = ""

    return "<a " + write_all_attribs(elem) + ">" + text + _parse_children(toc, elem) + "</a>"

def parse_b(toc, elem):
    return "<b>" + fixup_text(elem.text + _parse_children(toc, elem), toc) + "</b>"

def parse_p(toc, elem):
    return "<p>" + _parse_inner_xml(toc, elem) + "</p>"

def parse_icode(toc, elem):
    return "<span class=hammock-icode>" + fixup_code(toc, elem.text + _parse_children(toc, elem)) + "</span>"

def parse_code(toc, elem):
    cssClass = "hammock-code"
    if "syntax" in elem.attrib:
        cssClass += " sh_" + elem.attrib['syntax'];
    return "<pre class='" + cssClass + "'>" + fixup_code(toc, elem.text + _parse_children(toc, elem)) + "</pre>"

def parse_output(toc, elem):
    cssClass = "hammock-output"
    if "syntax" in elem.attrib:
        cssClass += " sh_" + elem.attrib['syntax'];
    return "<pre class='" + cssClass + "'>" + fixup_code(toc, elem.text + _parse_children(toc, elem)) + "</pre>"

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

# html_tuple is:
#   (HEAD_HTML, TOC_HTML, CONTENT_HTML)
def _apply_template(template, html_tuple):
    out = template.replace("{HAMMOCK_HEAD}", html_tuple[0])
    out = out.replace("{HAMMOCK_TOC}", html_tuple[1])
    out = out.replace("{HAMMOCK_CONTENTS}", html_tuple[2])
    return out

def gen_single_page(outdir, outfilename, templateFilename, toc, elem):
    if outdir[-1] != "/":
        outdir += "/"
    create_output_directory(outdir)
    destfile = open(outdir + outfilename, "w")
    if not destfile:
        print "FATAL: Could not open " + outdir + outfilename + " for write."
        return

    (head, toc, contents) = _parse_element(toc, elem)

    template = """
<html>
    <head>
        {HAMMOCK_HEAD}
    </head>
    <body>
        {HAMMOCK_TOC}
        {HAMMOCK_BODY}
    </body>
</html>"""

    if templateFilename != "":
        with open(templateFilename) as templateFile:
            template = templateFile.read()

    html = _apply_template(template, (head, toc, contents))
    destfile.write(html)
    destfile.close()


def get_option(args, argname, default):
    for arg in args:
        if arg.startswith(argname):
            return arg.split("=")[1]
    return default

def get_arg(args, idx):
    for arg in args:
        if arg.startswith("-"):
            continue
        if idx == 0:
            return arg
        idx = idx -1
    return None

def write_all_attribs(elem):
    out = ""
    for attrib in elem.attrib:
        out += attrib + "=\"" + elem.attrib[attrib] + "\" "
    return out

def main(infilename):
    outdir = get_option(sys.argv, "--outdir", "out/")
    template = get_option(sys.argv, "--template", "")
    outfilename = ".".join(infilename.split(".")[0:-1]) + ".html"
    pageMode = "single" # | "chapters" | "sections"
    tree = ET.parse(infilename)
    root = tree.getroot()
    toc = ToC(root)
    gen_single_page(outdir, outfilename, template, toc, root)

if __name__ == "__main__":
    infilename = get_arg(sys.argv, 1)
    if infilename == None:
        print "usage: python hammock.py [<OPTIONS>] <XMLFILENAME>"
        print "options:"
        print "   --outdir=/path/to/outdir"
        print "   --template=templatefile"
        sys.exit(0)
    main(infilename)
