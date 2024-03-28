import io

from minio.error import S3Error
from minio import Minio


class MinioStorage:
    def __init__(self, conf, bucket_name='eadran'):
        self.bucket_name = bucket_name
        self.minioClient = Minio(conf['minio_server'],
                                 access_key=conf['minio_access'],
                                secret_key=conf['minio_secret'],
                                 secure=False)
        if not self.minioClient.bucket_exists(bucket_name):
            self.minioClient.make_bucket(bucket_name, location='us-east-1')

    def get(self, key):
        try:
            data = self.minioClient.get_object(self.bucket_name, key)
            return data.read()
        except S3Error as err:
            print(err)
            return None

    def put(self, key, value):
        try:
            self.minioClient.put_object(self.bucket_name, key, io.BytesIO(value), len(value))
            return len(value)
        except S3Error as err:
            print(err)
            return None

    def delete(self, key):
        try:
            self.minioClient.remove_object(self.bucket_name, key)
            return key
        except S3Error as err:
            print(err)
            return None