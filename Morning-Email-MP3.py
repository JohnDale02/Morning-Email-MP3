from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
import os.path
import base64
from bs4 import BeautifulSoup
import openai
from gtts import gTTS
from twilio.rest import Client
from datetime import datetime

#---------------- FILL OUT ALL THE INFOMRATION BELOW-----------------------------------

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    # Will have the user Authenticate themselves through the Gmail GoogleAPI
openai.api_key = 'YOUR_OPEN_AI_KEY_HERE'
    # Key for integrating ChatGPT for summarization purposes
savePath = "C:/Users/YOUR USER/Dropbox/Public/Emaildebrief.mp3"
    # Location where the final MP3 should be stored ---> Put into Public Dropbox Folder!
TwilioAccountSid  = 'YOUR_PERSONAL_TWILIO_SID' 
TwilioAuthToken = 'YOUR_PERSONAL_TWILIO_AUTH_TOKEN'
myTwilioNumber = '+YOUR_PERSONAL_TWILIO_NUMBER'
myCellPhone = '+YOUR_PERSONAL_CELL_PHONE_NUMBER'
MP3media = 'https://www.dropbox.com//home/ADD_IN_YOUR_PATH_TO_THE_EMAIL_FILE'
    # Twilio authentication SID and Token & Number to recieve Debrief messages

#--------------------- Personalization: -------------------------------------------------

hoursOffline = 48  # number of hours you want this scipt to look back on for unread emails
messagesAllowed = 10 # MAX number of messages you are willing to recieve in 1 MP3 file

#---------------------------------------------------------------------------------------

monthTranslation = {'Jan': ['January', '1'], 
                    'Feb': ['February','2'], 
                    'March': ['March', '3'],
                    'April': ['April', '4'],
                    'May': ['May', '5'],
                    'Jun': ['June', '6'],
                    'July': ['July', '7'],
                    'Aug': ['August', '8'],
                    'Sept': ['September', '9'],
                    'Oct': ['October', '10'],
                    'Nov': ['November', '11'],
                    'Dec': ['December', '12'],
                     }

weekdayTranslations = {'Mon,': 'Monday',
                       'Tue,' : 'Tuesday',
                       'Wed,': 'Wednesday',
                       'Thu,': 'Thursday',
                       'Fri,': 'Friday',
                       'Sat,': 'Saturday',
                       'Sun,': 'Sunday',
                        }
             
dateTranslation =  {'01': '1st', 
                    '02': '2nd',
                    '03': '3rd',
                    '04': '4th', 
                    '05': '5th',
                    '06': '6th',
                    '07': '7th', 
                    '08': '8th',
                    '09': '9th',
                    '10': '10th', 
                    '12': '12th',
                    '13': '13th',
                    '14': '14th', 
                    '15': '15th',
                    '16': '16th',
                    '17': '17th', 
                    '18': '18th',
                    '19': '19th',
                    '20': '20th', 
                    '21': '21st',
                    '22': '22nd',
                    '23': '23rd', 
                    '24': '24th',
                    '25': '25th',
                    '26': '26th', 
                    '27': '27th',
                    '28': '28th',
                    '29': '29th',
                    '30': '30th',
                    '31': '31st',
                    }


def getDistance(hour, day, month, year):
    distance = 0
    chour = datetime.now().hour
    cday = datetime.now().day
    cmonth = datetime.now().month
    cyear = datetime.now().year
        # Distance for Year difference
    if cyear - year != 0:
        if cmonth > month:
            distance += 365*24* (cyear-year)
        if cmonth == month and cday > day:
            distance += 365*24* (cyear-year)
        if cmonth == month and cday <= day:
            distance += 365*24* ((cyear-year)-1)
        # Distance for Month difference
    if cmonth - month !=0:
        if cday > day:
            distance += 24*30* (cmonth-month)
        if cday == day and chour > hour:
            distance += 24*30* (cmonth-month)
        if cday == day and chour <= hour:
            distance += 24*30* ((cmonth-month)-1)
        # Distance for Day difference 
    if cday - day != 0:
        if chour > hour:
            distance += 24* (cday-day)
        if chour == hour:
            distance += 24* (cday-day)
        # Distance for hour difference
    if chour - hour != 0:
        distance += (chour-hour)

    return distance

def isTooOld(distance, hoursOffline, messageCount, messagesAllowed):
    if distance >= hoursOffline or messageCount >= messagesAllowed:
        return True
    else:
        return False
    
def verifyCredentials():
    creds = None
    tooOld = False  # Emails are not yet too old

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        
    return creds

def chatGptSummary(body, subject, sender):

    Summary = ''  # create a empty string for this message summary
    Prompt = "Summarize this email into a single sentence: "

    if body == None or body == '':
        chatGPTinput = Prompt + "Email Subject: " + subject + " Email Sender: " + sender 
    else:
        chatGPTinput = Prompt + "Email Subject: " + subject + " Email Sender: " + sender + " Email body " + body
        if len(chatGPTinput) > 4000:
            chatGPTinput = chatGPTinput[:4000]

    try:
        chatGPToutput = openai.Completion.create(
            engine="text-davinci-003",
            prompt=chatGPTinput,
            temperature=0.7,
            max_tokens=709,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            )
        
        for i in chatGPToutput.choices:
            Summary += i.text

    except Exception as e:
        print(f"\nSome unread emails still await reading: Error {e}")
        Summary+= "Some unread emails still await reading"

    return Summary

