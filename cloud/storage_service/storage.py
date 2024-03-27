from minio.error import MinioException
from minio import Minio


class MinioStorage:
    def __init__(self, conf, bucket_name='eadran'):
        self.bucket_name = bucket_name
        self.minioClient = Minio(conf['minio_server'],
                                 access_key=conf['minio_access'],
                                secret_key=conf['minio_secret'])
        self.minioClient.make_bucket(bucket_name, location='us-east-1')

    def get(self, key):
        try:
            data = self.minioClient.get_object(self.bucket_name, key)
            return data.read()
        except MinioException as err:
            print(err)
            return None

    def put(self, key, value):
        try:
            self.minioClient.put_object(self.bucket_name, key, value, len(value))
            return value
        except MinioException as err:
            print(err)
            return None

    def delete(self, key):
        try:
            self.minioClient.remove_object(self.bucket_name, key)
            return key
        except MinioException as err:
            print(err)
            return None