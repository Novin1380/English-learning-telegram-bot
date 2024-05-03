import telebot
from telebot import types
import openai
import requests
import os
import mysql.connector
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
from telebot import custom_filters
import re
from references import *
import random
from configs import TOKEN,your_api_key,db_config

state_storage = StateMemoryStorage()

# Initialize the bot with your token
bot = telebot.TeleBot(token=TOKEN,parse_mode="HTML",state_storage=state_storage)


# Define the list of hobbies
hobbies = ["Game", "Reading", "Sports", "Music", "Travel","Social Media" , "done"]
series = ['Breaking Bad', 'Money Heist' , 'Friends' , 'Vikings' , 'Picky Blinders' , "done2"]
english_levels = ['beginner', 'intermediate', 'advance']


# Variable to track the state of the conversation


## Data Base Configuration
user_data = {}
user_data_hobb = {}
user_data_ser = {}
user_prompt = {}




## This section is for managing states of learning words
class LearningStates(StatesGroup):
    add_words = State()
    choose_hobbies = State()
    choose_series = State()
    get_text = State()
    get_level = State()
    random_words = State()


## This section is for managing states of accounts
class accounts(StatesGroup):
    accs = State()

## This part is for support section
chat_ids = []
texts = {}
class Support(StatesGroup):
    text = State()
    respond = State()

def escape_special_characters(text):
    special_characters = r"([\*\_\[\]\(\)\~\`\>\#\+\-\=\|\{\}\.\!])"
    return re.sub(special_characters, r'\\\1', text)

@bot.message_handler(commands=['start'])
def start(message):
    """Send a message when the /start command is issued."""
    bot.delete_state(user_id=message.from_user.id, chat_id=message.chat.id)
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    print(message.from_user.id)
    sql = f"SELECT id FROM data WHERE id = {message.from_user.id}"
    cursor.execute(sql)
    result = cursor.fetchone()

    if result is None:
        sql = f'INSERT INTO data (id) VALUES ({message.from_user.id})'
        cursor.execute(sql)
        sql1 = f"UPDATE data SET usename = '{message.from_user.first_name}' WHERE id = {message.from_user.id}"
        cursor.execute(sql1)
        connection.commit()
        

        bot.send_message(chat_id=message.chat.id, text=f"""Hello <b>{message.from_user.first_name}</b>, welcome to <b>Personalized Learning bot</b> 💫

<b>Explore Language with Story AI Bot</b>✨️
Dive into language learning on Telegram with our bot! It teaches vocabulary through stories and crafts images for each tale.
Engage, learn, and visualize with every word! 🔥""")
        
        bot.send_message(chat_id=message.chat.id, text="Let's see how good your language level is ...")
        language_level(message)
    else:
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add("🧠 Vocabulary Learning")
        markup.add("👤 My account","☎️ Support")
        bot.send_message(chat_id=message.chat.id, text=f"welcome back {message.from_user.first_name}!, I'm here to help you learn words quickly👋")
        bot.send_message(chat_id=message.chat.id, text="Select one of the buttons to start",reply_markup=markup)


def language_level(message):
    """ chosing three sentences for finding accounts language level"""
    bot.set_state(user_id=message.from_user.id, state=LearningStates.get_level, chat_id=message.chat.id)
    x = random.randint(0,len(beginner_sentences)-1)
    y = random.randint(0,len(intermediate_sentences)-1)
    z = random.randint(0,len(advanced_sentences)-1)

    beginner  =  beginner_sentences[x]
    intermediate  =  intermediate_sentences[y]
    advance  =  advanced_sentences[z]
    bot.send_message(chat_id=message.chat.id, text="<b>Please choose the sentence that you completely understand!</b>")
    keyboard = types.InlineKeyboardMarkup()
    
    button1 = types.InlineKeyboardButton(text='Sentence1️⃣', callback_data='beginner')
    button2 = types.InlineKeyboardButton(text='Sentence2️⃣', callback_data='intermediate')
    button3 = types.InlineKeyboardButton(text='Sentence3️⃣', callback_data='advance')
    keyboard.add(button1)
    keyboard.add(button2)
    keyboard.add(button3)
    bot.send_message(chat_id=message.chat.id, text=f"""Sentence1️⃣: 
<code>{beginner}</code>  
                                     
Sentence2️⃣: 
<code>{intermediate}</code>

Sentence3️⃣: 
<code>{advance}</code>       
                    """, reply_markup=keyboard)
    
    