def connectToMessages(creds):
    try:
        # Connect to the Gmail API
        service = build('gmail', 'v1', credentials=creds)

        # request a list of all the messages
        #result = service.users().messages().list(userId='me').execute()

        # We can also pass maxResults to get any number of emails. Like this:
        result = service.users().messages().list(maxResults=messagesAllowed, labelIds = ["INBOX", "UNREAD"], userId='me').execute()
        messages = result.get('messages', [])

        # messages is a list of dictionaries where each dictionary contains a message id.

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'Unable to connect to Gmail Service: {error}')
        exit()

    return messages, service

def readEmails(messages, service):

    AllEmailSummaries = ""  # variable to hold all email summary text
    messageCount = 0
    distance = 0
    
   # iterate through all the messages
    for msg in messages:
        
        # Get the message from its id
        txt = service.users().messages().get(userId='me', id=msg['id']).execute()

        # Use try-except to avoid any Errors
        
        # Get value of 'payload' from dictionary 'txt'
        payload = txt['payload']
        headers = payload['headers']

        # Look for Subject and Sender Email in the headers
        for values in headers:
            if values['name'] == 'Subject':
                subject = values['value']
            if values['name'] == 'From':
                sender = values['value']
            if values['name'] == 'Date':
                dateRaw = values['value']
            
        distance = emailDate(dateRaw)
        tooOld = isTooOld(distance, hoursOffline, messageCount, messagesAllowed)

        if tooOld == True:
            return AllEmailSummaries, messageCount

        # decode the message details and form the email into a string
        try:
            parts = payload.get('parts')[0]  
            data = parts['body']['data']
            data = data.replace("-","+").replace("_","/")
            decoded_data = base64.b64decode(data)
            soup = BeautifulSoup(decoded_data , "lxml")
            body = soup.body.string   # prints body of text as string

        except Exception as e:
            print(f"Couldn't get paylods, Error {e}")
            body = f"Could not summarize email from {sender}, read it manually"
            
        # Creating prompt for ChatGPT and creating each summary text to be entered

        Summary = chatGptSummary(body, subject, sender)

        messageCount += 1
            # Creating block of text == All email Summaries


        AllEmailSummaries += str(messageCount) + "). Recieved " + str(distance) + " hours ago." + Summary + "\n\n"

    return AllEmailSummaries, messageCount

def emailDate(dateRaw):
    hour = None # making sure hourRaw is chaned w/correct time zone
    MN = "AM"   # by default times are AM

    dateSplit = dateRaw.split()  # splits raw date data into weekday, day number, month, year

    weekday = weekdayTranslations[dateSplit[0]]  # gets Monday, Tuesday... 
    dayRaw = dateSplit[1]   # get the day number of month 1, 10, 19 ...
    day = dateTranslation[dayRaw]   # gets 1st, 2nd, 3rd .....
    month = monthTranslation[dateSplit[2]][0]  # gets month January, March, April .... 
    monthRaw = monthTranslation[dateSplit[2]][1] # get month number 1, 6 .... 12 
    year = dateSplit[3]  # gets year 2023, 2019....
    timezone = dateSplit[5]  # gets '+0000' [timezone]
    
    timeRaw = dateSplit[4]   # gets 19:54:26 -> break into hours, minutes
    hourRaw = timeRaw[0:2]  # hours
    minute = timeRaw[3:5]  # minutes
    
        # correcting for timezones
    print(timezone)
    if timezone == '+0000' or timezone == 'GMT':
        hour = str((int(hourRaw) + 19) % 24)
    if timezone == '-0600':
        hour = str((int(hourRaw) + 1) % 24)
    if timezone == '-0700':
        hour = str((int(hourRaw) + 2) % 24)
    if timezone == '-0400':
        hour = str((int(hourRaw) + 1) % 24)
        
        # military to normal [AM or PM]
    if hour != None and int(hour) >= 12: 
        hour = str(int(hour) - 12)
        MN = "PM" 
    
    time = hour + ":" + minute + " " + MN
    date = weekday + " " +  month + " " +  day + " at " + time
    distance = getDistance(int(hour), int(dayRaw), int(monthRaw), int(year))

    return distance

def getEmails():
    
    creds = verifyCredentials()
    messages, service = connectToMessages(creds)
    AllEmailSummaries, messageCount = readEmails(messages, service)

    return AllEmailSummaries, messageCount

def twilioSendEmailSummary():

    AllEmailsString, messageCount = getEmails()  # String representing all email summaries

    MP3_Text = "Debrief of your " + str(messageCount) + " unread email(s) over the past " +  str(hoursOffline) + " hours.\n\n" +  AllEmailsString

    print(f"MP3_Text: {MP3_Text}")

    EmailMP3 = gTTS(text=MP3_Text, lang='en', slow=False)  # Email imput, english, Not slow
    EmailMP3.save(savePath)

    twilioCli = Client(TwilioAccountSid, TwilioAuthToken)
    print(type(twilioCli))

    message = twilioCli.messages.create(
        body=f'Here is an MP3 of your {messageCount} unread emails over the past {hoursOffline} hours. >> {MP3media} <<',
        from_=myTwilioNumber,
        to=myCellPhone
    )

    return twilioCli, messageCount


if __name__ == '__main__':
    
    twilioSendEmailSummary()
   