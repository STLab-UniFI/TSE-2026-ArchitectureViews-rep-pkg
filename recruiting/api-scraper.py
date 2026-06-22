import os
import subprocess
from urllib.parse import urljoin
import pandas as pd
import requests
import time
from datetime import datetime, timedelta, timezone


resultdir = "./recent-contrib"
os.makedirs(resultdir, exist_ok=True)
workdir = "./temp_repos"
os.makedirs(workdir, exist_ok=True)
exec_time = datetime.now()


def read_string_from_file(file_path):
    with open(file_path, 'r') as file:
        string = file.read().strip()
    return string

token = read_string_from_file('ANONYMIZED')

GITHUB_BASEURL = 'https://github.com'

def next_repo(doc_path, start_after=None):
    df = pd.read_csv(doc_path)
    start_index = 0
    
    if start_after is not None:
        start_index = df[df.iloc[:, 0] == start_after].index
        if not start_index.empty:
            start_index = start_index[0] + 1
        else:
            start_index = 0
    
    for repo in df.iloc[start_index:, 0].drop_duplicates():
        yield repo

#def next_repo(doc_path):
#    df = pd.read_csv(doc_path)
#    for repo in df.iloc[:, 0].drop_duplicates():
#        yield repo
        
def get_contributors_from_api_OLD(repo_id):
    repo_name = repo_id.split("/")[-1].replace(".git", "")
    owner = repo_id.split("/")[0]
    
    contributors_df = pd.DataFrame(columns=['Name', 'Email', 'Repository'])

    url = f"https://api.github.com/repos/{owner}/{repo_name}/contributors"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)


    if response.status_code == 200:
        contributors = response.json()
        for contributor in contributors:
            username = contributor['login']
            user_url = f"https://api.github.com/users/{username}"
            user_response = requests.get(user_url, headers=headers)
            if user_response.status_code == 200:
                mail = user_response.json()['email']
                if mail is not None:
                    print(mail)
                    #new_line = {username, mail, urljoin(owner, repo_name)}
                    new_line = {'Name': username, 'Email': mail, 'Repository': repo_id}
                    #contributors_df= contributors_df.append(new_line, ignore_index=True)
                    contributors_df = pd.concat([contributors_df, pd.DataFrame([new_line])], ignore_index=True)
                    #contributors_df = pd.concat([contributors_df, new_line], ignore_index=True)
            else:
                print(f"Errore: {response.status_code} - {response.text}")
                if '403' in response.status_code and 'API rate limit exceeded' in response.text:
                    print('sleeping 1 hour')
                    time.sleep(3600)
                
    else:
        print(f"Errore: {response.status_code} - {response.text}")
        if '403' in response.status_code and 'API rate limit exceeded' in response.text:
            print('sleeping 1 hour')
            time.sleep(3600)
            return get_contributors_from_api(repo_id)
    return contributors_df


def get_contributors_from_api(repo_id):
    repo_name = repo_id.split("/")[-1].replace(".git", "")
    owner = repo_id.split("/")[0]
    
    contributors_df = pd.DataFrame(columns=['Name', 'Email', 'Repository'])

    url = f"https://api.github.com/repos/{owner}/{repo_name}/contributors"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)


    if response.status_code == 200:
        contributors = response.json()
        for contributor in contributors:
            username = contributor['login']
            new_line = get_contributor_mail(username, headers)    
            if new_line is not None:
                new_line['Repository'] = repo_id
                contributors_df = pd.concat([contributors_df, pd.DataFrame([new_line])], ignore_index=True)
    else:
        print(f"Errore: {response.status_code} - {response.text}")
        if 'API rate limit exceeded' in response.text:
            print('sleeping until the next hour')
            time.sleep(240)
            return get_contributors_from_api(repo_id)
    return contributors_df

