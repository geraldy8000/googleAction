from flask import Flask
from flask import make_response
from flask import request
# from flask_cors import CORS,cross_origin
from random import randint
from multiprocessing import Queue
import json
import requests
import threading
import urllib3
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
app=Flask(__name__)
# CORS(app)
conversation_id=0
queues={}
replies={}

textTmp = '{"conversationToken":"{\\"state\\":null,\\"data\\":{}}","expectUserResponse":true,"expectedInputs":[{"inputPrompt":{"richInitialPrompt":{"items":[{"simpleResponse":{"ssml":"<speak>%s</speak>","displayText":"%s"}}],"suggestions":[]}},"possibleIntents":[{"intent":"actions.intent.TEXT"}]}]}'

cardTmp = '{"conversationToken":"","expectUserResponse":true,"expectedInputs":[{"inputPrompt":{"richInitialPrompt":{"items":[{"simpleResponse":{"textToSpeech":"Math and prime numbers it is!","displayText":"Displayed Card"}},{"basicCard":{"title":"Math & prime numbers","formattedText":"42 is an even composite number.It\n is composed of three distinct prime numbers multiplied together. It\n has a total of eight divisors. 42 is an abundant number, because the\n sum of its proper divisors 54 is greater than it self. To count from\n 1 to 42 would take you about twenty-one…","image":{"url":"https://www.telkomsel.com/sites/default/files/upload/Virtual%20Asset%20Personalised%20Menu%20-%20Greeting%20rev01-02.jpg","accessibilityText":"Imagealternatetext"},"buttons":[{"title":"Readmore","openUrlAction":{"url":"https://upload.wikimedia.org/wikipedia/commons/d/dd/Minnesota_Twins_42.png"}}],"imageDisplayOptions":"CROPPED"}}],"suggestions":[]}},"possibleIntents":[{"intent":"actions.intent.TEXT"}]}]}'

helloTmp = '{"conversationToken":"","expectUserResponse":true,"expectedInputs":[{"inputPrompt":{"richInitialPrompt":{"items":[{"simpleResponse":{"textToSpeech":"Hello, you can call me Veronika","displayText":"Hello, you can call me Veronika"}},{"basicCard":{"title":"I am Veronika Assistant","formattedText":" Aku Veronika, asisten virtual untuk membantu kebutuhan Telkomsel Kamu mulai dari bayar tagihan, isi pulsa hingga tukar POIN!","image":{"url":"https://www.telkomsel.com/sites/default/files/upload/Virtual%20Asset%20Personalised%20Menu%20-%20Greeting%20rev01-02.jpg","accessibilityText":"Imagealternatetext"},"imageDisplayOptions":"CROPPED"}}],"suggestions":[]}},"possibleIntents":[{"intent":"actions.intent.TEXT"}]}]}'

caroTmp = '{"conversationToken":"","expectUserResponse":true,"expectedInputs":[{"inputPrompt":{"initialPrompts":[{"textToSpeech":"%s"}],"noInputPrompts":[]},"possibleIntents":[{"intent":"actions.intent.OPTION","inputValueData":{"@type":"type.googleapis.com/google.actions.v2.OptionValueSpec","carouselSelect":{"items":[{"optionInfo":{"key":"%s","synonyms":["%s"]},"title":"%s","description":"%s","image":{"url":"%s","accessibilityText":"%s"}},{"optionInfo":{"key":"%s","synonyms":["%s"]},"title":"%s","description":"%s","image":{"url":"%s","accessibilityText":"%s"}}]}}}]}]}'

permissionTmp = '{"conversationToken":"{\\"state\\":null,\\"data\\":{}}","expectUserResponse":true,"expectedInputs":[{"inputPrompt":{"richInitialPrompt":{"items":[{"simpleResponse":{"textToSpeech":"To know you more","displayText":"To know you more"}}],"suggestions":[]},"noInputPrompts":[]},"possibleIntents":[{"intent":"actions.intent.PERMISSION","inputValueData":{"@type":"type.googleapis.com/google.actions.v2.PermissionValueSpec","optContext":"To know you more","permissions":["NAME"]}}]}]}'

