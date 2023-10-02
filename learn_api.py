# IMPORT LIBRARIES FOR REGEX, PANDAS, NUMPY, SQLITE3, MATPLOTLIB, SEABORN, AND WARNINGS (TO IGNORE VISUALIZATION RESULT WARNING
import re
import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

# IMPORT LIBRARY FOR FLASK AND SWAGGER
from flask import Flask, jsonify, request
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flasgger import swag_from

# DEFAULT FLASK AND SWAGGER DEFAULT SETTING
app = Flask(__name__)
app.json_encoder = LazyJSONEncoder
swagger_template = dict(
info = {
    'title': LazyString(lambda: 'API Documentation for Data Processing and Modeling'),
    'version': LazyString(lambda: '1.0.0'),
    'description': LazyString(lambda: 'Dokumentasi API untuk Data Processing dan Modeling'),
    },
    host = LazyString(lambda: request.host)
)
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'docs',
            "route": '/docs.json',
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}
swagger = Swagger(app, template=swagger_template,             
                  config=swagger_config)

# IMPORT ABUSIVE.CSV AND NEW_KAMUSALAY.CSV TO PANDAS DATAFRAME (EACH)
df_abusive = pd.read_csv('abusive.csv')
df_kamusalay = pd.read_csv('new_kamusalay.csv', encoding='latin-1', header=None)
df_kamusalay.columns=["tidak baku","baku"]

# DEFINE ENDPOINTS: BASIC GET
@swag_from("D:/MY 2020 DATA JOURNEY/FROM D MY DOCUMENT/BINAR ACADEMY/some_project/docs/hello_world.yml", methods=['GET'])
@app.route('/', methods=['GET'])
def hello_world():
    json_response = {
        'status_code': 200,
        'description': "Menyapa Hello World",
        'data': "Hello World",
    }
    response_data = jsonify(json_response)
    return response_data

# DEFINE ENDPOINTS: POST FOR TEXT PROCESSING FROM TEXT INPUT
@swag_from("D:/MY 2020 DATA JOURNEY/FROM D MY DOCUMENT/BINAR ACADEMY/some_project/docs/text_processing.yml", methods=['POST'])
@app.route('/text-processing', methods=['POST'])
def text_processing():
    
    text = request.form.get('text')
    
    json_response = {
        'status_code': 200,
        'description': "Teks yang sudah diproses",
        'data': re.sub(r'[^a-zA-Z0-9]',' ', text)
    }
    
    response_data = jsonify(json_response)
    return response_data

