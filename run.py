#!/usr/bin/python
"""Amazon List Parser and save results to CSV"""
from pprint import pprint

import argparse
import textwrap
from datetime import datetime
import csv
import os
from enum import Enum
from urllib.parse import urlparse, unquote
import requests
from bs4 import BeautifulSoup
from prettytable import PrettyTable
from prettytable.colortable import ColorTable, Themes, Theme

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

def create_dir(new_dir):
    """Try to create dir."""
    try:
        os.makedirs(new_dir)
    except FileExistsError:
        # directory already exists
        pass
    except OSError as create_dir_error:
        print(f"Error: Unable to create directory {new_dir}: {create_dir_error}")
        exit(0)

def save_content(dst_dir='', csv_file='', csv_title='', csv_items=None, save_images=False):
    """Save parsed content to csv file."""

    # current date and time
    now_str = datetime.now().strftime("%Y%m%d%H%M%S")
    # now_str = now.strftime("%Y%m%d%H%M%S")
    if csv_file:
        csv_file = f"{csv_file}_{now_str}"
    else:
        csv_file = f"{now_str}"

    if ".csv" not in csv_file:
        csv_file += ".csv"

    filename = f"{dst_dir}/{csv_title}_{csv_file}"

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
            if save_images:
                images_dst_dir = f"{dst_dir}/{csv_title}/"
                create_dir(images_dst_dir)
                save_image(images_dst_dir, image)

def save_image(dst_dir='', image_url=''):
    """Save images from url."""
    # filename = unquote(urlparse(image_url).path)
    image_filename = unquote(urlparse(image_url).path.split("/")[-1])
    filename = f"{dst_dir}/{image_filename}"

    with open(filename, 'wb') as handle:
        response = requests.get(image_url, stream=True, timeout=5)

        if not response.ok:
            print(response)

        for block in response.iter_content(1024):
            if not block:
                break

            handle.write(block)

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

class Styles(Enum):
    """Table Styles definition."""
    DEFAULT =       Theme(default_color="", vertical_color="", horizontal_color="", junction_color="")
    OCEANYELLOW =   Theme(default_color="22", vertical_color="33", horizontal_color="44", junction_color="55")
    LINES =         Theme(default_color="1", vertical_color="9", horizontal_color="9", junction_color="9")
    LIGHT =         Theme(default_color="7", vertical_color="", horizontal_color="", junction_color="")
    DARK =          Theme(default_color="2", vertical_color="7", horizontal_color="7", junction_color="7")
    BLINK =         Theme(default_color="5", vertical_color="5", horizontal_color="5", junction_color="5")
    DARKBGRED =     Theme(default_color="31", vertical_color="41", horizontal_color="41", junction_color="41")
    DARKBGGREEN =   Theme(default_color="32", vertical_color="42", horizontal_color="42", junction_color="42")
    DARKBGYELLOW =  Theme(default_color="33", vertical_color="43", horizontal_color="43", junction_color="43")
    DARKBGBLU =     Theme(default_color="34", vertical_color="44", horizontal_color="44", junction_color="44")
    DARKBGMAGENTA = Theme(default_color="35", vertical_color="45", horizontal_color="45", junction_color="45")
    DARKBGCYANO =   Theme(default_color="36", vertical_color="46", horizontal_color="46", junction_color="46")
    DARKBGGRAY =    Theme(default_color="37", vertical_color="47", horizontal_color="47", junction_color="47")

    BGRED =         Theme(default_color="91", vertical_color="7", horizontal_color="7", junction_color="7")
    BGGREEN =       Theme(default_color="92", vertical_color="7", horizontal_color="7", junction_color="7")
    BGYELLOW =      Theme(default_color="93", vertical_color="7", horizontal_color="7", junction_color="7")
    BGBLU =         Theme(default_color="94", vertical_color="7", horizontal_color="7", junction_color="7")
    BGMAGENTA =     Theme(default_color="95", vertical_color="7", horizontal_color="7", junction_color="7")
    BGCYANO =       Theme(default_color="96", vertical_color="7", horizontal_color="7", junction_color="7")
    BGGRAY =        Theme(default_color="97", vertical_color="7", horizontal_color="7", junction_color="7")

    TEST =          Theme(default_color="5", vertical_color="5", horizontal_color="5", junction_color="5")

