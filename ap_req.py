import requests

def get_posts():
    url = 'https://dictionaryapi.com/api/v3/references/collegiate/json/{}?key=5ee324bd-b771-49b5-9ccf-79291f952239'.format('bacchanal')

    try:
        response = requests.get(url)
        print(response)
        if response.status_code == 200:
            posts = response.json()
            return posts
        else:
            print('Error:', response.status_code)
            return None
    except requests.exceptions.RequestException as e:
        print('Error:', e)
        return None

def main():
    posts = get_posts()
    print(len(posts))
    print(posts)
    if posts:
        for val in posts:
            print('First Post Title:', val.get('meta'))
            print('First Post Title:', val.get('meta').get('id'))
            print('First Post Body:', val.get('et'))
            print('First Post Body:', val['fl'])
            print('First Post Body:', val['shortdef'])
    else:
        print('Failed to fetch posts from API.')

if __name__ == '__main__':
    main()