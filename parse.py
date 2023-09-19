import csv, re, time
import json
import os
from sys import exit

import tkinter
from tkinter import filedialog

VERSION = 2.3
WelcomeMsg = f"\t\tProvisioning Audit Tool v{VERSION}\n"

root = tkinter.Tk()
root.withdraw() #use to hide tkinter window
WORKDIR=None

def ask_auditfiles_directory_path():
    currdir = os.getcwd()
    tempdir = filedialog.askdirectory(parent=root, initialdir=currdir, title='Please select a directory')

    if len(tempdir) > 0:
        #print ("You chose: %s" % tempdir)
        return tempdir + "/"
    else:
        return None


def parse_pg(filepath, outputfile=None):
    # define a list with a CSV header
    requests = [
                    ['Dials','Status','Total','Total-TICK215','Total-APN586','Total-TICK190','Total-TICK201','Total-NOT CONNECTED','Failed','Total-TICK214','Total-TICK203','Total-TICK205']
               ]
    requests_count=0
    requests_failed=0
    requests_tick=0
    requests_tickk=0
    requests_ttick=0
    requests_tick14=0
    requests_tick3=0
    requests_tick5=0
    requests_apn=0
    requests_stats=0
    with open(filepath,'r') as file:
        tick_found=False
        tick215_found=False
        tick190_found=False
        tick201_found=False
        stats_found=False
        apn_found=False
        tick214_found=False
        tick203_found=False
        tick205_found=False

        for line in file:
            if "hgsdp:msisdn=" in line.lower():
                matches = re.findall(r"\d+", line.lower().split("hgsdp:msisdn")[1]) #Use regex only on the part which contains the phone number
                requests_count+=1
                requests.append([matches[0]])

            if "586                           83    NO             IPV4    15" in line:
                apn_found=True
                requests_apn+=1

            if (not tick_found):
                if "TICK-215" in line:
                    tick215_found=True
                    tick_found=True
                    requests_tick+=1

                if "TICK-190" in line:
                    tick190_found=True
                    tick_found=True
                    requests_tickk+=1

                if "TICK-201" in line:
                    tick201_found=True
                    tick_found=True
                    requests_ttick+=1

                if "TICK-214" in line:
                    tick214_found=True
                    tick_found=True
                    requests_tick14+=1

                if "TICK-203" in line:
                    tick203_found=True
                    tick_found=True
                    requests_tick3+=1

                if "TICK-205" in line:
                    tick205_found=True
                    tick_found=True
                    requests_tick5+=1

            if "NOT CONNECTED" in line:
                stats_found=True
                requests_stats+=1

            if line.startswith("END"):
                reqstatus = []
                if apn_found:
                    reqstatus.append("APN586")
                if tick215_found:
                    reqstatus.append("TICK-215")
                if tick190_found:
                    reqstatus.append("TICK-190")
                if tick201_found:
                    reqstatus.append("TICK-201")
                if stats_found:
                    reqstatus.append("NOT CONNECTED")
                if tick214_found:
                    reqstatus.append("TICK-214")
                if tick203_found:
                    reqstatus.append("TICK-203")
                if tick205_found:
                    reqstatus.append("TICK-205")

                if (stats_found):
                    requests_failed+=1
                elif (not apn_found and not tick_found):
                    #print("Failed: " +" "+ str(requests[requests_count]) +" "+ str(tick215_found) +" "+str(tick190_found) +" "+ str(tick201_found) +" "+ str(tick214_found) +" "+ str(tick203_found) +" "+ str(tick205_found))
                    requests_failed+=1

                if not reqstatus:
                    reqstatus.extend(["Failed"])

                requests[requests_count].extend([(",").join(reqstatus)])
                tick215_found=False
                tick190_found=False
                tick201_found=False
                stats_found=False
                apn_found=False
                tick_found=False
                tick214_found=False
                tick203_found=False
                tick205_found=False

    #['Dials','Status','Total','Total-TICK215','Total-APN586','Total-TICK190','Total-TICK201','Total-NOT CONNECTED','Failed','Total-TICK214','Total-TICK203','Total-TICK205']
    try:
        requests[1].extend([requests_count,requests_tick,requests_apn,requests_tickk,requests_ttick,requests_stats,requests_failed,requests_tick14,requests_tick3,requests_tick5])
    except:
        print(requests_count)

    if outputfile is not None:
        # Write All rows to a csv file
        with open(outputfile, "w", newline="") as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerows(requests)

    return requests

