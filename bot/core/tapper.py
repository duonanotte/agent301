import asyncio
import os
import json
import traceback
import aiohttp
import aiofiles
import random

from datetime import datetime, timedelta
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from typing import Tuple
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.types import InputBotAppShortName
from urllib.parse import unquote, parse_qs

from bot.config import settings
from bot.core.agents import generate_random_user_agent
from bot.utils import logger
from bot.exceptions import InvalidSession
from bot.utils.connection_manager import connection_manager
from .headers import headers

class Tapper:
    def __init__(self, tg_client: Client, proxy: str):
        self.tg_client = tg_client
        self.session_name = tg_client.name
        self.proxy = proxy
        self.ref = 'onetime6434058521'

        self.user_agents_dir = "user_agents"
        self.session_ug_dict = {}
        self.headers = headers.copy()

    async def init(self):
        os.makedirs(self.user_agents_dir, exist_ok=True)
        await self.load_user_agents()
        user_agent, sec_ch_ua = await self.check_user_agent()
        self.headers['User-Agent'] = user_agent
        self.headers['Sec-Ch-Ua'] = sec_ch_ua

    async def generate_random_user_agent(self):
        user_agent, sec_ch_ua = generate_random_user_agent(device_type='android', browser_type='webview')
        return user_agent, sec_ch_ua

    async def load_user_agents(self) -> None:
        try:
            os.makedirs(self.user_agents_dir, exist_ok=True)
            filename = f"{self.session_name}.json"
            file_path = os.path.join(self.user_agents_dir, filename)

            if not os.path.exists(file_path):
                logger.info(f"{self.session_name} | User agent file not found. A new one will be created when needed.")
                return

            try:
                async with aiofiles.open(file_path, 'r') as user_agent_file:
                    content = await user_agent_file.read()
                    if not content.strip():
                        logger.warning(f"{self.session_name} | User agent file '{filename}' is empty.")
                        return

                    data = json.loads(content)
                    if data['session_name'] != self.session_name:
                        logger.warning(f"{self.session_name} | Session name mismatch in file '{filename}'.")
                        return

                    self.session_ug_dict = {self.session_name: data}
            except json.JSONDecodeError:
                logger.warning(f"{self.session_name} | Invalid JSON in user agent file: {filename}")
            except Exception as e:
                logger.error(f"{self.session_name} | Error reading user agent file {filename}: {e}")
        except Exception as e:
            logger.error(f"{self.session_name} | Error loading user agents: {e}")

    async def save_user_agent(self) -> Tuple[str, str]:
        user_agent_str, sec_ch_ua = await self.generate_random_user_agent()

        new_session_data = {
            'session_name': self.session_name,
            'user_agent': user_agent_str,
            'sec_ch_ua': sec_ch_ua
        }

        file_path = os.path.join(self.user_agents_dir, f"{self.session_name}.json")
        try:
            async with aiofiles.open(file_path, 'w') as user_agent_file:
                await user_agent_file.write(json.dumps(new_session_data, indent=4, ensure_ascii=False))
        except Exception as e:
            logger.error(f"{self.session_name} | Error saving user agent data: {e}")

        self.session_ug_dict = {self.session_name: new_session_data}

        logger.info(f"{self.session_name} | User agent saved successfully: {user_agent_str}")

        return user_agent_str, sec_ch_ua

    async def check_user_agent(self) -> Tuple[str, str]:
        if self.session_name not in self.session_ug_dict:
            return await self.save_user_agent()

        session_data = self.session_ug_dict[self.session_name]
        if 'user_agent' not in session_data or 'sec_ch_ua' not in session_data:
            return await self.save_user_agent()

        return session_data['user_agent'], session_data['sec_ch_ua']

    async def check_proxy(self) -> bool:
        try:
            response = await self.http_client.get(url='https://ipinfo.io/json', timeout=aiohttp.ClientTimeout(total=5))
            data = await response.json()

            ip = data.get('ip')
            city = data.get('city')
            country = data.get('country')

            logger.info(
                f"{self.session_name} | Check proxy! Country: <cyan>{country}</cyan> | City: <light-yellow>{city}</light-yellow> | Proxy IP: {ip}")

            return True

        except Exception as error:
            logger.error(f"{self.session_name} | Proxy error: {error}")
            return False

    async def get_tg_web_data(self):
        # logger.info(f"Getting data for {self.session_name}")
        if self.proxy:
            proxy = Proxy.from_str(self.proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict

        try:
            if not self.tg_client.is_connected:
                try:
                    await self.tg_client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            while True:
                try:
                    peer = await self.tg_client.resolve_peer('Agent301Bot')
                    break
                except FloodWait as fl:
                    fls = fl.value
                    logger.warning(f"{self.session_name} | FloodWait {fl}")
                    wait_time = random.randint(3600, 12800)
                    logger.info(f"{self.session_name} | Sleep {wait_time}s")
                    await asyncio.sleep(wait_time)

            web_view = await self.tg_client.invoke(RequestAppWebView(
                peer=await self.tg_client.resolve_peer('Agent301Bot'),
                app=InputBotAppShortName(bot_id=await self.tg_client.resolve_peer('Agent301Bot'), short_name="app"),
                platform='android',
                write_allowed=True,
                start_param=self.ref
            ))

            auth_url = web_view.url
            self.http_client.headers['Authorization'] = unquote(
                string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]
            )

            self.tg_acc_info = self.get_dict(query=unquote(
                string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]
            ))

            return True

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(
                f"<light-yellow>{self.session_name}</light-yellow> | Unknown error during Authorization: {error}")
            await asyncio.sleep(delay=3)

        finally:
            if self.tg_client.is_connected:
                await self.tg_client.disconnect()

    def get_dict(self, query: str):
        parsed_query = parse_qs(query)
        parsed_query['user'] = json.loads(unquote(parsed_query['user'][0]))
        return parsed_query

    async def wheel(self, spin_count: int):
        json_data = {}

        response = await self.http_client.post('https://api.agent301.org/wheel/load', json=json_data)
        response = await response.json()

        if int(datetime.now().timestamp()) >= response['result']['tasks']['daily']:
            json_data_daily = {
                'type': 'daily',
            }
            daily_resp = await self.http_client.post('https://api.agent301.org/wheel/task', json=json_data_daily)
            daily_resp = await daily_resp.json()
            if daily_resp['ok']:
                logger.success(f"{self.session_name} | Claimed 1 ticket for daily reward")
            await asyncio.sleep(random.uniform(*settings.TASK_SLEEP))
        else:
            time_left = timedelta(seconds=response['result']['tasks']['daily'] - int(datetime.now().timestamp()))
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            logger.info(
                f"{self.session_name} | Daily reward of 1 ticket can be claimed in {hours}h {minutes}m"
            )

        if not response['result']['tasks']['rps']:
            json_data_rps = {
                'type': 'rps',
            }
            rps_resp = await self.http_client.post('https://api.agent301.org/wheel/task', json=json_data_rps)
            rps_resp = await rps_resp.json()
            if rps_resp['ok']:
                logger.success(f"{self.session_name} | Claimed 1 ticket for task")
            await asyncio.sleep(random.uniform(*settings.TASK_SLEEP))


        if not response['result']['tasks']['bird']:
            json_data_bird = {
                'type': 'bird',
            }
            bird_resp = await self.http_client.post('https://api.agent301.org/wheel/task', json=json_data_bird)
            bird_resp = await bird_resp.json()
            if bird_resp['ok']:
                logger.success(f"{self.session_name} | Claimed 1 TICKET for task")
            await asyncio.sleep(random.uniform(*settings.TASK_SLEEP))

        current_spin_count = spin_count

        while current_spin_count > 0:
            json_data = {}

            try:
                spin_resp = await self.http_client.post('https://api.agent301.org/wheel/spin', json=json_data)
                spin_resp = await spin_resp.json()

                toncoin = spin_resp['result'].get('toncoin', 0) / 100
                notcoin = spin_resp['result'].get('notcoin', 0)

                logger.info(
                    f"{self.session_name} | Wheel balance: <green>{toncoin:.2f}</green> TON | <green>{notcoin}</green> NOT"
                )

                remaining_tickets = spin_resp['result'].get('tickets', 0)
                result = spin_resp['result']['reward']

                if result == 'c1000':
                    logger.success(f"{self.session_name} | <cyan>Reward:</cyan> 1,000 AP | Remaining tickets: {remaining_tickets}")
                elif result == 'c10000':
                    logger.success(f"{self.session_name} | <cyan>Reward:</cyan> 10,000 AP | Remaining tickets: {remaining_tickets}")
                elif result == 't1':
                    logger.success(f"{self.session_name} | <cyan>Reward:</cyan> 1 TICKET | Remaining tickets: {remaining_tickets}")
                elif result == 't3':
                    logger.success(f"{self.session_name} | <cyan>Reward:</cyan> 3 TICKETS | Remaining tickets: {remaining_tickets}")
                elif result == 'tc1':
                    logger.success(f"{self.session_name} | <cyan>Reward:</cyan> 0.01 TON | Remaining tickets: {remaining_tickets}")
                elif result == 'tc4':
                    logger.success(f"{self.session_name} | <cyan>Reward:</cyan> 4 TON | Remaining tickets: {remaining_tickets}")
                elif result == 'nt1':
                    logger.success(f"{self.session_name} | <cyan>Reward:</cyan> 1 NOT | Remaining tickets: {remaining_tickets}")
                elif result == 'nt5':
                    logger.success(f"{self.session_name} | <cyan>Reward:</cyan> 5 NOT | Remaining tickets: {remaining_tickets}")

                current_spin_count = spin_resp['result'].get('tickets', 0)

            except Exception as e:
                logger.error(f"{self.session_name} | Error during wheel spin: {e}")
                break

            await asyncio.sleep(random.uniform(*settings.MINI_SLEEP))

    async def complete_task(self, task: str, max_count: int = 1, reduced_count: int = 1, initial_count: int = 0):
        count = initial_count
        response = None

        for i in range(reduced_count):
            json_data = {
                'type': task,
            }

            try:
                async with self.http_client.post('https://api.agent301.org/completeTask', json=json_data) as response:
                    response_text = await response.text()
                    response.raise_for_status()
                    response_json = await response.json()

                    if 'ok' in response_json and response_json['ok']:
                        count += 1
                        if task == 'video':
                            logger.success(
                                f"{self.session_name} | Completed <light-yellow>{count}/{max_count}</light-yellow> (Planned: {reduced_count}): Received {response_json['result']['reward']} for task {task}"
                            )
                        else:
                            logger.success(
                                f"{self.session_name} | Received {response_json['result']['reward']} for task {task}"
                            )
                    else:
                        logger.warning(f"{self.session_name} | Task completion unsuccessful. Response: {response_json}")

            except aiohttp.ClientResponseError as error:
                logger.error(
                    f"{self.session_name} | HTTP error during task completion: {error.status} - {error.message}")
            except aiohttp.ClientError as error:
                logger.error(f"{self.session_name} | HTTP client error during task completion: {error}")
            except asyncio.TimeoutError:
                logger.error(f"{self.session_name} | Timeout error during task completion.")
            except json.JSONDecodeError:
                logger.error(f"{self.session_name} | Invalid JSON response: {response_text}")
            except Exception as error:
                logger.error(f"{self.session_name} | Unknown error during task completion: {error}")

            delay = random.uniform(20, 30)
            await asyncio.sleep(delay)

        return response

    async def get_me(self):
        try:
            if str(self.tg_acc_info['user']['id']) == self.ref[7:]:
                json_data = {'referrer_id': 0}
            else:
                json_data = {'referrer_id': int(self.ref[7:])}

            async with self.http_client.post('https://api.agent301.org/getMe', json=json_data) as response:
                status = response.status
                headers = dict(response.headers)
                try:
                    body = await response.text()
                    json_body = await response.json()
                except:
                    json_body = None
                    body = await response.read()

                full_response = {
                    'status': status,
                    'headers': headers,
                    'body': body,
                    'json': json_body
                }

                if status == 500:
                    logger.error(f"{self.session_name} | Server returned 500 error for getMe.")
                    logger.error(f"Full response: {full_response}")
                    await asyncio.sleep(60)
                    return None

                response.raise_for_status()

                if 'result' not in json_body:
                    logger.error(f"{self.session_name} | Invalid response from getMe: {full_response}")
                    return None

                return json_body

        except aiohttp.ClientError as e:
            logger.error(f"{self.session_name} | Error in getMe request: {e}")
            logger.error(f"Request details: URL=https://api.agent301.org/getMe, Data={json_data}")
            return None
        except Exception as e:
            logger.error(f"{self.session_name} | Unexpected error in getMe: {e}")
            return None

    async def get_tasks(self, max_retries=3, retry_delay=60):
        for attempt in range(max_retries):
            try:
                json_data = {}
                response = await self.http_client.post('https://api.agent301.org/getTasks', json=json_data)
                response = await response.json()
                return response
            except aiohttp.ClientError as error:
                logger.error(f"{self.session_name} | Error getting tasks (attempt {attempt + 1}/{max_retries}): {error}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    raise

    async def login(self):
        try:
            tg_web_data = await self.get_tg_web_data()
            if tg_web_data == False:
                return False
            return True
        except Exception as err:
            logger.error(f"{self.session_name} | Login failed: {err}")
            return False

    async def run(self):
        if settings.USE_RANDOM_DELAY_IN_RUN:
            random_delay = random.randint(settings.RANDOM_DELAY_IN_RUN[0], settings.RANDOM_DELAY_IN_RUN[1])
            logger.info(
                f"{self.session_name} | The Bot will go live in <y>{random_delay}s</y>")
            await asyncio.sleep(random_delay)

        await self.init()

        proxy_conn = ProxyConnector().from_url(self.proxy) if self.proxy else None
        self.http_client = aiohttp.ClientSession(headers=self.headers, connector=proxy_conn)
        connection_manager.add(self.http_client)

        if settings.USE_PROXY:
            if not self.proxy:
                logger.error(f"{self.session_name} | Proxy is not set. Aborting operation.")
                return
            if not await self.check_proxy(http_client):
                logger.error(f"{self.session_name} | Proxy check failed. Aborting operation.")
                return

        while True:
            try:
                if self.http_client.closed:
                    if proxy_conn:
                        if not proxy_conn.closed:
                            await proxy_conn.close()

                    proxy_conn = ProxyConnector().from_url(self.proxy) if self.proxy else None
                    self.http_client = aiohttp.ClientSession(headers=self.headers, connector=proxy_conn)
                    connection_manager.add(self.http_client)

                login_success = await self.login()
                if not login_success:
                    logger.error(f"{self.session_name} | Login failed. Retrying in 1 hour.")
                    await asyncio.sleep(3600)
                    continue

                logger.info(f"{self.session_name} | Login successfully!")

                user = await self.get_me()
                if user is None:
                    logger.error(f"{self.session_name} | Failed to get user info. Retrying in 5 minutes.")
                    await asyncio.sleep(300)
                    continue

                logger.info(
                    f"{self.session_name} | Balance: <green>{user['result']['balance']:,}</green> | Tickets: <green>{user['result']['tickets']}</green>"
                )

                if user['result']['daily_streak']['showed']:
                    logger.info(
                        f"{self.session_name} | Claim daily reward | Day <light-yellow>{user['result']['daily_streak']['day']}</light-yellow>"
                    )
                await asyncio.sleep(random.uniform(*settings.MINI_SLEEP))

                try:
                    tasks_response = await self.get_tasks()
                except Exception as e:
                    logger.error(f"{self.session_name} | Failed to get tasks after several attempts: {e}")
                    await asyncio.sleep(300)
                    continue

                if tasks_response is None or 'result' not in tasks_response or 'data' not in tasks_response['result']:
                    logger.error(f"{self.session_name} | Invalid response from get_tasks. Skipping tasks.")
                    await asyncio.sleep(300)
                    continue

                tasks = tasks_response['result']['data']

                random.shuffle(tasks)
                for task in tasks:
                    if not task['is_claimed'] and task['type'] not in settings.BLACKLIST:
                        if task['type'] == 'video':
                            max_count = task.get('max_count', 1)
                            count = task.get('count', 0)
                            remaining_count = max(max_count - count, 0)
                            reduced_count = max(remaining_count - random.randint(1, 4), 0)

                            await self.complete_task(task=task['type'], max_count=max_count,
                                                     reduced_count=reduced_count, initial_count=count)
                        else:
                            await self.complete_task(task=task['type'], max_count=1)

                tickets = min(user['result']['tickets'], settings.MAX_SPIN_PER_CYCLE)
                try:
                    await self.wheel(spin_count=tickets)
                except Exception as wheel_error:
                    logger.error(f"{self.session_name} | Error during wheel spin: {wheel_error}")

            except aiohttp.ClientConnectorError as error:
                delay = random.randint(1800, 3600)
                logger.error(f"{self.session_name} | Connection error: {error}. Retrying in {delay} seconds.")
                logger.debug(f"Full error details: {traceback.format_exc()}")
                await asyncio.sleep(delay)


            except aiohttp.ServerDisconnectedError as error:
                delay = random.randint(900, 1800)
                logger.error(f"{self.session_name} | Server disconnected: {error}. Retrying in {delay} seconds.")
                logger.debug(f"Full error details: {traceback.format_exc()}")
                await asyncio.sleep(delay)


            except aiohttp.ClientResponseError as error:
                delay = random.randint(3600, 7200)
                logger.error(
                   f"{self.session_name} | HTTP response error: {error}. Status: {error.status}. Retrying in {delay} seconds.")
                logger.debug(f"Full error details: {traceback.format_exc()}")
                await asyncio.sleep(delay)


            except aiohttp.ClientError as error:
                delay = random.randint(3600, 7200)
                logger.error(f"{self.session_name} | HTTP client error: {error}. Retrying in {delay} seconds.")
                logger.debug(f"Full error details: {traceback.format_exc()}")
                await asyncio.sleep(delay)


            except asyncio.TimeoutError:
                delay = random.randint(7200, 14400)
                logger.error(f"{self.session_name} | Request timed out. Retrying in {delay} seconds.")
                logger.debug(f"Full error details: {traceback.format_exc()}")
                await asyncio.sleep(delay)


            except InvalidSession as error:
                logger.critical(f"{self.session_name} | Invalid Session: {error}. Manual intervention required.")
                logger.debug(f"Full error details: {traceback.format_exc()}")
                raise error


            except json.JSONDecodeError as error:
                delay = random.randint(1800, 3600)
                logger.error(f"{self.session_name} | JSON decode error: {error}. Retrying in {delay} seconds.")
                logger.debug(f"Full error details: {traceback.format_exc()}")
                await asyncio.sleep(delay)

            except KeyError as error:
                delay = random.randint(1800, 3600)
                logger.error(
                    f"{self.session_name} | Key error: {error}. Possible API response change. Retrying in {delay} seconds.")
                logger.debug(f"Full error details: {traceback.format_exc()}")
                await asyncio.sleep(delay)


            except Exception as error:
                delay = random.randint(7200, 14400)
                logger.error(f"{self.session_name} | Unexpected error: {error}. Retrying in {delay} seconds.")
                logger.debug(f"Full error details: {traceback.format_exc()}")
                await asyncio.sleep(delay)

            finally:
                if self.http_client:
                    await self.http_client.close()
                    connection_manager.remove(self.http_client)
                if proxy_conn and not proxy_conn.closed:
                    await proxy_conn.close()

                next_claim = random.randint(settings.SLEEP_TIME[0], settings.SLEEP_TIME[1])
                hours = int(next_claim // 3600)
                minutes = (int(next_claim % 3600)) // 60
                logger.info(
                    f"{self.session_name} | Sleep before wake up <yellow>{hours} hours</yellow> and <yellow>{minutes} minutes</yellow>")
                await asyncio.sleep(next_claim)


async def run_tapper(tg_client: Client, proxy: str | None):
    session_name = tg_client.name
    if settings.USE_PROXY and not proxy:
        logger.error(f"{session_name} | No proxy found for this session")
        return
    try:
        await Tapper(tg_client=tg_client, proxy=proxy).run()
    except InvalidSession:
        logger.error(f"{session_name} | Invalid Session")
