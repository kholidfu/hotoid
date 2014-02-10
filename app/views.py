# author: @sopier

from flask import render_template, request, redirect, send_from_directory
from flask import make_response # untuk sitemap
from app import app
# untuk find_one based on data id => db.freewaredata.find_one({'_id': ObjectId(file_id)})
# atom feed
from werkzeug.contrib.atom import AtomFeed
#from bson.objectid import ObjectId 
from filters import slugify, splitter, onlychars, get_first_part, get_last_part, formattime, cleanurl
import urllib2
import json
import datetime
import redis

r = redis.Redis()

from pycassa.pool import ConnectionPool
from pycassa.columnfamily import ColumnFamily
from pycassa.types import *

# database terms
pool_terms = ConnectionPool('Terms', ['162.243.79.52:9160'])
col_term = ColumnFamily(pool_terms, 'Term')
col_term.column_validators['added'] = DateType()
col_term.column_validators['hits'] = IntegerType()

# database berita
pool_topics = ConnectionPool('Topics', ['162.243.79.52:9160'])
col_topic = ColumnFamily(pool_topics, 'Topic')


@app.template_filter()
def slug(s):
    """ 
    transform words into slug 
    usage: {{ string|slug }}
    """
    return slugify(s)

@app.template_filter()
def split(s):
    """ 
    split string s with delimiter '-' 
    return list object
    usage: {{ string|split }}
    """
    return splitter(s, '-')

@app.template_filter()
def getlast(text, delim=' '):
    """
    get last word from string with delimiter ' '
    usage: {{ string|getlast }}
    """
    return get_last_part(text, delim)

@app.template_filter()
def getfirst(text, delim=' '):
    """
    get first word from string with delimiter '-'
    usage: {{ string|getfirst }}
    """
    return get_first_part(text, delim)

@app.template_filter()
def getchars(text):
    """
    get characters and numbers only from string
    usage: {{ string|getchars }}
    """
    return onlychars(text)

@app.template_filter()
def sectomins(seconds):
    """
    convert seconds to hh:mm:ss
    usage: {{ seconds|sectomins }}
    """
    return formattime(seconds)

@app.template_filter()
def urlcleaner(text):
    """
    clean url from string
    """
    return cleanurl(text)

# handle robots.txt file
@app.route("/robots.txt")
def robots():
    # point to robots.txt files
    return send_from_directory(app.static_folder, request.path[1:])

@app.route("/")
def index():
    #terms = r.lrange('terms', 0, -1) # -1 show all, n => max n
    terms = [i[0] for i in col_term.get_range()]
    return render_template("index.html", terms=terms)


@app.route("/get")
def cari():
    q = request.args.get('q')
    return redirect("/berita/" + slugify(q), 301)


@app.route("/berita/<topik>")
def berita(topik):
    topik = slugify(topik)

    col_term.insert(unicode(topik.replace('-', ' ')), {'added': datetime.datetime.now(), 'hits': 1})

    query = topik.replace('-', '+')

    url1 = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&key=AIzaSyDgVEQ1PB5N4Q0YizPpyLdafL6FmgjdN1w&cx=002126600575969604992:lhhlw8muw00&gl=en&rsz=8&start=0&q=' + query + '+site:kompas.com'
    url2 = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&key=AIzaSyDgVEQ1PB5N4Q0YizPpyLdafL6FmgjdN1w&cx=002126600575969604992:lhhlw8muw00&gl=en&rsz=8&start=0&q=' + query + '+site:detik.com'
    url3 = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&key=AIzaSyDgVEQ1PB5N4Q0YizPpyLdafL6FmgjdN1w&cx=002126600575969604992:lhhlw8muw00&gl=en&rsz=8&start=0&q=' + query + '+site:viva.co.id'
    url4 = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&key=AIzaSyDgVEQ1PB5N4Q0YizPpyLdafL6FmgjdN1w&cx=002126600575969604992:lhhlw8muw00&gl=en&rsz=8&start=0&q=' + query + '+site:kaskus.co.id'
    url5 = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&key=AIzaSyDgVEQ1PB5N4Q0YizPpyLdafL6FmgjdN1w&cx=002126600575969604992:lhhlw8muw00&gl=en&rsz=8&start=0&q=' + query + '+site:merdeka.com'
    url6 = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&key=AIzaSyDgVEQ1PB5N4Q0YizPpyLdafL6FmgjdN1w&cx=002126600575969604992:lhhlw8muw00&gl=en&rsz=8&start=0&q=' + query + '+site:republika.co.id'
    #url6 = 'https://gdata.youtube.com/feeds/api/videos?q='+query+'&v=2&alt=jsonc'

    try:
        col_topic.get(topik)['kompas']
        data1 = json.loads(col_topic.get(topik)['kompas'])
    except:
        response1 = urllib2.urlopen(url1).read()
        col_topic.insert(topik, {'kompas': response1}, ttl=86400 * 7)
        data1 = json.loads(col_topic.get(topik)['kompas'])

    try:
        col_topic.get(topik)['detik']
        data2 = json.loads(col_topic.get(topik)['detik'])
    except:
        response2 = urllib2.urlopen(url2).read()
        col_topic.insert(topik, {'detik': response2}, ttl=86400 * 7)
        data2 = json.loads(col_topic.get(topik)['detik'])

    try:
        col_topic.get(topik)['vivanews']
        data3 = json.loads(col_topic.get(topik)['vivanews'])
    except:
        response3 = urllib2.urlopen(url3).read()
        col_topic.insert(topik, {'vivanews': response3}, ttl=86400 * 7)
        data3 = json.loads(col_topic.get(topik)['vivanews'])

    try:
        col_topic.get(topik)['kaskus']
        data4 = json.loads(col_topic.get(topik)['kaskus'])
    except:
        response4 = urllib2.urlopen(url4).read()
        col_topic.insert(topik, {'kaskus': response4}, ttl=86400)
        data4 = json.loads(col_topic.get(topik)['kaskus'])

    try:
        col_topic.get(topik)['merdeka']
        data5 = json.loads(col_topic.get(topik)['merdeka'])
    except:
        response5 = urllib2.urlopen(url5).read()
        col_topic.insert(topik, {'merdeka': response5}, ttl=86400 * 7)
        data5 = json.loads(col_topic.get(topik)['merdeka'])

    try:
        col_topic.get(topik)['republika']
        data6 = json.loads(col_topic.get(topik)['republika'])
    except:
        response6 = urllib2.urlopen(url6).read()
        col_topic.insert(topik, {'republika': response6}, ttl=86400 * 7)
        data6 = json.loads(col_topic.get(topik)['republika'])

    return render_template("berita2.html", data1=data1, data2=data2, data3=data3, data4=data4, data5=data5, data6=data6, topik=topik)
    