def parse_mtas(filepath, outputfile=None):
    # define a list with a CSV header
    requests = [
                    ['Dials','Status','Have DCF','Total','Success','Failed','Failed (excl. login failed)','Total Have DCF']
               ]
    requests_count=0
    requests_failed=0
    requests_loginfailed=0
    requests_have_dcf=0
    with open(filepath,'r') as file:
        for line in file:
            if "----------------Request for " in line:
                matches = re.findall(r"\d+", line)
                requests_count+=1
                requests.append([matches[0],'Success','False'])

            if "id=\"DCF" in line:
                requests_have_dcf+=1
                requests[requests_count][2] = "True"

            if line.startswith("<respCode>"):
                matches = re.findall(r"\d+", line)
                requests[requests_count][1] = f"Failed ({matches[0]})"
                requests_failed+=1
                if matches[0] == '1095':
                    requests_loginfailed+=1

    # Insert "Total, Success, Failed" at row number 2
    requests[1].extend([requests_count,
                        requests_count-(requests_failed-requests_loginfailed),
                        requests_failed,
                        requests_failed-requests_loginfailed,
                        requests_have_dcf
                        ])
    if outputfile is not None:
        # Write All rows to a csv file
        with open(outputfile, "w", newline="") as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerows(requests)

    return requests

def parse_ism(filepath, outputfile=None):
    # define a list with a CSV header
    requests = [
                    ['Dials','Status','Total','Success','Failed']
               ]
    requests_count=0
    requests_failed=0
    with open(filepath,'r') as file:
        for line in file:
            if "----------------Request for " in line:
                matches = re.findall(r"\d+", line)
                requests_count+=1
                requests.append([matches[0],'Success'])

            if line.startswith("<faultcode>"):
                matches = re.findall(r"\d+", line)
                requests[requests_count][1] = f"Failed ({matches[0]})"
                requests_failed+=1

    # Insert "Total, Success, Failed" at row number 2
    requests[1].extend([f'{requests_count}',f'{requests_count-requests_failed}',f'{requests_failed}'])

    if outputfile is not None:
        # Write All rows to a csv file
        with open(outputfile, "w", newline="") as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerows(requests)

    return requests

def parse_enum(filepath, outputfile=None):
    # define a list with a CSV header
    requests = [
                    ['Dials','Status','Total','Success','Failed']
               ]
    requests_count=0
    requests_failed=0
    with open(filepath,'r', encoding='utf-16-le') as file:
        for line in file:
            if "list enumdnsched -where enumDn=" in line:
                matches = re.findall(r"\d+", line)
                requests_count+=1
                requests.append([matches[0],'Success'])

            if line.startswith("No matching object(s) found"):
                requests[requests_count][1] = "Failed"
                requests_failed+=1

    # Insert "Total, Success, Failed" at row number 2
    requests[1].extend([f'{requests_count}',f'{requests_count-requests_failed}',f'{requests_failed}'])

    if outputfile is not None:
        # Write All rows to a csv file
        with open(outputfile, "w", newline="") as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerows(requests)

    return requests


alldata = {}

