from urllib.request import urlopen
from bs4 import BeautifulSoup, Tag, ResultSet
from typing import Optional, List
from src.EntryParser import EntryParser
import os
from pathlib import Path


class PageList:
    """
    Parses the provided url and sets up methods to reach any of the pages containing the entries (if many).
    """

    def __init__(self, base_url: str, until_page: Optional[int] = None):
        """
        :param base_url: url to analyze
        :param until_page: the last page of entries to analyze (last available if None)
        """
        self.base_url: str = base_url
        self.base_page: BeautifulSoup = BeautifulSoup(urlopen(base_url), 'html.parser')
        self.last_pagination_item: {Tag: 3} = self.base_page.find("li", {"class": "pagination-last"})
        (self.page_suffix, self.last_page) = self.last_pagination_item.a.attrs["href"].rsplit("?")[1].rsplit("=")
        self.page_suffix: str = "?" + self.page_suffix + "="
        self.last_page: int = int(self.last_page)
        self.until_page: int = int(self.last_page) if until_page is None else min(until_page, self.last_page)

    def get_page(self, page_num: int) -> str:
        """
        :param page_num: number of the page to get url of
        :return: url of the required page
        """
        if page_num not in range(1, self.last_page + 1):
            raise RuntimeError("Requested page number " + str(page_num) + " does not exist in the page list.")
        return self.base_url + self.page_suffix + str(page_num)


class PageParser:
    """
    Manages parsing of the html pages containing entries of a given url, and export of the data.
    """

    def __init__(self, base_url: str, until_page: Optional[int] = None):
        """
        :param base_url: basic url of the site to analyze
        :param until_page: last required page (if many) of entries to analyze; counted from the newest entries
        """
        self.target_url: str = base_url
        self.page_list: PageList = PageList(self.target_url, until_page)

    def get_page_entries(self, page_num: int) -> ResultSet:
        """
        Get entries from the page of provided number in form of BeautifulSoup structures

        :param page_num: number of the page within the catalogue of entries
        :return: ResultSet of entries
        """
        analyze_page: str = self.page_list.get_page(page_num)
        page_soup: BeautifulSoup = BeautifulSoup(urlopen(analyze_page), "html.parser")
        page_entries = page_soup.find_all("div", {"class": "entry-inner"})
        return page_entries

    def parse_page(self, page_num: int) -> List[EntryParser]:
        """Parse entries at the page of provided number into EntryParser objects

        :param page_num: number of the page within the catalogue of entries
        :return: list of EntryParser parsed entries
        """
        return [EntryParser(page_entry) for page_entry in self.get_page_entries(page_num)]

    def parse_url(self) -> List[EntryParser]:
        """
        Parse all available pages for the stored url, until the 'until_page'

        :return: list of all found entries, parsed into EntryParser objects
        """
        all_entries: List[EntryParser] = []
        for ppage in range(1, self.page_list.until_page + 1):
            all_entries = all_entries + self.parse_page(ppage)
        return all_entries

    def parse_and_dump(self, outpath: Optional[str] = None) -> None:
        """
        Parse all available pages for the stored url (until 'until_page'), and dump them into a CSV file

        :param outpath: output path for the csv file, "./out/mnamky.csv" is default
        """
        if not outpath:
            path: Path = Path(os.path.dirname(__file__)).parent / "out/mnamky.csv"
        else:
            path: Path = Path(outpath)
        EntryParser.entries_to_pandas(self.parse_url()).to_csv(path, index=False)
