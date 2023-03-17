# How to connect to a M5 over CLI (via MQTT)

We've prepared a couple example files to demonstrate the functionality of this repository and it's intended to be used mostly by developers, but the purpose of this guide is to get the average user to the point where they can run the example files on their machine and actually interface with the printer.

The long term plan is to create a standalone CLI printer interface utility from the groundwork laid out here in this repository and transition that work to a new repository for distribution.

This guide is only written for Windows and MacOS since the AnkerMake slicer is required to be installed and is only natively supported on those two platforms at the time of writing this. If you're on Linux, chances are you don't need step-by-step instructions on this and you definitely had to set up Wine to run the slicer.

[TOC]

## Prerequisites

In order to run these scripts, you'll need to install some supporting software onto your machine (don't worry, it's really easy). Namely, you'll need Python 3, some pip packages (stands for "pip Install Packages" This is the Python package manager that comes bundled with Python), and the AnkerMake slicer.

### Windows (Python 3, and pip packages)

1. Install the AnkerMake slicer from [their website](https://www.ankermake.com/software). Make sure you open it and login, then you can close the app.

2. Using `git` or GitHub Desktop, clone this repository into a location of your choice and then navigate to that location in File Explorer.

3. Hold down the "Shift" key and right-click on some empty space in the repository top level folder. Select "Open in Terminal" from the context menu dropdown. (If the following commands do not work, try re-opening your terminal window as administrator and use the `cd` command to navigate to where you cloned this repository to)

4. Enter in the following command to install/check Python 3:

   ```powershell
   python3
   ```

   Now, one of two things will happen:

   - The first possibility is that the Microsoft Store will open and prompt you to install Python 3.10. You can do that and that's a perfectly fine way to install Python 3 (it's the method I used) or you can go to the [Python website](https://www.python.org/downloads/) and install it from there. Either way works, do whichever you prefer. Enter in the above command again after and you should see what's in the next bullet.

   - The other possibility is that you get a message similar to this:

     ```
     Python 3.10.10 (tags/v3.10.10:aad5f6a, Feb  7 2023, 17:20:36) [MSC v.1929 64 bit (AMD64)] on win32
     Type "help", "copyright", "credits" or "license" for more information.
     >>>
     ```

     This means you already have Python 3 installed and are good to go on to the next step. Enter in the following command to exit out of the Python 3 runtime environment.

     ```python
     quit()
     ```

5. Enter in the following command to install the required pip packages:

   ```
   pip3 install -r requirements.txt
   ```

   If required, enter `Y` to all installation prompts.

### MacOS (Python 3, and pip packages)

1. Install the AnkerMake slicer from [their website](https://www.ankermake.com/software). Make sure you open it and login, then you can close the app.

2. Using `git` or GitHub Desktop, clone this repository into a location of your choice and then navigate to that location in Finder.

3. Hold down the "Control" key and click the folder in the path bar, then choose "Open in Terminal". (If you don’t see the path bar at the bottom of the Finder window, choose View > Show Path Bar)

4. Install Python3 from the [Python website.](https://www.python.org/downloads/macos/)

5. Enter in the following command to install the required pip packages:

   ```
   pip3 install -r requirements.txt
   ```

   If required, enter `Y` to all installation prompts.



## Extracting your Auth Token

Your Auth Token is the "key to the kingdom" so-to-speak. The M5 uses this to verify who can connect to it over the internet (or LAN) to make sure it's actually you or someone you've shared your printer with (although, we haven't done any testing with shared printers so that's more of an educated guess). You're printer will refuse any connections that don't present your unique Auth Token, so let's get that out for future use.

1. Navigate to wherever you cloned this repository to. Open the "examples" folder and open a terminal window there, just like in the previous section.

2. Type in the following command:

   ```bash
    python3 extract-auth-token.py -a
   ```

   You should get back a long sequence of numbers and letters, that's your Auth Token. Copy that to the clipboard for use in the next section.



## Connecting to your M5 over MQTT

Now here comes the fun part, we have everything we need to actually connect to the printer. It uses the [MQTT standard](https://mqtt.org/), to communicate with the wider world. It is possible to use this standard coupled with this repository build a tool that can remotely monitor the printer, print files, execute movement commands, pre-heat the printer, initiate the Auto-Bed Leveling routine, and just about anything else the companion phone app can. In this example, we'll simply be monitoring the printer. We can also save the output to a log file if desired.

1. Navigate to wherever you cloned this repository to. Open the "examples" folder and open a terminal window there, just like in the previous section.

2. Type in the following command, but replace "YOUR_AUTH_TOKEN_HERE" with your actual Auth Token and no quotes:

   ```bash
   python3 mqtt-connect.py -r us -A "YOUR_AUTH_TOKEN_HERE"
   ```

3. **[Optional Step]** If desired, you can save the contents of the output to a log file by adding `> output.log` to the end of the command in the previous step:

   ```bash
   python3 mqtt-connect.py -r us -A "YOUR_AUTH_TOKEN_HERE" > output.log
   ```

Now you should see a bunch of data updating in your terminal, this happens in 1 second intervals. It should look something like this and will be quite a bit more colorful:

```
TOPIC [/phone/maker/YOUR_SERIAL_NUMBER_HERE/notice]
4d41c1000501020546c00100045b126436353163383633612d366266652d313033622d396234372d35623534393334336637356100000000000000000000000080d48d67e412394ccc2ef9d76b966687e047c862d36ca291d70a7c732aec8f28e7a315dc1dab0fc51eed678bee3959ae14af8ef3670553412e13cc90a0a6d2c4c0a949f072a716ef9153eed115eb7a7decf9c88bcb07922bae5cc925a96e954b1f70dfb55b079b696178f2c918c0af5c9e5861ae7809b97b80614cec6e948f86cc
MqttMsg(
    size=193,
    m3=5,
    m4=1,
    m5=2,
    m6=5,
    m7=70,
    packet_type=<MqttPktType.Single: 192>,
    packet_num=1,
    time=1678924548,
    device_guid='SOME_DATA_HERE',
    data=b'[{"commandType":1003,"currentTemp":5263,"targetTemp":18000},{"comman
dType":1004,"currentTemp":3990,"targetTemp":6000}]'
)
```

There's quite a bit to see, but let's just talk about the more interesting data from a layman's perspective  here:

The TOPIC (that giant wall of numbers and letters at the top) is a string of data that represents what the printer is doing right now (homing, pre-heating, probing, etc.). When building your program, you could translate these messages to meaningful status messages for display.

The MQTTMsg is what contains a bunch little data points about the printer like nozzle temp, bed temp, what command it most recently received, etc. When building your program, you could use these messages to update data live as long as the MQTT connection was established.

## Conclusion

This should be very useful to people looking some kind of web interface for this machine (kinda like kilpper or octoprint) and not all the capabilities of this repository are demonstrated here. A great use case for this repository is developing a Cura plugin that uses the MQTT API we've put together to send a print job directly to the printer. There's still a lot to discover about the AnkerMake API and we'll continue to experiment and update this repository with out findings. Feel free to contribute Pull Requests, open Issues, and create documentation for this code!
