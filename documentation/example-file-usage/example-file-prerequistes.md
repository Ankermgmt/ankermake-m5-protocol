# Prerequisites for using the example scripts

In order to run the example scripts, you'll need to install some supporting software onto your machine (don't worry, it's really easy). 

You'll need Python 3, some pip packages, and the AnkerMake slicer. 

If you're on Linux, you'll also need Wine to install the AnkerMake slicer unless you are ok with ripping files from another machine using MacOS or Windows.

We also include the Transwarp Complier in our `requirements.txt` file for convenience should you want to generate new configs of the standards from this repository.

## Installation

### Windows

1. Install the AnkerMake slicer from [their website](https://www.ankermake.com/software). Make sure you open it and login, then you can close the app.

2. Using `git` or [GitHub Desktop](https://desktop.github.com/), clone this repository into a location of your choice and then navigate to that location in File Explorer.

3. Hold down the "Shift" key and right-click on some empty space in the repository top level folder. Select "Open in Terminal" from the context menu dropdown. (If the following commands do not work, try re-opening your terminal window as administrator and use the `cd` command to navigate to where you cloned this repository to)

4. Enter in the following command to install/check Python 3:

   ```powershell
   python3
   ```

   Now, one of two things will happen:

- The first possibility is that the Microsoft Store will open and prompt you to install Python 3.10. You can do that and that's a perfectly fine way to install Python 3 or you can go to the [Python website](https://www.python.org/downloads/) and install it from there. Either way works, do whichever you prefer. Then enter in the above command again after and you should see what's in the next bullet.

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

5. Enter in the following command to install the required pip packages and the Transwarp Complier:

   ```powershell
   pip3 install -r requirements.txt
   ```

   If required, enter `Y` to all installation prompts.



### MacOS

1. Install the AnkerMake slicer from [their website](https://www.ankermake.com/software). Make sure you open it and login, then you can close the app.

2. Using `git` or [GitHub Desktop](https://desktop.github.com/), clone this repository into a location of your choice and then navigate to that location in Finder.

3. Hold down the "Control" key and click the folder in the path bar, then choose "Open in Terminal". (If you don’t see the path bar at the bottom of the Finder window, choose View > Show Path Bar)

4. Install Python3 from the [Python website.](https://www.python.org/downloads/macos/)

5. Enter in the following command to install the required pip packages and the Transwarp Complier:

   ```bash
   pip3 install -r requirements.txt
   ```

   If required, enter `Y` to all installation prompts.

### Linux

1. Install the AnkerMake slicer from [their website ](https://www.ankermake.com/software) on your machine via [Wine](https://www.winehq.org/). Alternatively, you can install the slicer on a officially supported operating system that you have access to (Windows or MacOS) and use the `login.json` file from that machine. Either way you choose, make sure you open it and login.

   **NOTE:** The slicer app does not need to be open for the rest of these steps.

2. Using `git`, clone this repository into a location of your choice and then navigate to that location in your terminal app of choice.

4. Install Python3 from whatever package manager your distro uses via the terminal.

5. Enter in the following command to install the required pip packages and the Transwarp Complier:

   ```bash
   pip3 install -r requirements.txt
   ```

   If required, enter `Y` to all installation prompts.