#!/usr/bin/env python

# Import INA219 library
from ina219 import INA219
from ina219 import DeviceRangeError

# Import time
from time import sleep

# Import PyOTA library
import iota
from iota import Address

# Hotel owner IOTA seed used for payment transaction
# Replace with your own devnet seed
seed = b"YOUR9SEED9GOES9HERE"

# Solar panel owner reciever address
# Replace with your own devnet reciever address
addr = "MICIKTVQFXDBZARARUUBXY9OBFDCOFBTYXGOWBWYFZIPYVZVPDLMBVKRF9EUSFASVECRT9PBVBMWMZWADPWZPDDLOD"

# URL to IOTA fullnode used when interacting with the Tangle
iotaNode = "https://nodes.devnet.iota.org:443"

# Define IOTA api object
api = iota.Iota(iotaNode, seed=seed)

# Define and configure INA219 sensor
SHUNT_OHMS = 0.1
ina = INA219(SHUNT_OHMS)
ina.configure()

# Function for retrieving current power consumption from INA219 sensor
def get_current_mW():
    try:
        current_mW = ina.power()
        print("Current Power Consumption: %.3f mW" % current_mW)
        return current_mW
    except DeviceRangeError as e:
        print(e)

# Function for sending IOTA payment
def pay(payment_value):
    
    # Display preparing payment message
    print('Preparing payment of ' + str(payment_value) + ' IOTA to address: ' + addr + '\n')
               
    # Create transaction object
    tx1 = iota.ProposedTransaction( address = iota.Address(addr), message = None, tag = iota.Tag(iota.TryteString.from_unicode('HOTELIOTA')), value = payment_value)

    # Send transaction to tangle
    print('Sending transaction..., please wait\n')
    SentBundle = api.send_transfer(depth=3,transfers=[tx1], inputs=None, change_address=None, min_weight_magnitude=9)       

    # Display transaction sent confirmation message
    print('Transaction sendt...\n')
    
# Define some variables
pay_frequency = 60
pay_counter = 0
accumulated_mW = 0.0
mW_price = 0.2 # 0.2 IOTA's per mW/s

# Main loop that executes every 1 second
while True:
    
    # Check if payment round has been completed 
    if pay_counter == pay_frequency:
        
        # Calculate average power consumption for this round
        average_mW = accumulated_mW / pay_frequency
        print("*** Avearge Power Consumption: %.3f mW" % average_mW)
        
        # Calculate IOTA payment based on current mW price and average power consumption
        # Discard any decimals
        pay_value = int((average_mW * pay_frequency)*mW_price)
               
        # Send IOTA payment
        pay(pay_value)
        
        # Reset and prepare for next payment round
        accumulated_mW = 0.0
        pay_counter = 0
       

    # Get current power consumption
    current_mW = get_current_mW()
    
    # Add current power consumption to accumulated power consumption 
    accumulated_mW = accumulated_mW + current_mW 
    
    # Increase pay counter
    pay_counter = pay_counter +1
    
    # Wait for one second before taking a new reading
    sleep(1)
