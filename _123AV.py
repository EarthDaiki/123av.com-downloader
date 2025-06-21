import requests
from bs4 import BeautifulSoup
import re
from SegmentsDownload import Downloader
import json
import demjson3

import time

class _123AV:
    def __init__(self):
        '''
        Initializes the _123AV class with a persistent HTTP session.
        '''
        self.session = requests.Session()

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
    
    def __get_master_url(self, url):
        '''
        Retrieves the video metadata in JSON format from the video player page.

        Args:
            url (str): The video player page URL.

        Returns:
            dict: A dictionary containing video metadata, including the stream URL.
        '''
        if url is None:
            raise ValueError("url is None.")
        res = self.session.get(url)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            url_element = soup.find(id='player').get('v-scope')
            match = re.search(r'Video\(\d+,\s*({.*})\)', url_element)
            if match:
                json_str = match.group(1)
                json_str = json_str.replace(r'\/', '/')  # スラッシュを正規化
                data = json.loads(json_str)
            return data
        
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
        index_url = url.rsplit('/', 1)[0] + '/qc/v.m3u8'
        return index_url

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
        # Using video_info, get video_id
        video_urls = self.__get_video_urls(video_info['id'])
        if len(video_urls) > 1:
            print(f'The video is split into {len(video_urls)} part(s).')
            print('Download all parts and join them into one video.')

        segment_urls = []
        # Using video_urls, get master url
        for video_url in video_urls:
            master_url = self.__get_master_url(video_url)
            index_url = self.__get_index_url(master_url['stream'])
            urls = self.__get_segments(index_url)
            segment_urls.extend(urls)
        downloader.get_video(segment_urls, outputfolder, title)

'''
By updating, these methods are not used right now.
'''

# def __get_html(self, url):
#     '''
#     Retrieves the full HTML of the video page, including iframe contents,
#     using a headless Chrome browser.

#     Args:
#         url (str): The URL of the 123AV video page.

#     Returns:
#         str: The HTML content of the page.
#     '''
#     if url is None or "":
#         raise ValueError("Video url is None. Set a proper video url.")
#     options = Options()
#     options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36")
#     options.add_argument("--headless=new")
#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
#     driver.get(url)
#     iframe = WebDriverWait(driver, 20).until(
#         EC.presence_of_element_located((By.TAG_NAME, "iframe"))
#     )
#     html = driver.page_source
#     driver.quit()
#     return html

# def __get_video_url(self, html):
#     '''
#     Extracts the video iframe URL from the page's HTML and constructs
#     the video page URL used to access the actual video player.

#     This method is required to get a video.m3u8!!

#     Args:
#         html (str): The HTML content of the original 123AV video page.

#     Returns:
#         str: The constructed video player page URL.
#     '''
#     if html is None:
#         raise ValueError("html is None.")
#     soup = BeautifulSoup(html, "html.parser")
#     url = soup.find("iframe").get('src')
#     return url

# def __get_index_url(self, m3u8_url):
#     '''
#     Retrieves the actual .m3u8 playlist URL from the master playlist.

#     Args:
#         m3u8_url (str): The URL to the master .m3u8 playlist.

#     Returns:
#         str: The full URL to the actual .m3u8 file containing segment list.
#     '''
#     if m3u8_url is None:
#         raise ValueError("m3u8_url is None. Cannot proceed to fetch index URL.")
#     res = self.session.get(m3u8_url)
#     if res.status_code == 200:
#         match = re.search(r'^.*\.m3u8$', res.text, flags=re.MULTILINE)
#         if match:
#             base_url = m3u8_url.rsplit('/', 1)[0]
#             path = match.group()
#             return base_url + '/' + path