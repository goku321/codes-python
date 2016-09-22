#!/usr/bin/python

import os, sys
import json, pymysql, requests
from facepy import utils

app_id = 169563383448696
app_secret = 'd05e8e420ee33f7740e94ee2408b17d2'
data = []

# Returns timestamp of last Entry

def get_last_entry_time(dbConnection,table_name):
    cursor = dbConnection.cursor()
    #SELECT  createdAt FROM fbAlbumList_copy ORDER BY createdAt DESC LIMIT 1
    query = "select createdAt from "+table_name+" order by createdAt DESC LIMIT 1"
    cursor.execute(query)
    time = cursor.fetchall()
    print(time)
    return time[0][0]

def get_album_list(url):
    get_response = requests.get(url)
    data_dict = json.loads(get_response.text)
    try:
        album_list = data_dict['albums']['data']
    except KeyError:
        return None, None
    else:
        next_url = ''
        if 'paging' in data_dict:
            if 'next' in data_dict['paging']:
                next_url = data_dict['paging']['next']
        return album_list, next_url

def get_image_list(url):
    get_response = requests.get(url)
    try:
        image_list = json.loads(get_response.text)['photos']['data']
    except KeyError:
        return None
    else:
        return image_list

def get_image_urls(image_list):
    image_urls = []
    for image in image_list:
        image_tags = ''
        image_url = image['images'][0]['source']
        image_name = ''
        #define get_image_tags method
        if 'name' in image:
            image_tags = get_image_tags(image['name'])
            image_name = image['name']
        #do something with image url
        image_data = {'id':image['id'], 'name': image_name,\
                      'created_time': image['created_time'],\
                      'url': image_url, 'tags': image_tags}
        image_urls.append(image_data)
    return image_urls
        
def process_albums(url, created_time, access_token):
    while url:
        album_list, next_url = get_album_list(url)
        for album in album_list:
            album_created_time = album['created_time']
            if album_created_time > created_time:
                album_id = album['id']
                album_name = album['name']
                owner_name = album['from']['name']
                owner_id = album['from']['id']
                album_description = ''
                if 'description' in album:
                    album_description = album['description']
                #get image list from this album
                album_url = 'https://graph.facebook.com/'+album_id+\
                            '?fields=photos.limit(100){created_time,id, name, images}'\
                            +'&access_token='+access_token
                image_list = get_image_list(album_url)
                #print(image_list)
                image_urls = get_image_urls(image_list)
                album_data = {'id': album_id, 'name': album_name,\
                              'desc': album_description, 'created_time'\
                              : album_created_time, 'owner_id': owner_id,\
                              'owner_name': owner_name, 'images': image_urls}
                data.append(album_data)
                
                pass
            else:
                #skip this album
                pass
            url = next_url
    return data

def get_image_tags(image_name):
    tags = ''
    while image_name.find('#') != -1:
        i = image_name.find('#')
        image_name = image_name[i:]
        j = image_name.find(' ')
        if j != -1:
            tags = image_name[1:j] + ',' + tags
            image_name = image_name[j+1:]
        else:
            tags = image_name[1:] + ',' + tags
            image_name = ''
    return tags

def get_db_connection():
    try:
        db_connection = pymysql.connect(host=\
                        'storewalk.cmmvprsamssl.ap-southeast-1.rds.amazonaws.'\
                                        +'com', user='labdesk',\
                                        passwd='labd3sk123', db='storewalk')
    except:
        return None
    else:
        return db_connection

def get_access_token(app_id, app_secret):
    access_token = utils.get_application_access_token(app_id, app_secret)
    #extended_access_token = utils.get_extended_access_token(access_token,
                                                            #app_id, app_secret)
    return access_token

def insert_data(db_connection, data):
    cursor = db_connection.cursor()
    cursor.execute('SET NAMES utf8;')
    cursor.execute('SET CHARACTER SET UTF8;')
    cursor.execute('SET character_set_connection=utf8;')

    #insert data into table1
    for album in data:
        insert_query = "INSERT INTO fbAlbumList_test (albumId, albumName,"\
                       +" albumDescription, createdAt, createdBy,"\
                       +" ownerId, profileImage, viewsCount) VALUES ('"\
                       + album['id'] + "','" + album['name'] + "','" \
                       + album['desc'] + "','" + album['created_time'] + "','"\
                       + album['owner_name'] + "','" + album['owner_id']\
                       + "','" +'profile' + "','" + '100' + "')"
        try:
            cursor.execute(insert_query)
            print('success')
        except:
            print('insert query failed1')
            print(insert_query)
            pass
        else:
            db_connection.commit()

    #insert data into table2
    for album in data:
        image_list = album['images']
        for image in image_list:
            #write insert query here
            insert_query = "INSERT INTO collections_test (title, banner,"\
                           +" description, tag, store, active, customActive"\
                           +", brand, type, parent, child, width, height, "\
                           +"`group`, showTitle, showDescription, bannerId, "\
                           +"priceRange, text3, gtag, catalogueVersion, "\
                           +"wizard, tags, sellerTags, albumName, imageId, "\
                           +"albumId, url1, url2, owner, ownerId, profileImage"\
                           +", albumIcons, onlineUrl) VALUES ('"+''\
                           +"','" + 'banner' + "','" + image['name'] + "','" + \
                           image['tags'] + "','" + '0' + "','" + '1' + "','"\
                           + '1' + "','" + 'brand' + "','" + 'type' + "','" \
                           + 'parent' + "','" + 'child' + "','" + '100' +"','"\
                           +'100' + "','" + '' + "','" + '1' + "','"\
                           +'1' + "','" + 'banner' + "','" + 'price' + "','"\
                           +'text3' + "','" + 'gtag' + "','" + 'version' + "','"\
                           + '0' + "','" + image['tags'] + "','" + 'sellertags' \
                           + "','" + album['name'] + "','" + image['id'] + "','" \
                           +album['id'] + "','" + image['url'] + "','"  +\
                           'url2' + "','" + album['owner_name'] + \
                           "','" + album['owner_id'] + "','" + 'profile' + \
                           "','" + 'icons' + "','" + 'online_url' "')"
            try:
                cursor.execute(insert_query)
            except:
                print('insert query failed2')
                print(insert_query)
                pass
            else:
                db_connection.commit()
#main
group_id = str(1348546491841540)
#get access token
access_token = get_access_token(app_id, app_secret)
db_connection = get_db_connection()
url = 'https://graph.facebook.com/'+group_id+'?'\
      +'fields=albums.limit(100){id, name,'\
      +' created_time, from}&access_token='\
      +access_token
#created_time = get_last_entry_time(db_connection, 'fbAlbumList_test')
created_time = "2015-09-22T10:02:43+0000"
data = process_albums(url, created_time, access_token)
#insert data into db
l = data[0:2]
insert_data(db_connection, l)
