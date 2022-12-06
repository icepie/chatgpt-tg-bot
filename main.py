#!/usr/bin/env python3

# Builtins
import json
import os
import time

from telethon import TelegramClient, events

# Local
from Classes import auth as Auth
from Classes import chat as Chat

# Fancy stuff
import colorama
from colorama import Fore

colorama.init(autoreset=True)

# Check if config.json exists
if not os.path.exists("config.json"):
    print(">> config.json is missing. Please create it.")
    print(f"{Fore.RED}>> Exiting...")
    exit(1)

# Read config.json
with open("config.json", "r") as f:
    config = json.load(f)
    # Check if email & password are in config.json
    if "email" not in config or "password" not in config:
        print(">> config.json is missing email or password. Please add them.")
        print(f"{Fore.RED}>> Exiting...")
        exit(1)

    # Get email & password
    email = config["email"]
    password = config["password"]
    use_proxy = config["use_proxy"]
    proxy_url = config["proxy_url"]
    
    # Tg
    tg_api_id = config["tg_api_id"]
    tg_api_hash = config["tg_api_hash"]
    tg_username = config["tg_username"]

previous_convo_id = None
access_token = Auth.get_access_token()

# print(client.get_me().stringify())

expired_creds = Auth.expired_creds()
print(f"{Fore.GREEN}>> Checking if credentials are expired...")
if expired_creds:
    print(f"{Fore.RED}>> Your credentials are expired." + f" {Fore.GREEN}Attempting to refresh them...")
    open_ai_auth = Auth.OpenAIAuth(email_address=email, password=password, use_proxy=use_proxy, proxy=proxy_url)

    print(f"{Fore.GREEN}>> Credentials have been refreshed.")
    open_ai_auth.begin()
    time.sleep(3)
    is_still_expired = Auth.expired_creds()
    if is_still_expired:
        print(f"{Fore.RED}>> Failed to refresh credentials. Please try again.")
        exit(1)
    else:
        print(f"{Fore.GREEN}>> Successfully refreshed credentials.")
else:
    print(f"{Fore.GREEN}>> Your credentials are valid.")

print(f"{Fore.GREEN}>> Starting chat..." + Fore.RESET)


# api_hash from https://my.telegram.org, under API Development.
client = TelegramClient(tg_username, tg_api_id, tg_api_hash, auto_reconnect=True)

client.start()


@client.on(events.NewMessage())
async def handler(event):
    global previous_convo_id
    global access_token
    global open_ai_auth
    
    global email 
    global password 
    global use_proxy
    global proxy_url
    

    print(event.message)
    # client.action(event.chat, 'typing')
    # # await client.action(event.chat_id, 'typing')
    # # typing animation
    async with client.action(event.chat_id, 'typing'):

        # judge if @bot is mentioned
        if not (event.message.mentioned or event.is_private):
                # await event.reply('Hi!')
            return
        
        # 判断是否回复的是自己
        if event.is_reply and not event.message.mentioned:
            return
            
        # tirm the space and @bot
        msg = event.raw_text.replace('@' +  tg_username, '').strip()
        if len(msg) == 0:
            await event.reply("请输入有意义的内容哦~")
            return
        if "重置会话" in msg:
            # chatbot.refresh_session()  # Uses the session_token to get a new bearer token
            # chatbot.reset_chat()
            previous_convo_id = None
            await event.reply("会话已重置")
            return

        if access_token == "":
            print(f"{Fore.RED}>> Access token is missing in /Classes/auth.json.")
            await event.reply("出错了，请重试")
            return
        # user_input = input("You: ")
        answer, previous_convo = Chat.ask(auth_token=access_token,
                                        prompt=msg,
                                        previous_convo_id=previous_convo_id)
        if answer == "400" or answer == "401":
            print(f"{Fore.RED}>> Your token is invalid. Attempting to refresh..")
            open_ai_auth = Auth.OpenAIAuth(email_address=email, password=password)
            open_ai_auth.begin()
            # time.sleep(3)
            access_token = Auth.get_access_token()
            await event.reply("出错了，请重试")
            return
        else:
            if previous_convo is not None:
                previous_convo_id = previous_convo

            print(f"Chat GPT: {answer}")
            
            await event.reply(answer)

client.run_until_disconnected()






