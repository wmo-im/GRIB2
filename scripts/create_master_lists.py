import csv, re, sys, argparse
import dicttoxml

from os import listdir
from os.path import isfile, join
from xml.dom.minidom import parseString
from datetime import datetime


def load_files(pattern,basedir="."):
    files = [f for f in listdir(basedir) if isfile(join(basedir,f)) and pattern in f ]

    return files 
  
class CSVWriter:


    def __init__(self,outfile,headers):
    
        csvfile_out = open(outfile, "w" , encoding="utf8",newline='')
        self.csvwriter = csv.DictWriter(csvfile_out, delimiter=",", quotechar='"', fieldnames=headers )
        self.csvwriter.writeheader()
        
        
    def write_row(self,row):
        # minimal change: remove fields not in fieldnames (octetCount) to avoid error
        for key in list(row.keys()):
            if key not in self.csvwriter.fieldnames:
                del row[key]
        self.csvwriter.writerow(row)


    def close(self):
        pass
        #self.csvwriter.close()
    

    
class XMLWriter:

    xmlheader = '<dataroot xmlns:od="urn:schemas-microsoft-com:officedata" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'


    def __init__(self,outfile,elements,item_name):
        
        self.outfile = outfile
        self.elements = elements
        self.item_name = item_name
        
        self.element_list = []
        
    def write_row(self,row):
        row_copy = {}
        for k in self.elements:
            row_copy[k] = row[k]
            
        self.element_list.append(row_copy)

        
    def close(self):
        with open(self.outfile,"w",encoding="utf8") as xmlfile:

            my_item_func = lambda x: self.item_name

            xml = dicttoxml.dicttoxml(self.element_list,attr_type=False,item_func=my_item_func,custom_root="dataroot")
            dom = parseString(xml)

            xml = dom.toprettyxml()
            xml = xml.replace("<dataroot>",  self.xmlheader.replace("###ITEM_NAME###",self.item_name))
            
            xmlfile.write(xml)            

  
    
def process_files(files,pattern,writers,title_prefix):
        
    rows=[]
    for f in files:
        #print(f)
        m1=re.match(r"GRIB2_(CodeFlag|Template)_(\d+)_(\d+)_(\d+)_(\d+)_(.*)_en\.csv".format(pattern),f)
        if m1 is not None:
           print(m1)
           major_nr = m1.group(2)
           minor_nr = m1.group(3)
           title_prefix = m1.group(6)
        else:
            m2=re.match(r"GRIB2_(CodeFlag|Template)_(\d+)_(\d+)_(.*)_en\.csv".format(pattern),f)
            print(m2)
            major_nr = m2.group(2)
            minor_nr = m2.group(3)
            title_prefix = m2.group(4)
        
        # 
        r = re.findall('[A-Z]',title_prefix)
        idxs = [ title_prefix.find(c) for c in r ] + [len(title_prefix),]
            
        parts = []
        prev_idx = 0
        for i in range(1,len(idxs)):
            parts.append(title_prefix[prev_idx:idxs[i]])
            prev_idx=idxs[i]
        
        parts = [parts[0],] + [p.lower() for p in parts[1:] ]
        
        nr = "{} {}.{}".format(" ".join(parts),major_nr,minor_nr)
        
        csvfile = open(f,encoding="utf8")
        csvreader = csv.DictReader(csvfile, delimiter=',', quotechar='"',)
        for row in csvreader:
            #row["No"]="{:.1f}".format(i)
            row["Title_en"] =  nr + " - " + row["Title_en"] 
            
            rows.append(row)
    
    # sort rows here
    decorated = []
    
    if pattern == 'GRIB2_CodeFlag':
        for i,row in enumerate(rows):
            m = re.search(r'(\d+)\.(\d+)',row['Title_en'])
            m2 = re.search(r'discipline (\d+)',row['SubTitle_en'])
            m3 = re.search(r'category (\d+):',row['SubTitle_en'])
            
            subtitle_order = int(m2.group(1)) if m2 else 0
            subtitle_order2 = int(m3.group(1)) if m3 else 0
            
            if m: 
                decorated.append((int(m.group(1)),int(m.group(2)),subtitle_order,subtitle_order2,i,row))
            else:
                decorated.append((0,0,0,0,i,row))
            
    elif pattern == 'GRIB2_Template':
        for i,row in enumerate(rows):
            m = re.search(r'(\d+)\.(\d+)',row['Title_en'])
            m2 = re.search(r'(\d+)-?(\d+)?',row["OctetNo"])
            
            octet_order = int(m2.group(1)) if m2 else 0
            if m:
                decorated.append((int(m.group(1)),int(m.group(2)),octet_order,0,i,row))
            else:
                decorated.append((0,0,0,0,i,row))
            
    decorated.sort()
    rows = [row for *_,row in decorated]
    
    
    for row in rows:
        for writer in writers:
            writer.write_row(row)            
                
    for writer in writers:
        writer.close()
   
if __name__ == "__main__":
    
    # not implemented yet
    parser = argparse.ArgumentParser()
    parser.add_argument('-x', '--xml', default=False)
    parser.add_argument('-c', '--csv', default=False)
    parser.add_argument('-cf', '--codeflag', default=False)
    parser.add_argument('-te', '--template', default=False)
    
    parser.add_argument('-v', dest='verbose', action='store_true')
    args = parser.parse_args()
    

    files = load_files("GRIB2_CodeFlag",basedir=".")

    # CodeFlag tables
    fieldnames=["Title_en","SubTitle_en","CodeFlag","Value","MeaningParameterDescription_en","Note_en","noteIDs","UnitComments_en","Status"]    
    csv_writer = CSVWriter("txt/CodeFlag.txt",fieldnames)
    
    xml_elements=["Title_en","SubTitle_en","CodeFlag","MeaningParameterDescription_en","Status"]
    xml_writer = XMLWriter("xml/CodeFlag.xml",xml_elements,"GRIB2_CodeFlag_en")

    writers = [csv_writer,xml_writer]
    process_files(files,"GRIB2_CodeFlag",writers,"Code Table")
            
    # Template tables
    template_files = load_files("GRIB2_Template",basedir=".")

    fieldnames=["Title_en","OctetNo","Contents_en","Note_en","noteIDs","codeTable","flagTable","Status"]    
    csv_writer = CSVWriter("txt/Template.txt",fieldnames)
    
    xml_elements=["Title_en","OctetNo","Contents_en","Note_en","noteIDs","codeTable","flagTable","Status"]
    xml_writer = XMLWriter("xml/Template.xml",xml_elements,"GRIB2_Template_en")

    writers = [csv_writer,xml_writer]
    process_files(template_files,"GRIB2_Template",writers,"Identification template")