@app.route('/',methods=['POST'])
def hello():
    global conversation_id
    conversation_id+=1
    req_body=json.loads(request.data)
    if req_body['inputs'][0]['intent']=='actions.intent.MAIN':
        res=make_response(helloTmp)
    elif req_body['inputs'][0]['intent']=='actions.intent.OPTION' or req_body['inputs'][0]['intent']=='actions.intent.TEXT' or req_body['inputs'][0]['intent']=='actions.intent.PERMISSION':
        if req_body['inputs'][0]['rawInputs'][0]['query']=='bye':
            res=make_response('{"expectUserResponse":false,"finalResponse":{"speechResponse":{"textToSpeech":"See you again soon. Goodbye!"}}}')
        elif req_body['inputs'][0]['rawInputs'][0]['query']=='yes':
            res=make_response(textTmp %('Thank you', 'Thank you'))
        else:
            is_killed=False
            log_file=open('log.txt','a+')
            log_file.write(str(conversation_id)+'\n')
            log_file.write(req_body['inputs'][0]['rawInputs'][0]['query']+'\n')
            log_file.close()
            queue=Queue()
            print(conversation_id)
            print(req_body['inputs'][0]['rawInputs'][0]['query'])
            thread=threading.Thread(args=((queue),conversation_id,req_body,),target=reply)
            thread.start()
            thread.join(7)
            try:
                temp = queue.get()
                global queues
                queues[temp['conversation_id']]=temp['response']
            except:
                pass
            if thread.isAlive():
                is_killed=True
                print ("Thread killed.")
            if is_killed:
                rand=randint(0,2)
                if rand==0:
                    speech='Could you repeat, please?'
                elif rand==1:
                    speech='Pardon me?'
                elif rand==2:
                    speech='Your question was not clear.'
                res=make_response('{"conversationToken":"{\\"state\\":null,\\"data\\":{}}","expectUserResponse":true,"expectedInputs":[{"inputPrompt":{"initialPrompts":[{"ssml":"<speak>%s</speak>"}],"noInputPrompts":[{"ssml":"Please say something."}]},"possibleIntents":[{"intent":"actions.intent.TEXT"}]}]}'%(speech))
            else:
                res=queues[conversation_id]
    return res

def reply(queue,c_id,req_body):
    with app.app_context():
        resp = get_response(req_body)
        print(req_body['inputs'][0]['rawInputs'][0]['inputType'])
        responseData = requests.post('https://c8314b6d.ngrok.io/test_reply',data=resp,headers={'User-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.89 Safari/537.36'},verify=False)
        response = responseData.json()
        print(response)
        speech=response['speech']
        speech_type=response['speech_type']
        if speech_type=='text':
            res=make_response(textTmp %(speech, speech))
        elif speech_type=='card':
            res=make_response(cardTmp)
        elif speech_type=='permit':
            res=make_response(permissionTmp)
        elif speech_type=='caro':
            description1=response['options'][0]['description']
            key1=response['options'][0]['key']
            synonim1=response['options'][0]['synonyms'][0]
            title1=response['options'][0]['title']
            url1=response['options'][0]['url']
            description2=response['options'][1]['description']
            key2=response['options'][1]['key']
            synonim2=response['options'][1]['synonyms'][0]
            title2=response['options'][1]['title']
            url2=response['options'][1]['url']
            res=make_response(caroTmp  %(speech, key1, synonim1, title1, description1, url1, title1, key2, synonim2, title2, description2, url2, title2))
        queue.put({
            'conversation_id': c_id,
            'response': res
        })
        
def get_response(req_body):
    if any(char.isdigit() for char in req_body['inputs'][0]['rawInputs'][0]['query']):
        print("number found")
        return  req_body['inputs'][0]['rawInputs'][0]['query']
    else:
        print("number not found")
        return  req_body['inputs'][0]['rawInputs'][0]['query']
    """
    if not req_body['inputs'][0]['rawInputs'][0]['query'].isdigit():
        print("no number found")
        return  req_body['inputs'][0]['rawInputs'][0]['query']
    elif req_body['inputs'][0]['rawInputs'][0]['query'].isdigit():
        print("number found")
        return  req_body['inputs'][0]['rawInputs'][0]['query']
    """

@app.route('/test_reply',methods=['POST'])
def test_reply():
    reqData=request.data.decode("utf-8")
    print(reqData)
    if 'halo' in reqData:
        response={
            'speech':'Post API success with halo',
            'speech_type':'text'
        }
    elif 'card' in reqData:
        response={
            'speech':'Post API success with card',
            'speech_type':'card'
        }
    elif 'caro' in reqData:
        response={
            'speech':'Post API success with caro',
            'speech_type':'caro',
            'options':[{'description':'Alaska','key':'0','synonyms':["alaska"],'title':'Alaska','url':'http://worldjourneys.co.nz/upload-images/World-Journeys-Historic-Alaska-and-Yukon-Milepost--0-4752-thumb.jpg'},{'description':'California','key':'1','synonyms':["california"],'title':'California','url':'http://www.princess.com/images/learn/destinations/california_coastals/pacific_coastals_150x100.jpg'}]
        }
    elif 'permit' in reqData:
        response={
            'speech':'Post API success with permit',
            'speech_type':'permit'
        }
    else: 
        response={
            'speech':'API success',
            'speech_type':'text'
        }
    json_data = json.dumps(response)
    print(json_data)
    return json_data

if __name__=='__main__':
    app.run(debug=True,host='0.0.0.0',port=5000,threaded=True)