# DEFINE ENDPOINTS: POST FOR TEXT PROCESSING FROM FILE
@swag_from("D:/MY 2020 DATA JOURNEY/FROM D MY DOCUMENT/BINAR ACADEMY/some_project/docs/text_processing_file.yml", methods=['POST'])
@app.route('/text-processing-file', methods=['POST'])
def text_processing_file():
    global post_df
    
    # USING REQUEST TO GET FILE THAT HAS BEEN POSTED FROM API ENDPOINT
    file = request.files.get('file')
    
    # IMPORT FILE OBJECT INTO PANDAS DATAFRAME (YOU CAN SPECIFY NUMBER OF ROWS IMPORTED USING PARAMETER nrows=(integer value) )
    post_df = pd.read_csv(file, encoding='latin-1')
    
    # SET THE TWEET COLUMN ONLY FOR THE DATAFRAME
    post_df = post_df[['Tweet']]
    
    # DROP DUPLICATED TWEETS
    post_df.drop_duplicates(inplace=True)
    
    # CREATE NEW NUMBER OF CHARACTERS (NO_CHAR) COLUMN THAT CONSISTS OF LENGTH OF TWEET CHARACTERS
    post_df['no_char'] = post_df['Tweet'].apply(len)
    
    # CREATE NEW NUMBER OF WORDS (NO_WORDS) COLUMN THAT CONSISTS OF NUMBER OF WORDS OF EACH TWEET
    post_df['no_words'] = post_df['Tweet'].apply(lambda x: len(x.split()))
    
    # CREATE A FUNCTION TO CLEAN DATA FROM ANY NON ALPHA-NUMERIC (AND NON-SPACE) CHARACTERS, AND STRIP IT FROM LEADING/TRAILING SPACES
    def tweet_cleansing(x):
        tweet = x
        cleaned_tweet = re.sub(r'[^a-zA-Z0-9 ]','',tweet).strip()
        return cleaned_tweet
    
    # APPLY THE TWEET_CLEANSING FUNCTION ON TWEET COLUMN, AND CREATE A NEW CLEANED_TWEET COLUMN
    post_df['cleaned_tweet'] = post_df['Tweet'].apply(lambda x: tweet_cleansing(x))
    
    # CREATE NEW NO_CHAR, AND NO_WORDS COLUMNS BASED ON CLEANED_TWEET COLUMN
    post_df['no_char_2'] = post_df['cleaned_tweet'].apply(len)
    post_df['no_words_2'] = post_df['cleaned_tweet'].apply(lambda x: len(x.split()))
    
    # CREATE A FUNCTION TO COUNT NUMBER OF ABUSIVE WORDS FOUND IN A CLEANED TWEET
    def count_abusive(x):
        cleaned_tweet = x
        matched_list = []
        for i in range(len(df_abusive)):
            for j in x.split():
                word = df_abusive['ABUSIVE'].iloc[i]
                if word==j.lower():
                    matched_list.append(word)
        return len(matched_list)
    
    # APPLY THE FUNCTION TO COUNT ABUSIVE WORDS, AND CREATE A NEW COLUMN BASED OFF OF IT
    post_df['estimated_no_abs_words'] = post_df['cleaned_tweet'].apply(lambda x: count_abusive(x))
    
    # CONNECT / CREATE NEW DATABASE AND CREATE NEW TABLE CONSISTING LISTED TABLES
    conn = sqlite3.connect('database_project.db')
    q_create_table = """
    create table if not exists post_df (Tweet varchar(255), no_char int, no_words int, cleaned_tweet varchar(255), no_char_2 int, no_words_2 int);
    """
    conn.execute(q_create_table)
    conn.commit()
    
    # CHECK WHETHER TABLE ALREADY HAS DATA IN IT (TABLE HAS ROWS OF DATA IN IT)
    cursor = conn.execute("select count(*) from post_df")
    num_rows = cursor.fetchall()
    num_rows = num_rows[0][0]
    
    #  DO DATA INSERTIONS IF TABLE HAS NO DATA IN IT    
    if num_rows == 0:
    # DO ITERATIONS TO INSERT DATA (EACH ROW) FROM FINAL DATAFRAME (POST_DF)
        for i in range(len(post_df)):
            tweet = post_df['Tweet'].iloc[i]
            no_char = int(post_df['no_char'].iloc[i])
            no_words = int(post_df['no_words'].iloc[i])
            cleaned_tweet = post_df['cleaned_tweet'].iloc[i]
            no_char_2 = int(post_df['no_char_2'].iloc[i])
            no_words_2 = int(post_df['no_words_2'].iloc[i])
    
            q_insertion = "insert into post_df (Tweet, no_char, no_words, cleaned_tweet, no_char_2, no_words_2) values (?,?,?,?,?,?)"
            conn.execute(q_insertion,(tweet,no_char,no_words,cleaned_tweet,no_char_2,no_words_2))
            conn.commit()    
    
    conn.close()
    
    # VISUALIZE THE NUMBER OF ABUSIVE WORDS USING BARPLOT (COUNTPLOT)
    plt.figure(figsize=(10,7))
    countplot = sns.countplot(data=post_df, x="estimated_no_abs_words")
    for p in countplot.patches:
        countplot.annotate(format(p.get_height(), '.0f'), (p.get_x() + p.get_width() / 2., p.get_height()),  ha = 'center'
                            , va = 'center', xytext = (0, 10), textcoords = 'offset points')

    # %matplotlib inline
    # warnings.filterwarnings('ignore', category=FutureWarning)

    plt.title('Count of Estimated Number of Abusive Words')
    plt.xlabel('Estimated Number of Abusive Words')
    plt.savefig('new_countplot.jpeg')
    
    plt.figure(figsize=(20,4))
    boxplot = sns.boxplot(data=post_df, x="no_words_2")

    print()
    
    # VISUALIZE THE NUMBER OF WORDS USING BOXPLOT
    # %matplotlib inline
    # warnings.filterwarnings('ignore', category=FutureWarning)

    plt.title('Number of Words Boxplot (after tweet cleansing)')
    plt.xlabel('')
    plt.savefig('new_boxplot.jpeg')
    
    # OUTPUT THE RESULT IN JSON FORMAT
    json_response = {
        'status_code': 200,
        'description': "Teks yang sudah diproses",
        'data': list(post_df['cleaned_tweet'])
    }
    
    response_data = jsonify(json_response)
    return response_data

if __name__ == "__main__":
    app.run()