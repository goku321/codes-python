#!/usr/bin/python

import json, os, sys, requests

access_token = 'AXkAcqOQLa9UzpucHrIimseai89JFHwfLddXoPJDd0toEAAubQAAAAA'

def get_state():
    filename = 'pinterest_config.json'
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
    filename = 'pinterest_config.json'
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

#method to create a board
def create_board(access_token, name, description=''):
    url = 'https://api.pinterest.com/v1/boards/?'\
          +'access_token='+access_token+'&fields=id'
    print(url)
    payload = {"name": name,
               "description": description}
    try:
        res = requests.post(url, data=payload)
    except:
        print('board cannot be created')
        return None
    else:
        board_id = None
        if res.status_code == 201:
            response = json.loads(res.text)
            board_id = response['data']['id']
            print(board_id, response)
        return board_id

def create_pin(board_id, desc, image_url, link=''):
    url = 'https://api.pinterest.com/v1/pins/?'\
          +'access_token='+access_token
    #create payload
    payload = {"board": board_id,
               "note": desc, "link":link,
               "image_url": image_url}
    try:
        res = requests.post(url, data=payload)
    except:
        print('pin cannot be added.')
    else:
        if res.status_code == 201:
            print('pin added successfully.')
        else:
            print('pin cannot be added.')

def post_to_pinterest(image_list, board_name):
    #create board
    board_id = create_board(access_token, board_name)
    #create pins
    for image in image_list:
        create_pin(board_id, image['tags'], image['banner'])

#main
N, counter = get_state()
if N!= None and counter != None:
    for i in range(N):
        url = 'https://admin.storewalk.in:1133/'\
              +'catalogue/v3/collections/online/1/'\
              +str(counter)
        #fetch album
        album = get_album(url)
        counter += 1
        if album != None:
            album_id = album['albumId']
            url = 'https://admin.storewalk.in:1133/catalogue/usergenerated/imagelist/'+album_id
            #fetch images
            image_list = get_image_list(url)
            if image_list != None:
                post_to_pinterest(image_list, album['albumDescription'])
                write_state(N, counter)
                #create a board
                #add pins to the board
                #create_pin(board_id, desc, link, image_url)
            else:
                print('empty image list.')
        else:
            print('album does not exist.')
