# ScrapeToLive

## Prerequisites
1) Install [Anaconda](https://docs.anaconda.com/miniconda/)
2) Install [Chrome](https://www.google.com/chrome/)
3) Install [ChromeDriver](https://developer.chrome.com/docs/chromedriver/downloads)
Take care to install a proper version of ChromeDriver that matches your Chrome version. Also add the location of the ChromeDriver to your PATH.

## Setup
1) Create conda env with the following command:
```bash
conda create --name scraping --file req.txt
```
2) Activate the conda env with the following command:
```bash
conda activate scraping
```
3) Update your search parameters in the 'search_parameters.json' file.
4) Start the scraper with the following command:
```bash
python ScraperBase.py
```