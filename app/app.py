import requests
import os
import sys
from dotenv import load_dotenv

# Parameters
load_dotenv()
fsi_url = os.getenv("FSI_URL")
fsi_api_key = os.getenv("FSI_API_KEY")
fsi_api_secret = os.getenv("FSI_API_SECRET")
fsi_api_code = ''
fsi_api_token = False
fsi_api_refresh_token = ''
fsi_api_token_expiry = 0
edumate_client_id = os.getenv('EDUMATE_CLIENT_ID')
edumate_client_secret = os.getenv('EDUMATE_CLIENT_SECRET')
edumate_url = os.getenv('EDUMATE_URL')
edumate_auth_url = os.getenv('EDUMATE_AUTH_URL')
edumate_access_token = False
edumate_access_token_expiry = 0
edumate_access_refresh_token = ''

# Functions
def get_edumate_token(edumate_session):
    """
    Authenticate and authorise to the Edumate API
    """
    data = {
        "grant_type": "client_credentials",
        "client_id": edumate_client_id,
        "client_secret": edumate_client_secret,
        "refresh_token": '1'
    }
    try:
        response = edumate_session.post(edumate_auth_url, data=data).json()
        if not response['success']:
            raise Exception(response['data'])
        # Update the global variables
        global edumate_access_token
        global edumate_access_token_expiry
        global edumate_access_refresh_token
        edumate_access_token = response['data']['access_token']
        edumate_access_token_expiry = response['data']['expires_in']
        edumate_access_refresh_token = response['data']['refresh_token']

    except Exception as err:
        print(f"Failed to authorise to Edumate: {err}")

def get_edumate_contacts(edumate_session):
    """
    Get a current list of contacts and their details from Edumate
    """
    print('Getting Edumate contacts.', end="")
    headers = {
        'Authorization': f'Bearer {edumate_access_token}'
    }
    all_contacts = []
    contact_types = ['staff', 'student']

    try:
        for contact_type in contact_types:
            url = str('')
            if contact_type == 'staff':
                # Use the contacts endpoint for staff to include casuals
                url = edumate_url + '/contacts/contacts/current?contactType=staff'
            elif contact_type == 'student':
                # Use the lms endpoint for students to include the classgrade field
                url = edumate_url + '/lms/students'
            while url:
                response = edumate_session.get(url, headers=headers).json()
                if not response['success']:
                    raise Exception(response['data'])
                
                # Extend the list of all items with the data from the current page
                all_contacts.extend(response['data'])

                # Pagination
                if 'next' in response['pagination']:
                    url = response['pagination']['next']
                    # Print simple loading progress
                    print('.', end="")
                else:
                    url = False
        return all_contacts

    except Exception as err:
        print(f"Failed to get contacts from Edumate: {err}")
        sys.exit(1)

def get_fsi_code(fsi_session):
    """
    Initialise the calls by getting the API code
    """
    data = {
        "action": "get_code",
        "apikey": fsi_api_key
    }
    try:
        response = fsi_session.post(fsi_url, data=data).json()
        return response['code']
    except Exception as err:
        print(f"Failed to get API code: {err}")
        return False

def get_fsi_token(fsi_session):
    """
    Get the token which is used to authenticate API calls
    """
    global fsi_api_code
    fsi_api_code = get_fsi_code(fsi_session)
    data = {
        "action": "get_token",
        "code": fsi_api_code,
        "apisecret": fsi_api_secret
    }
    try:
        response = fsi_session.post(fsi_url, data=data).json()
        global fsi_api_token
        global fsi_api_refresh_token
        global fsi_api_token_expiry
        fsi_api_refresh_token = response['renewtoken']
        fsi_api_token = response['token']
        fsi_api_token_expiry = response['expire']
    except Exception as err:
        print(f"Failed to get API code: {err}")
        return False

def get_fsi_patron(fsi_session, email):
    """
    Get a FSI patron by email address
    """
    data = {
        "action": "get_patron",
        "token": fsi_api_token,
        "keyfield": "email",
        "keyvalue": email
    }
    try:
        response = fsi_session.post(fsi_url, data=data).json()
        if not response['result']:
            raise Exception(response['msg'])
        print(response)
    except Exception as err:
        print(f"Failed to post FSI patron: {err}")
        return False

