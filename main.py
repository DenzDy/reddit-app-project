from dataclasses import dataclass, field
import flet as ft
from flet.auth.oauth_provider import OAuthProvider
from flet.auth.authorization import Authorization
import aiohttp
import base64
import json
@dataclass
class App:
    page : ft.Page
    access_token : str = ""
    lv : ft.ListView = ft.ListView()
    after_t3_id : str = ""
    current_t3_id : str = ""
    controls_dict = {
        "score": int,
        "dir": int,
        "score-text": ft.Text,
        "upvote-button": ft.IconButton,
        "downvote-button": ft.IconButton,
    }
    async def display_feed(self, access_token : str):
        current_count : int = 0
        await self.page.clean_async()
        async def on_click_refresh(e:ft.ControlEvent):
            self.after_t3_id = ""
            await self.page.clean_async()
            await App(self.page).display_feed(access_token)
        async def on_click_logout(e:ft.ControlEvent):
            await self.page.clean_async()
            await App(self.page).display()
        async def on_click_load_more(e:ft.ControlEvent):
            self.lv.controls.pop()
            await create_listview(await get_new_feed(self.after_t3_id))
            await self.page.update_async()
        self.page.appbar = ft.AppBar(
            leading=ft.Icon(ft.icons.REDDIT_ROUNDED),
            leading_width=40,
            title=ft.Text("Home"),
            actions=[
                ft.IconButton(ft.icons.REFRESH, on_click = on_click_refresh),
                ft.PopupMenuButton(
                    items=[ft.PopupMenuItem(text="Logout",on_click=on_click_logout)]
                )
            ]
        )
        # get feed data
        async def get_new_feed(after_param : str = ''):
            headers = {
            'Authorization': f'Bearer {access_token}'
            }
            request = aiohttp.request(
            method='GET',
            url="https://oauth.reddit.com/new.json",
            params={'after':after_param},
            headers=headers,
            )
            async with request as resp:
                response_data = await resp.json()
                return response_data
        r = await get_new_feed()
        def match_init_vote_case(data) -> int:
            if data == True:
                return 1
            elif data == False:
                return -1
            else:
                return 0
        async def make_upvote_button(post_id: str, text : ft.Text) -> ft.IconButton:
            async def upvote_clicked(post_id: str, current_case: int):
                headers = {
                'Authorization': f'Bearer {access_token}'
                }
                request = aiohttp.request(
                method='POST',
                url="https://oauth.reddit.com/api/vote",
                data={'id':post_id, 'dir': current_case},
                headers=headers,
                )
                async with request as resp:
                    response_data = await resp.json()
                    return response_data
            async def on_upvote(e : ft.ControlEvent):
                nonlocal post_id
                score = self.controls_dict[post_id]['score']
                if self.controls_dict[post_id]['dir'] == -1:
                    score += 1
                    self.controls_dict[post_id]['downvote-button'].icon_color = "gray"
                    await self.page.update_async()
                match e.control.icon_color:
                    case "orange":
                        e.control.icon_color = "gray"
                        self.controls_dict[post_id]['score'] = score - 1
                        self.controls_dict[post_id]['dir'] = 0
                        text.value = self.controls_dict[post_id]['score']
                        text.color = get_color(0, "upvote")
                    case "gray":
                        e.control.icon_color = "orange"
                        self.controls_dict[post_id]['score'] = score + 1
                        self.controls_dict[post_id]['dir'] = 1
                        text.value = self.controls_dict[post_id]['score']
                        text.color = get_color(1, "upvote")
                await self.page.update_async()
                await upvote_clicked(post_id, self.controls_dict[post_id]['dir'])
            return ft.IconButton(ft.icons.ARROW_UPWARD_ROUNDED, icon_color=get_color(self.controls_dict[post_id]['dir'],"upvote"), on_click=on_upvote)
        async def make_downvote_button(post_id: str, text : ft.Text) -> ft.IconButton:
            async def downvote_clicked(post_id: str, current_case: int):
                headers = {
                'Authorization': f'Bearer {access_token}'
                }
                request = aiohttp.request(
                method='POST',
                url="https://oauth.reddit.com/api/vote",
                data={'id':post_id, 'dir': current_case},
                headers=headers,
                )
                async with request as resp:
                    response_data = await resp.json()
                    return response_data
            async def on_downvote(e : ft.ControlEvent):
                nonlocal post_id
                score = self.controls_dict[post_id]['score']
                if self.controls_dict[post_id]['dir'] == 1:
                    score -= 1
                    self.controls_dict[post_id]['upvote-button'].icon_color = "gray"  
                    await self.page.update_async()  
                match e.control.icon_color:
                    case "blue":
                        e.control.icon_color = "gray"
                        self.controls_dict[post_id]['score'] = score + 1
                        self.controls_dict[post_id]['dir'] = 0
                        text.value = self.controls_dict[post_id]['score']
                        text.color = get_color(0, "downvote")
                    case "gray":
                        e.control.icon_color = "blue"
                        self.controls_dict[post_id]['score'] = score - 1
                        self.controls_dict[post_id]['dir'] = -1
                        text.value = self.controls_dict[post_id]['score']
                        text.color = get_color(-1, "downvote")
                await self.page.update_async()
                await downvote_clicked(post_id, self.controls_dict[post_id]['dir'])
            return ft.IconButton(ft.icons.ARROW_DOWNWARD_ROUNDED, icon_color=get_color(self.controls_dict[post_id]['dir'], "downvote"), on_click=on_downvote)
        self.lv = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=False)
        def get_color(c_case : int, vote_type: str) -> str:
            match vote_type:
                case "upvote":
                    match c_case:
                        case 1: return "orange"
                        case 0: return "gray"
                        case -1: return "gray"
                case "downvote":
                    match c_case:
                        case 1: return "gray"
                        case 0: return "gray"
                        case -1: return "blue"
                case "text":
                    match c_case:
                        case 1: return "orange"
                        case 0: return "gray"
                        case -1: return "blue"
        async def make_post(post_id : str, feed_data):
            await self.page.clean_async()
            async def get_post_json():
                headers = {
                'Authorization': f'Bearer {access_token}'
                }
                request = aiohttp.request(
                method='GET',
                url=f"https://oauth.reddit.com/comments/{post_id[3:]}",
                headers=headers,
                )
                async with request as resp:
                    response_data = await resp.json()
                    return response_data
            post_data = await get_post_json()
            def get_comments(json_data):
                parsed_comments : list = []
                if json_data['kind'] == 't1' and json_data['data']['replies'] == '':
                    return {
                            "post-id":"t1_" + json_data['data']['id'],
                            "author": json_data['data']['author'],
                            "score": json_data['data']['score'],
                            "body": json_data['data']['body'],
                            "dir": json_data['data']['likes'],
                            "replies": [],
                        }
                else:
                    match json_data['kind']:
                        case 'Listing':
                            temp = []
                            for comment in json_data['data']['children']:
                                temp.append(get_comments(comment))
                            parsed_comments += temp
                        case 't1':
                            return {
                                "post-id":"t1_"+json_data['data']['id'],
                                "author": json_data['data']['author'],
                                "score": json_data['data']['score'],
                                "body": json_data['data']['body'],
                                "dir": json_data['data']['likes'],
                                "replies": get_comments(json_data['data']['replies'])
                            }
                return parsed_comments
            async def display_comments(json_data, indent : int = 0):
                lv = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=False)
                for comment in json_data:
                    t : ft.Text = ft.Text(value="",color="gray")
                    post_id = comment['post-id']
                    self.controls_dict[post_id]={
                        "post-id":comment['post-id'],
                        "author": comment['author'],
                        "score": comment['score'],
                        "body": comment['body'],
                        "dir": match_init_vote_case(comment['dir']),
                        "score-text" : t,
                    }
                    self.controls_dict[post_id]={
                        "post-id":comment['post-id'],
                        "author": comment['author'],
                        "score": comment['score'],
                        "body": comment['body'],
                        "dir": match_init_vote_case(comment['dir']),
                        "score-text" : t,
                        "upvote-button": await make_upvote_button(post_id, t),
                        "downvote-button": await make_downvote_button(post_id, t),  
                    }
                    t.value = self.controls_dict[post_id]['score']
                    t.color=get_color(self.controls_dict[post_id]['dir'],"text")
                    await self.page.update_async()
                    lv.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Column(
                                    [
                                        ft.Text(value=comment['author'],style=ft.TextThemeStyle.LABEL_MEDIUM, weight=ft.FontWeight.W_600),
                                        ft.Text(value=comment['body']),
                                        ft.Row([
                                            self.controls_dict[post_id]['upvote-button'],
                                            self.controls_dict[post_id]['score-text'],
                                            self.controls_dict[post_id]['downvote-button'],
                                        ]),
                                        ft.Row([
                                            await display_comments(comment['replies'], indent + 1)
                                        ]),
                                    ]
                                    , spacing=15
                                    ,scroll=ft.ScrollMode.AUTO
                                ),
                            ]
                            ),
                            margin = ft.margin.only(left= 100 + (indent * 15)),
                            border=ft.border.only(left=ft.border.BorderSide(4, "white")),
                            padding=ft.padding.only(left=20),
                            width=1200
                        )
                    )
                return lv
            async def on_click_refresh(e : ft.ControlEvent):
                nonlocal post_id, feed_data
                await self.page.clean_async()
                await make_post(post_id, feed_data)
            async def on_click_back(e : ft.ControlEvent):
                nonlocal access_token
                await self.page.clean_async()
                await App(self.page).display_feed(access_token)
            async def display_post():
                nonlocal feed_data
                lv = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=False)
                lv.controls.append(
                    ft.Column([
                        ft.Row([ft.IconButton(icon=ft.icons.ARROW_BACK_IOS_ROUNDED, on_click=on_click_back),ft.IconButton(icon=ft.icons.REFRESH, on_click=on_click_refresh)]),
                        ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Container(
                                            content=ft.Column([self.controls_dict[post_id]['upvote-button'], 
                                                self.controls_dict[post_id]['score-text'], 
                                                self.controls_dict[post_id]['downvote-button']],
                                                horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                            height=100,
                                        ),
                                        ft.Column([
                                                ft.Row([ft.Text(value=str(feed_data['data']['author']),weight=ft.FontWeight.W_600),
                                                        ft.Text(value=str(feed_data['data']['subreddit_name_prefixed']))], spacing=15),
                                                ft.Text(value=str(feed_data['data']['title'] ),style=ft.TextThemeStyle.TITLE_LARGE,weight=ft.FontWeight.W_600,width=(1920-400)),
                                                ft.Text(value=feed_data['data']['selftext'],width=1700), 
                                                ft.Container(
                                                    content=ft.Row([
                                                        ft.Icon(name=ft.icons.MESSENGER_OUTLINE_ROUNDED),
                                                        ft.Text(value=str(feed_data['data']['num_comments']) + " comments"),
                                                        ])
                                                    ,padding=ft.padding.only(top=50,bottom=20)
                                                ),
                                                ],wrap=True,width=700, spacing=20, scroll=ft.ScrollMode.HIDDEN) 
                                    ]
                                    , spacing=45
                                    ,vertical_alignment=ft.CrossAxisAlignment.START
                                )
                            ,padding=ft.padding.only(bottom=50,left=50)
                        ),
                    ], scroll=ft.ScrollMode.HIDDEN),
                )
                lv.controls.append(    
                    ft.Container(
                        content=await display_comments(get_comments(post_data[1])),
                        )
                    )
                return lv
            await self.page.add_async((await display_post()))
            await self.page.update_async()
        async def make_card(post_id : str, feed_data):
            async def load_post(post_id : str):
                nonlocal feed_data
                await make_post(post_id, feed_data)
            async def on_container_click(e : ft.ControlEvent):
                nonlocal post_id
                await load_post(post_id)
            def display_card():
                nonlocal feed_data
                return ft.Card(
                        content=ft.Container(
                            content=ft.Row(
                                [
                                    ft.Column([self.controls_dict[post_id]['upvote-button'], 
                                            self.controls_dict[post_id]['score-text'], 
                                            self.controls_dict[post_id]['downvote-button']], 
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                    ft.Column([ft.Text(value=str(feed_data['data']['title']), width=(1920-500)), 
                                            ft.Row([
                                                    ft.Text(value=str(feed_data['data']['created'])),
                                                    ft.Text(value=str(feed_data['data']['num_comments']) + " comments"),
                                                    ft.Text(value=str(feed_data['data']['author'])),
                                                    ft.Text(value=str(feed_data['data']['subreddit_name_prefixed'])),
                                                    ])],wrap=True,width=700) 
                                ]
                                , spacing=45
                            )
                        ,padding=50
                        ,alignment=ft.alignment.bottom_left
                        ,on_click = on_container_click
                        )
                    )
            return display_card()
        async def create_listview(feed):
            self.after_t3_id = str(feed['data']['after'])
            for i in range(0, 25):
                feed_data = feed['data']['children'][i]
                t : ft.Text = ft.Text(value="",color="gray")
                post_id = feed_data['data']['name']
                self.controls_dict[feed_data['data']['name']] = {
                    "score": feed_data['data']['score'],
                    "dir": match_init_vote_case(feed_data['data']['likes']),
                    "score-text": t,
                }
                self.controls_dict[feed_data['data']['name']] = {
                    "score": feed_data['data']['score'],
                    "dir": match_init_vote_case(feed_data['data']['likes']),
                    "score-text": t,
                    "upvote-button": await make_upvote_button(post_id, t),
                    "downvote-button": await make_downvote_button(post_id, t),
                }
                t.value=str(self.controls_dict[feed_data['data']['name']]['score'])
                t.color=get_color(self.controls_dict[feed_data['data']['name']]['dir'],"text")
                self.lv.controls.append(await make_card(post_id, feed_data))
                if i >=24:
                    self.lv.controls.append(ft.ElevatedButton(text="Load More...", width="100%", on_click=on_click_load_more))
                else:
                    continue
            await self.page.update_async()
            await self.page.add_async(self.lv)
        await create_listview(r)
        await self.page.update_async()
    async def display(self):
        b_auth_url : str = ""
        b_auth_api: str = ""
        b_auth_url_field = ft.TextField(label='Base Auth URL', value="https://www.reddit.com")
        b_auth_api_field = ft.TextField(label='Base API URL', value="https://oauth.reddit.com")
        self.page.appbar = ft.AppBar(
            leading=ft.Icon(ft.icons.REDDIT_ROUNDED),
            leading_width=40,
            title=ft.Text("Login")
        )
        async def on_login_button(e:ft.ControlEvent):
            b_auth_url = b_auth_url_field.value
            b_auth_api = b_auth_api_field.value
            provider = OAuthProvider(
                client_id="b9ep6t9JoJ4zkv1NYXiWHw",
                client_secret='',
                authorization_endpoint=f'{b_auth_url}/api/v1/authorize.compact?duration=permanent',
                token_endpoint=f'{b_auth_url}/api/v1/access_token',
                redirect_url='https://cs12222project-dy-denzell-robyn.onrender.com/api/oauth/redirect',
                user_scopes=['identity','read','vote']
            )
            await self.page.login_async(provider, authorization=MyAuthorization)
        login_button = ft.ElevatedButton('Login', on_click=on_login_button)
        await self.page.add_async(b_auth_url_field)
        await self.page.add_async(b_auth_api_field)
        await self.page.add_async(login_button)
    @classmethod
    async def main(cls, page:ft.Page) -> None:
        async def on_login(e:ft.ControlEvent):
            if e.error:
                print("Error")
                return
            else:
                access_token = page.auth.token.access_token
                print("Access Token: ", access_token)
                await App(page, page.auth.token.access_token).display_feed(access_token)
        page.on_login = on_login
        await App(page).display()
class Controls():
    score : int
    checker : bool    
class MyAuthorization(Authorization):
            def __init__(self, *args, **kwargs):
                super(MyAuthorization, self).__init__(*args, **kwargs)

            def _Authorization__get_default_headers(self):
                username = "b9ep6t9JoJ4zkv1NYXiWHw"
                encoded = base64.b64encode(f'{username}:'.encode('utf8')).decode('utf8')
                return {"User-Agent": f"Flet/0.6.2", "Authorization": f"Basic {encoded}"}
app = ft.app(target=App.main, port=80, view=ft.WEB_BROWSER)