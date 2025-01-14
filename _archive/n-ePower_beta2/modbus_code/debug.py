"""
#title           :debug.py
#description     :debugging functions for PyModbus, used through main.py file
#author          :Nicholas Putra Rihandoko
#date            :2023/05/12
#version         :0.1
#usage           :Modbus programming in Python
#notes           :
#python_version  :3.7.3
#==============================================================================
"""

import logging
import datetime
import csv
import os

def debugging():
    # Print the python library's process log for troubleshooting
    logging.basicConfig()
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

def print_response(server,cpu_temp,timer):
    #return
    # Print the object's attribute, uncomment as needed
    for i in range(len(server)):
        print(server[i]._name, "MEASUREMENTS")
        print("Time             :", timer.strftime("%d/%m/%Y-%H:%M:%S"))
        print("CPU Temperature  :", cpu_temp, "degC")
        for attr_name, attr_value in vars(server[i]).items():
            if not isinstance(attr_value, list):
                if "SOC" in attr_name:
                    print(attr_name, "=", attr_value, "%")
                elif "Frequency" in attr_name:
                    print(attr_name, "=", attr_value, "Hz")
                elif "Voltage" in attr_name:
                    print(attr_name, "=", attr_value, "Volts")
                elif "Current" in attr_name:
                    print(attr_name, "=", attr_value, "Amps")
                elif "Power" in attr_name:
                    print(attr_name, "=", attr_value)
                elif ("Ah" in attr_name) or ("Wh" in attr_name) or ("Arh" in attr_name):
                    print(attr_name, "=", attr_value)
                elif "Temperature" in attr_name:
                    print(attr_name, "=", attr_value, "degC")
                elif "Count" in attr_name:
                    print(attr_name, "=", attr_value)
            else:
                #continue
                if not isinstance(attr_value[0], list):
                    print(attr_name, "=", attr_value)
                else:
                    for i in range(len(attr_value)):
                        print(attr_name, i+1, "=", attr_value[i])
        print("")

def get_cpu_temperature():
    # Read CPU temperature from file
    with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
        temp = round(float(f.read().strip())/1000,1)
    return temp

def strval(array):
    # Change an array into a string (used to upload array value into MySQL database)
    string = " ".join(map(str, array))
    return string

def mtemp(array):
    # Simplify a nested array into normal array (only picking the necessary values)
    var = [array[0][0], array[2][0], array[4][0], array[6][0],
            array[8][0], array[10][0], array[12][0], array[14][0]]
    return var

def get_bootup_time():
    # Used to gat the startup timestamp of the script
    time = datetime.datetime.now()
    return time
bootup_time = get_bootup_time()

def get_time(db, timer):
    global bootup_time
    # Read the previous timestamps from database
    read_c1 = ("SELECT startup_date, startup_time, total_uptime, shutdown_date, shutdown_time, total_downtime, downtime FROM `machine_data_exp` ORDER BY id DESC LIMIT 1")
    with db.cursor() as read:
        read.execute(read_c1)
        data_datetime = read.fetchall()
        if len(data_datetime) == 0 or None in data_datetime:
            # In case of no previous data, initiate the values
            prev_startup = bootup_time
            total_uptime = datetime.timedelta(seconds=0)
            prev_update = timer
            total_downtime = datetime.timedelta(seconds=0)
            downtime = datetime.timedelta(seconds=0)
        else:
            # Change the format into suitable timedate objects
            for data in data_datetime:
                prev_startup = datetime.datetime.combine(data[0], datetime.datetime.min.time()) + data[1]
                total_uptime = data[2]
                prev_update = datetime.datetime.combine(data[3], datetime.datetime.min.time()) + data[4]
                total_downtime = data[5]
                downtime = data[6]

    # calculate the time difference and culmulative period from the timestamps
    uptime = (timer - bootup_time)
    if abs(bootup_time - prev_startup) < datetime.timedelta(seconds=60):
        total_uptime = total_uptime + abs(timer - prev_update)
    else:
        downtime = abs(bootup_time - prev_update)
        total_downtime = total_downtime + downtime
    return [uptime, total_uptime, downtime, total_downtime]

def update_database(server,db,cpu_temp,timer):
    global bootup_time
    #return
    # Define MySQL queries which will be used in the program
    add_c1 = ("INSERT INTO `dataparameter`"
                "(dc_bus_v_ref, power_supply_vol, power_supply_current, "
                "dc_bus_side_power, power_supply_freq, power_factor, "
                "electric_power_kwh, regene_power_kwh, out_freq, "
                "out_current, out_vol_ref, out_power, "
                "soc, total_vol, cell_avg_vol, "
                "avg_temp, dataentered, CPU_temp, "
                "power_supply_side_power) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
    try:
        # Write data in database
        db.cursor().execute(add_c1,
                (server[1].DC_Voltage_command, server[1].AC_Voltage, server[1].AC_Current,
                server[1].DC_Power_kW, server[1].AC_Frequency, server[1].Power_Factor,
                server[1].Consumed_Energy_kWh, server[1].Consumed_Energy_kWh, server[2].Output_Frequency,
                server[2].Output_Current, server[2].Output_Voltage_ref, server[2].Output_Power_kW,
                server[0].SOC, server[0].Total_Voltage, server[0].Cell_Voltage_avg,
                server[0].Temperature_avg, timer.strftime("%Y-%m-%d %H:%M:%S"), cpu_temp,
                server[1].AC_Power_kW))
        db.commit()
        print("<===== Data is sent to database =====>")
        print("")
    except BaseException as e:
        # Print the error message
        print("Cannot update MySQl database")
        print("problem with -->",e)
        print("<===== ===== continuing ===== =====>")
        print("")

def is_valid_date(date_string):
    # Check if a string is in correct format date
    try:
        datetime.datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        return True
    except ValueError:
        return False

def log_in_csv(server,cpu_temp,timer,first_row=False):
    global bootup_time
    #return
    # Define the directory of the backup file and the data to be logged
    directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'save/modbus_log.csv')
    
    # Check how long has the data been logged
    with open(directory, 'r') as file:
        csv_log = csv.reader(file)
        # Read the line in the CSV file
        for row in csv_log:
            if len(row) > 0:
                csv_date = row[0]
                if is_valid_date(csv_date):
                    # Calculate the difference in weeks
                    log_date = datetime.datetime.strptime(csv_date, '%Y-%m-%d %H:%M:%S')
                    timediff = (timer - log_date).days
                    # Clean the CSV file if the difference is more than 1 month
                    if timediff > 31:
                        with open(directory, 'w') as clean_file:
                            clean_file.write('')
                    break

    # Write new data into csv file
    with open(directory, mode='a', newline='') as file:
        line = csv.writer(file, delimiter =',')
        if first_row:
            column_title = ["DateTime", "RPi_Temp"]
            line.writerow(column_title)
        else:
            data = [timer.strftime("%Y-%m-%d %H:%M:%S"), cpu_temp]
            line.writerow(data)