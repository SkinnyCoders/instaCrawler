import urllib.request
from urllib.error import HTTPError, URLError
import requests
import json
import os
import re
import pyquery
import get_comments
import time
import sys
import logging
from socket import timeout

all_posts = []
post_cnt = 0

def writeDataToJson(data):
    global dname
    with open(dname + 'data_instagram.json', 'w') as outfile:
        json.dump(data, outfile)

def get_web_url(url):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            print('Failed', response.status_code)
    except Exception as e:
        print(e)

def get_post(edges):
    global all_post
    global post_cnt

    for edge in edges:
        shortcode = edge['node']['shortcode']
        url_shortcode = 'https://www.instagram.com/p/'+shortcode+'/?__a=1'
        with urllib.request.urlopen(url_shortcode) as temp_u:
            js_data = json.loads(temp_u.read().decode('utf-8'))

        #get all comments
        comments = get_comments.get_comments(shortcode)
        # comments = None

        photo_in_post_count=0
        post = []
        caption = None
        timestamp = None

        # jika foto lebih dari satu 
        if 'edge_sidecar_to_children' in js_data['graphql']['shortcode_media']:
            edges_shortcode = js_data['graphql']['shortcode_media']['edge_sidecar_to_children']['edges']
        
            for edge_s in edges_shortcode:
                # get content url
                if edge_s['node']['is_video'] and edge_s['node']['video_url'] != 'https://static.cdninstagram.com/rsrc.php/null.jpg':
                    display_url = edge_s['node']['video_url']
                elif edge_s['node']['display_url']:
                    display_url = edge_s['node']['display_url']
                post.append(display_url)

            # mengambil caption
            try:
                try_caption = edge['node']['edge_media_to_caption']['edges'][0]['node']['text']
                caption = edge['node']['edge_media_to_caption']['edges'][0]['node']['text']
            except:
                caption = None

            # mengambil timestamp
            try:
                try_timestamp = edge['node']['taken_at_timestamp']
                timestamp = edge['node']['taken_at_timestamp']
            except:
                timestamp = None

            try:
                typename = edge['node']['__typename']
            except:
                typename = None

            id_post =  edge['node']['id']

            try:
                total_like = edge['node']['edge_media_preview_like']['count']
            except:
                total_like = None

            if(edge['node']['is_video']):
                video_view = edge['node']['video_view_count']
            else:
                video_view = None

            location_data = {}
            try:
                location_data['location_name'] = edge['node']['location']['name']
                location_data['address_json'] = js_data['graphql']['shortcode_media']['location']['address_json']
            except:
                location_data = None

            data['post'].append({   
                '__typename' : typename,
                'id' :  id_post,
                'content_url' : post,
                'caption' : caption, 
                'total_like' : total_like,
                'video_view_count': video_view,
                'timestamp' : timestamp, 
                'location' : location_data,
                'comments' : comments
            })
            writeDataToJson(data)
            post_cnt=post_cnt+1  
        else:    
            # jika data berupa gambar     
            if js_data['graphql']['shortcode_media']['is_video'] and js_data['graphql']['shortcode_media']['video_url'] != 'https://static.cdninstagram.com/rsrc.php/null.jpg':
                display_url = js_data['graphql']['shortcode_media']['video_url']
                media_type = 'video'
            elif js_data['graphql']['shortcode_media']['display_url']:
                media_type = 'image'
                display_url = js_data['graphql']['shortcode_media']['display_url']

            post.append(display_url)

            # mengambil caption
            try:
                try_caption = edge['node']['edge_media_to_caption']['edges'][0]['node']['text']
                caption = edge['node']['edge_media_to_caption']['edges'][0]['node']['text']
            except:
                caption = None

            # mengambil timestamp
            try:
                try_timestamp = edge['node']['taken_at_timestamp']
                timestamp = edge['node']['taken_at_timestamp']
            except:
                timestamp = None

            try:
                typename = edge['node']['__typename']
            except:
                typename = None

            id_post =  edge['node']['id']

            try:
                total_like = edge['node']['edge_media_preview_like']['count']
            except:
                total_like = None

            if(edge['node']['is_video']):
                video_view = edge['node']['video_view_count']
            else:
                video_view = None

            location_data = {}
            try:
                location_data['location_name'] = edge['node']['location']['name']
                location_data['address_json'] = js_data['graphql']['shortcode_media']['location']['address_json']
            except:
                location_data = None

            data['post'].append(
                {   
                    '__typename' : typename,
                    'id' :  id_post,
                    'content_url' : display_url,
                    'caption' : caption, 
                    'total_like' : total_like,
                    'video_view_count': video_view,
                    'timestamp' : timestamp, 
                    'location' : location_data,
                    'comments' : comments
                })
            writeDataToJson(data)
            # with open(dname + 'data.json', 'w') as outfile:
            #     json.dump(data, outfile)
        all_posts.append(post)
        post_cnt=post_cnt+1

