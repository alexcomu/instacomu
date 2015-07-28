import bottle_session
import bottle
from bottle import route, redirect, post, run, request
from instagram import client, subscriptions

bottle.debug(True)

app = bottle.app()
plugin = bottle_session.SessionPlugin(cookie_lifetime=6000)
app.install(plugin)

CONFIG = {
    'client_id': '120ccddf9ac647b19535cea821e8cf8b',
    'client_secret': 'f30aba766da14e3f8ee6223242db82b9',
    'redirect_uri': 'http://0.0.0.0:8080/oauth_callback'
}

unauthenticated_api = client.InstagramAPI(**CONFIG)

def process_tag_update(update):
    print update

reactor = subscriptions.SubscriptionsReactor()
reactor.register_callback(subscriptions.SubscriptionType.TAG, process_tag_update)

@route('/')
def home():
    try:
        url = unauthenticated_api.get_authorize_url(scope=["likes","comments"])
        return '<a href="%s">Connect with Instagram</a>' % url
    except Exception, e:
        print e

def get_nav(): 
    nav_menu = ("<h1>HACKADEMY TEST - python example</h1>"
                "<ul>"
                    "<!-- <li><a href='/recent'>User Recent Media</a> Calls user_recent_media - Get a list of a user's most recent media</li>"
                    "<li><a href='/user_media_feed'>User Media Feed</a> Calls user_media_feed - Get the currently authenticated user's media feed uses pagination</li>"              
                    "<li><a href='/location_recent_media'>Location Recent Media</a> Calls location_recent_media - Get a list of recent media at a given location, in this case, the Instagram office</li>"
                    "<li><a href='/media_search'>Media Search</a> Calls media_search - Get a list of media close to a given latitude and longitude</li>"
                    "<li><a href='/media_popular'>Popular Media</a> Calls media_popular - Get a list of the overall most popular media items</li>"
                    "<li><a href='/user_search'>User Search</a> Calls user_search - Search for users on instagram, by name or username</li>"
                    "<li><a href='/user_follows'>User Follows</a> Get the followers of @instagram uses pagination</li>"
                    "<li><a href='/location_search'>Location Search</a> Calls location_search - Search for a location by lat/lng</li>"      
                    "<li><a href='/tag_search'>Tags</a> Search for tags, view tag info and get media by tag</li>-->"
                    "<li><a href='/hackademy/selfie'>HACKADEMY</a> hackademy is great!</li>"
                    "<li><a href='/ask/selfie'>ASK</a> Ask!</li>"
		"</ul>")
            
    return nav_menu

@route('/ask/<tag>')
def ask(session, tag="selfie"):
    import requests, json
    cont = page = 0
    stopCondition = True
    body = []
    photos = []
    access_token = session.get('access_token')
    content = "<br><h3>Results for tag: <u>%s</u></h3><br>" % tag
    if not access_token:
        return 'Missing Access Token'
    try:
        api = client.InstagramAPI(access_token=access_token)
        next_req = "https://api.instagram.com/v1/tags/%s/media/recent?access_token=%s" % (tag, access_token)
        while(stopCondition):
            req = requests.get(next_req)
            myJson = req.json()
            for temp in myJson['data']:
                body.append(dict(count=temp['likes']['count'],data=temp))
            next_req = myJson['pagination']['next_url']
            page += 1
            if page >= 20:
                stopCondition = False
            #content += ''.join(photos) 
        body.sort(reverse=True)
        for element in body:
	    print element
	    photos.append('<a href="%s" target="blank"><img src="%s" alt="%s" /></a>' % (element['data']['link'],element['data']['images']['standard_resolution']['url'], element['count']))
        content += ''.join(photos) 
    except Exception, e:
        print e
    return "%s %s <br/>Remaining API Calls = %s/%s" % (get_nav(),content,api.x_ratelimit_remaining,api.x_ratelimit)


@route('/hackademy/<tag>')
def hackademy(session, tag="selfie"):
    import requests, json
    print tag
    cont = 0
    stopCondition = True
    body = []
    photos = []
    access_token = session.get('access_token')
    content = "<br><h3>Results for tag: <u>%s</u></h3><br>" % tag
    if not access_token:
        return 'Missing Access Token'
    try:
        api = client.InstagramAPI(access_token=access_token)
        next_req = "https://api.instagram.com/v1/tags/%s/media/recent?access_token=%s" % (tag, access_token)
        while(stopCondition):
            req = requests.get(next_req)
            myJson = req.json()
            for temp in myJson['data']:
                if temp['location']:
                    body.append(temp)
                    photos.append('<img src="%s" />' % (temp['images']['standard_resolution']['url']))
                    cont += 1
            next_req = myJson['pagination']['next_url']
            if cont >= 25:
                stopCondition = False
            content += ''.join(photos) 
            print "DONE: ", cont
    except Exception, e:
        print e
    return "%s %s <br/>Remaining API Calls = %s/%s" % (get_nav(),content,api.x_ratelimit_remaining,api.x_ratelimit)

