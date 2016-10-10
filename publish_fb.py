#!/usr/bin/python

import json, os, requests, sys

access_token = 'EAAXutiFG06gBADArZBBriLTsGrZC7vYOfZCup2B7QHXY9O6O4URcbmoOQMsYdy3zUZAVLhIz6S1DgchHs9QIbZCCK1RXFIbt6qL0tKG9UzQf7CZBJu6YCKevQDpEYWZBUieRVNUgWX4jF2vUTmef3ChvFv8eCRxcKZAxKKfQbWKvugZDZD'
id = '1519143218341774'
url = 'https://admin.storewalk.in:1133/catalogue/usergenerated/imagelist/XJV2CWPdM'

def get_state():
    filename = 'config.json'
    try:
        with open(filename) as f_obj:
            data = json.load(f_obj)
            print(data)
            no_of_albums = data['N']
            counter = data['counter']
    except FileNotFoundError:
        print(filename + ' does not exist.')
        return None, None
    except KeyError:
        print('unsupported config file.')
        return None, None
    else:
        try:
            no_of_albums = int(no_of_albums)
            counter = int(counter)
        except ValueError:
            print('invalid types in config file.')
            return None, None
        else:
            return no_of_albums, counter

def write_state(no_of_albums, counter):
    filename = 'config.json'
    with open(filename, 'w'):
        pass
    state = {'N': no_of_albums, 'counter': counter}
    try:
        with open(filename, 'w') as f_obj:
            json.dump(state, f_obj)
    except FileNotFoundError:
        print(filename + ' does not exist.')

def get_album(url):
    try:
        res = requests.get(url, headers={'version': 'A'})
    except:
        print('unable to get album.')
        return None
    else:
        data = json.loads(res.text)
        if 'status' in data and data['status'] == 'PASS':
            data = data['message'][0]
            if not data:
                return None
            else:
                return data
        else:
            return None
        
def post_to_fb(id, payload):
    url = 'https://graph.facebook.com/v2.7/'+id+'/photos/'
    try:
        res = requests.post(url, data=payload, headers={})
    except:
        print('unable to post')
        return None
    else:
        if res.status_code == 200:
            photo_id = json.loads(res.text)['id']
            print('uploaded successfully.')
            return photo_id
        else:
            print(res.text)
            print('uploading failed.')
            return None

def get_image_list(url):
    try:
        res = requests.get(url)
    except:
        print('unable to fetch image list.')
        return None
    else:
        data = json.loads(res.text)
        if 'status' in data and data['status'] == 'PASS':
            data = data['message']
            if not data:
                return None
            else:
                return data
        else:
            return None

def get_unpublished_ids(image_list):
    unpublished_ids = []
    for image in image_list:
        #create payload
        payload = {'url': image['banner'],
                   'access_token': access_token,
                   'caption': image['tags'],
                   'published': 'false'}
        photo_id = post_to_fb(id, payload)
        if photo_id != None:
            unpublished_ids.append(photo_id)
    return unpublished_ids

def post_album(image_list, description):
    url = 'https://graph.facebook.com/v2.7/'+id+'/feed'
    unpublished_ids = get_unpublished_ids(image_list)
    #create payload
    payload = {'message': description, 'access_token': access_token}
    for i in range(len(unpublished_ids)):
        payload['attached_media['+str(i)+']'] = '{media_fbid:'+unpublished_ids[i]+'}'
    print(payload)
    try:
        res = requests.post(url, data=payload, headers={})
    except:
        print('album upload failed')
    else:
        print(res.text)

#main
N, counter = get_state()
if N != None and counter != None:
    for i in range(N):
        url = 'https://admin.storewalk.in:1133/'\
              +'catalogue/v3/collections/online/1/'\
              +str(counter)
        album = get_album(url)
        print(counter)
        counter += 1
        print(counter)
        if album != None:
            album_id = album['albumId']
            url = 'https://admin.storewalk.in:1133/catalogue/usergenerated/imagelist/'+album_id
            #process album and get image list
            image_list = get_image_list(url)
            if image_list != None:
                post_album(image_list, album['albumDescription'])
                write_state(N, counter)
            else:
                print('empty image list.')
        else:
            print('album does not exist.')
