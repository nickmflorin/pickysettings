from bs4 import BeautifulSoup
import requests
import os


TAB = "    "


def write_list_to_python_file(data, filename, listname, wrapper='"%s"'):

    if '.py' not in filename:
        filename = "%s.%s" % (filename, "py")

    working_dir = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(working_dir, filename)
    with open(filename, 'w+') as file:
        file.write("%s = [\n" % listname)
        for element in data:
            wrapped = "%s," % (wrapper % element)
            file.write("%s%s\n" % (TAB, wrapped))
        file.write("]\n")


def scrape():
    URL = "https://www.webopedia.com/quick_ref/fileextensionsfull.asp"
    resp = requests.get(URL)
    soup = BeautifulSoup(resp.content)

    extensions = []
    table = soup.find_all('table')[1]
    rows = table.find_all('tr')[1:]
    for row in rows:
        ext = row.find_all('td')[0].text
        if ext:
            extensions.append(ext)

    write_list_to_python_file(extensions, "extensions", "EXTENSIONS")
