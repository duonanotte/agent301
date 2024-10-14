# 🤖 Guid for launching [Agent301](https://t.me/Agent301Bot/app?startapp=onetime6434058521) bot

![img1](Agent301.png)

## Table of Contents

- [Step 1: Preparation](#step-1-preparation)
- [Step 2: Create and Activate Virtual Environment](#step-2-create-and-activate-virtual-environment)
- [Step 3: Install Dependencies](#step-3-install-dependencies)
- [Step 4: Create and Fill .env File](#step-4-create-and-fill-env-file)
- [Step 5: Proxy Setup](#step-5-proxy-setup)
- [Step 6: Create Sessions or Use Existing Ones](#step-6-create-sessions-or-use-existing-ones)
- [Step 7: Run the script](#step-7-run-the-script)
  

> ⚠️ **WARNING**:  
> _Use the script at your own risk. The author of this script is not responsible for any actions taken by users and their consequences, including account bans and other restrictions. We recommend that you exercise caution and avoid sharing confidential information, as this may lead to the compromise of your data. Before using, be sure to review the terms of service of the applications you are working with to avoid violating their rules. Keep in mind that automation may result in unwanted consequences, such as temporary or permanent suspension of your account. Always act consciously and consider the potential risks._


## Need help? Join our community!
If you have any questions or need assistance, feel free to join our **community on Telegram**:

[![Static Badge](https://img.shields.io/badge/Telegram-Channel-Link?style=for-the-badge&logo=Telegram&logoColor=white&logoSize=auto&color=blue)](https://t.me/web3community_ru)

---

## Features

| Feature | Supported | 
|---------|-----------|
| Support for pyrogram .session | <div align="center"> ☑️ </div> |
| Multithreading | <div align="center"> ☑️ </div> |
| Proxy binding to session | <div align="center"> ☑️ </div> |
| Generation of User-Agent for each session | <div align="center"> ☑️ </div> |
| Registration via your referral link without restrictions | <div align="center"> ☑️ </div> |
| Earning rewards for referrals | <div align="center"> ☑️ </div> |
| Automatic task execution | <div align="center"> ☑️ </div> |
| Daily reward claim | <div align="center"> ☑️ </div> |



## Step 1: Preparation

   * Ensure that **`Python 3.10`** is installed | Installation guide for [Python](https://www.python.org/downloads/)
   * Download and extract the archive or use the command
     
     ```
     git clone [REPOSITORY URL]
     ```
## Step 2: Create and Activate Virtual Environment

* For Windows:
  
     ```
  python -m venv venv
  venv/Scripts/activate
     ```
* For Linux:
    ```
  python3.10 -m venv venv
  source venv/bin/activate
    ```

## Step 3: Install Dependencies

* Navigate to the script folder:

   ```
   cd Agent301
   ```
* Install the required libraries:

   ```
   pip install -r requirements.txt
   ```

## Step 4: Create and Fill `.env` File

* In the terminal enter
  
     ```
    copy .env-example .env
     ```
* Enter the **API_ID** and **API_HASH** obtained from the [`https://my.telegram.org/auth`](#) website

## Step 5: Proxy Setup

* Fill in the `session_proxy.json` file, linking each account to a separate proxy.
* For automatic filling, add all your proxies to the `proxies.txt` file and name your sessions, for example, "1-Andrey", "2-John".
* In the terminal run the command
  
  ```
  python session_proxy_matcher.py
  ```
* The script will match each proxy line with the account number and add them to the `session_proxy.json` file. This way, you will have a ready-made file where the first proxy line corresponds to the first account, and so on.

## Step 6: Create Sessions or Use Existing Ones

   * To use existing sessions, add them to the `sessions` folder.
   * To create new sessions, select option "2" in the main menu of the program.

## Step 7: Run the script

   * Select option "1" in the main menu, and the script will start running.