@bot.callback_query_handler(func=lambda call: call.data in english_levels)
def level_handler(call):
    chat_id = call.message.chat.id
    level = call.data
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    sql1 = f"UPDATE data SET level = '{level}' WHERE id = {chat_id}"
    cursor.execute(sql1)
    connection.commit()
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🧠 Vocabulary Learning")
    markup.add("👤 My account","☎️ Support")
    bot.send_message(chat_id=call.message.chat.id, text=f"Great! Your english level is <code>{level}</code>")
    bot.delete_state(user_id=call.message.from_user.id, chat_id=call.message.chat.id)
    # bot.send_message(chat_id=call.message.chat.id, text="Select one of the buttons to start",reply_markup=markup)
    bot.send_message(chat_id=call.message.chat.id, text=f"Now let me get to know you better")
    bot.set_state(user_id=call.message.from_user.id, state=LearningStates.choose_hobbies, chat_id=call.message.chat.id)
    display_hobbies(call.message)
    
    
    



################ My account button details #################
def country(user):

    sql = f"SELECT country FROM data WHERE id = {user}"

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    cursor.execute(sql)
    result = cursor.fetchone()

    return result

def prompts(user):
    sql = f"SELECT prompt FROM data WHERE id = {user}"
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    cursor.execute(sql)
    result = cursor.fetchone()

    return result



@bot.message_handler(func= lambda message: message.text == "👤 My account")
def account(message):
    bot.delete_state(user_id=message.from_user.id, chat_id=message.chat.id)
    bot.set_state(user_id=message.from_user.id, state=accounts.accs, chat_id=message.chat.id)
    Country = country(user=message.from_user.id)
    Prompts = prompts(user=message.from_user.id)
    bot.send_message(chat_id=message.chat.id, text=f"""📊 Your account details:

👤 Username: <a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>
🪪 User_id: <code>{message.from_user.id}</code>

💡 Prompts: {Prompts[0]}
🌎 Country: {Country[0]}
💰 Balance: 0 $ """, parse_mode="HTML")
    bot.delete_state(user_id=message.from_user.id, chat_id=message.chat.id)



################################################################


##################### Vocabulary Learning functions #####################
@bot.message_handler(func= lambda m: m.text == "🧠 Vocabulary Learning")
def Learning_words(message):
    bot.delete_state(user_id=message.from_user.id, chat_id=message.chat.id)
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    sql = f"SELECT prompt FROM data WHERE id = {message.from_user.id}"
    cursor.execute(sql)
    result = cursor.fetchone()
    print(result[0])
    if result[0] == 0:
        bot.send_message(chat_id=message.chat.id, text=f"""Hello <b>{message.from_user.first_name}</b>, welcome to <b>Vocabulary Learning bot</b> 💫

<b>Explore Language with Story AI Bot</b>✨️
In this section, based on the information you've shared about yourself, we'll recommend words that are appropriate for your language level and can help you improve your vocabulary.

<b>Our learning method involves creating stories accompanied by images to help you solidify the words in your mind.</b>

just enjoy🔥""")
        

        bot.send_message(chat_id=message.chat.id, text="""Based on your english level, I recommend you to learn the following words:""" )
    else :
        bot.send_message(chat_id=message.chat.id, text="""Based on your english level, I recommend you to learn the following words:""" )
        
    try: 
        sql = f"SELECT level FROM data WHERE id = {message.from_user.id}"
        cursor.execute(sql)
        result1 = cursor.fetchone()[0]
        print(result1)
        if not result1 is None :
            print("HI")
            bot.set_state(user_id=message.from_user.id, state=LearningStates.random_words, chat_id=message.chat.id)
            if result1 == "beginner":
                display_word_options(message, beginner_words)
            elif result1 == "intermediate":
                display_word_options(message, intermediate_words)
            elif result1 == "advance":
                print("advance")
                display_word_options(message, advanced_words)
            else:
                print("bye")
        else:
            bot.send_message(chat_id=message.chat.id, text="Let's see how good your language level is ...")
            language_level(message)
    except Exception as e:
        print(f"{e}")

        
