## Helper Scripts for Metadata Management

This package has 2 scripts:

* `update_metadata.py`
* `generate_report.py`

The first script helps in reading the file names and adding metadata based on it. The second script iterates over the existing resources and creates a report of the file name and corresponding metadata. 

### Installation

#### Python Version
The code is written for Python3. Please ensure you have the python 3.x. To check the version, please try:

    python --version

OR 

    python3 --version

If you need to use `python3` as the command, please ensure you have `pip` installed for `python3`. Typically, this command will be available as `pip3`. On Mac, you can install these using [HomeBrew](https://brew.sh/) as:

    brew install python@3
    brew install pip3

Ensure you have the latest version of `pip` by running this command:

    pip3 install --upgrade pip

#### Libraries

The scripts rely on 3 main libraries:
* `cloudinary`: This is the [Python SDK](https://cloudinary.com/documentation/django_integration) from Cloudinary for accessing our APIs.
* `backoff` and `ratelimit`: These libraries are used to enforce rate limiting so that you don't exceed the [usage limits](https://cloudinary.com/documentation/admin_api#usage_limits).

To install the libraries, please run the following.

    pip3 install -r requirements.txt

### Script Execution

#### Updating Metadata

The script `update_metadata.py` can update metadata by doing the reading the file name (aka public id in Cloudinary language). The assumption is that the file name will have the following format: NNN_col_pos where:

* NNN: A sequence of numbers corresponding to Product ID.
* col: A string representing the color
* pos: A string of 2-3 characters that maps to the display order for the image

By reading the name, this script updates the object. It sets 3 [Structured Metadata](https://cloudinary.com/documentation/cloudinary_glossary#structured_metadata) fields and replicate the same name=value pair as [Contextual Metadata](https://cloudinary.com/documentation/cloudinary_glossary#contextual_metadata) fields.

The script can take an optional parameter to restrict the analysis to a single folder (and it's sub-folders). The usage is as follows:

```
python3 update_metadata.py --folder <<folder to analyze>> --log <<log file name>>

where,
--folder FOLDER  Update metadata for objects in a fixed folder. Default=None (ie, process all objects in the account)
--log LOG        File name for report. default = "report.csv"
```

Both `--folder` and `--log` are optional parameters. Omitting will result in script analyzing ALL images and generating a log file named `log.csv`.

#### Generating Report

The script `generate_report.py` can be used to report on the metadata associated with the objects in your account. It looks at 3 specific metadata fields - Product ID, Color Code and Display Position. The report generated will have the following format:

| Public ID                                                          | Type   | Resource Type | Color Code | Display Position | Product Id |
| ------------------------------------------------------------------ | ------ | ------------- | ---------- | ---------------- | ---------- |
| images/111\_green\_l                                               | upload | image         | green      | 15               | 111        |
| images/Black-Crocs-On-The-Clock-Work-Slip-On-\_205073\_001\_IS.jpg | upload | image         | blue       | 2                | 205073     |

Here's the usage:

```
python3 generate_metadata.py --folder <<folder to analyze>> --log <<log file name>> --report <<report file name>>

where,
--report REPORT  File name for report. default = "report.csv"
--log LOG        File name for report. default = "report.csv"
--folder FOLDER  Update metadata for objects in a fixed folder. Default=None (ie, process all objects in the account)
```

All parameters are optional. Omitting the parameters will result in the report being generated for ALL assets in the account as `report.csv` and log files created as `log.csv`.
