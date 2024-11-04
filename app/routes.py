from flask import Flask, render_template, request
from utils.vectorizer import process_and_encode_articles,encode_dataset, preprocess_text, download_parse_article
from utils.indexer import get_index, index_dataset,similarity_search
from utils.util import read_from_partitions,read_from_local_partitions
import pandas as pd
from flask import Flask, jsonify, session
from creds import awsconfig
from news_articles.news_articles.spider_runner import NewsArticleSpiderRunner

app = Flask(__name__)

@app.route('/')
def index():
    # Render the main page with the input form
    return render_template('index.html')

@app.route('/search_paragraph', methods=['POST'])
def search_paragraph():
        # Get the text passage from the form
        text_passage = request.form['paragraph']
        if len(text_passage) <100:
            return render_template('error.html', message="Paragraph too Short. Minimum 100 characters required.")

        summary, embedding = process_and_encode_articles([text_passage])

        index = get_index()
        D, I = similarity_search(embedding[0].reshape(1,-1), 5, index)

        bucket_name = 'hrnewsarticles'
        base_file_path = 'NYTimes'
        aws_access_key_id = awsconfig["aws_access_key_id"]
        aws_secret_access_key =awsconfig["aws_secret_access_key"]
        df =read_from_local_partitions(I[0], 990)

        # To enable AWS:
        #df = read_from_partitions(bucket_name, base_file_path,  I[0], 990, aws_access_key_id, aws_secret_access_key)

        result = {i:j for i,j in zip(df['headline'],df['link'])}
        return render_template('results.html', results= result)

@app.route('/search_url', methods=['POST'])
def search_url():
        selected_source = request.form.get('source')

        if selected_source == 'huffpost':
            # Use customized scraper for Huffpost
             print("running spider")
             raw_text = NewsArticleSpiderRunner.run_spider(request.form['url'])

             text_passage = preprocess_text(raw_text[0])
        else:
            # Use package to scrape for other cases
            raw_text = download_parse_article(request.form['url'])
            text_passage = preprocess_text(raw_text)

        summary, embedding = process_and_encode_articles([text_passage])

        index = get_index()
        D, I = similarity_search(embedding[0].reshape(1,-1), 5, index)

        bucket_name = 'hrnewsarticles'
        base_file_path = 'NYTimes'
        aws_access_key_id = awsconfig["aws_access_key_id"]
        aws_secret_access_key =awsconfig["aws_secret_access_key"]
        df =read_from_local_partitions(I[0], 990)
        # To enable AWS:
        #df = read_from_partitions(bucket_name, base_file_path,  I[0], 990, aws_access_key_id, aws_secret_access_key)

        result = {i:j for i,j in zip(df['headline'],df['link'])}
        return render_template('results.html', results= result)


# @app.route('/search_url', methods=['POST'])
# def search_url():
#
#         raw_text = download_parse_article(request.form['url'])
#         text_passage = preprocess_text(raw_text)
#
#         summary, embedding = process_and_encode_articles([text_passage])
#
#         index = get_index()
#         D, I = similarity_search(embedding[0].reshape(1,-1), 5, index)
#
#         bucket_name = 'hrnewsarticles'
#         base_file_path = 'NYTimes'
#         aws_access_key_id = awsconfig["aws_access_key_id"]
#         aws_secret_access_key =awsconfig["aws_secret_access_key"]
#
#         df = read_from_partitions(bucket_name, base_file_path,  I[0], 990, aws_access_key_id, aws_secret_access_key)
#
#         result = {i:j for i,j in zip(df['headline'],df['link'])}
#         return render_template('results.html', results= result)

if __name__ == '__main__':
    app.run(debug=True)