def display_word_options(message, word_list):
    print("done")
    bot.set_state(user_id=message.from_user.id, state=LearningStates.random_words, chat_id=message.chat.id)

    word_keyboard = telebot.types.InlineKeyboardMarkup()

    # Randomly select 10 words from the word list
    selected_words_from_list = random.sample(word_list, 10)

    # Add the words to the keyboard markup
    for word in selected_words_from_list:
        button = telebot.types.InlineKeyboardButton(text=word, callback_data=word)
        word_keyboard.add(button)

    # Add the "Done" button to the keyboard markup
    done_button = telebot.types.InlineKeyboardButton(text="Done✅", callback_data="done3")
    word_keyboard.add(done_button)

    # Send the keyboard markup
    bot.send_message(chat_id=message.chat.id, text="""Please select the word(s) whose meaning you dont know!
                     
When you're done entering words, click the 'Done✅' button to proceed.""", reply_markup=word_keyboard)
            
# Handle the callback queries for word selection
@bot.callback_query_handler(func=lambda call: call.data in beginner_words + intermediate_words + advanced_words)
def handle_word_selection(call):
    chat_id = call.message.chat.id
    word = call.data
    
    if chat_id not in user_data:
        user_data[chat_id] = {'user_words': []}  # ایجاد یک لیست خالی برای user_words
    if word in user_data[chat_id]['user_words']:
        user_data[chat_id]['user_words'].remove(word)
        bot.answer_callback_query(call.id, text=f"{word} removed from your words selection.")
    else:
        user_data[chat_id]['user_words'].append(word)
        bot.answer_callback_query(call.id, text=f"{word} added to your words selection.")
    
    

# Handle the "Done" callback query
@bot.callback_query_handler(func=lambda call: call.data == "done3")
def handle_done(call):
    chat_id = call.message.chat.id
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    print(chat_id)
    print(user_data[chat_id]['user_words'])
    if user_data[chat_id]['user_words']:
        bot.send_message(chat_id=call.message.chat.id, text=f"You selected: {', '.join(user_data[chat_id]['user_words'])}")
    else:
        bot.send_message(chat_id=chat_id, text="You didn't select any words.")
    sql = f"SELECT hobbies FROM data WHERE id = {chat_id}"
    cursor.execute(sql)
    result = cursor.fetchone()[0]
    hobbies = result
    sql1 = f"SELECT series FROM data WHERE id = {chat_id}"
    cursor.execute(sql1)
    res = cursor.fetchone()[0]
    series = res
    bot.delete_state(user_id=call.message.from_user.id, chat_id=call.message.chat.id)
    bot.set_state(user_id=call.message.from_user.id, state=LearningStates.get_text, chat_id=call.message.chat.id)
    get_text(call.message , hobbies ,series)





##################### Support Functions #####################
@bot.message_handler(func= lambda m: m.text == "☎️ Support")
def sup(m):
    bot.delete_state(user_id=m.from_user.id, chat_id=m.chat.id)
    bot.send_message(chat_id=m.chat.id, text="Please send your message:")

    bot.set_state(user_id=m.from_user.id, state=Support.text, chat_id=m.chat.id)


@bot.message_handler(state=Support.text)
def sup_text(m):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="Answer", callback_data=m.chat.id))

    bot.send_message(chat_id=103148378, text=f"Recived a message from <code>{m.from_user.id}</code> with username @{m.from_user.username}:\nMessage text:\n\n<b>{escape_special_characters(m.text)}</b>", reply_markup=markup, parse_mode="HTML")

    bot.send_message(chat_id=m.chat.id, text="Your message was sent to admin!")

    texts[m.from_user.id] = m.text

    bot.delete_state(user_id=m.from_user.id, chat_id=m.chat.id)



