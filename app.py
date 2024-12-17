import os
import json
import time
import logging
from web3 import Web3
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ERC20_TOKEN_ADDRESS = os.getenv("ERC20_TOKEN_ADDRESS")
ETH_RPC_URL = os.getenv("ETH_RPC_URL")

# Connect to Ethereum node
web3 = Web3(Web3.HTTPProvider(ETH_RPC_URL))
logger.info("Connected to Ethereum node: %s", ETH_RPC_URL)

# Load or initialize config.json
CONFIG_FILE = "/data/config.json"
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"monitor": [], "last_handled_block": "0x0"}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

config = load_config()
logger.debug("Loaded configuration: %s", config)

# ERC20 ABI (Minimal for balanceOf and Transfer events)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    }
]

# Initialize contract
if not ERC20_TOKEN_ADDRESS or not Web3.is_address(ERC20_TOKEN_ADDRESS):
    logger.error("Invalid or missing ERC20_TOKEN_ADDRESS environment variable.")
    raise ValueError("Invalid or missing ERC20_TOKEN_ADDRESS environment variable.")
contract = web3.eth.contract(address=web3.to_checksum_address(ERC20_TOKEN_ADDRESS), abi=ERC20_ABI)
logger.info("Initialized contract at address: %s", ERC20_TOKEN_ADDRESS)

# Telegram bot handlers
def start(update: Update, context: CallbackContext):
    logger.debug("Received /start command from user: %s", update.message.chat_id)
    update.message.reply_text(f"Welcome! Use /monitor <address> to monitor an address in ERC20 token {ERC20_TOKEN_ADDRESS}.")

def monitor(update: Update, context: CallbackContext):
    logger.debug("Received /monitor command from user: %s", update.message.chat_id)
    if len(context.args) != 1:
        update.message.reply_text("Usage: /monitor <address>")
        return

    address = context.args[0]
    if not Web3.is_address(address):
        update.message.reply_text("Invalid address.")
        return

    tg_id = update.message.chat_id
    address = web3.to_checksum_address(address)

    # Update the config
    for entry in config["monitor"]:
        if entry["tg_id"] == tg_id:
            entry["address"] = address
            break
    else:
        config["monitor"].append({"tg_id": tg_id, "address": address})

    save_config(config)
    logger.info("User %s is now monitoring address: %s", tg_id, address)
    update.message.reply_text(f"You are now monitoring {address}.")

# Polling function
def poll_events(context: CallbackContext):
    logger.debug("Polling events...")
    last_handled_block = int(config["last_handled_block"], 16)
    latest_block = web3.eth.block_number

    if last_handled_block >= latest_block:
        logger.debug("No new blocks to process. Last handled block: %s, Latest block: %s", last_handled_block, latest_block)
        return

    try:
        logs = web3.eth.get_logs({
            "fromBlock": last_handled_block + 1,
            "toBlock": latest_block,
            "address": web3.to_checksum_address(ERC20_TOKEN_ADDRESS),
            "topics": [web3.keccak(text="Transfer(address,address,uint256)").hex()]
            })

        for log in logs:
            topics = log["topics"]
            data = log["data"]
            value = int(log["data"].hex(), 16)
            from_address = "0x" + topics[1].hex()[24:]
            to_address = "0x" + topics[2].hex()[24:]

            logger.debug("Detected transfer from %s to %s", from_address, to_address)

            # Notify users monitoring the `from` or `to` address
            for entry in config["monitor"]:
                tg_id = entry["tg_id"]
                monitored_address = entry["address"]
                logger.debug("Check against address %s user %s", monitored_address.lower(),tg_id)

                if monitored_address.lower() == to_address.lower():
                    balance = contract.functions.balanceOf(monitored_address).call()
                    logger.info("Found inbound tx to %s, balance is %s", monitored_address, balance)
                    context.bot.send_message(
                            chat_id=tg_id,
                            text=(
                                f"Transaction detected from {from_address}\n"
                                f"value: {web3.from_wei(value, 'ether')}\n"
                                f"current {monitored_address} balance: {web3.from_wei(balance, 'ether')} tokens.\n"
                                )
                            )
                else:
                    if monitored_address.lower() == from_address.lower():
                        balance = contract.functions.balanceOf(monitored_address).call()
                        logger.info("Found outbound tx from %s, balance is %s", monitored_address, balance)
                        balance = contract.functions.balanceOf(monitored_address).call()
                        context.bot.send_message(
                                chat_id=tg_id,
                                text=(
                                    f"Transaction detected to {to_address}\n"
                                    f"value: {web3.from_wei(value, 'ether')}\n"
                                    f"current {monitored_address} balance: {web3.from_wei(balance, 'ether')} tokens.\n"
                                    )
                                )

        # Update last handled block
        config["last_handled_block"] = hex(latest_block)
        save_config(config)
        logger.debug("Updated last handled block to: %s", latest_block)

    except Exception as e:
        logger.error("Error while polling events: %s", str(e))

# Main function
def main():
    logger.info("Starting bot...")
    updater = Updater(token=TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("monitor", monitor))

    # Job to poll events
    updater.job_queue.run_repeating(poll_events, interval=30, first=3)

    updater.start_polling()
    logger.info("Bot started. Waiting for events...")
    updater.idle()

if __name__ == "__main__":
    main()