def next_url(user_id, first_cursor):
    try:
        url_next = 'https://instagram.com/graphql/query/?query_id=17888483320059182&id='+user_id+'&first=50&after='+first_cursor
        with urllib.request.urlopen(url_next, timeout=5) as temp_u:
            url_next_data = json.loads(temp_u.read().decode('utf-8'))

    except (HTTPError, URLError) as error:
        print('Data of instagram not retrieved because ERROR, URL: [' +url_next+ ']')
        return False
    except ConnectionResetError:
        print('connection to '+url_next+' was error')
        return False
    except timeout:
        print('Socket timed out')
        #  logging.error('socket timed out - URL : '+url)
        return False

    return url_next_data

#username instagram target crawling
if len(sys.argv) > 1:
    user_name = sys.argv[1]
else:
    print('ERROR: params username is undefined')
    exit()
    
#path file location
dname = '/home/ristanto/Documents/data_ig3/'
# check folder is exist
if not os.path.exists(dname):
    os.makedirs(dname)
else:
    print(dname," already set")

#total query post = 12*(max_post_iter+1)
max_post_iter=10000


url = 'https://www.instagram.com/' + user_name
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
}

html = get_web_url(url)
user_id = re.findall('profilePage_([0-9]+)', html, re.S)[0]
doc = pyquery.PyQuery(html)
items = doc('script[type="text/javascript"]').items()
data = {}

print("user_id:", user_id)
print("url:",url)

for item in items:
    if item.text().strip().startswith('window._sharedData'):
        js_data = json.loads(item.text()[21:-1].encode('utf-8'))
        # print(js_data)
        edges = js_data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['edges']
        bios = js_data['entry_data']['ProfilePage'][0]['graphql']['user']['biography']
        full_name = js_data['entry_data']['ProfilePage'][0]['graphql']['user']['full_name']
        username = js_data['entry_data']['ProfilePage'][0]['graphql']['user']['username']
        followers = js_data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_followed_by']['count']
        follows = js_data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_follow']['count']
        cursor = js_data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['page_info']['end_cursor']
        flag = js_data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['page_info']['has_next_page']
        
        print("get post from: "+user_name, str(len(edges)))
        data['id_user'] = user_id
        data['username'] = username
        data['full_name'] = full_name
        data['url_user'] = url
        data['biography_user'] = bios
        data['followers_user'] = followers
        data['follows_user'] = follows
        data['post'] = []
        get_post(edges)
        
for index in range(0, max_post_iter):  
    if (flag):
        js_data = next_url(user_id, cursor)
        if(js_data):
            edges = js_data['data']['user']['edge_owner_to_timeline_media']['edges']
            cursor = js_data['data']['user']['edge_owner_to_timeline_media']['page_info']['end_cursor']
            flag = js_data['data']['user']['edge_owner_to_timeline_media']['page_info']['has_next_page']
            print('get next post from '+ username, str(len(edges)))
            get_post(edges)
        else:
            pass
        
    else:
        break

# print(data)
writeDataToJson(data)
# with open(dname + 'data1.json', 'w') as outfile:
#     outfile.write(json.dumps(data))
    # json.dump(data, outfile)