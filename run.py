#!/usr/bin/python
"""Amazon List Parser and save results to CSV"""
from pprint import pprint

import argparse
import textwrap
from datetime import datetime
import csv
import requests
from bs4 import BeautifulSoup
from prettytable import PrettyTable

# HEADERS ={"User-Agent":'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36'}
HEADERS = {"User-Agent": 'FakeAgent/6.9 (FakeOS 1337; FakeOS; xQ) FakeWebKit/0.666 (KHTML, like Gecko) FakeCrawler/0'}

# ** 2023/10/06 - Current HTML Printable List Output Example:

# <tr id="tableRow_XXXXXXXXXXXX" class="a-align-center g-print-view-row">
#     <td id="itemImage_XXXXXXXXXXXX" class="a-text-center a-align-center g-image">
#         <img alt="--" src="https://m.media-amazon.com/images/x/x_.jpg" height="42dp" width="42dp">
#     </td>
#     <td class="a-align-center">
#         <span class="a-text-bold">--</span><br>--- |
#     </td>
#     <td class="a-align-center"></td>
#     <td class="a-text-center a-align-center">
#         <span>€ 228,90</span>
#     </td>
#     <td class="a-text-center a-align-center">
#         <span>1</span>
#     </td>
#     <td class="a-text-center a-align-center">
#         <span>0</span>
#     </td>
# </tr>


def save_content(csv_file='', csv_title='', csv_items=None):
    """Save parsed content to csv file."""

    # current date and time
    now_str = datetime.now().strftime("%Y%m%d%H%M%S")
    # now_str = now.strftime("%Y%m%d%H%M%S")
    csv_file += f"{csv_file}_{now_str}"

    if ".csv" not in csv_file:
        csv_file += ".csv"

    filename = f"{csv_title}_{csv_file}"

    with open(filename, 'w', newline='', encoding="utf-8") as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=';',
                                quotechar='"', quoting=csv.QUOTE_ALL)
        csv_writer.writerow(
            ['Image', 'Description', 'Price', 'Quantity', 'HA']
        )
        for image, description, price, quantity, ha in zip(
                csv_items["images"],
                csv_items["descriptions"],
                csv_items["prices"],
                csv_items["quantities"],
                csv_items["has"]):

            csv_writer.writerow(
                [image, description, price, quantity, ha]
            )


def parse_content(url_to_parse=''):
    """Parse Amazon list and extract all items to separate list."""

    try:
        response = requests.get(
            url_to_parse, headers=HEADERS, timeout=3, verify=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

        title_text = ''
        # ** GET LIST TITLE
        # title = soup.find('h3').find('span').getText()
        # print(title)
        title_header = soup.find('h3')
        if title_header:
            title_text = title_header.find('span').getText()
        else:
            print("No valid data to parse, exiting ...")
            exit()

        if title_text:
            # ** GET IMAGE ROWS
            images_html = soup.find_all('img')
            # for image in images_html:
            #     print(f"IMAGE : {image['src']}")
            images = [image['src'] for image in images_html]
            # pprint(images)

            # ** GET DESCRIPTION ROWS
            # <td class="a-align-center">
            #   <span class="a-text-bold">-----------------</span>
            #   <br>di Fractal Design (Accessorio) |
            # </td>
            descriptions_html = soup.find_all('span', class_='a-text-bold')[5:]
            # for description in descriptions_html:
            #     print(f"DESC : {description.text}")
            descriptions = [
                description.text for description in descriptions_html]
            # pprint(descriptions)

            # ** GET PRICE QUANTITY HA ROWS
            # <td class="a-text-center a-align-center"><span>€ 144,75</span></td>
            prices_quantities_has_html = soup.find_all(
                'td', class_='a-text-center a-align-center')
            # pprint(prices_quantities_has)

            # ** split rows in sublist chuncks
            p_q_h_sublist_chuncks = list(
                divide_chunks(prices_quantities_has_html, 3))

            # ** create separate lists from sublist extracted chunks
            prices_html = extract_item_from_list(p_q_h_sublist_chuncks, 0)
            quantities_html = extract_item_from_list(p_q_h_sublist_chuncks, 1)
            has_html = extract_item_from_list(p_q_h_sublist_chuncks, 2)

            prices = [price.text for price in prices_html]
            quantities = [quantity.text for quantity in quantities_html]
            has = [ha.text for ha in has_html]

            # pprint(prices)
            # for price in prices:
            #     print(f"PRICE : {price.text}")

            # pprint(quantities)
            # for quantity in quantities:
            #     print(f"QUANTITIES : {quantity.text}")

            # pprint(has)
            # for ha in has:
            #     print(f"HA : {ha.text}")

            return title_text, images, descriptions, prices, quantities, has

    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("OOps: Something Else", err)

def show_table(csv_items=None):
    pt = PrettyTable()
    pt.field_names = ['Description', 'Price', 'Quantity', 'HA']
    
    pt.align['Description'] = "l"
    pt.align['Price'] = "c"
    pt.align['Quantity'] = "c"
    pt.align['HA'] = "c"

    for description, price, quantity, ha in zip(
            csv_items["descriptions"],
            csv_items["prices"],
            csv_items["quantities"],
            csv_items["has"]):
        pt.add_row([description, price, quantity, ha])
    print(pt.get_string())

def divide_chunks(lst, n):
    """Yield successive n-sized chunks from lst."""

    # ** looping till length lst
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def extract_item_from_list(lst, idx):
    """Extract item with index idx from sublist list."""

    # # Driver code
    # lst = [[1, 2], [3, 4, 5], [6, 7, 8, 9]]
    # print(Extract(lst))
    # Output:
    #     [1, 3, 6]

    # Unpack version
    # return list(list(zip(*lst))[0])
    # For version
    return [item[idx] for item in lst]


if __name__ == '__main__':
    try:
        # ** Init from config
        URL_TO_PARSE = ''
        CSV_FILE = ''

        # ** Parse command line arguments
        # ** ASCII art is verrrry nice: https://www.asciiart.eu/text-to-ascii-art
        parser = argparse.ArgumentParser(
            description="""
            Amazon List to CSV
            """,
            prog='run.py',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=textwrap.dedent('''\
            example:
                ./run.py -u 'URL' -c 'file.csv' -v

                run with URL, in verbose mode writing results into file.csv.
            '''))
        parser.add_argument('-u', '--url', metavar='URL',
                            help='specify url to parse')
        parser.add_argument('-c', '--csv', metavar='CSV',
                            help='specify csv file to use')
        parser.add_argument('-t', '--table',
                            action="store_true", help='show table')
        parser.add_argument('-v', '--verbose',
                            action="store_true", help='show info')
        args = parser.parse_args()

        # ** Manage URL from args and replace default
        if args.url:
            URL_TO_PARSE = args.url
        else:
            print(f"Error: URL to parse not found")
            exit(0)

        # ** Manage CSV from args and replace default
        if args.csv:
            CSV_FILE = args.csv

        # ** Write to CSV file
        try:
            title, images, descriptions, prices, quantities, has = parse_content(
                URL_TO_PARSE)

            list_items = {
                "images": images,
                "descriptions": descriptions,
                "prices": prices,
                "quantities": quantities,
                "has": has
            }
            save_content(CSV_FILE, title, list_items)

            # ** Show table with parsed content
            if args.table:
                show_table(list_items)

        except Exception as error:
            print(f'ERROR: {repr(error)}')
            raise ValueError("ERROR") from error

    except KeyboardInterrupt:
        exit()
