"""Function to store image size in S3 metadata."""

import struct
import imghdr
import boto3

# Example payload
# {
#     "Records": [
#         {
#             "eventVersion": "2.1",
#             "eventSource": "aws:s3",
#             "awsRegion": "eu-west-1",
#             "eventTime": "2021-12-22T20:21:59.618Z",
#             "eventName": "ObjectCreated:Put",
#             "userIdentity": {
#                 "principalId": "redacted"
#             },
#             "requestParameters": {
#                 "sourceIPAddress": "1.2.3.4"
#             },
#             "responseElements": {
#                 "x-amz-request-id": "0N7JY9NKNQPJ3TW3",
#                 "x-amz-id-2": "tKKKzyxKwRZt32JLWKTpc9d078tAc2tK7bBgafLTSeT+XMpbCth+WRonDC80skSfi340F18GHDnxblZiWUyU3KqwLs0IKhFd"
#             },
#             "s3": {
#                 "s3SchemaVersion": "1.0",
#                 "configurationId": "N2EzOGNjOGItODVjMy00MTRjLThkNzAtMmE1OGYwZGNjYTE5",
#                 "bucket": {
#                     "name": "serverlessintegrationtes-s3eventconstructeventbuc-18iijril97dy2",
#                     "ownerIdentity": {
#                         "principalId": "A2VVHKNJJYJF2V"
#                     },
#                     "arn": "arn:aws:s3:::serverlessintegrationtes-s3eventconstructeventbuc-18iijril97dy2"
#                 },
#                 "object": {
#                     "key": "Slide35.png",
#                     "size": 1210955,
#                     "eTag": "01f44406871a4d8b0d95a06996e105a5",
#                     "sequencer": "0061C388E7818BB7B2"
#                 }
#             }
#         }
#     ]
# }

s3_client = boto3.client("s3")


def event_handler(event, _context):
    """Run the main lambda function."""
    for record in event["Records"]:
        parse_image(record)


def parse_image(record):
    """Download an image from S3 and extract its dimensions."""
    object_key = record["s3"]["object"]["key"]
    bucket_name = record["s3"]["bucket"]["name"]
    s3_event_name = record["eventName"]
    if s3_event_name == "ObjectCreated:Copy":
        print("Not processing copy commands to prevent infinite loops")
        return

    # Copy the file to local disk
    filename = object_key.split("/")[-1]
    local_file_location = f"/tmp/{filename}"
    image_object = s3_client.get_object(Bucket=bucket_name, Key=object_key)
    with open(local_file_location, "wb") as file_loc:
        file_loc.write(image_object["Body"].read())

    # Determine the image dimensions
    try:
        image_width, image_height = get_image_size(local_file_location)
    except Exception as exc:
        raise RuntimeError("Failed to get image dimensions") from exc

    # Copy the object back to its original location, but with metadata
    s3_client.copy_object(
        Key=object_key,
        Bucket=bucket_name,
        ContentType=image_object["ContentType"],
        CopySource={"Bucket": bucket_name, "Key": object_key},
        Metadata={
            "IMAGE_WIDTH": str(image_width),
            "IMAGE_HEIGHT": str(image_height),
        },
        MetadataDirective="REPLACE",
    )


def get_image_size(fname):
    """
    Determine the image type of fhandle and return its size.

    Copied from https://stackoverflow.com/a/20380514/1600866
    """
    with open(fname, "rb") as fhandle:
        head = fhandle.read(24)
        if len(head) != 24:
            raise RuntimeError("Head is not 24 bytes")
        if imghdr.what(fname) == "png":
            check = struct.unpack(">i", head[4:8])[0]
            if check != 0x0D0A1A0A:
                raise RuntimeError("Magic number is not 0x0D0A1A0A")
            width, height = struct.unpack(">ii", head[16:24])
        elif imghdr.what(fname) == "gif":
            width, height = struct.unpack("<HH", head[6:10])
        elif imghdr.what(fname) == "jpeg":
            try:
                fhandle.seek(0)  # Read 0xff next
                size = 2
                ftype = 0
                while not 0xC0 <= ftype <= 0xCF:
                    fhandle.seek(size, 1)
                    byte = fhandle.read(1)
                    while ord(byte) == 0xFF:
                        byte = fhandle.read(1)
                    ftype = ord(byte)
                    size = struct.unpack(">H", fhandle.read(2))[0] - 2
                # We are at a SOFn block
                fhandle.seek(1, 1)  # Skip `precision' byte.
                height, width = struct.unpack(">HH", fhandle.read(4))
            except Exception as exc:  # pylint: disable=broad-except
                raise RuntimeError("Failed to parse jpeg") from exc
        else:
            raise RuntimeError("Unsupported image type")
        return width, height