@route('/oauth_callback')
def on_callback(session): 
    code = request.GET.get("code")
    if not code:
        return 'Missing code'
    try:
        access_token, user_info = unauthenticated_api.exchange_code_for_access_token(code)
        print "access token= " + access_token
        if not access_token:
            return 'Could not get access token'
        api = client.InstagramAPI(access_token=access_token)
        session['access_token']=access_token
    except Exception, e:
        print e
    return get_nav()

@route('/recent')
def on_recent(session): 
    access_token = session.get('access_token')
    content = "<h2>User Recent Media</h2>"
    if not access_token:
        return 'Missing Access Token'
    try:
        api = client.InstagramAPI(access_token=access_token)
        recent_media, next = api.user_recent_media()
        photos = []
        for media in recent_media:
            photos.append('<div style="float:left;">')
            if(media.type == 'video'):
                photos.append('<video controls width height="150"><source type="video/mp4" src="%s"/></video>' % (media.get_standard_resolution_url()))
            else:
                photos.append('<img src="%s"/>' % (media.get_low_resolution_url()))
            print media
            photos.append("<br/> <a href='/media_like/%s'>Like</a>  <a href='/media_unlike/%s'>Un-Like</a>  LikesCount=%s</div>" % (media.id,media.id,media.like_count))
        content += ''.join(photos)
    except Exception, e:
        print e              
    return "%s %s <br/>Remaining API Calls = %s/%s" % (get_nav(),content,api.x_ratelimit_remaining,api.x_ratelimit)

@route('/media_like/<id>')
def media_like(session,id): 
    access_token = session.get('access_token')
    api = client.InstagramAPI(access_token=access_token)
    api.like_media(media_id=id)
    redirect("/recent")

@route('/media_unlike/<id>')
def media_unlike(session,id): 
    access_token = session.get('access_token')
    api = client.InstagramAPI(access_token=access_token)
    api.unlike_media(media_id=id)
    redirect("/recent")

@route('/user_media_feed')
def on_user_media_feed(session): 
    access_token = session.get('access_token')
    content = "<h2>User Media Feed</h2>"
    if not access_token:
        return 'Missing Access Token'
    try:
        api = client.InstagramAPI(access_token=access_token)
        media_feed, next = api.user_media_feed()
        photos = []
        for media in media_feed:
            photos.append('<img src="%s"/>' % media.get_standard_resolution_url())
        counter = 1
        while next and counter < 3:
            media_feed, next = api.user_media_feed(with_next_url=next)
            for media in media_feed:
                photos.append('<img src="%s"/>' % media.get_standard_resolution_url())
            counter += 1
        content += ''.join(photos)
    except Exception, e:
        print e              
    return "%s %s <br/>Remaining API Calls = %s/%s" % (get_nav(),content,api.x_ratelimit_remaining,api.x_ratelimit)

@route('/location_recent_media')
def location_recent_media(session): 
    access_token = session.get('access_token')
    content = "<h2>Location Recent Media</h2>"
    if not access_token:
        return 'Missing Access Token'
    try:
        api = client.InstagramAPI(access_token=access_token)
        recent_media, next = api.location_recent_media(location_id=514276)
        photos = []
        for media in recent_media:
            photos.append('<img src="%s"/>' % media.get_standard_resolution_url())
        content += ''.join(photos)
    except Exception, e:
        print e              
    return "%s %s <br/>Remaining API Calls = %s/%s" % (get_nav(),content,api.x_ratelimit_remaining,api.x_ratelimit)

@route('/media_search')
def media_search(session): 
    access_token = session.get('access_token')
    content = "<h2>Media Search</h2>"
    if not access_token:
        return 'Missing Access Token'
    try:
        api = client.InstagramAPI(access_token=access_token)
        media_search = api.media_search(lat="37.7808851",lng="-122.3948632",distance=1000)
        photos = []
        for media in media_search:
            photos.append('<img src="%s"/>' % media.get_standard_resolution_url())
        content += ''.join(photos)
    except Exception, e:
        print e              
    return "%s %s <br/>Remaining API Calls = %s/%s" % (get_nav(),content,api.x_ratelimit_remaining,api.x_ratelimit)

