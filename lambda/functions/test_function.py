import os
import requests
from elasticsearch import Elasticsearch, RequestsHttpConnection

from requests_aws4auth import AWS4Auth
import boto3

aws_es_endpoint = 'search-ipesdomain-e2x7tyfwfiqxxmwy7a5s34ksqe.us-east-1.es.amazonaws.com'




def elasticsearch_sign():
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, 'us-east-1', service, session_token=credentials.token)

    es_client = Elasticsearch( hosts=[{'host': aws_es_endpoint, 'port': 443}],
                               http_auth=awsauth,
                               use_ssl=True,
                               verify_certs=True,
                               connection_class=RequestsHttpConnection)
    print 'AMOL-: SIGN: ES Init Done! Instance={}'.format(es_client)

    try:
        print 'AMOL-: SIGN: Indices={}'.format(es_client.indices.get_alias().keys())
        print 'AMOL-: SIGN: Indice Query PASS'
    except:
        print 'AMOL-: SIGN: Indice Query FAIL'

    document = {
        "title": "Moneyball",
        "director": "Bennett Miller",
        "year": "2011"
    }

    print 'AMOL: SIGN: Index Document={}'.format(es_client.index(index="movies", doc_type="_doc", id="5", body=document))

    print 'AMOL: SIGN: Indexed Document={}'.format(es_client.get(index="movies", doc_type="_doc", id="5"))


def lambda_handler(event, context):
    print 'AMOL: event={}'.format(event)
    print 'AMOL: context={}'.format(context)

    # PASSES
    elasticsearch_sign()





if __name__ == '__main__':
    lambda_handler(None, None)