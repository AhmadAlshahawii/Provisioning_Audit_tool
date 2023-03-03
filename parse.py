import csv, re, time
import json


def parse_pg(filepath, outputfile=None):
    # define a list with a CSV header
    requests = [
                    ['Dials','Status','Total','Total-TICK215','Total-APN586','Failed']
               ]
    requests_count=0
    requests_failed=0
    requests_tick=0
    requests_apn=0
    with open(filepath,'r') as file:
        tick_found=False
        apn_found=False
        for line in file:
            if "hgsdp:msisdn=" in line.lower():
                matches = re.findall(r"\d+", line.lower().split("hgsdp:msisdn")[1]) #Use regex only on the part which contains the phone number
                requests_count+=1
                requests.append([matches[0]])
            
            if "TICK-215" in line:
                tick_found=True
                requests_tick+=1
            
            if "586                           83    NO             IPV4    15" in line:
                apn_found=True
                requests_apn+=1
                
            if line.startswith("END"):
                reqstatus = []
                if apn_found:
                    reqstatus.append("APN")
                if tick_found:    
                    reqstatus.append("TICK-215")
                if (not apn_found or not tick_found):
                    requests_failed+=1

                if not reqstatus:
                    reqstatus.extend(["Failed"])

                requests[requests_count].extend([(",").join(reqstatus)])
                tick_found=False
                apn_found=False
    try:    
        requests[1].extend([requests_count,requests_tick,requests_apn,requests_failed])
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
    ism_data = parse_ism(ism_path)
    try:
        for entry in ism_data[1:]:
            if entry[0] in alldata:
                alldata[entry[0]]['ISM']=entry[1]
            else:
                print(f"ISM ignoring line: \"{entry}\"") 
    except:
        print("ISM ERROR: Faulty dial:" + str(entry))
        
    # Process MTAS Values
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
    with open('Dials_analysis.csv', 'w', newline="") as csv_file:  
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
    
    # Summary
    summary_text= ["Summary:\n",
                    f"PG:\n\tTotal:{pg_data[1][2]}\n\tTICK215:{pg_data[1][3]}\n\tAPN586:{pg_data[1][4]}\n\tFailed:{pg_data[1][5]}\n",
                    f"ISM:\n\tTotal:{ism_data[1][2]}\n\tSuccess:{ism_data[1][3]}\n\tFailed:{ism_data[1][4]}\n",
                    f"MTAS:\n\tTotal:{mtas_data[1][3]}\n\tSuccess:{mtas_data[1][4]}\n\tFailed:{mtas_data[1][5]}\n\tFailed (excl. login failed):{mtas_data[1][6]}\n\tHave DCF:{mtas_data[1][7]}\n",
                    f"ENUM:\n\tTotal:{enum_data[1][2]}\n\tSuccess:{enum_data[1][3]}\n\tFailed:{enum_data[1][4]}"
    ]

    for line in summary_text:
        print(line)

    with open("summary.txt", "w", newline="") as summary_file:
        summary_file.writelines(summary_text)

#parse_ism(r"C:\Users\admin\Desktop\OMAR_DIALS\ISM_omar_D", "ism.csv")
#parse_mtas(r"D:\Provisioning_Auto\MTAS_BT8_1711", "mtas.csv")
#parse_pg(r"C:\Users\admin\Desktop\OMAR_DIALS\OMAR_Dials.txt.log","pg.csv")
#parse_enum(r"C:\Users\admin\Desktop\OMAR_DIALS\R1IPW07_2022-11-22_2_56_04 PM.log", "enum.csv")
read_dials_from_file(r"Batch_EMA.csv",  pg_path=r"PG.txt.log",
                                        mtas_path=r"MTAS", 
                                        ism_path=r"ISM", 
                                        enum_path=r"ENUM.log")