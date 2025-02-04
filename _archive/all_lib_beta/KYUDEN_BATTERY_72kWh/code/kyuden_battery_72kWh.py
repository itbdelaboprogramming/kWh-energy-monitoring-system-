"""
#title           :kyuden_battery_72kWh.py
#description     :modbus library for Kyuden Battery (BMS) 72kWh
#author          :Nicholas Putra Rihandoko
#date            :2023/05/09
#version         :0.1
#usage           :Energy Monitoring System
#notes           :
#python_version  :3.7.3
#==============================================================================
"""
import time

# FUNCTION CODE PYMODBUS SYNTAX
# 0x03 (3) = read_holding_registers
# 0x04 (4) = read_input_registers
# 0x06 (6) = write_register
# 0x10 (16) = write_registers

# the memory addresses are in 1 hex increment

class node:
    def __init__(self,unit,name,client,delay=300):
        self._unit                      = unit
        self._name                      = name
        self._client                    = client
        self._client_transmission_delay = delay/1000    # in seconds 
        # Write commands that is available, add if needed
        self._write_dict = {
            "write_something_register":     {"fc":0x06, "address":0xFFFF, "param":0x0700},
            "write_something_registers":    {"fc":0x10, "address":0x200C, "scale":10},
            "write_something_registers2":    {"fc":0x10, "address":0x200C}}       

    def reset_read_attr(self):
        # Reset (and/or initiate) object's attributes
        for attr_name, attr_value in vars(self).items():
            if not isinstance(attr_value, list):
                if not attr_name.startswith("_"):
                    setattr(self, attr_name, 0)
        self.Module_Voltage             = [0 for _ in range(16)]
        self.Cell_Voltage               = [[0 for _ in range(12)] for _ in range(16)]
        self.Module_Temperature         = [[0 for _ in range(3)] for _ in range(16)] # only three values

    def handle_sign(self,register):
        # Handle negative byte values
        signed_values = []
        for data in register:
            if data >= 0x8000:
                signed_value = -((data ^ 0xFFFF) + 1)  # Two's complement conversion
            else:
                signed_value = data
            signed_values.append(signed_value)
        return signed_values

    def save_read(self,response,save,num):
        reg = self.handle_sign(response.registers)
        # Save responses to object's attributes
        if save == 1:
            self.Count_Module           = reg[0]
            self.Count_Module_Series    = reg[1]
            self.Count_Module_Parallel  = reg[2]
            self.Count_CMU              = reg[3]
        if save == 2:
            self.Status                 = reg[0]
            self.Error                  = reg[1]
            self.SOC                    = reg[2]        # %
            self.Total_Voltage          = reg[3]/10     # Volts
            self.Cell_Voltage_max       = reg[4]/1000   # Volts
            self.Cell_Voltage_min       = reg[5]/1000   # Volts
            self.Cell_Voltage_avg       = reg[6]/1000   # Volts
            self.Temperature_max        = reg[7]-55  # deg Celcius
            self.Temperature_min        = reg[8]-55  # deg Celcius
            self.Temperature_avg        = reg[9]-55  # deg Celcius
            self.Balance_Voltage        = reg[10]/1000   # Volts
            self.Balance_Voltage_diff   = reg[11]/1000  # Volts
            self.Mode                   = reg[12]
        if save == 3:
            self.Module_Voltage[num]            = reg[0]/1000        # Volts
            for c in range(len(self.Cell_Voltage[0])):
                self.Cell_Voltage[num][c]       = reg[c+1]/1000      # Volts
            self.Module_Temperature[num][0]     = reg[13]-55      # deg Celcius
            self.Module_Temperature[num][1]     = reg[14]-55      # deg Celcius
        if save == 4:
            for m in range(len(self.Module_Voltage)):
                self.Module_Temperature[m][2]   = reg[m]-55       # deg Celcius

    def reading_sequence(self,fc,address,count,save,num=None):        
        # Send the command and read response with function_code 0x03 (3) or 0x04 (4)
        if fc == 0x03:
            response = self._client.read_holding_registers(address=address, count=count, unit=self._unit)
        if fc == 0x04:
            response = self._client.read_input_registers(address=address, count=count, unit=self._unit)
        self.save_read(response,save,num)
        time.sleep(self._client_transmission_delay)
        return response

    def writting_sequence(self,fc,address,param):
        if param == None:
            print(" -- no parameter to be written, command was not completed --")
            return None
        # Send the command with function_code 0x06 (6) or 0x10 (16)
        if fc == 0x06:
            response = self._client.write_register(address=address, value=param, unit=self._unit)
        if fc == 0x10:
            # convert parameter input into two 4 bit hexadecimal format
            hex_param = hex(param)[2:].zfill(8)
            values = [val for val in [int(hex_param[i:i+4], 16) for i in (0, 4)]]
            response = self._client.write_registers(address=address, values=[values[1]], unit=self._unit)
        time.sleep(self._client_transmission_delay)
        return response

    def send_command(self,command,param=None):
        # Send the command and read response with function_code 0x03 (3)
        if command == "read_others":
            fc = 0x03
            #response = self.reading_sequence(fc=fc, address=0x0000, count=16, save=1)
            #print("-- read is a success --")
            return
  
        # Send the command and read response with function_code 0x04 (4)
        if command == "read_measurement":
            fc = 0x04
            response = self.reading_sequence(fc=fc, address=0x1003, count=4, save=1)
            response = self.reading_sequence(fc=fc, address=0x1010, count=13, save=2)
            response = self.reading_sequence(fc=fc, address=0x1100, count=16, save=3, num=0)
            response = self.reading_sequence(fc=fc, address=0x1110, count=16, save=3, num=1)
            response = self.reading_sequence(fc=fc, address=0x1120, count=16, save=3, num=2)
            response = self.reading_sequence(fc=fc, address=0x1130, count=16, save=3, num=3)
            response = self.reading_sequence(fc=fc, address=0x1140, count=16, save=3, num=4)
            response = self.reading_sequence(fc=fc, address=0x1150, count=16, save=3, num=5)
            response = self.reading_sequence(fc=fc, address=0x1160, count=16, save=3, num=6)
            response = self.reading_sequence(fc=fc, address=0x1170, count=16, save=3, num=7)
            response = self.reading_sequence(fc=fc, address=0x1180, count=16, save=3, num=8)
            response = self.reading_sequence(fc=fc, address=0x1190, count=16, save=3, num=9)
            response = self.reading_sequence(fc=fc, address=0x11A0, count=16, save=3, num=10)
            response = self.reading_sequence(fc=fc, address=0x11B0, count=16, save=3, num=11)
            response = self.reading_sequence(fc=fc, address=0x11C0, count=16, save=3, num=12)
            response = self.reading_sequence(fc=fc, address=0x11D0, count=16, save=3, num=13)
            response = self.reading_sequence(fc=fc, address=0x11E0, count=16, save=3, num=14)
            response = self.reading_sequence(fc=fc, address=0x11F0, count=16, save=3, num=15)
            response = self.reading_sequence(fc=fc, address=0x1200, count=16, save=4)
            #print("-- read is a success --")
            return
        
        # start writting sequence to send command with function_code 0x06 (6) or 0x10 (16)
        if self._write_dict.get(command) is not None:
            com = self._write_dict[command]
            if com.get("param") is not None:
                response = self.writting_sequence(fc=com["fc"], address=com["address"], param=com["param"])
            else:
                if com.get("scale") is not None:
                    response = self.writting_sequence(fc=com["fc"], address=com["address"], param=param*com["scale"])
                else:
                    response = self.writting_sequence(fc=com["fc"], address=com["address"], param=param)
            #print(response)
            #print(" -- write is a success --") 
            pass
        else:
            print("-- unrecognized command --")
            return