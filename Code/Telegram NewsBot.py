import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async
import os
import pandas as pd
import newspaper
from newsplease import NewsPlease
import datetime

PORT = int(os.environ.get('PORT', 5000))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
TOKEN = 'YOUR_TOKEN'

news_pages = {'Ecuador': ['https://www.primicias.ec/','https://www.eluniverso.com/','https://www.expreso.ec/'],
             'Paraguay': ['https://www.ultimahora.com/contenidos/nacional.html','https://www.lanacion.com.py/','https://www.abc.com.py/nacionales/'],
             'Argentina':['https://www.lanacion.com.ar/','https://www.clarin.com/','https://www.cronista.com/','https://www.infobae.com/','https://www.ambito.com/'],
             'El Salvador':['https://www.elsalvador.com/','https://diario.elmundo.sv/'],
             'Guatemala':['https://republica.gt/','https://www.prensalibre.com/guatemala/','https://lahora.gt/']}

class NewsFeed:

    def __init__(self,url_list,language):
        self.url_list = url_list
        self.language = language

    def get_news(self):
        self.article_list=[]
        for link in self.url_list:
            page = newspaper.build(link,language=self.language,memoize_articles=False)
            #page.clean_memo_cache()
            for art in page.articles:
                self.article_list.append(art.url)
        self.article_list=list(set(self.article_list))

    def filter_news(self,keywords):
        keywords = keywords.split(',')
        self.filtered_urls=[]
        for art in self.article_list:
            if any(word in art for word in keywords):
                self.filtered_urls.append(art)
        print('Done')

    def news_summary(self):
        dic={'Title':[],'Date':[],'URL':[]}
        self.articles = NewsPlease.from_urls(self.filtered_urls)
        today = datetime.datetime.today()
        for i in self.articles.keys():

            if type(self.articles[i].date_publish)!= datetime.datetime:
                date = today
            else:
                 date = self.articles[i].date_publish

            if abs(today - date).days>1:
                pass
            else:
                dic['Title'].append(self.articles[i].title)
                dic['Date'].append(date)
                dic['URL'].append(i)

        parsed_arts = pd.DataFrame(dic).sort_values(by='Date',ascending=False).drop_duplicates(subset ="Title").reset_index()
        parsed_arts['Date']=parsed_arts['Date'].apply(lambda x: x.strftime('%m/%d/%Y %H:%M'))
        parsed_arts.loc[parsed_arts['Date'] == today.strftime('%m/%d/%Y %H:%M'),'Date'] = 'not available'
        parsed_arts['numb'] = parsed_arts.index.to_list()
        self.m='\n'+parsed_arts['numb'].apply(lambda x: str(x+1))+') '+parsed_arts['Title'] +'\n'+ parsed_arts['URL'] + '\nDate: '+ parsed_arts['Date']+'\n'
        self.parsed_news=''
        for i in self.m:
            self.parsed_news+=i

def start(update, context):
    update.message.reply_text(text="Get news feed for available countries:\n"+
                                    "Argentina - Ecuador - El Salvador - Guatemala - Paraguay \n Send country name and press /update\n"+
                                    "Then, send a list of keywords separated by comma and press /get")

def parse_user_input(update,context):
    global user_input
    user_input=update.message.text

def update(update,context):
    update.message.reply_text("Updating data...")
    global news
    try:
        news = NewsFeed(news_pages[user_input],'es')
        news.get_news()
        update.message.reply_text("Data updated")
    except:
        update.message.reply_text("Error: data not available")

def print_news(update,context):
    news.filter_news(str(user_input))
    update.message.reply_text('Please wait, parsing....')
    try:
        news.news_summary()
    except:
        update.message.reply_text('Error: please try again')

    if news.parsed_news!='':
        for i in news.m:
            update.message.reply_text(i)
    else:
        update.message.reply_text('Not available news for given keywords')

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True, workers=100)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start, run_async = True))
    dp.add_handler(CommandHandler("update", update,run_async = True))
    dp.add_handler(CommandHandler("get", print_news, run_async = True))
    dp.add_handler(MessageHandler(Filters.text,parse_user_input, run_async = True))

    # log all errors
    dp.add_error_handler(error,run_async = True)

    # Start the Bot
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN)
    updater.bot.setWebhook('https://your_app.herokuapp.com/' + TOKEN)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