def show_all_themes():
    """
    0: normal
    1: white
    2: gray
    3: italic
    4: underline
    5: blink
    6: blink
    7: bgwhite_fgblack
    8: bgblack_fgblack
    9: strike
    10-20: normal
    21: double underline
    22-29: normal
    30: dark_black
    31: dark_red
    32: dark_green
    33: dark_yellow
    34: dark_blu
    35: dark_magenta
    36: dark_cyano
    37: dark_gray
    38-39: normal
    40: bgdark_black_fgwhite
    41: bgdark_red_fgwhite
    42: bgdark_green_fgwhite
    43: bgdark_yellow_fgwhite
    44: bgdark_blu_fgwhite
    45: bgdark_magenta_fgwhite
    46: bgdark_cyano_fgwhite
    47: bgdark_gray_fgwhite
    48-52: normal
    53: upperline
    54-89: normal
    90: light_black
    91: light_red
    92: light_green
    93: light_yellow
    94: light_blu
    95: light_magenta
    96: light_cyano
    97: light_gray
    98-99: normal
    100: bgblack_fgwhite
    101: bgdarkred_fgwhite
    102: bgdarkgreen_fgwhite
    103: bgdarkyellow_fgwhite
    104: bgdarkblu_fgwhite
    105: bgdarkmagenta_fgwhite
    106: bgdarkcyano_fgwhite
    107: bgdarkgray_fgwhite
    108-255: normal
    """
    for i in range(0,255):
        print(f"Current index: {str(i)}")
        pt = ColorTable(theme=Theme(default_color=str(i),
                                    vertical_color=str(i),
                                    horizontal_color=str(i),
                                    junction_color=str(i)))
        if pt:
            pt.field_names = ['FieldA', 'FieldB', 'FieldC']

            pt.align['FieldA'] = "l"
            pt.align['FieldB'] = "c"
            pt.align['FieldC'] = "c"

            for r in range(0,3):
                pt.add_row(['FieldA', 'FieldB', 'FieldC'])

            print(pt.get_string())

def get_theme(style=None):
    """Get theme for table."""
    if style:
        style = str(style).upper()
        styles = [member.name for member in Styles]
        if style in styles:
            return Styles[style].value
        else:
            return Styles['DEFAULT'].value

def show_table(csv_items=None, table_style=None):
    """Show table from content."""
    pt = None
    if table_style is not None:
        # print("Colortable")
        # pt = ColorTable(theme=Themes.OCEAN)
        pt = ColorTable(theme=get_theme(table_style))
    else:
        # print("Prettytable")
        pt = PrettyTable()

    if pt:
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
        SAVE_IMAGES = False
        DST_DIR = ''

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
                ./run.py -u 'URL' -c 'file.csv' -d 'dest_dir' -t -s 'STYLE'

                run with URL, in verbose mode writing results into file.csv.
            '''))
        parser.add_argument('-u', '--url', metavar='URL',
                            help='specify url to parse')
        parser.add_argument('-c', '--csv', metavar='CSV',
                            help='specify csv file to use')
        parser.add_argument('-i', '--images',
                            action="store_true", help='save images from content')
        parser.add_argument('-d', '--dst', metavar='DST',
                            help='specify csv dst dir to use')
        parser.add_argument('-t', '--table',
                            action="store_true", help='show table')
        parser.add_argument('-s', '--style', metavar='STYLE',
                            help='specify table style')
        parser.add_argument('-ds', '--debugstyles',
                            action="store_true", help='debug color themes')
        parser.add_argument('-v', '--verbose',
                            action="store_true", help='show info')
        args = parser.parse_args()

        # ** Debug colors for table and exit
        if args.debugstyles:
            show_all_themes()
            exit(0)

        # ** Manage URL from args and replace default
        if args.url:
            URL_TO_PARSE = args.url
        else:
            print("Error: URL to parse not found")
            exit(0)

        # ** Manage CSV from args and replace default
        if args.csv:
            CSV_FILE = args.csv

        # ** Manage images from args and replace default
        if args.images:
            SAVE_IMAGES = args.images

        # ** Manage DST from args and replace default
        if args.dst:
            create_dir(args.dst)
            DST_DIR = args.dst

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
            save_content(DST_DIR, CSV_FILE, title, list_items, SAVE_IMAGES)

            # ** Manage images from args and replace default
            USER_STYLE = None
            if args.style:
                USER_STYLE = args.style

            # ** Show table with parsed content
            if args.table:
                show_table(list_items, USER_STYLE)

        except Exception as error:
            print(f'ERROR: {repr(error)}')
            raise ValueError("ERROR") from error

    except KeyboardInterrupt:
        exit()
