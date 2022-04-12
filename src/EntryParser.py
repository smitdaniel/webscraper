import re
from typing import Union, Dict, List, Any
import pandas as pd
from bs4 import Tag


class EntryParser:
    """
    Manages parsing of a BeautifulSoup Tag representing a blog entry
    """

    def __init__(self, entry_tag: Tag):
        """
        :param entry_tag: the entry tag content to parse and convert into EntryParser object
        """
        self.entry_tag: Tag = entry_tag
        self.img_url: str = self._get_image_url()
        self._parse_body()

    def _get_image_url(self) -> str:
        """Get image url for the entry, if any, return 'no image' otherwise"""
        img_tag: Tag = self.entry_tag.find("img")
        if "data-srcset" in img_tag.attrs:
            return img_tag.attrs["data-srcset"].split(" 360w")[0]
        else:
            return "no image"

    def _parse_body(self) -> None:
        """Parse entry body and extract title, link, and description text"""
        entry_punchline: Tag = self.entry_tag.find("div", {"class": "entry-body"}).find("a")
        self.href: str = entry_punchline["href"]
        self.title: str = entry_punchline["title"]
        self.entry_body: str = self.entry_tag.find("p", {"class": "entry-body__text"}).string.strip()
        match = re.search('Mňamka #([0-9]{0,3})', self.title)
        if match:
            if match.group(1):
                self.entry_num: Union[int, str] = int(match.group(1))
        else:
            self.entry_num = "none"

    def as_dict(self) -> Dict[str, Union[str, int]]:
        """Convert the parser content into a dictionary"""
        return {"title": self.title,
                "summary": self.entry_body,
                "url": self.href,
                "img_url": self.img_url,
                "number": self.entry_num}

    @staticmethod
    def entries_to_pandas(entry_list: List[Any]) -> pd.DataFrame:
        """Convert a list of EntryParser objects into a pandas data frame.

        Orders the entries in ascending order. If the ordinal is not available, places those at beginning.
        Removes the ordinals from the final DataFrame.
        """
        def get_int(entry: Dict[str, str]) -> int:
            num = entry['number']
            if isinstance(num, int):
                return num
            else:
                return 0

        entry_dics: List[Dict[str, Union[str, int]]] = [entry.as_dict() for entry in entry_list]
        return pd.DataFrame(sorted(entry_dics, key=get_int)).drop(['number'], axis=1)
