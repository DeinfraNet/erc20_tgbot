# Guide for Setting Up and Launching an ERC20 Telegram Bot

This guide describes the steps to configure and launch an ERC20 Telegram bot.

1. **Clone the repository**  
    Run the following command to clone the repository:

   ```bash
   git clone https://github.com/DeinfraNet/erc20_tgbot
   cd erc20_tgbot
   ```

2. **Register an account**  
    Execute the following command to register your account in the devnet of chain 3:

   ```bash
   tpe acc register
   ```

3. **Create a container**  
    Use the following command to create a container:

   ```bash
   tpe container create -k <your_key.pem> -n <container_name>
   ```

   Replace `<your_key.pem>` with the path to your key and `<container_name>` with the desired container name.  
    Example:

   ```bash
   tpe container create -k power_wallet_3_AA100000005033174828.pem -n erc20_tgbot_jackkru69
   ```

   Optional additional parameters:

   - Container index: `-i 2`
   - Private key file: `-f container_erc20_tgbot_jackkru69_private_key.pem`
   - Path to source code: `-t ../../../erc20_tgbot`

   Full example command:

   ```bash
   tpe container create -k power_wallet_3_AA100000005033174828.pem -i 2 -f container_erc20_tgbot_jackkru69_private_key.pem -t ../../../erc20_tgbot -c 1
   ```

4. **Upload the container**  
    After creating the container, upload it using this command:

   ```bash
   tpe container upload -k <your_key.pem> -i <index> -f <key_file> -t <path>
   ```

   Example:

   ```bash
   tpe container upload -k power_wallet_3_AA100000005033174828.pem -i 2 -f container_erc20_tgbot_jackkru69_private_key.pem -t ../../../erc20_tgbot -c 1
   ```

5. **Start the container**  
    Execute the following command to start the container:

   ```bash
   tpe container actions -m container_start -i <index> -f <key_file> -p <parameter>
   ```

   Example:

   ```bash
   tpe container actions -m container_start -i 2 -f container_erc20_tgbot_jackkru69_private_key.pem -p 2
   ```

6. **Completion**  
   After completing all the steps, your ERC20 Telegram bot should be successfully launched.
