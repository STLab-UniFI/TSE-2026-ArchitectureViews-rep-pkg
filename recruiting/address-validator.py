import pandas as pd
import os
import re

addresspath="./result-recent/collapsed-result.csv"
#addresspath="./addresses-tocheck-test.csv"
resultdir = "./result-recent"

#def iterate_address(doc_path, start_after=None):
#    df = pd.read_csv(doc_path)
#    print("inizio")
#    print(df)
#    start_index = 0
#    
#    if start_after is not None:
#        start_index = df[df.iloc[:, 0] == start_after].index
#        if not start_index.empty:
#            start_index = start_index[0] + 1
#        else:
#            start_index = 0
#    
#    for index, row in df.iloc[start_index:].drop_duplicates(subset=['col1']).iterrows():
#        yield row

def iterate_address(doc_path, start_after=None):
    df = pd.read_csv(doc_path)
    start_index = 0
    
    if start_after is not None:
        start_index = df[df.iloc[:, 0] == start_after].index
        if not start_index.empty:
            start_index = start_index[0] + 1
        else:
            start_index = 0
    
#    for address in df.iloc[start_index:, 0].drop_duplicates():
#        yield address
    for index, row in df.iloc[start_index:].drop_duplicates().iterrows():
        yield row
        

def convert_email(text_email):
    real_email = re.sub(r'\bat\b', '@', text_email)
    real_email = re.sub(r'\bdot\b', '.', real_email)
    real_email = real_email.replace(" ", "")
    return real_email

# Filtrare le email valide
def is_valid_email(email):
    email_regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return re.match(email_regex, email) is not None


restart_from = None
if restart_from is None:
    verified_mails = pd.DataFrame(columns=['Email', 'Name', 'Repository'])
    verified_mails.to_csv(os.path.join(resultdir, 'verified.csv'), index=False)

for row in iterate_address(addresspath):
    address_original = row[0]
    converted_address = convert_email(row['Email'])
    if is_valid_email(converted_address):
        row['Email'] = converted_address
        #verified_mails = pd.concat([verified_mails, pd.DataFrame([row])], ignore_index=True)
        #verified_mails.to_csv(os.path.join(resultdir, 'verified.csv'), mode='a', header=False, index=False)
        pd.DataFrame([row]).to_csv(os.path.join(resultdir, 'verified.csv'), mode='a', header=False, index=False)


print("fine")