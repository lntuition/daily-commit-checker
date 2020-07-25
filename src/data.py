import os
import pytablewriter as ptw
import requests
import statistics

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from pytablewriter.style import Style as ptwStyle
from textwrap import dedent
from typing import Any, Dict, List, Tuple


class DataManager():
    # Constants
    DATE_FORMAT = "%Y-%m-%d"
    DATE_IDX = 0

    def __init__(self, username: str, start: str, end: str) -> None:
        self.username = username
        self.start = start
        self.end = end

        self.start_dt = datetime.strptime(start, self.DATE_FORMAT)
        self.end_dt = datetime.strptime(end, self.DATE_FORMAT)

    @staticmethod
    def _get_formatted_dt(year: int, week: int):
        return f"Week {week} of {year}"

    # After python 3.6 dict acts like OrderedDict
    def _crawl_data(self) -> Dict[datetime, int]:
        raw_data = {}

        start_year = self.start_dt.year
        end_year = self.end_dt.year

        for year in range(start_year, end_year + 1):
            response = requests.get(
                f"https://github.com/{self.username}?from={year}-01-01")
            soup = BeautifulSoup(response.text, "html.parser")

            for info in soup.select(".day"):
                dt = datetime.strptime(info["data-date"], self.DATE_FORMAT)
                if self.start_dt <= dt <= self.end_dt:
                    raw_data[dt] = int(info["data-count"])

        return raw_data

    def generate_report(self, save_path: str) -> None:
        raw_data = self._crawl_data()

        # Header Section
        header = dedent(f""" 
            # Welcome to {self.username}'s Contribution Report
            This report is auto generated by [daily-contribution-checker](https://github.com/lntuition/daily-contribution-checker).
            If you have any question or problem, please report [here](https://github.com/lntuition/daily-contribution-checker/issues).
            I hope this report will be a companion for your contribution trip :airplane:

        """)

        # Summary Section
        max_dt = self.start_dt
        max_cnt = 0

        continous_start = self.start_dt
        continous_len = 0
        tmp_continous_start = self.start_dt
        tmp_continous_len = 0

        for dt, cnt in raw_data.items():
            if cnt > max_cnt:
                max_dt = dt
                max_cnt = cnt

            if cnt > 0:
                tmp_continous_len += 1
                if tmp_continous_len == 1:
                    tmp_continous_start = dt
            else:
                tmp_continous_len = 0

            if tmp_continous_len > continous_len:
                continous_start = tmp_continous_start
                continous_len = tmp_continous_len
        continous_end = continous_start + timedelta(days=max(continous_len-1,0))

        cnt_list = [value for value in raw_data.values()]
        
        cur_len = 0
        for cnt in reversed(cnt_list):
            if cnt == 0:
                break
            cur_len += 1
        cur_start = self.end_dt - timedelta(days=max(cur_len-1, 0))

        summary = dedent(f"""
            ## Summary
            - **{self.end}** is **{(self.end_dt - self.start_dt).days + 1}th day** since the start of trip
            - During the trip, total contribution count is **{sum(cnt_list)}** 
            and average contribution count is **{statistics.mean(cnt_list):.2f}**
            - daily maximum contribution day is **{max_dt.strftime(self.DATE_FORMAT)}**, which is **{max_cnt:d}**.
            - Longest continous contribution trip was **{continous_len}** days 
            From **{continous_start.strftime(self.DATE_FORMAT)}** to **{continous_end.strftime(self.DATE_FORMAT)}** :walking:
            - Current continous contribution trip is **{cur_len}** days 
            From **{cur_start.strftime(self.DATE_FORMAT)}** :running:
            - There was **{cnt_list[-1] if cnt_list[-1] > 0 else "NO"}** new contribution at **{self.end}**.
            {"Good job :+1:" if cnt_list[-1] > 0 else "Cheer up :muscle:"}
        """)

        # TODO : Graph Section
        graph = dedent(f"""
            ## Graph
            - Graph is not implemented yet, please wait a moment :sweat_smile: 
        """)

        # Table Section
        writer = ptw.MarkdownTableWriter()
        writer.headers = ["DATE", "MON", "TUE",
                          "WED", "THU", "FRI", "SAT", "SUN"]
        writer.table_name = None
        writer.column_styles = [ptwStyle(align="center")] * 8
        writer.margin = 1
        writer.value_matrix = []

        for dt, cnt in raw_data.items():
            year, week, day = dt.isocalendar()
            formatted_dt = self._get_formatted_dt(year=year, week=week)

            if not writer.value_matrix or writer.value_matrix[-1][self.DATE_IDX] != formatted_dt:
                writer.value_matrix.append([formatted_dt] + [""] * 7)

            writer.value_matrix[-1][day] = cnt

        # pytablewriter dumps without front blank, so dedent doesn't work well
        table = f"""
## Contribution table
{writer.dumps(flavor="github")}
        """

        with open(save_path, "w") as fp:
            fp.write(header)
            fp.write(summary)
            fp.write(graph)
            fp.write(table)