@bot.message_handler(state=Support.respond)
def answer_text(m):
    chat_id = chat_ids[-1]

    if chat_id in texts:
        bot.send_message(chat_id=chat_id, text=f"Your message:\n<i>{escape_special_characters(texts[chat_id])}</i>\n\nSupport answer:\n<b>{escape_special_characters(m.text)}</b>", parse_mode="HTML")
        bot.send_message(chat_id=m.chat.id, text="Your answer was sent!")

        del texts[chat_id]
        chat_ids.remove(chat_id)
    else:
        bot.send_message(chat_id=m.chat.id, text="Something went wrong. Please try again...")

    bot.delete_state(user_id=m.from_user.id, chat_id=m.chat.id)




@bot.message_handler(state=LearningStates.choose_hobbies)
def display_hobbies(message):
    """Display the list of hobbies as inline keyboard buttons."""
    keyboard = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text='Game🎮', callback_data='Game')
    button2 = types.InlineKeyboardButton(text='Reading📖', callback_data='Reading')
    button3 = types.InlineKeyboardButton(text='Sports⛹️‍♂️', callback_data="Sports")
    button4 = types.InlineKeyboardButton(text="Music🎧", callback_data="Music")
    button5 = types.InlineKeyboardButton(text="Travel🛩", callback_data="Travel")
    button6 = types.InlineKeyboardButton(text="Social Media📱", callback_data="Social Media")
    keyboard.add(button1)
    keyboard.add(button2)
    keyboard.add(button3)
    keyboard.add(button4)
    keyboard.add(button5)
    keyboard.add(button6)
    done_button = types.InlineKeyboardButton(text="Done✅", callback_data="done")
    keyboard.add(done_button)
    bot.send_message(chat_id=message.chat.id, text="""What <b>hobbies</b> do you usually do in your free time?

You can select up to 4 hobbies""", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data in hobbies)
def button_clicked(call):
    """Handle the callback when a hobby button or the 'Done' button is clicked."""

    chat_id = call.message.chat.id

    if chat_id not in user_data_hobb:
        user_data_hobb[chat_id] = {'selected_hobbies': []}

    hobb = user_data_hobb[chat_id]['selected_hobbies']
    if call.data == "done":
        if len(hobb) > 0:
            bot.send_message(chat_id=call.message.chat.id, text=f"You have selected the following hobbies: {', '.join(hobb)}")
            try:
                hobbies_str = ", ".join(hobb)
                hobbies_sql = f"{hobbies_str}"
                connection = mysql.connector.connect(**db_config)
                cursor = connection.cursor()
                sql1 = f"UPDATE data SET hobbies = '{hobbies_sql}' WHERE id = {chat_id}"
                cursor.execute(sql1)
                connection.commit()
                print("result : len>0 done, saved")
                bot.delete_state(user_id=call.message.from_user.id, chat_id=call.message.chat.id)
                bot.set_state(user_id=call.message.from_user.id, state=LearningStates.choose_series, chat_id=call.message.chat.id)
                hobbies = user_data_hobb[chat_id]['selected_hobbies']
                display_series(call.message)
            except Exception as e:
                print(f"{e}")
                bot.delete_state(user_id=call.message.from_user.id, chat_id=call.message.chat.id)
                bot.set_state(user_id=call.message.from_user.id, state=LearningStates.choose_series, chat_id=call.message.chat.id)
                hobbies = user_data_hobb[chat_id]['selected_hobbies']
                display_series(call.message)
        else:
            bot.send_message(chat_id=call.message.chat.id, text="You haven't selected any hobbies.")
    elif call.data == "Social Media" or "Travel" or "Music" or "Sports" or 'Game' or 'Reading':
        hobby = call.data
        if hobby in hobb:
            user_data_hobb[chat_id]['selected_hobbies'].remove(hobby)
            bot.answer_callback_query(call.id, text=f"{hobby} removed from your selection.")
        elif len(hobb) < 4:
            user_data_hobb[chat_id]['selected_hobbies'].append(hobby)
            bot.answer_callback_query(call.id, text=f"{hobby} added to your selection.")
        else:
            bot.answer_callback_query(call.id, text="You can only select up to 4 hobbies.")

        if len(hobb) == 4:
            bot.send_message(chat_id=call.message.chat.id, text=f"You have selected the maximum number of hobbies. \nYou have selected the following hobbies: {', '.join(hobb)}")
            try:
                hobbies_str = ", ".join(hobb)
                hobbies_sql = f"{hobbies_str}"
                connection = mysql.connector.connect(**db_config)
                cursor = connection.cursor()
                sql1 = f"UPDATE data SET hobbies = '{hobbies_sql}' WHERE id = {chat_id}"
                cursor.execute(sql1)
                connection.commit()
                print("result : len=4 done, saved")
                bot.delete_state(user_id=call.message.from_user.id, chat_id=call.message.chat.id)
                bot.set_state(user_id=call.message.from_user.id, state=LearningStates.choose_series, chat_id=call.message.chat.id)
                hobbies = user_data_hobb[chat_id]['selected_hobbies']
                display_series(call.message)
                
            except Exception as e:
                print(f"{e}")
                bot.delete_state(user_id=call.message.from_user.id, chat_id=call.message.chat.id)
                hobbies = user_data_hobb[chat_id]['selected_hobbies']
                bot.delete_state(user_id=call.message.from_user.id, chat_id=call.message.chat.id)
                bot.set_state(user_id=call.message.from_user.id, state=LearningStates.choose_series, chat_id=call.message.chat.id)
                display_series(call.message)
                
    print(user_data_hobb)
    print(user_data)
    print(user_data_ser)

