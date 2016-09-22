#!/usr/bin/python

import os, sys
import facepy, json, pymysql, requests

f = open('error_log', 'w')
app_id = 169563383448696
app_secret = 'd05e8e420ee33f7740e94ee2408b17d2'

def find_page_id(store_name):
    access_token = get_access_token(app_id, app_secret)
    get_response = requests.get('https://graph.facebook.com/v2.7/search?q='+store_name+'&type=page&limit=1&fields=id&access_token='+access_token)

    try:
        page_id = json.loads(get_response.text)['data'][0]['id']
    except IndexError:
        return None
    except KeyError:
        return None
    else:
        return page_id

def get_image_urls(page_id, owner):
    access_token = get_access_token(app_id, app_secret)
    #list to hold data
    data = []

    #api call for album list
    get_response = requests.get('https://graph.facebook.com/'+page_id+'?fields=about,albums.limit(10){name, id, description, photos.limit(10){id, name, images}}&access_token='+access_token)

    try:
        albums_list = json.loads(get_response.text)['albums']['data']
        about_store = json.loads(get_response.text)['about']
    except KeyError:
        return None
    else:
        #iterating over albums_list to extract details about albums
        for album in albums_list:
            album_id = album['id']
            album_name = album['name']
            owner_id = page_id
            owner_name = owner 
            album_description = ''
            image_name = ''
            image_tags = ''
            album_desc = ''
            if 'description' in album:
                album_desc = album['description']
            #owner_name = store_name
            try:
                images_list = album['photos']['data']
            except KeyError:
                return None
            else:
                image_urls = []

                #iterating over images_list to extract image urls
                for image in images_list:
                    image_id = image['id']
                    if 'name' in image:
                        image_name = image['name']
                        image_tags = get_image_tags(image_name)
                    if image['images']:
                        try:
                            image_urls.append({'image_name': image_name, 'image_id': image_id, 'image_url': image['images'][2]['source'], 'image_tags': image_tags})
                        except:
                            image_urls.append({'image_id': image_id, 'image_url': image['images'][0]['source'], 'image_name': image_name, 'image_tags': image_tags})

                #appending a dictionary of info to a list
                temp_dict = {'album_id': album_id, 'album_name': album_name,\
                            'owner_id': owner_id, 'owner_name': owner_name, \
                            'image_urls': image_urls, \
                            'album_desc': album_desc, 'about_store': about_store}
                data.append(temp_dict)

        return data

def insert_data(db_connection, data, store_name):
    cursor = db_connection.cursor()

    #insert data into table fbStoreId
    insert_query = "INSERT INTO fbStoreId  (sellerId, storeName, \
                    fbBusinessId, aboutStore) VALUES ('" + store_name + "','" + \
                    data[0]['owner_name'] + "','" + data[0]['owner_id'] + "','" + \
                    data[0]['about_store']+"')"
    try:
        cursor.execute(insert_query)
    except:
        print('insert query failed1')
        f.write(insert_query+'\n')
        return None
    else:
        db_connection.commit()

    #insert data into table fbStoreAlbum
    for album in data:
        insert_query = "INSERT INTO fbStoreAlbum (AlbumId, fbBusinessId, \
                        albumName, description, ownerName) VALUES ('" +\
                        album['album_id'] + "','" + album['owner_id'] + "','" \
                        + album['album_name'] + "','" + album['album_desc'] + \
                        "','" + album['owner_name'] + "')"
        try:
            cursor.execute(insert_query)
        except:
            print('insert query failed2')
            f.write(insert_query+'\n')
            pass
            #return None
        else:
            db_connection.commit()

    #insert data into table fbAlbumImage
    for item in data:
        images_list = item['image_urls']
        for image in images_list:
            insert_query = "INSERT INTO fbAlbumImage (imageId, albumId, \
                    fbImageUrl, swImageUrl, imageName, imageTags) VALUES ('" + \
                    image['image_id'] + "','" + item['album_id'] + "','" + \
                    image['image_url'] + "','" + '' + "','" + \
                    image['image_name'] + "','" + image['image_tags']+"')"
            try:
                cursor.execute(insert_query)
            except:
                print('insert query failed3')
                f.write(insert_query+'\n')
                pass
                #return None
            else:
                db_connection.commit()

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
        db_connection = pymysql.connect(host='storewalk.cmmvprsamssl.ap-southeast-1.rds.amazonaws.com', user='labdesk', passwd='labd3sk123', db='storewalk')
    except:
        return None
    else:
        return db_connection

def get_access_token(app_id, app_secret):
    access_token = facepy.utils.get_application_access_token(app_id, app_secret)
    return access_token

def querydB(db_connection, table_name, seller_id):
    cursor = db_connection.cursor()
    query = "select * from " + table_name + " where sellerId = \
            '"+seller_id+"'"
    cursor.execute(query)
    length = len(cursor.fetchall())
    if length:
        return True
    else:
        return False

def get_sellers_list(db_connection, table_name):
    cursor = db_connection.cursor()
    query = 'SELECT seller_id, store_name FROM ' + table_name
    cursor.execute(query)
    response = cursor.fetchall()
    return response

#main
db_connection = get_db_connection()
#get user access token

sellers_list = get_sellers_list(db_connection, 'seller_profile')
for seller_id, store_name in sellers_list:
    print(seller_id, store_name)
    response = querydB(db_connection, 'fbStoreId', seller_id)
    if response:
        #update
        pass
    else:
        page_id = find_page_id(store_name)
        if page_id == None:
            print('page for '+store_name+' does not exist.')
        else:
            data = get_image_urls(page_id, store_name)
            if data == None:
                print('no albums exist for ' + store_name)
            else:
                insert_data(db_connection, data, store_name)

f.close()
