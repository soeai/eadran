# from minio.error import ResponseError
# from minio import Minio
#
# class MinioStorage:
#     def __init__(self, conf, bucket_name='eadran'):
#         self.bucket_name = bucket_name
#         self.minioClient = Minio(conf['MINIO_SERVER'], access_key=conf['MINIO_ACCESS', secret_key=conf['MINIO_SECRET'], secure=False)
#         self.minioClient.make_bucket('eadran', location='us-east-1')
#
#     def get(self, key):
#         try:
#             data = self.minioClient.get_object(self.bucket_name, key)
#             return data.read()
#         except ResponseError as err:
#             print(err)
#             return None
#
#     def put(self, key, value):
#         try:
#             self.minioClient.put_object(self.bucket_name, key, value, len(value))
#             return value
#         except ResponseError as err:
#             print(err)
#             return None
#
#     def delete(self, key):
#         try:
#             self.minioClient.remove_object(self.bucket_name, key)
#             return key
#         except ResponseError as err:
#             print(err)
#             return None