def done_hobbies(call,hobbies):
    print("done hobbie")
    bot.delete_state(user_id=call.message.from_user.id, chat_id=call.message.chat.id)
    bot.set_state(user_id=call.message.from_user.id, state=LearningStates.choose_series, chat_id=call.message.chat.id)
    hobbies = hobbies
    chat_id = call.message.chat.id
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    sql = f"SELECT series FROM data WHERE id = {chat_id}"
    cursor.execute(sql)
    result = cursor.fetchone()
    print(f"result: {result}")
    if result[0] is None:
        if chat_id in user_data:
            # Process the user's data here, for example, save it to a database or log it
            user_data[chat_id]['state'] = 'choose_series'
            bot.delete_state(user_id=call.message.from_user.id, chat_id=call.message.chat.id)
            bot.set_state(user_id=call.message.from_user.id, state=LearningStates.choose_series, chat_id=call.message.chat.id)
            display_series(call.message)
        else:
            pass
    else:
        series = result[0]
        print(series)
        bot.delete_state(user_id=call.message.from_user.id, chat_id=call.message.chat.id)
        
    bot.delete_state(user_id=call.message.from_user.id, chat_id=call.message.chat.id)
        
@bot.message_handler(state=LearningStates.choose_series)
def display_series(message):
    bot.set_state(user_id=message.from_user.id, state=LearningStates.choose_series, chat_id=message.chat.id)
    print("display")
    """Display the list of series as inline keyboard buttons."""
    keyboard = types.InlineKeyboardMarkup()

    button11 = types.InlineKeyboardButton(text='Breaking Bad', callback_data='Breaking Bad')
    button12 = types.InlineKeyboardButton(text='Friends', callback_data='Friends')
    button13 = types.InlineKeyboardButton(text='Money Heist', callback_data="Money Heist")
    button14 = types.InlineKeyboardButton(text="Picky Blinders", callback_data="Picky Blinders")
    button15 = types.InlineKeyboardButton(text="Vikings", callback_data="Vikings")
    keyboard.add(button11)
    keyboard.add(button12)
    keyboard.add(button13)
    keyboard.add(button14)
    keyboard.add(button15)
    done_button = types.InlineKeyboardButton(text="Done✅", callback_data="done2")
    keyboard.add(done_button)
    bot.send_message(chat_id=message.chat.id, text="""What <b>series</b> have you seen and become interested in it?

You can select up to 3 series""", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data in series)
def button_click(call):
    """Handle the callback when a series button or the 'Done' button is clicked."""
    chat_id = call.message.chat.id
    bot.set_state(user_id=call.message.from_user.id, state=LearningStates.choose_series, chat_id=call.message.chat.id)
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    sql = f"SELECT hobbies FROM data WHERE id = {chat_id}"
    cursor.execute(sql)
    result = cursor.fetchone()
    chat_id = call.message.chat.id

    if chat_id not in user_data_ser:
        user_data_ser[chat_id] = {'selected_series': []}

    serr = user_data_ser[chat_id]['selected_series']
    if call.data == "done2":
        if len(serr) > 0:
            bot.send_message(chat_id=call.message.chat.id, text=f"You have selected the following series: {', '.join(serr)}")
            try:
                series_str = ", ".join(serr)
                series_sql = f"{series_str}"
                connection = mysql.connector.connect(**db_config)
                cursor = connection.cursor()
                sql1 = f"UPDATE data SET series = '{series_sql}' WHERE id = {chat_id}"
                cursor.execute(sql1)
                connection.commit()
                print("result : len>0 done2, saved")
                bot.delete_state(user_id=call.message.from_user.id, chat_id=call.message.chat.id)
                series = user_data_ser[chat_id]['selected_series']
                welcome(call.message)
            except Exception as e:
                print(f"{e}")
                bot.delete_state(user_id=call.message.from_user.id, chat_id=call.message.chat.id)
                series = user_data_ser[chat_id]['selected_series']
                welcome(call.message)

        else:
            bot.send_message(chat_id=call.message.chat.id, text="You haven't selected any series.")
    elif call.data == "Picky Blinders" or "Vikings" or "Friends" or "Money Heist" or 'Breaking Bad':
        ser = call.data
        if ser in serr:
            user_data_ser[chat_id]['selected_series'].remove(ser)
            bot.answer_callback_query(call.id, text=f"{ser} removed from your series selection.")
        elif len(serr) < 3:
            user_data_ser[chat_id]['selected_series'].append(ser)
            bot.answer_callback_query(call.id, text=f"{ser} added to your series selection.")
        else:
            bot.answer_callback_query(call.id, text="You can only select up to 3 series.")

        if len(serr) == 3:
            bot.send_message(chat_id=call.message.chat.id, text=f"You have selected the maximum number of series. \nYou have selected the following series: {', '.join(serr)}")
            try:
                series_str = ", ".join(serr)
                series_sql = f"{series_str}"
                connection = mysql.connector.connect(**db_config)
                cursor = connection.cursor()
                sql1 = f"UPDATE data SET series = '{series_sql}' WHERE id = {chat_id}"
                cursor.execute(sql1)
                connection.commit()
                print("result : len=4 done2, saved")
                bot.delete_state(user_id=call.message.from_user.id, chat_id=call.message.chat.id)
                series = user_data_ser[chat_id]['selected_series']
                welcome(call.message)
            except Exception as e:
                print(f"{e}")
                bot.delete_state(user_id=call.message.from_user.id, chat_id=call.message.chat.id)
                welcome(call.message)
            
