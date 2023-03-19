# Extracting your Authentication Token

**NOTE:** You need to have to have logged into the AnkerMake slicer in order for this to work, but it doesn't need to be open during this.

1. Navigate to wherever you cloned this repository to and into the `examples` folder in your terminal.

2. MacOS and Windows users (who used the default AnkerMake slicer installation path), type in the following command:

   ```bash
    python3 extract-auth-token.py -a
   ```

   For linux users (and MacOS/Windows users that did not use the default installation path), it's a little more complicated since we can't assume where your `login.json` file is. Locate your `login.json` file in your system and use the following command, substituting the path to your file:

   ```bash
    python3 extract-auth-token.py -f /path/to/login.json
   ```

   You should get back a long sequence of numbers and letters in plain text. That's your Authentication Token.

