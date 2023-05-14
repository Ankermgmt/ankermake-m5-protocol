# Installation (docker)

## Windows

1. Install the [AnkerMake slicer](https://www.ankermake.com/software). Make sure you open it and login via the “Account” dropdown in the top toolbar.
   	**NOTE:** The slicer app does not need to be open for the rest of these steps.

2. Install Docker Desktop by following [this guide](https://docs.docker.com/desktop/install/windows-install/) (supplemental steps are provided below). It’s recommended for you to use the Windows Subsystem for Linux V2 (WSL 2) backend to run docker as it can be used on any edition of Windows. 

   Alternatively, you can setup docker to used Hyper-V if you are running a Pro, Enterprise, or Education version of Windows, but that option is beyond the scope of this guide. Setting up docker inside a virtual machine is possible, but requires you to disable basic security features and beyond the scope of this guide.

   - [ ] **[<u>Configure WSL 2</u>]** WSL is disabled by default. To enable it and install a Linux distro, follow this sub step. If you already have WLS 2 up and running and a distro configured, skip to the next sub step.

     - [ ] *[Check/Enable Hardware Virtualization]* Open Task Manger by right clicking the Windows icon on Taskbar and then selecting “Task Manager” or press and hold the CTRL, Shift, and ESC keys simultaneously.

       - [ ] Select the “Performance tab. If the tabs across the top of the window are not visible, click the “More Details” drop down arrow.
       - [ ] Select the “CPU” section from the side bar.
       - [ ] Look for the “Virtualization” attribute in the body section of the window. If the value is “Enabled”, proceed with this section. If the value is “Disabled”, you need to reboot into your BIOS menu and enable hardware virtualization. This is highly dependent on your CPU platform and motherboard manufacturer so use Google to find specific steps for your hardware. If you cannot enable hardware virtualization, docker is impossible to run on your system and you must use the [git installation method](./install-from-git.md).

     - [ ] *[Enable Necessary Windows Features]* Open the start menu by clicking the Windows icon on the Taskbar or by pressing the Windows button on your keyboard. Type in “Turn Windows features on or off” and click on the corresponding settings option when it appears.

       - [ ] In the pop up window, check the boxes for “Virtual Machine Platform” and “Windows Subsystem for Linux”. Then press “OK” and let the installation complete. Restart your computer if prompted to do so.

     - [ ] *[Install Linux Disto]* Open Task Manger by right clicking the Windows icon on Taskbar and then selecting “Windows PowerShell (Admin)”. Pres “Yes” on the UAC prompt.

       - [ ] Type `wsl --install` to install the default distro (Ubuntu). Just about any other available distro you can install via WSL should work, but there has been no testing done outside the default distro.

       - [ ] Wait for the installation to complete (3-30 min depending on hardware and internet speed) and proceed through the prompts to set up your Linux user account. 

         If the prompts to setup and account do not appear (a known bug in the WSL setup at the time of writing this), you will be logged in as the root user when you use WSL. It’s recommended to setup a user account as a Super User and a strong password instead of using the root user regularly. You can create a user account inside the Linux environment and set the default WSL distro user via PowerShell once the account is created.
         
         

   - [ ] **[<u>Install Docker Desktop</u>]** Download and install Docker Desktop using the linked docker docs guide. Once the install process is complete, open Docker Desktop and accept the EULA. You can close Docker Desktop for the remaining steps.

3. Download the latest version of ankerctl from the GitHub releases page and extract the contents wherever you’d like to run the program from. Navigate to that folder in File Explorer.

4. Hold down the "Shift" key and right-click on some empty space in the ankerctl top level folder. Select "Open in Terminal" from the context menu dropdown. (If the following commands do not work, try re-opening your terminal window as administrator and use the `cd` command to navigate to where you extracted it).

5. Run the following command to build the docker container(s) and volume(s) needed by ankerctl.

   `docker compose build`

## MacOS (UNDER CONSTRUCTION)

1. Install the [AnkerMake slicer](https://www.ankermake.com/software). Make sure you open it and login via the “Account” dropdown in the top toolbar.
   	**NOTE:** The slicer app does not need to be open for the rest of these steps.
2. 

## Linux (UNDER CONSTRUCTION)

1. Install the [AnkerMake slicer](https://www.ankermake.com/software). Make sure you open it and login via the “Account” dropdown in the top toolbar.
   	**NOTE:** The slicer app does not need to be open for the rest of these steps.
2. 