"""
@app.route("/berita/<topik>")
def berita(topik):
    query = topik.replace('-', '+')
    url1 = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&key=AIzaSyDgVEQ1PB5N4Q0YizPpyLdafL6FmgjdN1w&cx=002126600575969604992:lhhlw8muw00&gl=en&rsz=8&start=0&q=' + query + '+site:kompas.com'
    url2 = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&key=AIzaSyDgVEQ1PB5N4Q0YizPpyLdafL6FmgjdN1w&cx=002126600575969604992:lhhlw8muw00&gl=en&rsz=8&start=0&q=' + query + '+site:detik.com'
    url3 = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&key=AIzaSyDgVEQ1PB5N4Q0YizPpyLdafL6FmgjdN1w&cx=002126600575969604992:lhhlw8muw00&gl=en&rsz=8&start=0&q=' + query + '+site:viva.co.id'
    url4 = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&key=AIzaSyDgVEQ1PB5N4Q0YizPpyLdafL6FmgjdN1w&cx=002126600575969604992:lhhlw8muw00&gl=en&rsz=8&start=0&q=' + query + '+site:kaskus.co.id'
    url5 = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&key=AIzaSyDgVEQ1PB5N4Q0YizPpyLdafL6FmgjdN1w&cx=002126600575969604992:lhhlw8muw00&gl=en&rsz=8&start=0&q=' + query + '+site:merdeka.com'
    #url6 = 'https://gdata.youtube.com/feeds/api/videos?q='+query+'&v=2&alt=jsonc'

    if r.lrange(topik, 0, 10): # jika ada data
        data1 = json.loads(r.lrange(topik, 0, 10)[0]) # data kompas
        data2 = json.loads(r.lrange(topik, 0, 10)[1]) # data detik
        data3 = json.loads(r.lrange(topik, 0, 10)[2]) # data vivanews
        data4 = json.loads(r.lrange(topik, 0, 10)[3]) # data kaskus
        data5 = json.loads(r.lrange(topik, 0, 10)[4]) # data merdeka
    else:
        # kompas data
        response1 = urllib2.urlopen(url1).read()
        data_json_1 = json.loads(response1)
        r.rpush(topik, json.dumps(data_json_1))
        data1 = json.loads(r.lrange(topik, 0, 10)[0])
        # detik data
        response2 = urllib2.urlopen(url2).read()
        data_json_2 = json.loads(response2)
        r.rpush(topik, json.dumps(data_json_2))
        data2 = json.loads(r.lrange(topik, 0, 10)[1])
        # vivanews data
        response3 = urllib2.urlopen(url3).read()
        data_json_3 = json.loads(response3)
        r.rpush(topik, json.dumps(data_json_3))
        data3 = json.loads(r.lrange(topik, 0, 10)[2])
        # kaskus data
        response4 = urllib2.urlopen(url4).read()
        data_json_4 = json.loads(response4)
        r.rpush(topik, json.dumps(data_json_4))
        data4 = json.loads(r.lrange(topik, 0, 10)[3])
        # merdeka data
        response5 = urllib2.urlopen(url5).read()
        data_json_5 = json.loads(response5)
        r.rpush(topik, json.dumps(data_json_5))
        data5 = json.loads(r.lrange(topik, 0, 10)[4])

        # set expiry
        r.expire(topik, 86400) # 1 day

    return render_template("berita2.html", data1=data1, data2=data2, data3=data3, data4=data4, data5=data5, topik=topik)
"""

@app.route("/sitemap/<n>")
def sitemap(n):
    start = (int(n) * 50000) - 50000
    end = (int(n) * 50000)
    data = [i[0] for i in col_term.get_range()][start:end]
    sitemap_xml = render_template("sitemap.xml", data=data)
    response = make_response(sitemap_xml)
    response.headers['Content-Type'] = 'application/xml'

    return response

@app.route('/latest.atom')
def recent_feed():
    # http://werkzeug.pocoo.org/docs/contrib/atom/ 
    # wajibun: id(link) dan updated
    feed = AtomFeed('Recent Articles',
                   feed_url = request.url, url=request.url_root)
    data = [i[0] for i in col_term.get_range()][:100]
    for d in data:
        feed.add(
            d,
            content_type='text',
            url = 'http://www.hotoid.com/berita/' + slugify(d),
            updated = datetime.datetime.now(),
            )
        
    return feed.get_response()


@app.route("/head")
def get_head():
    head = request.headers
    return render_template("get_head.html", head=head['User-Agent'])
