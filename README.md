# Amazon List Scraper
### Parse Amazon List Printable URL and save to CSV, optionally show ascii table
#### Note that list must be public

You can clone repository using [github](https://github.com/AlessandroPerazzetta/amazonlist-to-csv.git) and run local:

### Clone sources
```bash
    $ git clone https://github.com/AlessandroPerazzetta/amazonlist-to-csv.git
```
### Create virtual env
```bash
    $ cd amazonlist-to-csv
    $ python3 -m venv venv
    $ source venv/bin/activate
```
### Install dependencies
```bash 
    $ pip install -r requirements.txt
```
#### Dependecies required

```
    - wheel >= 0.41.2
    - requests >= 2.31.0
    - lxml >= 4.9.3
    - bs4 >= 0.0.1
    - prettytable >= 3.9.0
```
## Usage 

```bash
$ ./run.py
Usage:

  run.py -u ....                          # amazon list url to parse
  run.py -c ....                          # (optional) csv filename output
  run.py -d ....                          # (optional) destination output dir
  run.py -t                               # (optional) show ascii table

Examples:

  $ ./run.py -u 'https://www.amazon.it/hz/wishlist/printview/xxxxxx?target=_blank&ref_=lv_pv&filter=unpurchased&sort=default' -c 'out' -d 'outdir' -t`

```

### Replace header env bin from run.py if executed from virtual env

    sed -i -e "s/\/usr\/bin\/python/.\/venv\/bin\/python/g" run.py

### 

---
# 2023/10/06 - Current HTML printable list parseable:
```
    <tr id="tableRow_XXXXXXXXXXXX" class="a-align-center g-print-view-row">
        <td id="itemImage_XXXXXXXXXXXX" class="a-text-center a-align-center g-image">
            <img alt="--" src="https://m.media-amazon.com/images/x/x_.jpg" height="42dp" width="42dp">
        </td>
        <td class="a-align-center">
            <span class="a-text-bold">--</span><br>--- |
        </td>
        <td class="a-align-center"></td>
        <td class="a-text-center a-align-center">
            <span>€ 228,90</span>
        </td>
        <td class="a-text-center a-align-center">
            <span>1</span>
        </td>
        <td class="a-text-center a-align-center">
            <span>0</span>
        </td>
    </tr>
```