@route('/media_popular')
def media_popular(session): 
    access_token = session.get('access_token')
    content = "<h2>Popular Media</h2>"
    if not access_token:
        return 'Missing Access Token'
    try:
        api = client.InstagramAPI(access_token=access_token)
        media_search = api.media_popular()
        photos = []
        for media in media_search:
            photos.append('<img src="%s"/>' % media.get_standard_resolution_url())
        content += ''.join(photos)
    except Exception, e:
        print e              
    return "%s %s <br/>Remaining API Calls = %s/%s" % (get_nav(),content,api.x_ratelimit_remaining,api.x_ratelimit)

@route('/user_search')
def user_search(session): 
    access_token = session.get('access_token')
    content = "<h2>User Search</h2>"
    if not access_token:
        return 'Missing Access Token'
    try:
        api = client.InstagramAPI(access_token=access_token)
        user_search = api.user_search(q="Instagram")
        users = []
        for user in user_search:
            users.append('<li><img src="%s">%s</li>' % (user.profile_picture,user.username))
        content += ''.join(users)
    except Exception, e:
        print e              
    return "%s %s <br/>Remaining API Calls = %s/%s" % (get_nav(),content,api.x_ratelimit_remaining,api.x_ratelimit)

@route('/user_follows')
def user_follows(session): 
    access_token = session.get('access_token')
    content = "<h2>User Follows</h2>"
    if not access_token:
        return 'Missing Access Token'
    try:
        api = client.InstagramAPI(access_token=access_token)
        # 25025320 is http://instagram.com/instagram
        user_follows, next = api.user_follows('25025320')
        users = []
        for user in user_follows:
            users.append('<li><img src="%s">%s</li>' % (user.profile_picture,user.username))
        while next:
            user_follows, next = api.user_follows(with_next_url=next)
            for user in user_follows:
                users.append('<li><img src="%s">%s</li>' % (user.profile_picture,user.username))
        content += ''.join(users)
    except Exception, e:
        print e              
    return "%s %s <br/>Remaining API Calls = %s/%s" % (get_nav(),content,api.x_ratelimit_remaining,api.x_ratelimit)

@route('/location_search')
def location_search(session): 
    access_token = session.get('access_token')
    content = "<h2>Location Search</h2>"
    if not access_token:
        return 'Missing Access Token'
    try:
        api = client.InstagramAPI(access_token=access_token)
        location_search = api.location_search(lat="37.7808851",lng="-122.3948632",distance=1000)
        locations = []
        for location in location_search:
            locations.append('<li>%s  <a href="https://www.google.com/maps/preview/@%s,%s,19z">Map</a>  </li>' % (location.name,location.point.latitude,location.point.longitude))
        content += ''.join(locations)
    except Exception, e:
        print e              
    return "%s %s <br/>Remaining API Calls = %s/%s" % (get_nav(),content,api.x_ratelimit_remaining,api.x_ratelimit)

@route('/tag_search')
def tag_search(session): 
    access_token = session.get('access_token')
    print access_token
    content = "<h2>Tag Search</h2>"
    if not access_token:
        return 'Missing Access Token'
    try:
        api = client.InstagramAPI(access_token=access_token)
        tag_search, next_tag = api.tag_search(q="selfie")
	print "tag search: ", tag_search, " next_tag: ", next_tag
        tag_recent_media, next = api.tag_recent_media(tag_name=tag_search[0].name)
        photos = []
	print "tag recent media: ", tag_recent_media, " next: ", next
        for tag_media in tag_recent_media:
            photos.append('<img src="%s"/>' % tag_media.get_standard_resolution_url())
        content += ''.join(photos)
    except Exception, e:
        print e              
    return "%s %s <br/>Remaining API Calls = %s/%s" % (get_nav(),content,api.x_ratelimit_remaining,api.x_ratelimit)

@route('/realtime_callback')
@post('/realtime_callback')
def on_realtime_callback():
    mode = request.GET.get("hub.mode")
    challenge = request.GET.get("hub.challenge")
    verify_token = request.GET.get("hub.verify_token")
    if challenge: 
        return challenge
    else:
        x_hub_signature = request.header.get('X-Hub-Signature')
        raw_response = request.body.read()
        try:
            reactor.process(CONFIG['client_secret'], raw_response, x_hub_signature)
        except subscriptions.SubscriptionVerifyError:
            print "Signature mismatch"




run(host='0.0.0.0', port=8515, reloader=True)