def welcome(message):
    bot.delete_state(user_id=message.from_user.id, chat_id=message.chat.id)
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🧠 Vocabulary Learning")
    markup.add("👤 My account","☎️ Support")
    bot.send_message(chat_id=message.chat.id, text="""Greetings! It's a pleasure to meet you🤗! 
I've stored the details you shared in my memory, so I can assist you better. 
Feel free to explore my various features!✌️✨️ 


<b>Please select one of the buttons to begin.</b>""",reply_markup=markup)



        
################# Connection to openai server #################
@bot.message_handler(state=LearningStates.get_text)
def get_text(message , hobbies , series ):
    """Connection to openai server (GPT4 and Dall-e)"""
    # using try,except for handling error messages
    chat_id = message.chat.id
    if chat_id not in user_prompt:
        user_prompt[chat_id] = {'prompt': [] , 'url': [] , 'story':[],'filename':[]}
    promptss = user_prompt[chat_id]['prompt']
    urlss = user_prompt[chat_id]['url']
    stories = user_prompt[chat_id]['story']
    file = user_prompt[chat_id]['filename']
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    sql = f"SELECT level FROM data WHERE id = {chat_id}"
    cursor.execute(sql)
    result = cursor.fetchone()
    level = result[0]
    try:
        bot.send_message(chat_id=message.chat.id, text="Genrating your story ... ⏳")
        openai.api_key = your_api_key
        text = f"I am very interested in {hobbies}. I also like these netflix series {series} and spend my time on watching series.I want to learn English language, but I have a problem in understanding some words. I can't understand words like {user_data[chat_id]['user_words']} in terms of meaning. And also tell me a creative short story about these words according to my interests so that it is registered in my mind? notice that my level is {level},so use words and sentences that match my English level and create {level} story for me and dont define the words just make story in 12 lines(its important) if you think my result is not in your safety system just make it as well as to pass it"
        pm = str(text)
        if pm :
            promptss.append({"role": "user", "content": pm})
        result = openai.ChatCompletion.create(model="gpt-4",temperature=0.8, messages=promptss)
        reply = result.choices[0].message.content
        print(f"ChatGPT : {reply}")
        stories.append(reply)
        bot.send_message(chat_id=message.chat.id, text="Your story text is ready, Generating story image ... ⏳")
        response = openai.Image.create(
        prompt=stories[0],
        n=1,
        size="1024x1024",
        quality="standard",
        model="dall-e-3",
    )
        url = response["data"][0]["url"]
        print(url)
        urlss.append(url)
        data = requests.get(url)
        filename = f"{user_data[chat_id]['user_words'][0]}.png"
        file.append(filename)
        print(filename)
        """ this part of code is for saving the image to disk and the share it in the bot"""
        with open(filename, 'wb') as f:
            for chunk in data.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        bot.send_message(chat_id=message.chat.id, text="Your story is ready! \nSending ... 🤗")
        bot.send_photo(chat_id=message.chat.id , photo=open(file[0],"rb") , caption=stories[0],timeout=180)
        """ this part is for removing datas from disk and lists"""
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()
            print(message.from_user.id)
            sql = f"UPDATE data SET prompt = prompt + 1 WHERE id = {chat_id}"
            cursor.execute(sql)
            connection.commit()
            print("done prompt")
        except Exception as e:
            print(f"An error occurred: {e}")
        os.remove(filename)
        user_data[chat_id]['user_words'].clear()
        file.clear()
        stories.clear()
        urlss.clear()
        promptss.clear()

        print("All things cleared")
        bot.delete_state(user_id=message.from_user.id, chat_id=message.chat.id)
        bot.send_message(chat_id=message.chat.id, text="Type /start to start again! ")

    except Exception as e:
        bot.delete_state(user_id=message.from_user.id, chat_id=message.chat.id)
        bot.send_message(chat_id=message.chat.id, text="""<b>Something went wrong!</b>


Type /start to restart the bot""")
        print(f"{e}")
    bot.delete_state(user_id=message.from_user.id, chat_id=message.chat.id)
##########################################################


@bot.callback_query_handler(func= lambda call: True)
def answer(call):
    bot.send_message(chat_id=call.message.chat.id, text=f"Send your answer to <code>{call.data}</code>:", parse_mode="HTML")

    chat_ids.append(int(call.data))

    bot.set_state(user_id=call.from_user.id, state=Support.respond, chat_id=call.message.chat.id)


# Start the bot
if __name__ == '__main__':
    bot.add_custom_filter(custom_filters.StateFilter(bot))
    bot.infinity_polling(skip_pending=True)