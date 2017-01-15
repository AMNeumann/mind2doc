
import sys, os.path, shelve
from argparse import ArgumentParser
import xml.etree.ElementTree as ET

class ReqIdMapper:
    def __init__(self, filename):
        self.shelf = shelve.open(filename)
        if len(self.shelf) > 0:
            self.maxId = max(self.shelf.values())
        else:
            self.maxId = 1
        
    def getId(self, rawId):
        try:
            return self.shelf[rawId]
        except KeyError:
            self.shelf[rawId] = self.maxId + 1
            self.maxId += 1
            return self.shelf[rawId]
        
    def close(self):
        self.shelf.close() 

class PlainTextExporter:
    def __init__(self, reqFileName):
        self.reqIdMapper = ReqIdMapper(reqFileName)
        
    def close(self):
        self.reqIdMapper.close()
        
    def printHeading(self, text, depth):
        return text + "\n\n"
    
    def printRequirement(self, text, identifier):
        return "Requirement " + str(identifier) + ": " + text + "\n\n"
        
    def printElement(self, elt, depth=0):
        ret = ""
        if len(elt) == 0:
            ret += elt.attrib["TEXT"] + '\n\n'
        
        headingDone = False
        for child in elt:
            if child.tag == 'font':
                if 'BOLD' in child.attrib and child.attrib['BOLD'] == 'true':
                    ret += self.printHeading(elt.attrib["TEXT"], depth)
                    headingDone = True
                elif 'ITALIC' in child.attrib and child.attrib['ITALIC'] == 'true':
                    ret += self.printRequirement(elt.attrib['TEXT'], self.reqIdMapper.getId(elt.attrib['ID']))
            elif child.tag == 'node':
                if not headingDone:
                    ret += elt.attrib["TEXT"] + '\n\n'
                    headingDone = True
                ret += self.printElement(child, depth=depth + 1)
        
        return ret


class MarkDownExporter(PlainTextExporter):
    def printHeading(self, text, depth):
        if depth > 5:
            print("Nesting too deep, Markdown will not produce the expected result.")
        return '#' * (depth + 1) + " " + text + '\n\n'
        
                
class WikiExporter(PlainTextExporter):
    def printHeading(self, text, depth):
        return 'h%i. %s\n\n' % (depth + 1, text)
    

if __name__ == "__main__":
    parser = ArgumentParser(description="Translate freemind file to document")
    parser.add_argument("FILE", help="Input file")
    parser.add_argument("-t", "--plaintext", action="store_true", help="Export to plaintext")
    parser.add_argument("-m", "--markdown", action="store_true", help="Export to Markdown")
    parser.add_argument("-w", "--wiki", action="store_true", help="Export to Wiki")


    args = parser.parse_args()

    if not args.plaintext and not args.markdown and not args.wiki:
        print("No export format specified!")
        parser.print_help()
        sys.exit(1)

    if not args.FILE:
        print("Missing input file!")
        parser.print_help()
        sys.exit(1)
    
    reqFilename = os.path.splitext(os.path.basename(args.FILE))[0] + '.req'    
    exporters = []
    if args.plaintext:
        exporters.append((PlainTextExporter(reqFilename), ".txt"))
    
    if args.markdown:
        exporters.append((MarkDownExporter(reqFilename), ".md"))
        
    if args.wiki:
        exporters.append((WikiExporter(reqFilename), ".wiki"))

    tree = ET.parse(args.FILE)
    root = tree.getroot()
    firstnode = None
    
    for exporter, suffix in exporters:
        filename = os.path.splitext(os.path.basename(args.FILE))[0] + suffix
        ofp = open(filename, "w")
        for child in root:
            if child.tag == 'node':
                ofp.write(exporter.printElement(child))
