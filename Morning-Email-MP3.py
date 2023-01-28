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
openai.api_key = 'ENTER YOUR OPENAI API_KEY HERE'
    # Key for integrating ChatGPT for summarization purposes
savePath = "C:/Users/ENTER_YOUR_USER/Dropbox/Public/Emaildebrief.mp3"
    # Location where the final MP3 should be stored ---> Put into Public Dropbox Folder!
TwilioAccountSid  = 'TWILIO_ACCOUNT_SID' 
TwilioAuthToken = 'TWILIO_AUTH_TOKEN'
myTwilioNumber = '+YOUR_TWILIO_NUMBER'
myCellPhone = '+PHONE_NUMBER_TO_RECIEVE_DEBRIEF'
MP3media = 'https://www.dropbox.com/URL_THAT_LEADS_TO_PUBLIC_DROPBOX_FILE_STORED_IN_SAVE_PATH_ABOVE'
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
                    'June': ['June', '6'],
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
                       'Thur,': 'Thursday',
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

def getEmails():
    # Variable creds will store the user access token.
    # If no valid token found, we will create one.
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
    
    try:
        # Connect to the Gmail API
        service = build('gmail', 'v1', credentials=creds)
    
        # request a list of all the messages
        #result = service.users().messages().list(userId='me').execute()
    
        # We can also pass maxResults to get any number of emails. Like this:
        result = service.users().messages().list(maxResults=messagesAllowed, labelIds = ["INBOX", "UNREAD"], userId='me').execute()
        messages = result.get('messages', [])
    
        # messages is a list of dictionaries where each dictionary contains a message id.
    
        AllEmailSummaries = ""  # variable to hold all email summary text
        
        messageCount = 0
        distance = 0

        # iterate through all the messages
        for msg in messages:

            # Get the message from its id
            txt = service.users().messages().get(userId='me', id=msg['id']).execute()
            
            Summary = "" # empty string to hold each summary

            # Use try-except to avoid any Errors
            try:
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
                        if timezone == '+0000':   
                            hour = str((int(hourRaw) + 19) % 24)
                        if timezone == '-0600':
                            hour = str((int(hourRaw) + 1) % 24)

                            # military to normal [AM or PM]
                        if hour != None and int(hour) >= 12: 
                            hour = str(int(hour) - 12)
                            MN = "PM" 
                        
                        time = hour + ":" + minute + " " + MN
                        date = weekday + " " +  month + " " +  day + " at " + time
                        distance = getDistance(int(hour), int(dayRaw), int(monthRaw), int(year))

                        return distance
                
                distance = emailDate(dateRaw)

                tooOld = isTooOld(distance, hoursOffline, messageCount, messagesAllowed)

                if tooOld == True:
                    return AllEmailSummaries, messageCount

                # The Body of the message is in Encrypted format. So, we have to decode it.
                # Get the data and decode it with base 64 decoder.
                try:
                    parts = payload.get('parts')[0]
                    data = parts['body']['data']
                    data = data.replace("-","+").replace("_","/")
                    decoded_data = base64.b64decode(data)
                    soup = BeautifulSoup(decoded_data , "lxml")
                    body = soup.body.string   # prints body of text as string
                except:
                    body = ''
                    pass
            except:
                print("Cannot get payload and headers")
            
            # Creating prompt for ChatGPT and creating each summary text to be entered

            Prompt = "Summarize this email into a single sentence: "

            if body == None or body == '':
                chatGPTinput = Prompt + "Email Subject: " + subject + " Email Sender: " + sender 
            else:
                chatGPTinput = Prompt + "Email Subject: " + subject + " Email Sender: " + sender + " Email body " + body

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

            except:
                print("\nSome Unread Emails still await you, ChatGPT has trouble summarizing them")

            # Creating block of text == All email Summaries
            messageCount += 1
            AllEmailSummaries += str(messageCount) + "). Recieved " + str(distance) + " hours ago." + Summary + "\n\n"

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')
    
    return AllEmailSummaries, messageCount
 

def twilioSendEmailSummary():

    AllEmailsString, messageCount = getEmails()  # String representing all email summaries

    MP3_Text = "Debrief of your " + str(messageCount) + " unread email(s) over the past " +  str(hoursOffline) + " hours.\n\n" +  AllEmailsString

    print(MP3_Text)

    EmailMP3 = gTTS(text=MP3_Text, lang='en', slow=False)  # Email imput, english, Not slow
    EmailMP3.save(savePath)

    twilioCli = Client(TwilioAccountSid, TwilioAuthToken)
    
    message = twilioCli.messages.create(
    from_=myTwilioNumber,
    to=myCellPhone,
    body = MP3media,
    )
    

twilioSendEmailSummary()