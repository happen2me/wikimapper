import sqlite3
from typing import List, Optional


class WikiMapper:
    """Uses a precomputed database created by `create_wikipedia_wikidata_mapping_db`."""

    def __init__(self, path_to_db: str):
        self._path_to_db = path_to_db

    def title_to_id(self, page_title: str, uncased=False) -> Optional[str]:
        """Given a Wikipedia page title, returns the corresponding Wikidata ID.

        The page title is the last part of a Wikipedia url **unescaped** and spaces
        replaced by underscores , e.g. for `https://en.wikipedia.org/wiki/Fermat%27s_Last_Theorem`,
        the title would be `Fermat's_Last_Theorem`.

        Args:
            page_title: The page title of the Wikipedia entry, e.g. `Manatee`.
            uncased (bool): Whether to ignore case when looking up the title. The speed drops
                significantly when this is set to `True`.

        Returns:
            Optional[str]: If a mapping could be found for `wiki_page_title`, then return
                           it, else return `None`.

        """

        with sqlite3.connect(self._path_to_db) as conn:
            c = conn.cursor()
            command = f"SELECT wikidata_id FROM mapping WHERE wikipedia_title=? {'COLLATE NOCASE' if uncased else ''}"
            c.execute(command, (page_title,))
            results = c.fetchall()

        if len(results) == 0:
            return None
        # Because the UNIQUE constraint on the mapping table is not enforced, we need to
        # check for multiple results and return the first non-None value.
        if any((item[0] for item in results)):
            return next((item[0] for item in results if item[0]))
        return None

    def url_to_id(self, wiki_url: str) -> Optional[str]:
        """Given an URL to a Wikipedia page, returns the corresponding Wikidata ID.

        This is just a convenience function. It is not checked whether the index and
        URL are from the same dump.

        Args:
            wiki_url: The URL to a Wikipedia entry.

        Returns:
            Optional[str]: If a mapping could be found for `wiki_url`, then return
                           it, else return `None`.

        """

        title = wiki_url.rsplit("/", 1)[-1]
        return self.title_to_id(title)

    def id_to_titles(self, wikidata_id: str) -> List[str]:
        """Given a Wikidata ID, return a list of corresponding pages that are linked to it.

        Due to redirects, the mapping from Wikidata ID to Wikipedia title is not unique.

        Args:
            wikidata_id (str): The Wikidata ID to map, e.g. `Q42797`.

        Returns:
            List[str]: A list of Wikipedia pages that are linked to this Wikidata ID.

        """

        with sqlite3.connect(self._path_to_db) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT DISTINCT wikipedia_title FROM mapping WHERE wikidata_id =?", (wikidata_id,)
            )
            results = c.fetchall()

        return [e[0] for e in results]


    def pid_to_id(self, wikipedia_id: str) -> Optional[str]:
        """Given a Wikipedia ID, return the Wikidata ID that is linked to it.

        Args:
            wikipedia_id (str): The Wikidata ID to map, e.g. `339`.

        Returns:
            Optional[str]: The Wikidata ID that is linked to this Wikipedia ID, e.g. `Q132524`.

        """
        with sqlite3.connect(self._path_to_db) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT DISTINCT wikidata_id FROM mapping WHERE wikipedia_id =?", (wikipedia_id,)
            )
            results = c.fetchall()
        if len(results) == 0:
            return None
        else:
            return results[0][0]
