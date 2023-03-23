# Extracting your Authentication Token

**NOTE:** You need to have to have logged into the AnkerMake slicer in order for this to work, but it doesn't need to be open during this.

1. Navigate to wherever you cloned this repository to and into the `examples` folder in your terminal.

2. MacOS and Windows users, type in the following command:

   ```bash
    python3 extract-auth-token.py -a
   ```

   For Linux users, it's a little more complicated since we can't assume where your `login.json` file is. Locate your `login.json` file in your system and use the following command, substituting the path to your file:

   ```bash
    python3 extract-auth-token.py -f /path/to/login.json
   ```

   Here's and example of the output:
   
   ```
   2ab96390c7dbe3439de74d0c9b0b1767
   ```
   
   That's your Authentication Token.
