import requests
import json
import os
import pyquery
import urllib
import time
from requests.exceptions import Timeout

def set_replies_comment(replies):
    replies_comments = []
    z = 0
    while z < len(replies):
        
        data_replies = {}

        data_replies['id_comment'] = replies[z]['node']['id']
        data_replies['text_comment'] = replies[z]['node']['text']
        data_replies['timestamp_comment'] = replies[z]['node']['created_at']
        # data_replies['liked_comment'] = replies[z]['node']['edge_liked_by']['count']
        data_replies['user_name_comment'] = replies[z]['node']['owner']['username']
        data_replies['user_id_comment'] = replies[z]['node']['owner']['id']
        data_replies['user_profil_pic_url'] = replies[z]['node']['owner']['profile_pic_url']
        
        z += 1

        replies_comments.append(data_replies)
        
    return replies_comments

def set_comments(comments):
    data_comments = []
    
    i = 0
    while i < len(comments):
        data = {}
        
        data['id_comment'] = comments[i]['node']['id']
        data['text_comment'] = comments[i]['node']['text']
        data['timestamp_comment'] = comments[i]['node']['created_at']
        # data['liked_comment'] = comments[i]['node']['edge_liked_by']['count']
        data['user_name_comment'] = comments[i]['node']['owner']['username']
        data['user_id_comment'] = comments[i]['node']['owner']['id']
        data['user_profil_pic_url'] = comments[i]['node']['owner']['profile_pic_url']

        if 'edge_threaded_comments' in comments[i]['node']:
            cek_replies = comments[i]['node']['edge_threaded_comments']['count']
            
            if  cek_replies > 0 :
                data['replies_comments'] = set_replies_comment(comments[i]['node']['edge_threaded_comments']['edges'])

            else:
                data['replies_comments'] = None

        else:
            data['replies_comments'] = None

        data_comments.append(data)
        i+=1

    return data_comments

def get_comments(shortcode):
    list_data = []
    req = requests.get('https://www.instagram.com/p/'+shortcode+'/')
    html = req.text
    doc = pyquery.PyQuery(html)
    items = doc('script[type="text/javascript"]').items()

    for item in items:
        if item.text().strip().startswith('window._sharedData'):
            js_data = json.loads(item.text()[21:-1].encode('utf-8'))
            comments = js_data['entry_data']['PostPage'][0]['graphql']['shortcode_media']['edge_media_to_parent_comment']['edges']
            flag = js_data['entry_data']['PostPage'][0]['graphql']['shortcode_media']['edge_media_to_parent_comment']['page_info']['has_next_page']
            cursor = js_data['entry_data']['PostPage'][0]['graphql']['shortcode_media']['edge_media_to_parent_comment']['page_info']['end_cursor']
            list_data.extend(set_comments(comments))
            print('get first comment row :'+ str(len(comments)))
            # print('is next : '+flag)
            # print(cursor)

    for index in range(0, 1000000):
        time.sleep(1)
        if(flag):
            try:
                headers = {
                    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36',
                    'cookie': 'ig_did=5A7E6D98-EDA5-47E4-AA37-D63A5A4131FF; mid=X0c3GgAEAAG1L7MoyqFB5_BBgrZo; ig_nrcb=1; ds_user_id=44471480152; rur=RVA; csrftoken=GGENO6d3tXsR7W1lnum4T0p5vI8RyhBx; sessionid=44471480152%3A5tSMBhR5Vhw4U5%3A27; urlgen="{\"103.121.213.202\": 58495}:1kadMU:1NleVhbLWtn93fUWRDcKpI9J0oQ"',
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
                }
                
                url_next = 'https://www.instagram.com/graphql/query/?query_hash=33ba35852cb50da46f5b5e889df7d159&variables={"shortcode":"'+shortcode+'","first":50,"after":"'+cursor+'"}'
                
                cookies = {'instagram.com': 'ig_pr'}
                req_comment = requests.get(url_next,headers=headers, cookies=cookies)
                html_next_comment = req_comment.text

                jdata = json.loads(html_next_comment.encode('utf-8'))
                # print(jdata)
                next_comments = jdata['data']['shortcode_media']['edge_media_to_comment']['edges']
                flag = jdata['data']['shortcode_media']['edge_media_to_comment']['page_info']['has_next_page']
                cursor = jdata['data']['shortcode_media']['edge_media_to_comment']['page_info']['end_cursor']
                print('get next comment row :'+str(len(next_comments)) )
                # print('is next : ' +flag)
                # print(cursor)
                list_data.extend(set_comments(next_comments))
            except Timeout:
                print("failed to get commets, request timed out")
            except:
                print("failed to get data comments")
        else:
            break

    return list_data
    
# print(get_comments())
# with open('/home/ristanto/data_comment_kyli.json', 'w') as outfile:
#     json.dump(data_comments, outfile)
# # print(data_comments)