def get_recent_contributors_from_api(repo_id):
    repo_name = repo_id.split("/")[-1].replace(".git", "")
    owner = repo_id.split("/")[0]
    
    contributors_df = pd.DataFrame(columns=['Name', 'Email', 'Repository'])

    url = f"https://api.github.com/repos/{owner}/{repo_name}/contributors"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        contributors = response.json()
        for contributor in contributors:
            username = contributor['login']
            if is_recent(username, repo_name, owner):
                new_line = get_contributor_mail(username, headers)    
                if new_line is not None:
                    new_line['Repository'] = repo_id
                    contributors_df = pd.concat([contributors_df, pd.DataFrame([new_line])], ignore_index=True)
            else:
                print(f"contributor {username} in {owner}/{repo_name} has not been active for more than one year")
    else:
        print(f"Errore: {response.status_code} - {response.text}")
        if 'API rate limit exceeded' in response.text:
            print('sleeping until the next hour')
            time.sleep(240)
            return get_contributors_from_api(repo_id)
    return contributors_df

def is_recent(contributor_username, repo, repo_owner):
    last_year = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat() + "Z"

    if not contributor_username:
        return false
    commits_url = f"https://api.github.com/repos/{repo_owner}/{repo}/commits"
    params = {
        "author": contributor_username,
        #"util": last_year,
        "since": last_year,
        "per_page": 1
    }
    headers = {"Authorization": f"Bearer {token}"}
    commits_response = requests.get(commits_url, headers=headers, params=params)
    if commits_response.status_code == 200 and commits_response.json():
        return True
    else:
        return False
    

def get_contributor_mail(username, headers):
    user_url = f"https://api.github.com/users/{username}"
    user_response = requests.get(user_url, headers=headers)
    if user_response.status_code == 200:
        mail = user_response.json()['email']
        if mail is not None:
            print(mail)
            return {'Name': username, 'Email': mail}
    else:
        print(f"Errore: {user_response.status_code} - {user_response.text}")
        if 'API rate limit exceeded' in user_response.text:
            print('sleeping a bit')
            time.sleep(240)
            return get_contributor_mail(username,headers)
        else:
            return None

def get_wait_time():
    current_time = datetime.now()

    elapsed_time = current_time - start_time
    elapsed_hours = elapsed_time.total_seconds() / 3600
    
    next_hour = (start_time + timedelta(hours=(elapsed_hours // 1) + 1)).replace(minute=0, second=0, microsecond=0)
    time_to_next_hour = next_hour - current_time
    
    wait_time = time_to_next_hour + timedelta(minutes=5)
    
    start_time = datetime.now()
    elapsed_time = current_time - start_time
    elapsed_hours = elapsed_time.total_seconds() / 3600
    
    return wait_time.total_seconds
    


def collapse_df(dataframe):
    return dataframe.groupby('Email').agg({
    'Name': 'first',
    'Repository': lambda x: list(x)
}).reset_index()


repo_list_path = "ECSA24-dataset.csv"
#repo_list_path = "list-test"

restart_from = None

if restart_from is None:
    contributors = pd.DataFrame(columns=['Name', 'Email', 'Repository'])
    contributors.to_csv(os.path.join(resultdir, 'result-recent.csv'), index=False)
for repo_id in next_repo(repo_list_path, restart_from):
    repo_contributors = get_recent_contributors_from_api(repo_id)
    repo_contributors.to_csv(os.path.join(resultdir, 'result-recent.csv'), mode='a', header=False, index=False)
    #contributors = pd.concat([contributors, repo_contributors], ignore_index=True)
    #contributors.to_csv(os.path.join(resultdir, 'result.csv'), index=False)
    

#contributors.to_csv(os.path.join(resultdir, 'result.csv'), index=False)

contributors_to_collapse = pd.read_csv(os.path.join(resultdir, 'result-recent.csv'))
collapsed_contributors = collapse_df(contributors_to_collapse)
collapsed_contributors.to_csv(os.path.join(resultdir, 'collapsed-result.csv'), index=False)

        



