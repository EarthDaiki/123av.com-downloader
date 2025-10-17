import requests
from bs4 import BeautifulSoup
import re
from SegmentsDownload import Downloader
import json
import demjson3
from sub_processes.network import _123AVWebManager

import time

class _123AV:
    def __init__(self):
        '''
        Initializes the _123AV class with a persistent HTTP session.
        '''
        self.session = requests.Session()
        self.web_manager = _123AVWebManager()
        self.verify = False
        if not self.verify:
            from urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    def __get_html(self, url):
        '''
        Retrieves the raw static HTML content from the specified URL using a simple HTTP GET request.
        This does not execute any JavaScript and only returns the initial HTML as received from the server,
        before any dynamic content is rendered.

        Args:
            url (str): The target webpage URL.

        Returns:
            bytes: The raw HTML content as bytes if the request is successful.
        '''
        res = self.session.get(url)
        if res.status_code == 200:
            return res.content

    def __get_video_info(self, soup):
        '''
        Extracts video metadata from the given HTML content by parsing the
        Vue `v-scope` attribute associated with the video player.

        Args:
            soup (BeautifulSoup): A parsed BeautifulSoup object of the HTML page.

        Returns:
            dict: A dictionary containing video metadata such as video ID and code.
        '''
        video_info_element = soup.find(id='page-video').get('v-scope')
        # Movie({id: 9133, code: 'FC2-PPV-2430778'})
        match = re.search(r'Movie\(\s*(\{.*?\})\s*\)', video_info_element)
        if match:
            js_object = match.group(1)
            data = demjson3.decode(js_object)
        return data

    def __get_video_urls(self, video_id):
        '''
        Retrieves a list of video player URLs by querying the AJAX endpoint
        for the specified video ID.

        Args:
            video_id (int): The numeric ID of the video (e.g., 9133).

        Returns:
            list: A list of URLs (str) pointing to video player pages.
        '''
        res = self.session.get(f'https://www1.123av.com/ja/ajax/v/{video_id}/videos')
        if res.status_code == 200:
            video_url_info = res.json()
            urls = [info['url'] for info in video_url_info['result']['watch']]
            return urls
        return None
    
    def __get_master_url(self, url):
        '''
        Retrieves the video metadata in JSON format from the video player page.

        Args:
            url (str): The video player page URL.

        Returns:
            dict: A dictionary containing video metadata, including the stream URL.
        '''
        master_url = self.web_manager.get_master_url(url)
        return master_url
        
        
    def __get_segments(self, index_url):
        '''
        Parses the .m3u8 index file and generates a list of .ts video segment URLs.
        Because the urls in .m3u8 index file are .jpeg, .gif, .png, or something like that,
        you need to change the extensions to .ts.

        You can download them as images' extension, but in this method, they are just changed.

        Args:
            index_url (str): The URL to the .m3u8 index file.

        Returns:
            list[str]: A list of .ts segment URLs.
        '''
        if index_url is None:
            raise ValueError("index url is None.")
        res = self.session.get(index_url, verify=self.verify)
        if res.status_code == 200:
            matches = re.findall(r'^(?!#).+', res.text, re.MULTILINE)
            urls = [index_url.rsplit('/', 1)[0] + '/' + match.rsplit('.', 1)[0] + '.ts' for match in matches]
            return urls
        else:
            raise Exception(f"Failed to get index_url: {res.status_code}")
        
    def __get_index_url(self, url):
        '''
        Constructs the index (master playlist) URL for the HLS video stream.

        Given a full HLS stream segment URL, this function removes the last path segment
        and appends the relative path to the master `.m3u8` playlist file.

        Args:
            url (str): The full HLS video segment URL.

        Returns:
            str: The constructed URL pointing to the master `.m3u8` playlist.
        '''
        max_res = 0
        res = requests.get(url)
        if res.status_code == 200:
            lines = res.text.strip().splitlines()
            for i, line in enumerate(lines):
                if "RESOLUTION=" in line:
                    # 例: RESOLUTION=1920x1080 → 幅と高さを取得
                    res_str = line.split("RESOLUTION=")[1].split(",")[0]
                    w, h = map(int, res_str.split("x"))
                    pixels = w * h  # 総画素数を比較
                    if pixels > max_res:
                        max_res = pixels
                        if i + 1 < len(lines):
                            index_url = lines[i + 1]
                            
            return url.rsplit('/', 1)[0] + '/' + index_url

    def __get_safe_title(self, soup, max_length=100):
        '''
        Extracts the title from the HTML and replaces any characters that
        are invalid in file names with underscores.

        Args:
            soup (BeautifulSoup): A parsed BeautifulSoup object of the HTML page.
            max_length (int, optional): Maximum length of the returned filename. Defaults to 100.

        Returns:
            str: A sanitized title string safe for use as a filename.
        '''
        if soup is None: 
            raise ValueError("soup is None.")
        title = soup.find("h1")
        if title is None:
            raise ValueError("check the url!")
        if max_length:
            return re.sub(r'[\\/*?:"<>|\'() ]', '_', title.text)[:max_length]
        return re.sub(r'[\\/*?:"<>|\'() ]', '_', title.text)
    
    def dl(self, url, outputfolder):
        '''
        Coordinates the full download process: retrieves video metadata,
        constructs the video stream URLs, and downloads the segments
        to the specified folder using a Downloader.

        Args:
            url (str): The 123AV video page URL.
            outputfolder (raw str): The folder where the video will be saved.
        '''
        downloader = Downloader()
        html = self.__get_html(url)
        soup = BeautifulSoup(html, "html.parser")
        title = self.__get_safe_title(soup)

        video_info = self.__get_video_info(soup)
        print(f"video info: {video_info}")
        # Using video_info, get video_id
        video_urls = self.__get_video_urls(video_info['id'])
        if len(video_urls) > 1:
            print(f'The video is split into {len(video_urls)} part(s).')
            print('Download all parts and join them into one video.')

        segment_urls = []
        if video_urls is None:
            raise ValueError("could not get video urls.")
        # Using video_urls, get master url
        for index, video_url in enumerate(video_urls):
            print(f"URL: {url}")
            master_url = self.__get_master_url(url)
            print(f"MASTER URL: {master_url}")
            index_url = self.__get_index_url(master_url)
            print(f"INDEX URL: {index_url}")
            urls = self.__get_segments(index_url)
            segment_urls.extend(urls)
            if index < len(video_urls) - 1:
                self.web_manager.click(index + 1)
        downloader.get_video(segment_urls, outputfolder, title)