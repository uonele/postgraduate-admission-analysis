import urllib.request
from html.parser import HTMLParser

class SimpleHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.in_table = False
        self.in_tr = False
        self.in_td = False
        self.current_table = []
        self.current_row = []
        self.current_cell = ""

    def handle_starttag(self, tag, attrs):
        if tag in ["table", "tbody"]:
            self.in_table = True
            if tag == "table":
                self.current_table = []
        elif tag == "tr" and self.in_table:
            self.in_tr = True
            self.current_row = []
        elif tag in ("td", "th") and self.in_tr:
            self.in_td = True
            self.current_cell = ""

    def handle_endtag(self, tag):
        if tag == "table":
            self.in_table = False
            self.tables.append(self.current_table)
        elif tag == "tr" and self.in_table:
            self.in_tr = False
            if self.current_row:
                self.current_table.append(self.current_row)
        elif tag in ("td", "th") and self.in_tr:
            self.in_td = False
            self.current_row.append(self.current_cell.strip())

    def handle_data(self, data):
        if self.in_td:
            self.current_cell += data.replace('\n', '').strip()

def get_tables(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req).read().decode('utf-8')
    parser = SimpleHTMLParser()
    parser.feed(html)
    return parser.tables

print("Checking 2025 (47631):")
tables = get_tables("https://coi.hzau.edu.cn/info/1611/47631.htm")
for i, t in enumerate(tables):
    if len(t)>0 and '姓名' in t[0]:
        print(t[0])
        print(t[1])
        break

print("Checking 2023 (33401):")
tables = get_tables("https://coi.hzau.edu.cn/info/1611/33401.htm")
for i, t in enumerate(tables):
    if len(t)>0 and '姓名' in t[0]:
        print(t[0])
        print(t[1])
        break

