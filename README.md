# missing-to-unidentified-persons-match

## File/Folder structure:
- DSCI 510 Project.docx - project description
- requirements.txt - all the requirements
- /data/ - static versions of the SQL databases
- /scripts/ - all the python scripts necessary for the project
- /shpfiles/ - geographic files for CA
- /output/ - analytical figures output

The above folder structure must be maintained in order for the project to be run. 

To scrape the full data and run analysis (takes roughly an hour and a half):
python full_analysis.py 

To print a sample of the data and run analysis on static data:
python full_analysis.py --static

A separate script is included to run the finder tool detailed in the project description. This tool queries the unidentified persons database to find matches for a given missing person. The tool will output a listing of all potential matches and a figure showing images of the missing person next to images of potential matches. To run the finder tool, you will need the name of a missing person of interest and then you can run:
python finder.py 'name'

finder.py takes the following arguments in order:
- name of missing person - required
- distance in miles - default to 50
- age years buffer - default to 10 years
- height buffer - default to 20 pounds
- weight buffer - default to 6 inches

Ex using defaults:
python finder.py 'Anita Qvist'

Ex with additional parameters:
python finder.py 'Anita Qvist' 100 0 0 0