def read_dials_from_file(ema_path, pg_path, ism_path, mtas_path, enum_path):
    # Get Dials from file
    with open(ema_path,'r') as file:
        for line in file:
            matches = re.findall(r"\d+", line)
            if len(matches) == 0:
                #print(f"skipping line: {line}")
                pass
            else:
                try:
                    alldata["20" + matches[0]] = {'PG':"", "ISM":"", "MTAS":"", "DCF":"", "ENUM":""}
                except:
                    print(f"Wrong entry found: {matches}")
                    pass

    # Process ENUM Values
    enum_data=None
    if enum_path:
        enum_data = parse_enum(enum_path)
        try:
            for entry in enum_data[1:]:
                if entry[0] in alldata:
                    alldata[entry[0]]['ENUM']=entry[1]
                else:
                    print(f"ENUM: ignoring line: \"{entry}\"")
        except:
            print("ENUM ERROR: Faulty dial:" + str(entry))

    # Process ISM Values
    ism_data=None
    if ism_path:
        ism_data = parse_ism(ism_path)
        try:
            for entry in ism_data[1:]:
                if entry[0] in alldata:
                    alldata[entry[0]]['ISM']=entry[1]
                else:
                    print(f"ISM: ignoring line: \"{entry}\"")
        except:
            print("ISM ERROR: Faulty dial:" + str(entry))

    # Process MTAS Values
    mtas_data=None
    if mtas_path:
        mtas_data = parse_mtas(mtas_path)
        try:
            for entry in mtas_data[1:]:
                if entry[0] in alldata:
                    alldata[entry[0]]['MTAS']=entry[1]
                    try:
                        alldata[entry[0]]['DCF']=entry[2]
                    except:
                        alldata[entry[0]]['DCF']="Error"
                        print(entry)
                else:
                    print(f"MTAS: ignoring line: \"{entry}\"")
        except:
            print("MTAS ERROR: Faulty dial:" + str(entry))

    # Process PG Values
    pg_data=None
    if pg_path:
        pg_data = parse_pg(pg_path)
        try:
            for entry in pg_data[1:]:
                if entry[0] in alldata:
                    alldata[entry[0]]['PG']=entry[1]
                else:
                    print(f"PG: ignoring line: \"{entry}\"")
        except:
            print("PG ERROR: Faulty dial:" + str(entry))

    # Write All results to a file
    with open(WORKDIR+'Dials_analysis.csv', 'w', newline="") as csv_file:
        writer = csv.writer(csv_file)
        # Extract CSV Header from dict
        valuesAsList = list(alldata.values())
        subkeylist = list(valuesAsList[0].keys())
        csvheader = ["Dials"]
        csvheader = csvheader + (subkeylist)
        writer.writerow(csvheader)
        # Write alldata from dict to CSV
        for key, value in alldata.items():
            if isinstance(value, dict):
                writer.writerow([key, value['PG'], value['ISM'], value['MTAS'], value['DCF'], value['ENUM']])
            else:
                print("***skip***")
                print(key)
                print(value)
                print("****")
    #['Dials','Status','Total','Total-TICK215','Total-APN586','Total-TICK190','Total-TICK201','Total-NOT CONNECTED','Failed','Total-TICK214','Total-TICK203','Total-TICK205']
    # Summary
    summary_text= ["Summary:\n"                   ]

    if pg_data:
        summary_text.append(f"PG:\n\tTotal:{pg_data[1][2]}\n\tTICK215:{pg_data[1][3]}\n\tAPN586:{pg_data[1][4]}\n\tTICK-190:{pg_data[1][5]}\n\tTICK-201:{pg_data[1][6]}\n\tNOT CONNECTED:{pg_data[1][7]}\n\tFailed:{pg_data[1][8]}\n\tTICK-214:{pg_data[1][9]}\n\tTICK-203:{pg_data[1][10]}\n\tTICK-205:{pg_data[1][11]}\n")
    if ism_data:
        summary_text.append(f"ISM:\n\tTotal:{ism_data[1][2]}\n\tSuccess:{ism_data[1][3]}\n\tFailed:{ism_data[1][4]}\n")
    if mtas_data:
        summary_text.append(f"MTAS:\n\tTotal:{mtas_data[1][3]}\n\tSuccess:{mtas_data[1][4]}\n\tFailed:{mtas_data[1][5]}\n\tFailed (excl. login failed):{mtas_data[1][6]}\n\tHave DCF:{mtas_data[1][7]}\n")
    if enum_data:
        summary_text.append(f"ENUM:\n\tTotal:{enum_data[1][2]}\n\tSuccess:{enum_data[1][3]}\n\tFailed:{enum_data[1][4]}\n")
    for line in summary_text:
        print(line)

    with open(WORKDIR+"summary.txt", "w", newline="") as summary_file:
        summary_file.writelines(summary_text)

#parse_ism(r"C:\Users\admin\Desktop\OMAR_DIALS\ISM_omar_D", "ism.csv")
#parse_mtas(r"D:\Provisioning_Auto\MTAS_BT8_1711", "mtas.csv")
#parse_pg(r"C:\Users\admin\Desktop\OMAR_DIALS\OMAR_Dials.txt.log","pg.csv")
#parse_enum(r"C:\Users\admin\Desktop\OMAR_DIALS\R1IPW07_2022-11-22_2_56_04 PM.log", "enum.csv")
print(WelcomeMsg)

WORKDIR = ask_auditfiles_directory_path()
if WORKDIR is None:
    exit(1)
else:
    print ("Processing files from: ", WORKDIR)

pg_path= WORKDIR+"PG"
mtas_path= WORKDIR+"MTAS"
ism_path= WORKDIR+"ISM"
enum_path1= WORKDIR+"ENUM"

if not os.path.isfile(pg_path) and not os.access(pg_path, os.R_OK):
    pg_path= None
if not os.path.isfile(ism_path) and not os.access(ism_path, os.R_OK):
    ism_path= None
if not os.path.isfile(mtas_path) and not os.access(mtas_path, os.R_OK):
    mtas_path= None
if not os.path.isfile(enum_path1) and not os.access(enum_path1, os.R_OK):
    enum_path1= None
if not os.path.isfile(WORKDIR+"Batch.csv") and not os.access(WORKDIR+"Batch.csv", os.R_OK):
    print(f"ERROR: Batch.csv is not found in {WORKDIR}")
    exit(1)

read_dials_from_file(WORKDIR+"Batch.csv",
                                    pg_path=pg_path,
                                    mtas_path=mtas_path,
                                    ism_path=ism_path,
                                    enum_path=enum_path1)
os.system('pause')
