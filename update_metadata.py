from ratelimit import limits, RateLimitException, sleep_and_retry
from backoff import on_exception, expo
from concurrent.futures import ThreadPoolExecutor as PoolExecutor, thread
import logging
import cloudinary.api
import cloudinary.uploader
import re
import argparse

################################ Script Setup ######################################
# modify the values below for processing your account, if needed
# this script processes either images or videos in one run
####################################################################################
RESOURCE_TYPE='image'
#RESOURCE_TYPE='video'
TYPE = 'upload'
PATTERN = re.compile(r'^(?:[a-zA-Z]{2,3})?(\d+)_([^\_]+)\_([^\_]+)')
POSITION = {
        'a': 1,
        'b': 2,
        'da': 3,
        'db': 4,
        'dc': 5,
        'ea': 6,
        'eb': 7,
        'eda': 8,
        'edb': 9,
        'eea': 10,
        'eeb': 11,
        'eec': 12,
        'el': 13,
        'esw': 14,
        'l': 15,
        'sw': 16
    }
####################### Script Setup Ends ##############################
########################################################################


def extract_metadata(public_id):
    '''
        Helper function that extracts based on PATTERN
        Currently, it assumes 3 parameters:
        1. Product ID
        2. Color/Colour Code
        3. Display Position

        Returns a formatted string that can be directly used in the API call
    '''    
    result = ''

    matches = PATTERN.search(public_id)

    # only if we have the right components in the file name, proceed
    if matches!=None and len(matches.groups())==3:
        result = f'product_id={matches.group(1)}|color_code={matches.group(2)}'
        display_position_code = matches.group(3)        
        
        # ensure that the lookup for position works, else log the error
        if display_position_code in POSITION:
            result += f'|display_position={POSITION[display_position_code]}'
        else:
            logging.error(f'{public_id},{display_position_code},display not found')
    return result
        


def update_metadata(public_id):
    '''
        Update one resource at a time by adding the metadata and context values
        The function uses "explicit" Upload API
        Details: https://cloudinary.com/documentation/image_upload_api_reference#explicit
    '''
    metadata = extract_metadata(public_id)
    
    # update the resource only if we have some metadata    
    if metadata != '':
        try:
            resp = cloudinary.uploader.explicit(
                public_id,
                type=TYPE,
                resource_type=RESOURCE_TYPE,
                metadata = metadata,
                context = metadata
            )
            logging.debug(f'{public_id},{metadata}')
        except Exception as e:
            logging.error(f'{public_id},{e},{metadata}')
    
    
# default rate limit is 5,000/hour = 83.33 calls/min
ONE_MINUTE = 60
MAX_CALLS_PER_MINUTE = 83

@sleep_and_retry
@limits(calls=MAX_CALLS_PER_MINUTE, period=ONE_MINUTE)
def list_resources(folder, next_cursor=None):    
    '''
        Function that makes the Admin API Resource call (https://cloudinary.com/documentation/admin_api#get_resources)
        Fetches a max of 500 resources in one operation

        Using a concurrency of 50 threads, updates the resources
        
        Admin API is rate limited to 5,000 calls/hour. Using a library, we are forcing the rate limits.
    '''
    total_resources = 0
    # initialize a pool of threads to do our updating job later
    with PoolExecutor(max_workers=50) as executor:
        while(1):
            resources = []
            try:
                # make an Admin API call to get the list of resources across all folders
                if folder==None:
                    resp = cloudinary.api.resources(
                        type = TYPE,
                        resource_type = RESOURCE_TYPE,
                        max_results = 500,
                        next_cursor = next_cursor                    
                    )
                else:
                    # make an Admin API call to get the list of resources from a specific folder
                    resp = cloudinary.api.resources(
                        type = TYPE,
                        resource_type = RESOURCE_TYPE,
                        prefix = folder,
                        max_results = 500,                        
                        next_cursor = next_cursor                    
                    )
                
                # loop and pull the public ids
                for _ in resp['resources']:            
                    resources.append(_['public_id'])
                
                total_resources += len(resp['resources'])
                # now update the metadata for these resources
                for _ in executor.map(update_metadata, resources):
                    pass

                # finally check if we have more resources - if so, use pagination
                # and fetch the next set and repeat. Else exit.
                if 'next_cursor' not in resp or resp['next_cursor']==None:
                    break                             
            except Exception as e:
                logging.error(f'Unable to fetch resources: {e} objects.')
    logging.info(f'Processed {total_resources}')
    

if __name__=="__main__":
    # Allow 2 optional parameters to set the log file and the report file names.
    parser = argparse.ArgumentParser(
        description="Script to parse file name and add metadata.",
        usage="python3 update_metadata.py --folder <<folder to analyze>> --log <<log file name>>"
        )
    
    parser.add_argument(
        '--folder', 
        default=None, 
        required=False, 
        help="Update metadata for objects in a fixed folder. Default=None (ie, process all objects in the account)"
    )

    parser.add_argument(
        '--log', 
        default="log.csv", 
        required=False, 
        help="File name for report. default = \"report.csv\""
    )

    args = parser.parse_args()

    # logging setup
    # we will be writing to a file named 'log.csv' to capture the output of this operation
    logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s,%(message)s',
                    filename=args.log,
                    filemode='w')
    logging.getLogger("urllib3").setLevel(logging.CRITICAL)
    logging.getLogger("cloudinary").setLevel(logging.CRITICAL)
    logging.getLogger("backoff").setLevel(logging.CRITICAL)
    logging.getLogger("boto3").setLevel(logging.CRITICAL)
    
    list_resources(folder = args.folder)    