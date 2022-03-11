import re
from flask import Flask, redirect, render_template
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import *
from dominate.tags import img
from boto3.dynamodb.conditions import Key
import boto3

dynamodb = boto3.resource('dynamodb',region_name='us-east-1')
table = dynamodb.Table("Skyhighdb")

logo = img(src='./static/img/SkyHigh_Memes.png', height="50", style="margin-top:-15px")
topbar = Navbar(View(logo, 'home'),
                View('Home', 'home'),
                View('Make a Meme', 'create_meme'),
                View('Subscriptions', 'get_subscriptions'),
                View('Sign up / Log in', 'handle_account'),
                )

# registers the "top" menubar
nav = Nav()
nav.register_element('top', topbar)
images = []
url='https://i.imgflip.com/681vl9.jpg'

app = Flask(__name__)
Bootstrap(app)


@app.route('/', methods=['GET'])
def home():
    return(render_template('home.html', page_name="Home"))

@app.route('/create', methods=['GET'])
def create_meme():
    return(render_template('create.html'))

@app.route('/subscriptions', methods=['GET'])
def get_subscriptions():
    return(render_template('home.html', page_name="Subscriptions"))

@app.route('/account', methods=['GET'])
def handle_account():
    return(render_template('account.html'))
nav.init_app(app)


# Shows the image the user clicked and other memes created by the user
#expects the images to be loaded up and url is pointing to the image clicked
@app.route("/viewmeme",methods=['GET','POST'])
def memepage():
    global images,url

    # for testing -> expecting the endpoint that redirect to this endpoint to call this function  
    if (len(images)==0): images=findAllMemesByUploader('test')

    
    # response = table.query(
    #             KeyConditionExpression=Key('url').eq("https://darpractice.s3.amazonaws.com/img1.jpg")  
    #         )
    # data = response['Items']        
    # print(data[0]['url'])

    # url = 'https://i.imgflip.com/681vl9.jpg' # mimicks the url 
    # images = findAllMemesByUploader('test')

    return (render_template('viewmeme.html',images = images,uploader='cloud9',url=url))        

@app.route("/viewmeme/<index>")
def morememe(index):
    global url

    images.append(url)
    url= images[int(index)-1]
    images.remove(url)
    return redirect(url_for('memepage'))


#  returns list of image url
#  Should not include the image selected by user
def findAllMemesByUploader(uploader):
    #  response = table.query(
    #             IndexName="uploader-index",
    #              KeyConditionExpression=Key('uploader').eq(uploader)
    #          )
    #  data = response['Items']
    #   print(data)
    #  for image in data:
    #      images.append(image['url'])

    images.append('https://i.imgflip.com/681nff.jpg')
    images.append('https://i.imgflip.com/6823f9.jpg')
    images.append('https://i.imgflip.com/682o0w.jpg')
    return images
if __name__ == '__main__':
  app.run()
  # app.run(host='127.0.0.1', port=5000, debug=True)