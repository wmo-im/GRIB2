import os
import csv
import glob
import json
from shutil import move

source_file = r"gribTemplates-notesMaster.csv"

note_id_name = "noteID"
#note_id_name = "master note id" 

mapper = {}
with open(source_file,encoding="utf8") as f:
    reader = csv.DictReader(f, delimiter=',', quotechar='"')
    for row in reader:
        key = "{octet}-{template}".format(**row)
        val = row[note_id_name]
        
        mapper[key]= [val,] if not key in mapper else  mapper[key] + [val,]
 
 
#print(json.dumps(mapper,indent=4))
        
files = glob.glob("*Template_en.csv")

for file in files:
    #print("processing {}".format(file))
    with open(file,encoding="utf8") as f:
        reader = csv.DictReader(f, delimiter=',', quotechar='"')
        new_file = file+".tmp"
        with open(new_file,"w",encoding="utf8",newline='') as f_out:
            idx = reader.fieldnames.index("Note_en")
            new_fieldnames = reader.fieldnames[0:idx+1 ] + ["noteIDs",] + reader.fieldnames[idx+1:]
            writer = csv.DictWriter(f_out, delimiter=",", quotechar='"',fieldnames=new_fieldnames )
            writer.writeheader()
            for row in reader:
                try:
                    base = os.path.basename(file)
                    key = "{}-{}".format(row["OctetNo"], base.replace(".csv",""))
                    row["noteIDs"] = ",".join(mapper[key]) if key in mapper else ""
                    writer.writerow(row)
                except ValueError as ve:
                    print(ve)
                    print(row)
                    
    move(new_file,file)
