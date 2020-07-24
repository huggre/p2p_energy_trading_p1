# Integrating physical devices with IOTA — Peer-to-peer energy trading with IOTA Part 1

## The 18th part in a series of beginner tutorials on integrating physical devices with the IOTA protocol.

![Image for post](https://miro.medium.com/max/4032/1*B7Q5-su5CfoNDKMpJzzYBQ.jpeg)

## Introduction

This is the 18th part in a series of beginner tutorials where we explore integrating physical devices with the IOTA protocol. This will be a two part tutorial where we look at using the IOTA token as the settlement currency in a peer-to-peer energy trading solution. In the first part we will focus on monitoring real time power consumption and making payments accordingly. In the second part we will look at dealing with variable energy prices.

*Note!*
*In this first tutorial the solar panel is optional as we will primarily be focusing on the circuit between the energy provider batteries and the end customer.*

------

## The Use Case

Lately our hotel owner have been thinking about installing some new garden lights in the backyard of his hotel. Only problem is that there is no electricity available to power the lights in that particular area of the garden. When discussing this problem with his next door neighbor, the neighbor explains that he has a solar power system near by, and that he might be able to provide the additional electricity if he is compensated for the extra cost of scaling up his existing system. This sounds like the perfect solution, but one question still remains; how do they deal with payments so that it reflects actual power usage, and at the same eliminate the manual burden of monitoring usage and dealing with manual payments?

After thinking about this problem for a while the hotel owner pitches the following idea to his neighbor:

------

## The proposal

1. First we take a Raspberry PI with an attached power monitoring sensor and puts it in the power circuit between the neighbors solar batteries and the hotel owners new garden lights.
2. Then, every second we have the PI take a reading from the sensor and log the current power usage.
3. Then, at some predefined period of time (lets say one hour) we calculate the average power usage for that period and multiply with the time (one hour) and the energy price in IOTA’s they both agree upon.
4. Finally, after each period (one hour), the PI automatically creates a new IOTA transaction and transfers the calculated IOTA tokens from the hotel manager to the neighbors receiver address before starting a new period.

Fortunately, the neighbor likes the idea so let’s start building :-)

*Note!
If we wanted to implement this use case on a true scale we would probably have to work with higher voltages such as 12V and above. However, to minimize the cost of components and at the same time focusing on safety, we scale everything down to a low voltage circuit. After all,* **no one should be playing around with high voltage circuits unless they absolutely know what they are doing***.*

------

## The components

First, lets take a quick look at the different hardware components used in this project.

Beside the Raspberry PI itself and some wires to hook it all up, we need the following components:

**INA219 current/voltage/power sensor**
The INA219 is a low cost current/voltage/power sensor that comes in the form of a breakout board that easily connects to the Raspberry PI’s GPIO pins. You should be able to get the INA219 sensor off ebay or amazon for less that 10 USD.

![Image for post](https://miro.medium.com/max/400/0*34I8XPROPk8_0LWd.jpg)

**Potentionmeter**
A potentionmeter is basically a variable resistor placed in the circuit to simulate variable power usage. Replacing the potentionmeter with some switchable LED’s or an adjustable DC motor would work equally well. Only reason i decided to go with the potentionmeter was to minimize the number of parts and connections in my circuit.

![Image for post](https://miro.medium.com/max/320/0*Rjnm7a1zAIUgGVkB.jpg)

**Resistor**
The resistor is placed in front of the LED to limit the current going in to the LED. Powering the LED directly from the battery without a resistor could damage the LED. A 200 to 500 Ohm resistor should work fine depending on the type of LED.

![Image for post](https://miro.medium.com/max/444/0*R3p5Hh4su5SUifze.jpg)

**LED**
The LED represents the garden lights in our use case. Turning the potentionmeter, we can adjust the amount of current going in to the LED, and thereby the amount of light it produces.

![Image for post](https://miro.medium.com/max/442/0*XpYQsCXOsnn4_H9b.jpg)

**Battery**
Finally we need a small battery with enough voltage to light up our LED (about 3V depending on the LED)

![Image for post](https://miro.medium.com/max/320/0*XFhVe2O6AbA1PI-e)

*Note!*
*In the second part of this tutorial we will be adding a solar panel together with a diode to charge our battery. Let’s look at those components in the next tutorial.*

------

## The wiring diagram

And here is a simple diagram that shows how to connect the circuit.

![Image for post](https://miro.medium.com/max/1225/1*3HQ9eqw1v2HfD8lB-1sPAQ.png)

*Note!*
*As discussed previously, the solar panel together with the diode is optional in this tutorial and can be excluded from the circuit.*

------

## Required Software and libraries

The following Python libraries are required for this project.

The [PyOTA library](https://github.com/iotaledger/iota.py) for communicating with the IOTA tangle.

The [INA219 library](https://pypi.org/project/pi-ina219/) for communicating with the INA219 sensor.

------

## The Python Code

The Python code for this project is pretty straight forward so i will not go into details except pointing out some important variables.

The **pay_frequency** variable defines the period in seconds from where we calculate the average power consumption and issues the IOTA payment transaction.

The **mW_price** variable specifies the price of IOTA’s per milliwatt/second (mW/s) of energy. Any decimals from the calculated IOTA transaction value are removed as we can not send fractions of an IOTA.

*Note!*
*As we are dealing with very low power usage in this small circuit it is more convenient for us to be working with milliwatts (mW) instead of the typical watts or kilowatts.*

```python
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
```

You can download the code from [here](https://gist.github.com/huggre/23a2db302eb7adb8b7e71fe3dc7e06cf)

------

## Running the project

To run the project, you first need to save the Python code from the previous section to your machine.

To execute the code, simply start a new terminal window, navigate to the folder where you saved the file and type:

**python** [**p2p_energy_trade.py**](https://gist.github.com/huggre/23a2db302eb7adb8b7e71fe3dc7e06cf)

You should now see the current LED power usage printed to the terminal every second. Notice how the value changes as you turn the potentionmeter.

Every 60 seconds, the average power usage for the last period (60 seconds) is calculated and printed to the monitor before an IOTA value (payment) transaction is created and sent to the tangle.

------

## Whats next?

In the second part of this tutorial we will take a look at managing variable energy prices, which is a common problem that must be addressed when dealing with renewable energy sources such as solar, wind, hydro etc.

------

## Contributions

If you would like to make any contributions to this tutorial you will find a Github repository [here](https://github.com/huggre/p2p_energy_trading_p1)

------

## Donations

If you like this tutorial and want me to continue making others feel free to make a small donation to the IOTA address below.

![Image for post](https://miro.medium.com/max/382/0*JSb0LwJEBYpCYhQA.png)

NYZBHOVSMDWWABXSACAJTTWJOQRPVVAWLBSFQVSJSWWBJJLLSQKNZFC9XCRPQSVFQZPBJCJRANNPVMMEZQJRQSVVGZ