def post_fsi_patron(fsi_session, patron):
    """
    Update or create a FSI patron
    """
    data = {
        "action": "set_patron",
        "token": fsi_api_token,
        "keyfield": "username",
        "allownew": True,
        "index": 1
    }
    # Add the patron data to the POST request
    combined_data = data.copy()
    combined_data.update(patron)
    try:
        response = fsi_session.post(fsi_url, data=combined_data).json()
        if not response['result']:
            raise Exception(response['msg'])
        print(f'Post success: {response['item'][0]['username']}')
    except Exception as err:
        print(f"Failed to post FSI patron: {err}")
        return False

def search_fsi_patrons(fsi_session, search_word, search_field):
    """
    Search for FSI patrons. 
    Pagination not yet implemented. Function not in use.
    """
    all_patrons = []
    page_number = 1
    page_count = 200
    data = {
        "action": "search_patron",
        "token": fsi_api_token,
        "pagenumber": page_number,
        "pagecount": page_count,
        # Simulate the array object post in JSON format (FSI Support Ticket)
        "keyword[0][tokens][0][key]":"findform_key",
        "keyword[0][tokens][0][value]":search_field,
        "keyword[0][tokens][1][key]":"findform_value",
        "keyword[0][tokens][1][value]":search_word,
        "keyword[0][tokens][2][key]":"findform_condition",
        "keyword[0][tokens][2][value]":"AND",
        "keyword[0][tokens][3][key]":"findform_method",
        "keyword[0][tokens][3][value]":"CONTAIN",
        "keyword[0][tokens][4][key]":"findform_type",
        "keyword[0][tokens][4][value]":"STRING"
    }
    try:
        response = fsi_session.post(fsi_url, data=data).json()
        if not response['result']:
            raise Exception(response['msg'])
    except Exception as err:
        print(f"Failed to search FSI: {err}")

def get_fsi_patrons(fsi_session):
    """
    Get all FSI patrons using the search endpoint
    """
    print('Getting FSI patrons.', end="")
    all_patrons = []
    search_words = [ 'Administrator', 'Staff', 'Student' ]
    for search_word in search_words:
        more_results_on_next_page = True
        page_number = 1
        page_count = 50
        while more_results_on_next_page:
            data = {
                "action": "search_patron",
                "token": fsi_api_token,
                "pagenumber": page_number,
                "pagecount": page_count,
                # Simulate the array object post in JSON format (FSI Support Ticket)
                "keyword[0][tokens][0][key]":"findform_key",
                "keyword[0][tokens][0][value]":"ALL",
                "keyword[0][tokens][1][key]":"findform_value",
                "keyword[0][tokens][1][value]":search_word,
                "keyword[0][tokens][2][key]":"findform_condition",
                "keyword[0][tokens][2][value]":"AND",
                "keyword[0][tokens][3][key]":"findform_method",
                "keyword[0][tokens][3][value]":"CONTAIN",
                "keyword[0][tokens][4][key]":"findform_type",
                "keyword[0][tokens][4][value]":"STRING"
            }
            try:
                response = fsi_session.post(fsi_url, data=data).json()
                if response['result']:
                    if len(response['item']) > 0:
                        # Extend the list of all items with the data from the current page
                        all_patrons.extend(response['item'])
                        # Increment pagination
                        page_number = page_number + 1
                        # Print simple loading progress
                        print('.', end="")
                    else:
                        more_results_on_next_page = False
                else:
                    raise Exception(response['msg'])
            except Exception as err:
                print(f"Failed to search FSI: {err}")
                sys.exit(1)
            # Improve error handling to prevent infinite errors. Exit on 'Invalidate session token'.
            # 2025-04-07T03:31:25.966+08:00
            # Getting Edumate contacts................
            # 2025-04-07T03:31:25.966+08:00
            # Edumate contacts found: 1572
            # 2025-04-07T03:31:25.996+08:00
            # Getting FSI patrons.Failed to search FSI: Invalidate session token.
            # 2025-04-07T03:31:26.020+08:00
            # Failed to search FSI: Invalidate session token.
            # 2025-04-07T03:31:26.045+08:00
            # Failed to search FSI: Invalidate session token.
            # 2025-04-07T03:31:26.069+08:00
            # Failed to search FSI: Invalidate session token.
            # 2025-04-07T03:31:26.094+08:00
            # Failed to search FSI: Invalidate session token.

    return all_patrons

