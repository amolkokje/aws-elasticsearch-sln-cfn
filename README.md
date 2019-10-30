# aws-elasticsearch-sln-cfn
Cloudformation templates and code to deploy secure AWS Elasticsearch solution




## RULES FOR JSON DATA DOCUMENT:
- A JSON doc should only have all documents going to the same "index", and same "object_key"
    - If you need to send to the same index, but a different object key, then create a new document
- JSON doc file name should have format: IndexName_ObjectKey_TestSuite_TimeStamp.json
    - This is used to decode the metadata information in lambda function triggered on object remove/delete from S3. This is because lambda will be able to get the object name but will not be able to read the object on delete. So the Lambda code can use this info to search the data in ES using Index, Key, to get the IDs, and then delete them.
- Each doc in the file should also have the ‘index’ and ‘object_key’ specified
    - This metadata info will go with the indexed data, and can be used for searching the data, mainly for delete operations.
- Relevant Elasticsearch Rules:
    - Index name must be lowercase
    - Always convert all int values to float in the JSON KPI dict. E.g. 20 should be 20.0