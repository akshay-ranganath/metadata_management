from ratelimit import limits, RateLimitException, sleep_and_retry
from backoff import on_exception, expo
from concurrent.futures import ThreadPoolExecutor as PoolExecutor, thread
import logging
import cloudinary.api
import cloudinary.uploader
import csv
import argparse


################################ Script Setup ######################################
# modify the values below for processing your account, if needed
# this script processes either images or videos in one run
####################################################################################
RESOURCE_TYPE='image'
#RESOURCE_TYPE='video'
TYPE = 'upload'
####################### Script Setup Ends ##############################
########################################################################

  
    
# default rate limit is 5,000/hour = 83.33 calls/min
ONE_MINUTE = 60
MAX_CALLS_PER_MINUTE = 83

@sleep_and_retry
@limits(calls=MAX_CALLS_PER_MINUTE, period=ONE_MINUTE)
@sleep_and_retry
@limits(calls=MAX_CALLS_PER_MINUTE, period=ONE_MINUTE)
def list_resources(folder, report_file, next_cursor=None):    
    '''
        Function that makes the Admin API Resource call (https://cloudinary.com/documentation/admin_api#get_resources)
        Fetches a max of 500 resources in one operation

        Using a concurrency of 50 threads, updates the resources
        
        Admin API is rate limited to 5,000 calls/hour. Using a library, we are forcing the rate limits.
    '''    
    total_resources = 0    
    # initialize a pool of threads to do our updating job later
    with open(report_file,'w') as f:
        writer = csv.writer(f)
        writer.writerow(['Public ID', 'Type', 'Resource Type', 'Color Code', 'Display Position', 'Product Id'])
        
        with PoolExecutor(max_workers=50) as executor:
            while(1):                                            

                # make an Admin API call to get the list of resources
                if folder==None:
                    resp = cloudinary.api.resources(
                        type = TYPE,
                        resource_type = RESOURCE_TYPE,
                        max_results = 500,
                        context=True,
                        metadata=True,
                        next_cursor = next_cursor                    
                    )
                else:
                    resp = cloudinary.api.resources(
                        type = TYPE,
                        resource_type = RESOURCE_TYPE,
                        prefix = folder,
                        max_results = 500,
                        context=True,
                        metadata=True,
                        next_cursor = next_cursor                    
                    )

                
                # loop and pull the public ids
                for _ in resp['resources']:   
                    row_data = []         
                    row_data.append(_['public_id'])
                    logging.debug(_['public_id'])
                    row_data.append(_['type'])
                    row_data.append(_['resource_type'])
                    
                    if 'metadata' in _:
                        metadata = _['metadata']
                        row_data.append(metadata['color_code'] if 'color_code' in metadata else '')
                        row_data.append(metadata['display_position'] if 'display_position' in metadata else '')
                        row_data.append(metadata['product_id'] if 'product_id' in metadata else '')
                        writer.writerow(row_data)
                
                total_resources += len(resp['resources'])    
                logging.info(f'Processed {total_resources} resources')                

                # finally check if we have more resources - if so, use pagination
                # and fetch the next set and repeat. Else exit.
                if 'next_cursor' not in resp or resp['next_cursor']==None:
                    break                             


if __name__=="__main__":

    # Allow 2 optional parameters to set the log file and the report file names.
    parser = argparse.ArgumentParser(
        description="Script to extract metadata and generate report ",
        usage="python3 generate_metadata.py --folder <<folder to analyze>> --log <<log file name>> --report <<report file name>>"
    )

    parser.add_argument(
        '--report', 
        default="report.csv", 
        required=False, 
        help="File name for report. default = \"report.csv\""
    )
    parser.add_argument(
        '--log', 
        default="log.csv", 
        required=False, 
        help="File name for report. default = \"report.csv\""
    )
    
    parser.add_argument(
        '--folder', 
        default=None, 
        required=False, 
        help="Update metadata for objects in a fixed folder. Default=None (ie, process all objects in the account)"
    )

    args = parser.parse_args()
    # logging setup
    # we will be writing to a file based on --report parameeter to capture the output of this operation
    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)s,%(message)s',
                        filename=args.log,
                        filemode='w')
    logging.getLogger("urllib3").setLevel(logging.CRITICAL)
    logging.getLogger("cloudinary").setLevel(logging.CRITICAL)
    logging.getLogger("backoff").setLevel(logging.CRITICAL)
    logging.getLogger("boto3").setLevel(logging.CRITICAL)


    logging.info("Starting metadata extract...")
    logging.info("Report will be written in CSV format to a file named \"report.csv\"")
    metadata_definitions = list_resources(args.folder, args.report)
    logging.info("Processing is now complete.")