def sync_to_fsi(fsi_session, fsi_patrons, edumate_contacts):
    """
    Sync Edumate contacts to FSI
    """
    patrons_to_create = []
    patrons_to_update = []

    # Check for contacts that don't exist as patrons
    for contact in edumate_contacts:

        # Check whether the contact has come from 'contacts' or 'lms' endpoint and normalise
        contact_details = {}
        if 'student_number' in contact:
            contact_details = {
                "student_number": contact['student_number'],
                "email_address": contact['email_address'],
                "firstname": contact['first_name'],
                "surname": contact['surname'],
                "form_short_name": contact['form_short_name']
            }
        else:
            staff_number = ''
            for ref in contact['general_info']['contact_reference']:
                if ref.get('contact_type') == 'staff':
                    staff_number = ref['staff_number']
            contact_details = {
                "staff_number": staff_number,
                "email_address": contact['general_info']['email_address'],
                "firstname": contact['general_info']['firstname'],
                "surname": contact['general_info']['surname']
            }

        patron_found = False
        for patron in fsi_patrons:            
            # Ignore Edumate contacts with no email address
            if contact_details['email_address'] is None:
                patron_found = True
                break
            # Ignore Edumate contacts with no Kambala domain
            if not 'kambala.nsw.edu.au' in contact_details['email_address']:
                patron_found = True
                break
            if contact_details['email_address'].lower() == patron['username'].lower():
                patron_found = True
                # Check for any updates required to the patron (firstname, surname, classgrade)
                if not contact_details['firstname'] == patron['firstname']:
                    patrons_to_update.append(contact_details)
                    break
                if not contact_details['surname'] == patron['surname']:
                    patrons_to_update.append(contact_details)
                    break
                if 'student_number' in contact_details:
                    clean_classgrade = patron['classgrade'].rstrip('|')
                    clean_classgrade = clean_classgrade.rstrip(' ')
                    if not contact_details['form_short_name'].rstrip('IB') == clean_classgrade:
                        patrons_to_update.append(contact_details)
                break
        if not patron_found:
            patrons_to_create.append(contact_details)
    print(f'Number of patrons to create: {len(patrons_to_create)}')
    print(f'Number of patrons to update: {len(patrons_to_update)}')

    patrons = patrons_to_create + patrons_to_update
    for contact in patrons:
        email = ''
        role = ''
        classgrade = ''
        external_id = ''
        if 'student_number' in contact:
            email = contact['email_address']
            role = 'Student'
            classgrade = contact['form_short_name'].rstrip('IB') # Remove 'IB' from year level
            external_id = contact['student_number']
        else:
            email = contact['email_address']
            role = 'Teacher'
            classgrade = 'Staff'
            external_id = contact['staff_number']
        patron = {
            "barcode": email,
            "username": email,
            "externalid": external_id,
            "firstname": contact['firstname'],
            "surname":contact['surname'],
            "email": email,
            "classgrade": classgrade,
            "room": role,
            "role": role
        }
        post_fsi_patron(fsi_session, patron)


##### Main Program #####
# Create sessions and authenticate
edumate_session = requests.Session()
get_edumate_token(edumate_session)
fsi_session = requests.Session()
get_fsi_token(fsi_session)
if not fsi_api_token or not edumate_access_token:
    print('Error authenticating to API endpoints')
    sys.exit(1)

# Get all current students and staff contacts from Edumate
edumate_contacts = get_edumate_contacts(edumate_session)
print(f'\nEdumate contacts found: {len(edumate_contacts)}')

# Get all patrons from FSI
fsi_patrons = get_fsi_patrons(fsi_session)
print(f'\nFSI patrons found: {len(fsi_patrons)}')

# Sync Edumate contacts to FSI
sync_to_fsi(fsi_session, fsi_patrons, edumate_contacts)
